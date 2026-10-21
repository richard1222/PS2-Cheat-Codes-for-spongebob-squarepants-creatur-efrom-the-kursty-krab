"""Regression checks: prevent false MIPS xrefs and inaccurate scan counts."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from ps2_mips_string_xrefs import analyze
from test_v05 import elf_fixture


class MipsStringReferenceRegression(unittest.TestCase):
    def _sequence_has_reference(self, intermediate):
        blob = elf_fixture()
        struct.pack_into('<I', blob, 0x104, intermediate)
        # Valid ADDIU using the LUI base, but it must not match if the
        # intermediate instruction already replaced that register.
        struct.pack_into('<I', blob, 0x108, (9 << 26) | (4 << 21) | (4 << 16) | 0x120)
        result = analyze(bytes(blob), ('debugpad',))
        return bool(result['strings'][0]['hits'][0]['references'])

    def test_special2_mul_overwrites_base_register(self):
        # SPECIAL2 MUL r4,r9,r10 writes rd=4 but not rt=10.
        mul = (28 << 26) | (9 << 21) | (10 << 16) | (4 << 11) | 2
        self.assertFalse(self._sequence_has_reference(mul))

    def test_ll_load_overwrites_base_register(self):
        # LL r4,0(r8), opcode 48, overwrites rt=4.
        load_linked = (48 << 26) | (8 << 21) | (4 << 16)
        self.assertFalse(self._sequence_has_reference(load_linked))

    def test_sc_writes_result_to_base_register(self):
        # SC r4,0(r8), opcode 56, writes success indicator to rt=4.
        store_conditional = (56 << 26) | (8 << 21) | (4 << 16)
        self.assertFalse(self._sequence_has_reference(store_conditional))

    def test_loaded_hits_count_is_not_capped(self):
        blob = elf_fixture()
        blob[0x230:0x239] = b'debugpad\0'
        result = analyze(bytes(blob), ('debugpad',), max_hits=1)['strings'][0]
        self.assertEqual(result['total_file_occurrences'], 2)
        self.assertEqual(result['loaded_occurrences'], 2)
        self.assertEqual(len(result['hits']), 1)
        self.assertTrue(result['truncated'])


if __name__ == '__main__':
    unittest.main()
