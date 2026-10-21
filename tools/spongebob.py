#!/usr/bin/env python3
"""SpongeBob research toolkit v1.0: read-only PS2 and DS analysis CLI.

This is not a retail-game patcher, ARM-to-MIPS engine port, or debug ISO builder.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path
from arm9_call_context import context
from ps2_elf_audit import ElfError, audit
from ps2_iso_probe import ISOError, inspect_iso
from ps2_mips_string_xrefs import analyze

VERSION = '1.0.0'
MAX_ELF = 64 * 1024 * 1024
MAX_ARM = 32 * 1024 * 1024

class ToolError(ValueError):
    pass


def load_bounded(path: Path, limit: int) -> bytes:
    """Refuse large files instead of reading unlimited bytes."""
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ToolError(f'input exceeds {limit:,} byte limit')
    return data


def save_report(report: dict, output: Path | None, input_path: Path | None) -> None:
    document = json.dumps(report, indent=2, sort_keys=True) + '\n'
    if output is None:
        print(document, end='')
        return
    if input_path and output.resolve() == input_path.resolve():
        raise ToolError('refusing to write report over input file')
    # Exclusive creation protects existing reports and symlinks. Do not fall
    # back to write mode, including when encountering filesystem errors.
    try:
        with output.open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(document)
    except FileExistsError as exc:
        raise ToolError('report already exists; choose a new output filename') from exc


def _health(name: str) -> dict:
    spec = importlib.util.find_spec(name)
    if spec is None:
        return {'installed': False, 'optional': True}
    try:
        mod = __import__(name)
        return {'installed': True, 'optional': True,
                'version': str(getattr(mod, '__version__', 'unknown'))}
    except Exception as exc:
        return {'installed': False, 'optional': True,
                'error': type(exc).__name__}


def doctor() -> dict:
    return {'toolkit_version': VERSION, 'python': sys.version.split()[0],
            'minimum_python': '3.10', 'optional_python': {
                'capstone': _health('capstone'), 'unicorn': _health('unicorn')},
            'optional_commands': {'clang': shutil.which('clang') is not None,
                                  'llvm-objdump': shutil.which('llvm-objdump') is not None},
            'status': 'core tools use Python standard library; optional packages are not required'}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=VERSION)
    subs = parser.add_subparsers(dest='command', required=True)
    d = subs.add_parser('doctor', help='Check optional dependencies (never installs)')
    d.add_argument('--json', type=Path)
    e = subs.add_parser('scan-elf', help='Read-only MIPS ELF string and xref analysis')
    e.add_argument('input', type=Path)
    e.add_argument('--term', dest='terms', action='append')
    e.add_argument('--lookahead', type=int, default=6)
    e.add_argument('--max-hits', type=int, default=100)
    e.add_argument('--json', type=Path)
    i = subs.add_parser('scan-iso', help='Read-only 2048-byte ISO9660 PS2 boot analysis')
    i.add_argument('input', type=Path)
    i.add_argument('--boot-name', default='SLUS_213.91')
    i.add_argument('--no-xrefs', action='store_true')
    i.add_argument('--json', type=Path)
    a = subs.add_parser('scan-arm9', help='Read-only DS ARM9 menu xrefs and call context')
    a.add_argument('input', type=Path)
    a.add_argument('--base', type=lambda s: int(s, 0), default=0x02000000)
    a.add_argument('--term', dest='terms', action='append')
    a.add_argument('--radius', type=int, default=12)
    a.add_argument('--max-hits', type=int, default=100)
    a.add_argument('--json', type=Path)
    return parser


def run(args: argparse.Namespace) -> dict:
    if args.command == 'doctor':
        return doctor()
    if args.command == 'scan-iso':
        result = inspect_iso(args.input, args.boot_name, not args.no_xrefs)
    elif args.command == 'scan-elf':
        if not 1 <= args.max_hits <= 10000:
            raise ToolError('--max-hits must be between 1 and 10000')
        if not 1 <= args.lookahead <= 64:
            raise ToolError('--lookahead must be between 1 and 64')
        from ps2_elf_audit import DEFAULT_TERMS as ELF_TERMS
        data = load_bounded(args.input, MAX_ELF)
        result = {'elf_audit': audit(data, args.terms or ELF_TERMS, args.max_hits),
                  'mips_string_xrefs': analyze(data, args.terms or ELF_TERMS,
                                              args.lookahead, args.max_hits)}
    elif args.command == 'scan-arm9':
        if not 1 <= args.max_hits <= 10000:
            raise ToolError('--max-hits must be between 1 and 10000')
        if not 0 <= args.radius <= 256:
            raise ToolError('--radius must be between 0 and 256')
        from arm9_string_xrefs import DEFAULT_TERMS as ARM_TERMS
        data = load_bounded(args.input, MAX_ARM)
        result = context(data, args.base, args.terms or ARM_TERMS,
                         args.radius, args.max_hits)
        result['sha256'] = hashlib.sha256(data).hexdigest()
    else:
        raise ToolError('unknown command')
    return {'toolkit_version': VERSION, 'command': args.command,
            'read_only': True, 'report': result}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = run(args)
        save_report(report, args.json,
                    getattr(args, 'input', None))
    except (ToolError, ElfError, ISOError, ValueError, OSError) as exc:
        parser.exit(2, f'Toolkit blocked: {exc}\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
