"""Deterministic release packaging tests."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from build_release import FILES,PACKAGE,package

class PackagingTests(unittest.TestCase):
    def test_reproducible_zip_with_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a.zip';b=Path(d)/'b.zip'
            one=package(a);two=package(b)
            self.assertEqual(one,two)
            self.assertEqual(a.read_bytes(),b.read_bytes())
            with ZipFile(a) as z:
                names=z.namelist()
                self.assertEqual(len(names),len(set(names)))
                self.assertTrue(all(n.startswith(PACKAGE+'/') for n in names))
                m=z.read(f'{PACKAGE}/MANIFEST.sha256').decode('ascii')
                for line in m.splitlines():
                    digest,filename=line.split('  ',1)
                    self.assertEqual(hashlib.sha256(z.read(f'{PACKAGE}/{filename}')).hexdigest(),digest)
    def test_disallow_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'release.zip';package(p)
            with self.assertRaises(FileExistsError):package(p)
    def test_no_game_data_in_package(self):
        self.assertTrue(all(not f.lower().endswith(('.iso','.nds','.elf','.exe','.bin','.zip','.prx')) for f in FILES))
        self.assertTrue(all('__pycache__' not in f for f in FILES))
if __name__=='__main__':unittest.main()
