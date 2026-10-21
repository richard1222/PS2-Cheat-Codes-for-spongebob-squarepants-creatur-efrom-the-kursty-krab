#!/usr/bin/env python3
"""Deterministic, source-only release packaging with embedded SHA-256 manifest."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

VERSION='1.1.0'
ROOT=Path(__file__).resolve().parents[1]
PACKAGE=f'spongebob-toolkit-v{VERSION}'
FILES=('README.md','RELEASE_NOTES.md','requirements-optional.txt',
       'tools/spongebob.py','tools/build_release.py','tools/nds_probe.py','tools/ps2_data_xrefs.py','tools/collect_menu_evidence.py',
       'tools/arm9_call_context.py','tools/arm9_llvm_disasm.py',
       'tools/arm9_string_xrefs.py','tools/arm_binary_to_mips.py',
       'tools/arm_binary_to_mips_v03.py','tools/check_optional_deps.py',
       'tools/ps2_elf_audit.py','tools/ps2_iso_probe.py',
       'tools/ps2_mips_string_xrefs.py',
       'tests/test_arm9_string_xrefs.py','tests/test_v03_guard.py',
       'tests/test_v04.py','tests/test_v05.py','tests/test_v10_cli.py',
       'tests/test_v10_release.py','tests/test_v10_bugfixes.py','tests/test_nds_probe.py','tests/test_ps2_data_xrefs.py','tests/test_menu_evidence.py')

def package(target:Path, root:Path=ROOT):
    source={}
    for filename in FILES:
        p=root / filename
        if not p.is_file() or p.is_symlink():
            raise ValueError(f'missing or symlinked source file: {filename}')
        source[filename]=p.read_bytes()
    manifest=''.join(f'{hashlib.sha256(source[name]).hexdigest()}  {name}\n'
                     for name in sorted(source)).encode('ascii')
    source['MANIFEST.sha256']=manifest
    if target.exists():raise FileExistsError(f'release ZIP exists: {target}')
    with ZipFile(target,'x',compression=ZIP_DEFLATED,compresslevel=9) as archive:
        for name in sorted(source):
            info=ZipInfo(f'{PACKAGE}/{name}',date_time=(2020,1,1,0,0,0))
            info.create_system=3
            info.external_attr=(0o100644<<16)
            info.compress_type=ZIP_DEFLATED
            archive.writestr(info,source[name],compress_type=ZIP_DEFLATED,compresslevel=9)
    return hashlib.sha256(target.read_bytes()).hexdigest()

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('output',type=Path)
    args=cli.parse_args()
    try:print('SHA-256:',package(args.output))
    except (OSError,ValueError) as e:cli.exit(2,str(e)+'\n')

if __name__=='__main__':main()
