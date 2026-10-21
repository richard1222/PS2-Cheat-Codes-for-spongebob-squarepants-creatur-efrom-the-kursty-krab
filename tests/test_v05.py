"""Synthetic ELF and ISO fixtures: no copyrighted game bytes needed."""
import struct
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ps2_mips_string_xrefs import analyze,address_from_pair
from ps2_iso_probe import ISOError, inspect_iso, _decode_record


def elf_fixture(endian='<',high=0x0010,low=0x0120,op=9):
    """Executable at 0x00100000, text at 0x100; debugpad at virtual 0x00100120."""
    b=bytearray(0x400)
    b[:4]=b'\x7fELF';b[4]=1;b[5]=1 if endian=='<' else 2;b[6]=1
    struct.pack_into(endian+'HHIIIIIHHHHHH',b,16,2,8,1,0x00100000,52,0,0,52,32,1,40,0,0)
    struct.pack_into(endian+'IIIIIIII',b,52,1,0x100,0x00100000,0x00100000,0x200,0x200,5,0x100)
    # virtual string address 0x00100120 corresponds to file 0x220
    b[0x220:0x229]=b'debugpad\0'
    lui=(15<<26)|(4<<16)|(high & 0xFFFF)
    lowword=(op<<26)|(4<<21)|(4<<16)|(low & 0xFFFF)
    struct.pack_into(endian+'I',b,0x100,lui)
    struct.pack_into(endian+'I',b,0x104,lowword)
    return b


def record(name: bytes,lba:int,size:int,flags=0):
    # ISO9660 directory record, even length
    length=33+len(name)
    if length%2:length+=1
    b=bytearray(length)
    b[0]=length
    b[2:6]=lba.to_bytes(4,'little');b[6:10]=lba.to_bytes(4,'big')
    b[10:14]=size.to_bytes(4,'little');b[14:18]=size.to_bytes(4,'big')
    b[25]=flags;b[28:30]=(1).to_bytes(2,'little');b[30:32]=(1).to_bytes(2,'big')
    b[32]=len(name);b[33:33+len(name)]=name
    return b


def iso_fixture(*,missing=False,broken_extent=False,bad_sector=False):
    elf=bytes(elf_fixture())
    image=bytearray(24*2048)
    pvd=16*2048
    image[pvd:pvd+7]=b'\x01CD001\x01'
    image[pvd+156:pvd+190]=record(b'\x00',20,2048,flags=2)
    root=20*2048
    name=b'NOT_FOUND.;1' if missing else b'SLUS_213.91;1'
    image[root:root+34]=record(b'\x00',20,2048,flags=2)
    item=record(name,999 if broken_extent else 21,len(elf))
    image[root+34:root+34+len(item)]=item
    image[21*2048:21*2048+len(elf)]=elf
    if bad_sector:image[pvd:pvd+7]=b'NOTISO!'
    return bytes(image)


class MipsScannerTests(unittest.TestCase):
    def test_direct_lui_addiu(self):
        r=analyze(bytes(elf_fixture()),('debugpad',))
        ref=r['strings'][0]['hits'][0]['references'][0]
        self.assertEqual(ref['lui_address'],'0x00100000')
        self.assertEqual(ref['low_address'],'0x00100004')
        self.assertEqual(ref['kind'],'ADDIU')
        self.assertEqual(ref['register'],'a0')
    def test_big_endian(self):
        r=analyze(bytes(elf_fixture('>')),('debugpad',))
        self.assertEqual(len(r['strings'][0]['hits'][0]['references']),1)
    def test_ori_low(self):
        r=analyze(bytes(elf_fixture(op=13)),('debugpad',))
        self.assertEqual(r['strings'][0]['hits'][0]['references'][0]['kind'],'ORI')
    def test_sign_extend_low(self):
        self.assertEqual(address_from_pair((15<<26)|(4<<16)|0x11,
                           (9<<26)|(4<<21)|(4<<16)|0x8120)[0],0x00108120)
    def test_sign_extension_for_string(self):
        # string 0x00100120 formed as 0x00110000 + (-0xFEE0)
        b=elf_fixture(high=0x0011,low=0x0120)  # positive, not matching
        self.assertEqual(analyze(bytes(b),('debugpad',))['strings'][0]['hits'][0]['references'],[])
        b=elf_fixture(high=0x0011,low=0x8120)
        # 0x00110000 - 0x7EE0 = 0x00108120, not 0x00100120
        self.assertEqual(analyze(bytes(b),('debugpad',))['strings'][0]['hits'][0]['references'],[])
        b=elf_fixture(high=0x0011,low=0x8120)
        # change string virtual address to 0x00108120 outside ELF -> no refs
        self.assertEqual(len(analyze(bytes(b),('debugpad',))['strings'][0]['hits'][0]['references']),0)
    def test_skips_clobbered_lui_register(self):
        b=elf_fixture()
        struct.pack_into('<I',b,0x104,0x24040000)  # addiu a0, zero,0 clobbers a0
        struct.pack_into('<I',b,0x108,0x24840120)  # addiu a0,a0,0x120
        self.assertEqual(analyze(bytes(b),('debugpad',))['strings'][0]['hits'][0]['references'],[])
    def test_stops_at_jal(self):
        b=elf_fixture()
        struct.pack_into('<I',b,0x104,0x0C000001)
        struct.pack_into('<I',b,0x108,(9<<26)|(4<<21)|(4<<16)|0x0120)
        self.assertEqual(analyze(bytes(b),('debugpad',))['strings'][0]['hits'][0]['references'],[])
    def test_load_with_gap(self):
        b=elf_fixture()
        struct.pack_into('<I',b,0x104,0)  # NOP
        struct.pack_into('<I',b,0x108,(9<<26)|(4<<21)|(4<<16)|0x0120)
        self.assertEqual(len(analyze(bytes(b),('debugpad',))['strings'][0]['hits'][0]['references']),1)
    def test_ignore_nonloaded_string(self):
        b=elf_fixture()
        b[0x340:0x349]=b'debugpad\0'
        report=analyze(bytes(b),('debugpad',))['strings'][0]
        self.assertEqual(report['total_file_occurrences'],2)
        self.assertEqual(len(report['hits']),1)
    def test_no_match_for_bad_lui(self):
        b=elf_fixture()
        struct.pack_into('<I',b,0x100,0)
        self.assertEqual(analyze(bytes(b),('debugpad',))['strings'][0]['hits'][0]['references'],[])
    def test_reject_invalid_bounds(self):
        with self.assertRaises(ValueError):analyze(bytes(elf_fixture()),lookahead=0)
        with self.assertRaises(ValueError):analyze(bytes(elf_fixture()),max_hits=0)
    def test_reject_missing_elf(self):
        with self.assertRaises(ValueError):analyze(b'not elf')

class ISOProbeTests(unittest.TestCase):
    def check_bytes(self,data,**kwargs):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'test.iso';path.write_bytes(data)
            return inspect_iso(path,**kwargs)
    def test_root_boot_audit(self):
        r=self.check_bytes(iso_fixture())
        self.assertTrue(r['boot_found'])
        self.assertEqual(r['boot_file']['lba'],21)
        self.assertEqual(r['boot_file']['iso_offset'],21*2048)
        self.assertEqual(r['elf_audit']['strings'][0]['term'],'debugpad')
        self.assertEqual(len(r['mips_debug_string_xrefs']['strings'][0]['hits'][0]['references']),1)
    def test_no_patch(self):
        data=iso_fixture()
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'test.iso';path.write_bytes(data)
            inspect_iso(path)
            self.assertEqual(path.read_bytes(),data)
    def test_missing(self):
        r=self.check_bytes(iso_fixture(missing=True))
        self.assertFalse(r['boot_found'])
        self.assertNotIn('elf_audit',r)
    def test_bad_image(self):
        with self.assertRaises(ISOError):self.check_bytes(iso_fixture(bad_sector=True))
    def test_extent_outside_image(self):
        with self.assertRaises(ISOError):self.check_bytes(iso_fixture(broken_extent=True))
    def test_invalid_name(self):
        with self.assertRaises(ISOError):self.check_bytes(iso_fixture(),boot_name='../SLUS_213.91')
    def test_bad_733_extent(self):
        bad=bytearray(record(b'X',2,50))
        bad[6:10]=(3).to_bytes(4,'big')
        with self.assertRaises(ISOError):_decode_record(bad)
    def test_disable_xrefs(self):
        r=self.check_bytes(iso_fixture(),enable_xrefs=False)
        self.assertNotIn('mips_debug_string_xrefs',r)
    def test_cap_executable(self):
        with self.assertRaises(ISOError):self.check_bytes(iso_fixture(),max_file_bytes=20)

if __name__=='__main__':unittest.main()
