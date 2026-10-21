"""Release interface integration tests; synthetic fixtures only."""
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from spongebob import VERSION, ToolError, load_bounded, save_report, run, build_parser
from test_v05 import elf_fixture, iso_fixture

CLI = ROOT / 'tools' / 'spongebob.py'

class ToolkitReleaseTests(unittest.TestCase):
    def invoke(self, *argv):
        return subprocess.run([sys.executable, str(CLI), *map(str, argv)],
                              text=True, capture_output=True, timeout=15, cwd=ROOT)

    def test_version(self):
        p=self.invoke('--version')
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn('1.1.0',p.stdout)

    def test_help_has_subcommands(self):
        p=self.invoke('--help')
        self.assertEqual(p.returncode,0)
        for x in ('doctor','scan-elf','scan-iso','scan-arm9'):
            self.assertIn(x,p.stdout)

    def test_doctor_does_not_install(self):
        p=self.invoke('doctor')
        self.assertEqual(p.returncode,0,p.stderr)
        a=json.loads(p.stdout)
        self.assertEqual(a['toolkit_version'], VERSION)
        self.assertIn('capstone',a['optional_python'])
        self.assertIn('unicorn',a['optional_python'])

    def test_elf_report_and_no_input_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            original=bytes(elf_fixture())
            src=Path(d)/'SLUS_213.91';src.write_bytes(original)
            out=Path(d)/'report.json'
            p=self.invoke('scan-elf',src,'--term','debugpad','--json',out)
            self.assertEqual(p.returncode,0,p.stderr)
            r=json.loads(out.read_text())
            self.assertEqual(r['toolkit_version'],'1.1.0')
            self.assertTrue(r['read_only'])
            self.assertEqual(len(r['report']['mips_string_xrefs']['strings'][0]['hits'][0]['references']),1)
            self.assertEqual(src.read_bytes(),original)

    def test_iso_cli_audit(self):
        with tempfile.TemporaryDirectory() as d:
            original=iso_fixture()
            src=Path(d)/'game.iso';src.write_bytes(original)
            p=self.invoke('scan-iso',src)
            self.assertEqual(p.returncode,0,p.stderr)
            report=json.loads(p.stdout)['report']
            self.assertEqual(report['boot_file']['lba'],21)
            self.assertEqual(src.read_bytes(),original)

    def test_iso_missing_boot_not_false_success(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'missing.iso';src.write_bytes(iso_fixture(missing=True))
            p=self.invoke('scan-iso',src)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertFalse(json.loads(p.stdout)['report']['boot_found'])

    def test_arm9_cli(self):
        with tempfile.TemporaryDirectory() as d:
            data=bytearray(64)
            data[32:45]=b'DEBUG OPTIONS'
            struct.pack_into('<I',data,0,0xE59F0008)
            struct.pack_into('<I',data,16,0x02000020)
            src=Path(d)/'arm9.bin';src.write_bytes(data)
            p=self.invoke('scan-arm9',src,'--term','DEBUG OPTIONS')
            self.assertEqual(p.returncode,0,p.stderr)
            result=json.loads(p.stdout)['report']
            self.assertEqual(len(result['entries'][0]['candidate_ldr_xrefs']),1)
            self.assertEqual(src.read_bytes(),data)

    def test_input_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'input.elf';original=bytes(elf_fixture())
            src.write_bytes(original)
            p=self.invoke('scan-elf',src,'--json',src)
            self.assertEqual(p.returncode,2)
            self.assertIn('over input',p.stderr)
            self.assertEqual(src.read_bytes(),original)

    def test_existing_report_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'input.elf';src.write_bytes(elf_fixture())
            report=Path(d)/'report.json';report.write_text('user data')
            p=self.invoke('scan-elf',src,'--json',report)
            self.assertEqual(p.returncode,2)
            self.assertIn('already exists',p.stderr)
            self.assertEqual(report.read_text(),'user data')

    def test_broken_elf_reports_error(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'broken.elf';src.write_bytes(b'NOT AN ELF')
            p=self.invoke('scan-elf',src)
            self.assertEqual(p.returncode,2)
            self.assertIn('blocked:',p.stderr)

    def test_missing_file_reports_error(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.invoke('scan-iso',Path(d)/'missing.iso')
            self.assertEqual(p.returncode,2)

    def test_limit_rejects_files_exceeding_limit(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'file';src.write_bytes(b'a'*10)
            with self.assertRaises(ToolError):load_bounded(src,9)

    def test_invalid_limits(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'sample.elf';src.write_bytes(elf_fixture())
            self.assertEqual(self.invoke('scan-elf',src,'--lookahead','100').returncode,2)
            self.assertEqual(self.invoke('scan-elf',src,'--max-hits','0').returncode,2)

    def test_deterministic_json(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'sample.elf';src.write_bytes(elf_fixture())
            a=self.invoke('scan-elf',src,'--term','debugpad')
            b=self.invoke('scan-elf',src,'--term','debugpad')
            self.assertEqual(a.stdout,b.stdout)

    def test_report_exclusive_creation(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'new.json'
            save_report({'a':1},out,None)
            with self.assertRaises(ToolError):save_report({'a':2},out,None)
            self.assertEqual(json.loads(out.read_text())['a'],1)

if __name__=='__main__':unittest.main()
