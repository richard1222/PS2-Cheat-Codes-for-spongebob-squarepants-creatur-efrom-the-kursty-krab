#!/usr/bin/env python3
"""Read-only ARM9 menu-string xref context and nearby direct branch targets.

This is a limited static A32 reader, NOT a whole-program call graph or an
executable-path proof. An LDR match can occur in non-code data.
"""
from __future__ import annotations
import argparse
import json
import struct
from pathlib import Path
from arm9_string_xrefs import DEFAULT_TERMS, locate, pc_relative_ldr_target

U32=0xffffffff

def sign24_branch(word: int, pc: int) -> int:
    field=word&0xffffff
    signed=field-0x1000000 if field&0x800000 else field
    return (pc+8+(signed<<2))&U32

def classify(word: int, pc: int) -> dict:
    """Describe only safely recognized instruction shapes, not general A32."""
    cond=word>>28
    result={'address':f'0x{pc:08X}','word':f'0x{word:08X}',
            'kind':'unknown','target':None}
    if cond==15:return result
    if (word&0x0FFFFFF0)==0x012FFF10:
        result['kind']='BX';result['register']=word&15
    elif (word&0x0E000000)==0x0A000000:
        result['kind']='BL' if word&(1<<24) else 'B'
        result['condition']=cond
        result['target']=f'0x{sign24_branch(word,pc):08X}'
    elif (slot:=pc_relative_ldr_target(word,pc)) is not None:
        result['kind']='LDR_LITERAL'
        result['target']=f'0x{slot:08X}'
        result['register']=(word>>12)&15
    elif (word&0x0C000000)==0x00000000:
        op=(word>>21)&15
        if op in (4,2,10,13) and cond==14:
            result['kind']={4:'ADD',2:'SUB',10:'CMP',13:'MOV'}[op]
    return result

def context(blob: bytes, base: int, terms=DEFAULT_TERMS, radius=12, max_hits=100) -> dict:
    if radius < 0 or radius>256:raise ValueError('radius must be between 0 and 256')
    source=locate(blob,base,terms,max_hits)
    for entry in source['entries']:
        for xref in entry['candidate_ldr_xrefs']:
            pc=int(xref['instruction_address'],16)
            off=pc-base
            near=[]
            for delta in range(-radius*4,(radius+1)*4,4):
                at=off+delta
                if at<0 or at+4>len(blob):continue
                if at%4:continue
                code=struct.unpack_from('<I',blob,at)[0]
                line=classify(code,base+at)
                line['is_anchor']=delta==0
                near.append(line)
            xref['nearby_instructions']=near
            xref['nearby_calls']=[i for i in near if i['kind']=='BL']
    source['context_instructions_each_side']=radius
    source['note']='Nearby BL targets are direct static candidates, not necessarily callable menu routines.'
    return source

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('arm9',type=Path)
    p.add_argument('--base',type=lambda s:int(s,0),default=0x02000000)
    p.add_argument('--term',action='append',dest='terms')
    p.add_argument('--radius',type=int,default=12)
    p.add_argument('--max-hits',type=int,default=100)
    p.add_argument('--json',type=Path)
    a=p.parse_args()
    try:
        report=context(a.arm9.read_bytes(),a.base,a.terms or DEFAULT_TERMS,
                       a.radius,a.max_hits)
    except (ValueError,OSError) as e:
        p.exit(2,f'Cannot scan: {e}\n')
    value=json.dumps(report,indent=2)+'\n'
    if a.json:a.json.write_text(value,encoding='utf-8')
    else:print(value,end='')
if __name__=='__main__':main()
