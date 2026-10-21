import struct
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from arm9_string_xrefs import locate, pc_relative_ldr_target

class StringXrefsTests(unittest.TestCase):
    def test_find_real_style_positive_ldr(self):
        # 0x02000000: E59F0008 -> literal at +16; literal -> 0x02000020
        data=bytearray(0x40)
        struct.pack_into('<I',data,0,0xE59F0008)
        struct.pack_into('<I',data,16,0x02000020)
        data[32:45]=b'DEBUG OPTIONS'
        r=locate(data,0x02000000,('DEBUG OPTIONS',))
        x=r['entries'][0]
        self.assertEqual(x['candidate_ldr_xrefs'][0]['instruction_address'],'0x02000000')
        self.assertEqual(x['candidate_ldr_xrefs'][0]['literal_slot_address'],'0x02000010')
    def test_negative_ldr(self):
        self.assertEqual(pc_relative_ldr_target(0xE51F000C,0x2000020),0x200001C)
    def test_reject_str_and_register_ldr(self):
        self.assertIsNone(pc_relative_ldr_target(0xE58F0008,0x2000000))
        self.assertIsNone(pc_relative_ldr_target(0xE79F0000,0x2000000))
    def test_no_made_up_references(self):
        r=locate(b'GAME SELECT hello',0x02000000,('GAME SELECT',))
        self.assertEqual(r['entries'][0]['candidate_ldr_xrefs'],[])
    def test_reject_overflow(self):
        with self.assertRaises(ValueError): locate(b'12345',0xfffffffc)
    def test_case_insensitive_matching(self):
        r=locate(b'debug options\x00',0x02000000,('DEBUG OPTIONS',))
        self.assertEqual(r['occurrences']['DEBUG OPTIONS'],1)
if __name__=='__main__':unittest.main()
