import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from arm_binary_to_mips_v03 import translate_safe

class SafeConverterTests(unittest.TestCase):
    def test_register_block_ok(self):
        b=struct.pack('<5I',0xE3A00005,0xE2801003,0xE3510008,0x0AFFFFFF,0xE12FFF1E)
        asm,rep=translate_safe(b,0x02000000,0,5)
        self.assertEqual(rep['status'],'generated_research_only')
        self.assertIn('beq $v0, $v1',asm)
    def test_ds_mmio_block(self):
        b=struct.pack('<3I',0xE3A0C301,0xE58CC208,0xEB000093)
        asm,rep=translate_safe(b,0x02000850,0,3)
        self.assertIsNone(asm)
        self.assertTrue(any('0x04000208' in x for x in rep['reasons']))
        self.assertTrue(any('function calls' in x for x in rep['reasons']))
    def test_any_memory_block(self):
        b=struct.pack('<I',0xE5901000)
        asm,rep=translate_safe(b,0x02000000,0,1)
        self.assertIsNone(asm)
        self.assertIn('unmapped memory',rep['reasons'][0])
    def test_conditional_branch_without_recent_cmp_block(self):
        b=struct.pack('<4I',0xE3500001,0xE3A01000,0x0AFFFFFF,0xE12FFF1E)
        asm,rep=translate_safe(b,0x02000000,0,4)
        self.assertIsNone(asm)
        self.assertIn('flag lifetime',rep['reasons'][0])
    def test_bl_block(self):
        b=struct.pack('<I',0xEB000000)
        asm,rep=translate_safe(b,0x02000000,0,1)
        self.assertIsNone(asm)
if __name__=='__main__':unittest.main()
