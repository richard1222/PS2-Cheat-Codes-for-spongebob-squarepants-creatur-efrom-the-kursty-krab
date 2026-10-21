#!/usr/bin/env python3
"""ARM9 literal-pool xref scanner for small, lawfully held NDS binaries.

Matches ASCII strings, little-endian 32-bit pointers to those strings, and
candidate ARM A32 PC-relative LDR instructions referencing those pointer slots.
These are static CANDIDATES, not proven function boundaries or executable paths.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import struct
from pathlib import Path

DEFAULT_TERMS = ('DEBUG OPTIONS', 'game_select_', 'levelselect', 'stageselect',
                 'debug', 'TEST INTRO UI', 'free camera')


def pc_relative_ldr_target(word: int, address: int) -> int | None:
    """Return literal effective address for A32 LDR Rt,[pc, +/- #imm12]."""
    # cond=0b1111 is special/unconditional-instruction space; do not decode.
    if word >> 28 == 15:
        return None
    # class [27:26] = 01, I=0, P=1, B=0, W=0, L=1, Rn=15
    if (word & 0x0F7F0000) != 0x051F0000:
        return None
    signed = (word & 0xFFF) * (1 if word & (1 << 23) else -1)
    return (((address + 8) & ~3) + signed) & 0xFFFFFFFF


def locate(blob: bytes, base: int, terms=DEFAULT_TERMS, limit=250) -> dict:
    if base % 4:
        raise ValueError('base address must be 4-byte aligned')
    if not (0 <= base <= 0xffffffff) or base + len(blob) > 0x100000000:
        raise ValueError('binary does not fit 32-bit address range')
    if limit < 1:
        raise ValueError('limit must be positive')
    words = [(i, struct.unpack_from('<I', blob, i)[0]) for i in range(0, len(blob) - 3, 4)]
    # Group candidate LDRs by the absolute word address they could read.
    ldrs_by_slot: dict[int, list[tuple[int, int]]] = {}
    for off, word in words:
        target = pc_relative_ldr_target(word, base + off)
        if target is not None and base <= target <= base + len(blob) - 4:
            ldrs_by_slot.setdefault(target, []).append((base + off, word))
    matches=[]
    summary={}
    search=blob.lower()
    word_offsets: dict[int, list[int]] = {}
    for off, word in words:
        word_offsets.setdefault(word, []).append(base+off)
    for term in terms:
        if not term or not term.isascii():
            raise ValueError('terms must be non-empty ASCII strings')
        raw=term.encode('ascii')
        needle=raw.lower()
        cursor=0; occurrences=[]
        while (idx:=search.find(needle,cursor)) != -1:
            occurrences.append(idx)
            cursor=idx+1
        summary[term] = len(occurrences)
        for idx in occurrences[:limit]:
            string_addr = base + idx
            ptrslots=word_offsets.get(string_addr, [])
            xrefs=[]
            for slot in ptrslots:
                for ldr_pc,ldr_word in ldrs_by_slot.get(slot,[]):
                    xrefs.append({'instruction_address':f'0x{ldr_pc:08X}',
                                  'opcode':f'0x{ldr_word:08X}',
                                  'literal_slot_address':f'0x{slot:08X}'})
            matches.append({'term':term,'string_address':f'0x{string_addr:08X}',
                            'file_offset':f'0x{idx:X}',
                            'literal_pointer_addresses':[f'0x{x:08X}' for x in ptrslots],
                            'candidate_ldr_xrefs':xrefs})
    return {'sha256':hashlib.sha256(blob).hexdigest(), 'base':f'0x{base:08X}',
            'bytes':len(blob),'occurrences':summary,'entries':matches,
            'disclaimer':'A32 opcode shape + matching pointer only; validate code/data and reachability in Ghidra.'}


def save_csv(report, path:Path):
    with path.open('w',encoding='utf-8',newline='') as fh:
        w=csv.writer(fh)
        w.writerow(['term','string_address','file_offset','literal_slot','candidate_ldr','opcode'])
        for x in report['entries']:
            if x['candidate_ldr_xrefs']:
                for ref in x['candidate_ldr_xrefs']:
                    w.writerow([x['term'],x['string_address'],x['file_offset'],
                               ref['literal_slot_address'],ref['instruction_address'],ref['opcode']])
            else:
                w.writerow([x['term'],x['string_address'],x['file_offset'],
                            ';'.join(x['literal_pointer_addresses']),'',''])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('arm9',type=Path)
    p.add_argument('--base',type=lambda s:int(s,0),default=0x02000000)
    p.add_argument('--term',action='append',dest='terms')
    p.add_argument('--limit',type=int,default=250)
    p.add_argument('--json',type=Path)
    p.add_argument('--csv',type=Path)
    a=p.parse_args()
    report=locate(a.arm9.read_bytes(),a.base,a.terms or DEFAULT_TERMS,a.limit)
    if a.json:a.json.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if a.csv:save_csv(report,a.csv)
    if not a.json and not a.csv:print(json.dumps(report,indent=2))
    print('Terms:',report['occurrences'])
    print('Candidate instruction-to-string links:',sum(len(x['candidate_ldr_xrefs']) for x in report['entries']))

if __name__=='__main__':main()
