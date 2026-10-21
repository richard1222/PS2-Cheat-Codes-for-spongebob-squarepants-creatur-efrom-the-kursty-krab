#!/usr/bin/env python3
"""Read-only PS2 MIPS ELF audit: segment ranges, offset/VA mapping, debug-string hits.

Never writes to, executes, or patches an input executable.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from pathlib import Path

DEFAULT_TERMS = ('debugpad', 'showfps', 'debugCamera', 'debugfont',
                 'Free Camera', 'nodebugoutput', 'DebugPackage', 'frontend_devpackage')

class ElfError(ValueError):
    pass

def _check_region(blob: bytes, start: int, size: int, description: str) -> None:
    if start < 0 or size < 0 or start > len(blob) or size > len(blob) - start:
        raise ElfError(f'{description} extends past end of ELF file')

def parse_elf(blob: bytes) -> dict:
    _check_region(blob, 0, 52, 'ELF header')
    if blob[:4] != b'\x7fELF':
        raise ElfError('not an ELF file')
    if blob[4] != 1 or blob[6] != 1:
        raise ElfError('expected ELF32 version 1')
    if blob[5] not in (1, 2):
        raise ElfError('unsupported ELF endianness')
    endian = '<' if blob[5] == 1 else '>'
    (kind, machine, version, entry, phoff, shoff, flags, ehsize,
     phentsize, phnum, shentsize, shnum, shstrndx) = struct.unpack_from(endian+'HHIIIIIHHHHHH', blob, 16)
    if machine != 8:
        raise ElfError(f'expected MIPS ELF (e_machine=8), got {machine}')
    if ehsize < 52 or phnum == 0 or phentsize < 32:
        raise ElfError('bad ELF header or missing program headers')
    _check_region(blob, phoff, phentsize*phnum, 'program-header table')
    segments=[]
    for n in range(phnum):
        ptype, off, vaddr, paddr, filesz, memsz, perm, align = struct.unpack_from(
            endian+'IIIIIIII', blob, phoff+n*phentsize)
        if ptype != 1:  # PT_LOAD only
            continue
        _check_region(blob, off, filesz, f'LOAD segment {n}')
        if memsz < filesz or vaddr + memsz > 0x100000000:
            raise ElfError(f'invalid LOAD segment {n} memory range')
        segments.append({'index': n, 'file_offset': off, 'vaddr': vaddr,
                         'filesz': filesz, 'memsz': memsz, 'flags': perm,
                         'readable': bool(perm & 4), 'writable': bool(perm & 2),
                         'executable': bool(perm & 1)})
    if not segments:
        raise ElfError('no PT_LOAD segments found')
    return {'bits':32,'endian':'little' if endian=='<' else 'big',
            'entry':entry,'type':kind,'machine':machine,'segments':segments}

def file_to_vaddr(elf: dict, offset: int) -> int | None:
    if offset < 0: raise ValueError('negative offset')
    matches=[s['vaddr']+(offset-s['file_offset']) for s in elf['segments']
             if s['file_offset'] <= offset < s['file_offset']+s['filesz']]
    if len(set(matches)) > 1:
        raise ElfError(f'ambiguous file offset 0x{offset:X}: multiple LOAD segments')
    return matches[0] if matches else None

def vaddr_to_file(elf: dict, vaddr: int) -> int | None:
    if vaddr < 0: raise ValueError('negative address')
    matches=[s['file_offset']+(vaddr-s['vaddr']) for s in elf['segments']
             if s['vaddr'] <= vaddr < s['vaddr']+s['filesz']]
    if len(set(matches)) > 1:
        raise ElfError(f'ambiguous virtual address 0x{vaddr:X}: multiple LOAD segments')
    return matches[0] if matches else None

def audit(blob: bytes, terms=DEFAULT_TERMS, max_hits=100, offsets=(), addresses=()) -> dict:
    if max_hits < 1: raise ValueError('max_hits must be >= 1')
    elf=parse_elf(blob)
    results=[]
    lower=blob.lower()
    for term in terms:
        if not term or not term.isascii():raise ValueError('search terms must be nonempty ASCII')
        needle=term.encode('ascii').lower()
        pos=0;found=0;hits=[]
        while (pos:=lower.find(needle,pos))!=-1:
            found+=1
            if len(hits)<max_hits:
                va=file_to_vaddr(elf,pos)
                hits.append({'file_offset':f'0x{pos:X}',
                             'vaddr':None if va is None else f'0x{va:08X}',
                             'in_load_segment':va is not None})
            pos+=1
        results.append({'term':term,'count':found,'hits':hits,
                        'truncated':found>len(hits)})
    foff={f'0x{x:X}':None if (a:=file_to_vaddr(elf,x)) is None else f'0x{a:08X}' for x in offsets}
    vaddr={f'0x{x:08X}':None if (a:=vaddr_to_file(elf,x)) is None else f'0x{a:X}' for x in addresses}
    return {'sha256':hashlib.sha256(blob).hexdigest(),'file_size':len(blob),
            'elf':elf,'strings':results,'file_offset_to_vaddr':foff,
            'vaddr_to_file_offset':vaddr,
            'note':'File offsets/addresses are specific to this exact SHA-256. Static strings alone do not prove reachable debug functionality.'}

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('elf',type=Path,help='Original SLUS_213.91, or other MIPS ELF')
    parser.add_argument('--term',action='append',dest='terms')
    parser.add_argument('--file-offset',action='append',type=lambda x:int(x,0),default=[])
    parser.add_argument('--vaddr',action='append',type=lambda x:int(x,0),default=[])
    parser.add_argument('--max-hits',type=int,default=100)
    parser.add_argument('--json',type=Path,help='Write research report, not patched binary')
    args=parser.parse_args()
    try:
        report=audit(args.elf.read_bytes(),args.terms or DEFAULT_TERMS,
                     args.max_hits,args.file_offset,args.vaddr)
    except (ElfError,ValueError,OSError) as ex:
        parser.exit(2,f'Could not audit ELF: {ex}\n')
    encoded=json.dumps(report,indent=2)+'\n'
    if args.json:args.json.write_text(encoded,encoding='utf-8')
    else:print(encoded,end='')
if __name__=='__main__':main()
