import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ps2_data_xrefs import inspect_addresses
from test_v05 import elf_fixture

class DataReferenceTests(unittest.TestCase):
    def fixture(self, middle=0):
        d=bytearray(elf_fixture())
        struct.pack_into('<III',d,0x100,0x3c040010,middle,0x8c850120)
        return d
    def test_load_and_read_only(self):
        d=self.fixture();before=bytes(d)
        row=inspect_addresses(d,[0x100120])['addresses'][0]
        self.assertEqual(row['memory_access_count'],1)
        self.assertEqual(row['memory_accesses'][0]['kind'],'LW')
        self.assertEqual(d,before)
    def test_clobber_blocks_match(self):
        row=inspect_addresses(self.fixture(0x24040000),[0x100120])['addresses'][0]
        self.assertEqual(row['memory_access_count'],0)
    def test_branch_blocks_match(self):
        row=inspect_addresses(self.fixture(0x10000001),[0x100120])['addresses'][0]
        self.assertEqual(row['memory_access_count'],0)
    def test_signed_offset(self):
        d=self.fixture();struct.pack_into('<III',d,0x100,0x3c040011,0,0x8c858120)
        row=inspect_addresses(d,[0x108120])['addresses'][0]
        self.assertEqual(row['memory_access_count'],1)
    def test_pointer_count_and_cap(self):
        d=self.fixture();struct.pack_into('<II',d,0x230,0x100120,0x100120)
        row=inspect_addresses(d,[0x100120],max_hits=1)['addresses'][0]
        self.assertEqual(row['pointer_count'],2);self.assertTrue(row['truncated'])
        self.assertEqual(len(row['pointer_slots']),1)
    def test_invalid_limits(self):
        for args in [([],6,100),([0x100000000],6,100),([1],0,100),([1],6,0)]:
            with self.assertRaises(ValueError):inspect_addresses(self.fixture(),*args)
