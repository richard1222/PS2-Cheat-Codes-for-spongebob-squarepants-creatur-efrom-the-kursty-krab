import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from nds_probe import inspect_nds

class NdsProbeTests(unittest.TestCase):
    def fixture(self):
        data=bytearray(1024)
        struct.pack_into('<4I',data,0x20,512,0x02000000,0x02000000,512)
        data[544:557]=b'DEBUG OPTIONS'
        struct.pack_into('<I',data,512,0xE59F0008)
        struct.pack_into('<I',data,528,0x02000020)
        return data
    def test_header_and_xref(self):
        data=self.fixture();before=bytes(data)
        report=inspect_nds(data,['DEBUG OPTIONS'])
        self.assertEqual(report['arm9']['size'],512)
        self.assertEqual(len(report['arm9_debug_analysis']['entries'][0]['candidate_ldr_xrefs']),1)
        self.assertEqual(data,before)
    def test_truncated_extent(self):
        with self.assertRaises(ValueError):inspect_nds(self.fixture()[:600],[])
    def test_entry_outside_arm9(self):
        data=self.fixture();struct.pack_into('<I',data,0x24,0)
        with self.assertRaises(ValueError):inspect_nds(data,[])
