import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from arm_binary_to_mips import decode, inspect, generate

class BinaryBridgeTests(unittest.TestCase):
    def test_arm_words_to_mips(self):
        words=[0xE3A00005,0xE2801003,0xE3510008,0x0A000000,0xE3A00000,0xE12FFF1E]
        inst=inspect(struct.pack('<6I',*words),0x02000000,0,6)
        asm=generate(inst)
        self.assertIn('li $t0, 5',asm)
        self.assertIn('addiu $t1, $t0, 3',asm)
        self.assertIn('beq $v0, $v1, L_02000014',asm)
        self.assertIn('L_02000014:',asm)
        self.assertIn('jr $ra',asm)
    def test_real_arm9_entry_first_mov(self):
        i=decode(0xE3A0C301,0x02000850)
        self.assertTrue(i.supported)
        self.assertIn('li $s2, 67108864',generate([i]))
    def test_real_arm9_entry_str(self):
        i=decode(0xE58CC208,0x02000854)
        self.assertTrue(i.supported)
        self.assertIn('sw $s2, 520($s2)',generate([i]))
    def test_reject_bl(self):
        i=decode(0xEB000093,0x02000858)
        self.assertFalse(i.supported)
        with self.assertRaisesRegex(ValueError,'unsupported'): generate([i])
    def test_reject_condition_flags(self):
        self.assertFalse(decode(0xE2900001,0).supported)
    def test_cmp_snapshot(self):
        inst=inspect(struct.pack('<4I',0xE3500001,0xE3A00003,0x0AFFFFFF,0xE12FFF1E),0,0,4)
        output=generate(inst)
        self.assertLess(output.index('move $v0, $t0'),output.index('li $t0, 3'))
    def test_immediate_rotate(self):
        self.assertEqual(decode(0xE3A0C301,0).operands[-1],('imm',0x4000000))
    def test_reject_branch_outside(self):
        with self.assertRaisesRegex(ValueError,'outside'):generate([decode(0xEA000000,0)])
    def test_reject_misaligned_memory(self):
        with self.assertRaisesRegex(ValueError,'unaligned'):generate([decode(0xE5910002,0)])
if __name__=='__main__':unittest.main()
