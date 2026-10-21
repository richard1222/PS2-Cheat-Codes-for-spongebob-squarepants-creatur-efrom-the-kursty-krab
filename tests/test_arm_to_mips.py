import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from arm_to_mips import translate,TranslationError
class TranslationTests(unittest.TestCase):
    def test_arithmetic(self):
        s=translate("MOV r0, #5\nADD r1, r0, #3\nSUB r2, r1, r0\nBX lr")
        self.assertIn("addu $t1, $t0, $at",s)
        self.assertIn("jr $ra",s)
    def test_branch(self):
        s=translate("CMP r0, #1\nBEQ yes\nBNE no")
        self.assertIn("beq $t0, $at, yes",s)
    def test_reject_load(self):
        with self.assertRaises(TranslationError): translate("LDR r0, [r1]")
    def test_reject_pc(self):
        with self.assertRaises(TranslationError): translate("MOV pc, r0")
    def test_reject_branch_without_cmp(self):
        with self.assertRaises(TranslationError): translate("BEQ yes")
if __name__=="__main__": unittest.main()
