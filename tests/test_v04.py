import sys
import struct
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ps2_elf_audit import ElfError,parse_elf,file_to_vaddr,vaddr_to_file,audit
from arm9_call_context import sign24_branch,classify,context


def mock_elf(endian='<',second=False):
    b=bytearray(0x300)
    b[:4]=b'\x7fELF'; b[4]=1; b[5]=1 if endian=='<' else 2;b[6]=1
    phnum=2 if second else 1
    struct.pack_into(endian+'HHIIIIIHHHHHH',b,16,2,8,1,0x100000,52,0,0,52,32,phnum,40,0,0)
    struct.pack_into(endian+'IIIIIIII',b,52,1,0x100,0x100000,0x100000,0x60,0x70,5,0x100)
    if second:
        struct.pack_into(endian+'IIIIIIII',b,84,1,0x200,0x200000,0x200000,0x40,0x50,6,0x100)
    b[0x120:0x120+8]=b'debugpad'
    b[0x130:0x130+7]=b'showfps'
    return bytes(b)

class ELFTests(unittest.TestCase):
    def test_parse_mips_little_and_big(self):
        for endian in ('<','>'):
            elf=parse_elf(mock_elf(endian))
            self.assertEqual(elf['entry'],0x100000)
            self.assertEqual(file_to_vaddr(elf,0x120),0x100020)
            self.assertEqual(vaddr_to_file(elf,0x100020),0x120)
    def test_bss_not_backed_by_file(self):
        self.assertIsNone(vaddr_to_file(parse_elf(mock_elf()),0x100065))
    def test_offsets_outside_load(self):
        self.assertIsNone(file_to_vaddr(parse_elf(mock_elf()),0x90))
    def test_multiple_segments(self):
        elf=parse_elf(mock_elf(second=True))
        self.assertEqual(vaddr_to_file(elf,0x200012),0x212)
        self.assertEqual(file_to_vaddr(elf,0x220),0x200020)
    def test_debug_string_hash_and_addresses(self):
        r=audit(mock_elf(),('debugpad','showfps'),offsets=(0x120,0x90),addresses=(0x100020,0x100065))
        self.assertEqual(r['strings'][0]['hits'][0]['vaddr'],'0x00100020')
        self.assertIsNone(r['file_offset_to_vaddr']['0x90'])
        self.assertIsNone(r['vaddr_to_file_offset']['0x00100065'])
        self.assertEqual(len(r['sha256']),64)
    def test_bad_elf_rejected(self):
        with self.assertRaises(ElfError):parse_elf(b'not elf')
    def test_truncated_segment_rejected(self):
        b=bytearray(mock_elf())
        struct.pack_into('<I',b,52+16,0x10000)
        with self.assertRaises(ElfError):parse_elf(b)
    def test_bad_machine_rejected(self):
        b=bytearray(mock_elf())
        struct.pack_into('<H',b,18,40)
        with self.assertRaises(ElfError):parse_elf(b)
    def test_ambiguous_vaddr_mapping_rejected(self):
        b=bytearray(mock_elf(second=True))
        struct.pack_into('<I',b,84+8,0x100000)
        with self.assertRaises(ElfError):vaddr_to_file(parse_elf(b),0x100020)

class ARMContextTests(unittest.TestCase):
    def test_branch_target_backward(self):
        self.assertEqual(sign24_branch(0xEAFFFFFE,0x02000850),0x02000850)
    def test_bl_classification(self):
        x=classify(0xEB000000,0x100)
        self.assertEqual(x['kind'],'BL')
        self.assertEqual(x['target'],'0x00000108')
    def test_literal_and_nearby_call(self):
        b=bytearray(100)
        struct.pack_into('<I',b,0,0xE59F0008) # LDR r0,[PC,8] reads slot 0x10
        struct.pack_into('<I',b,8,0xEB000001) # BL ... nearby
        struct.pack_into('<I',b,16,0x02000050)
        b[80:93]=b'DEBUG OPTIONS'
        r=context(bytes(b),0x02000000,('DEBUG OPTIONS',),radius=3)
        xs=r['entries'][0]['candidate_ldr_xrefs']
        self.assertEqual(len(xs),1)
        self.assertEqual(xs[0]['nearby_calls'][0]['target'],'0x02000014')
        self.assertEqual(xs[0]['nearby_instructions'][0]['is_anchor'],True)
    def test_no_nearby_calls_claimed(self):
        r=context(b'HELLO\0',0,('HELLO',))
        self.assertEqual(r['entries'][0]['candidate_ldr_xrefs'],[])

if __name__=='__main__':unittest.main()

class OptionalLLVMTests(unittest.TestCase):
    @unittest.skipUnless(__import__('shutil').which('clang') and __import__('shutil').which('llvm-objdump'),
                         'Clang/LLVM objdump unavailable')
    def test_real_instruction_encoding_disassembly(self):
        from arm9_llvm_disasm import disassemble
        src=struct.pack('<4I',0xE92D4010,0xE1A04000,0xE3A02023,0xE12FFF1E)
        result=disassemble(src,0x02004234,0,4)
        self.assertIn('push',result)
        self.assertIn('mov',result)
        self.assertIn('bx',result)
        self.assertIn('#35',result)

    def test_window_bounds_rejected(self):
        from arm9_llvm_disasm import disassemble
        with self.assertRaises(ValueError):disassemble(b'1234',0x02000000,0,200)
