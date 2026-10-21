import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from collect_menu_evidence import inventory

class MenuArchiveTests(unittest.TestCase):
    def fixture(self):
        b=bytearray(256)
        name=b'pause menu world.ps2\0'
        struct.pack_into('<13I',b,0,0,1,1,1,64,0,0,0,0,0,96,len(name),32)
        struct.pack_into('<8I',b,64,160,0,4,0,1,0,0,0)
        b[96:96+len(name)]=name;b[160:164]=b'TEST'
        return b
    def run_inventory(self,b):return inventory(lambda o,n:bytes(b[o:o+n]),len(b))
    def test_menu_inventory(self):
        b=self.fixture();before=bytes(b)
        r=self.run_inventory(b)
        self.assertEqual(r['entries'][0]['name'],'pause menu world.ps2')
        self.assertEqual(r['entries'][0]['offset'],160)
        self.assertEqual(b,before)
    def test_bad_extent(self):
        b=self.fixture();struct.pack_into('<I',b,64,255)
        with self.assertRaises(ValueError):self.run_inventory(b)
    def test_bad_name(self):
        b=self.fixture();struct.pack_into('<I',b,76,999)
        with self.assertRaises(ValueError):self.run_inventory(b)
    def test_bad_header(self):
        b=self.fixture();struct.pack_into('<I',b,4,0)
        with self.assertRaises(ValueError):self.run_inventory(b)

    def test_short_record_layout(self):
        b=self.fixture();struct.pack_into('<I',b,48,20)
        self.assertEqual(self.run_inventory(b)['method'],1)

    def test_iso_collection_and_no_overwrite(self):
        import tempfile
        from zipfile import ZipFile
        from collect_menu_evidence import collect
        from test_v05 import iso_fixture,record
        b=bytearray(iso_fixture())
        existing=record(b'SLUS_213.91;1',21,1024)
        at=20*2048+34+len(existing)
        rec=record(b'ALLPAKS.PS2;1',24,256)
        b[at:at+len(rec)]=rec
        b.extend(self.fixture())
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'original.iso';dst=Path(td)/'menu.zip'
            src.write_bytes(b)
            result=collect(src,dst)
            self.assertEqual(result['packages'],1)
            with ZipFile(dst) as z:self.assertEqual(z.read('packages/000.ps2'),b'TEST')
            before=dst.read_bytes()
            with self.assertRaises(FileExistsError):collect(src,dst)
            self.assertEqual(dst.read_bytes(),before)
            self.assertEqual(src.read_bytes(),b)
