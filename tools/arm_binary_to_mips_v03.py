#!/usr/bin/env python3
"""Fail-closed A32->MIPS translation gate for *pure* register/control-flow blocks.

Back-end is the limited research translator from v0.2. v0.3 explicitly blocks
memory operations, DS peripherals, and ambiguous CMP flag flow. Generated
assembly is NOT ABI-compatible PS2 code and must never be patched into an ISO.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from arm_binary_to_mips import inspect, generate

U32=0xFFFFFFFF

def analyze_block(inst):
    errors=[]
    constants={}  # register -> known constant; linear diagnostic only
    for n,i in enumerate(inst):
        op=i.mnemonic
        if not i.supported:
            errors.append(f'0x{i.address:08X}: {i.reason}')
            constants.clear()
            continue
        if op in ('LDR','STR'):
            rd,rn,displacement=i.operands
            base=constants.get(rn)
            if base is not None:
                addr=(base+displacement)&U32
                label=' (Nintendo DS hardware / MMIO region)' if 0x04000000<=addr<0x05000000 else ''
                errors.append(f'0x{i.address:08X}: {op} accesses 0x{addr:08X}{label}; PS2 memory mapping not defined')
            else:
                errors.append(f'0x{i.address:08X}: {op} uses an unmapped memory address; PS2 memory mapping not defined')
            if op=='LDR':constants.pop(rd,None)
            continue
        if op in ('MOV','ADD','SUB','AND','EOR','ORR','CMP'):
            rn,rd,rhs=i.operands
            if rhs[0]=='imm': rhs_known=rhs[1]
            else:rhs_known=constants.get(rhs[1])
            if op=='MOV': val=rhs_known
            elif op=='CMP':continue
            else:
                lhs=constants.get(rn)
                if lhs is None or rhs_known is None:val=None
                elif op=='ADD':val=(lhs+rhs_known)&U32
                elif op=='SUB':val=(lhs-rhs_known)&U32
                elif op=='AND':val=lhs&rhs_known
                elif op=='ORR':val=lhs|rhs_known
                else:val=lhs^rhs_known
            if val is None:constants.pop(rd,None)
            else:constants[rd]=val
            continue
        if op in ('BEQ','BNE'):
            if n==0 or inst[n-1].mnemonic!='CMP':
                errors.append(f'0x{i.address:08X}: conditional branch not directly after CMP; flag lifetime not established')
            constants.clear() # control-flow merge: assume unknown
        elif op=='B':constants.clear()
        elif op=='BX':constants.clear()
    return errors


def translate_safe(blob:bytes,base:int,offset:int,count:int):
    inst=inspect(blob,base,offset,count)
    reasons=analyze_block(inst)
    if reasons:
        return None, {'status':'blocked','reasons':reasons,'instructions':[i.to_dict() for i in inst]}
    try:
        asm=generate(inst)
    except ValueError as e:
        return None, {'status':'blocked','reasons':[str(e)],'instructions':[i.to_dict() for i in inst]}
    return asm, {'status':'generated_research_only','reasons':[], 'instructions':[i.to_dict() for i in inst]}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('arm_binary',type=Path)
    p.add_argument('--base',type=lambda v:int(v,0),default=0x02000000)
    p.add_argument('--offset',type=lambda v:int(v,0),default=0)
    p.add_argument('--count',type=int,default=8)
    p.add_argument('--report',type=Path)
    p.add_argument('--out',type=Path)
    a=p.parse_args()
    try:asm,report=translate_safe(a.arm_binary.read_bytes(),a.base,a.offset,a.count)
    except (ValueError,OSError) as e:p.exit(2,str(e)+'\n')
    if a.report:a.report.write_text(json.dumps(report,indent=2)+'\n')
    if asm is None:
        print('\n'.join(report['reasons']),file=sys.stderr)
        return 2
    if a.out:a.out.write_text(asm)
    else:print(asm,end='')
    return 0

if __name__=='__main__':raise SystemExit(main())
