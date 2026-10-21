import struct, sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from arm9_string_xrefs import locate,pc_relative_ldr_target
from arm_binary_to_mips_v03 import translate_safe

class XrefTests(unittest.TestCase):
    def test_positive_ldr_xref(self):
        data=bytearray(64)
        struct.pack_into('<I',data,0,0xE59F0008)
        struct.pack_into('<I',data,16,0x02000020)
        data[32:45]=b'DEBUG OPTIONS'
        x=locate(data,0x02000000,('DEBUG OPTIONS',))['entries'][0]
        self.assertEqual(x['candidate_ldr_xrefs'][0]['instruction_address'],'0x02000000')
    def test_negative_ldr(self):
        self.assertEqual(pc_relative_ldr_target(0xE51F000C,0x02000020),0x0200001C)
    def test_reject_store(self):
        self.assertIsNone(pc_relative_ldr_target(0xE58F0008,0x02000000))
    def test_reject_register_offset(self):
        self.assertIsNone(pc_relative_ldr_target(0xE79F0000,0x02000000))
    def test_no_invented_xrefs(self):
        self.assertEqual(locate(b'GAME SELECT',0x02000000,('GAME SELECT',))['entries'][0]['candidate_ldr_xrefs'],[])
    def test_address_overflow(self):
        with self.assertRaises(ValueError):locate(b'12345',0xfffffffc)
    def test_case_insensitive(self):
        self.assertEqual(locate(b'debug options',0,('DEBUG OPTIONS',))['occurrences']['DEBUG OPTIONS'],1)

class SafeTranslationTests(unittest.TestCase):
    def test_register_block(self):
        b=struct.pack('<5I',0xE3A00005,0xE2801003,0xE3510008,0x0AFFFFFF,0xE12FFF1E)
        asm,rep=translate_safe(b,0x02000000,0,5)
        self.assertEqual(rep['status'],'generated_research_only')
        self.assertIn('beq $v0, $v1',asm)
    def test_ds_hardware_block(self):
        b=struct.pack('<3I',0xE3A0C301,0xE58CC208,0xEB000093)
        asm,rep=translate_safe(b,0x02000850,0,3)
        self.assertIsNone(asm)
        self.assertTrue(any('0x04000208' in s for s in rep['reasons']))
    def test_unknown_memory_block(self):
        asm,rep=translate_safe(struct.pack('<I',0xE5901000),0,0,1)
        self.assertIsNone(asm)
        self.assertIn('unmapped memory',rep['reasons'][0])
    def test_flags_lifetime_block(self):
        b=struct.pack('<4I',0xE3500001,0xE3A01000,0x0AFFFFFF,0xE12FFF1E)
        asm,rep=translate_safe(b,0,0,4)
        self.assertIsNone(asm)
        self.assertIn('flag lifetime',rep['reasons'][0])
    def test_call_block(self):
        asm,rep=translate_safe(struct.pack('<I',0xEB000000),0,0,1)
        self.assertIsNone(asm)

if __name__=='__main__':unittest.main()
