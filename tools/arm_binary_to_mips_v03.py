#!/usr/bin/env python3
"""v0.3 fail-closed wrapper for the research-only A32 to MIPS converter.

Only pure register/basic-control-flow blocks are permitted. The output does NOT
implement the DS/PS2 memory map, ABI, system calls, engine or original menu.
"""
import argparse,json,sys
from pathlib import Path
from arm_binary_to_mips import inspect,generate
U32=0xffffffff

def analyze_block(inst):
    errors=[];constants={}
    for n,i in enumerate(inst):
        op=i.mnemonic
        if not i.supported:
            errors.append(f'0x{i.address:08X}: {i.reason}')
            constants.clear();continue
        if op in ('LDR','STR'):
            rd,rn,delta=i.operands
            if rn in constants:
                addr=(constants[rn]+delta)&U32
                mmio=' (Nintendo DS MMIO / hardware)' if 0x04000000<=addr<0x05000000 else ''
                errors.append(f'0x{i.address:08X}: {op} accesses 0x{addr:08X}{mmio}; PS2 mapping not defined')
            else:
                errors.append(f'0x{i.address:08X}: {op} uses unmapped memory; PS2 mapping not defined')
            if op=='LDR':constants.pop(rd,None)
            continue
        if op in ('MOV','ADD','SUB','AND','EOR','ORR','CMP'):
            rn,rd,rhs=i.operands
            rhs_val=rhs[1] if rhs[0]=='imm' else constants.get(rhs[1])
            if op=='CMP':continue
            if op=='MOV':value=rhs_val
            else:
                lhs=constants.get(rn)
                if lhs is None or rhs_val is None:value=None
                elif op=='ADD':value=(lhs+rhs_val)&U32
                elif op=='SUB':value=(lhs-rhs_val)&U32
                elif op=='AND':value=lhs&rhs_val
                elif op=='ORR':value=lhs|rhs_val
                else:value=lhs^rhs_val
            if value is None:constants.pop(rd,None)
            else:constants[rd]=value
            continue
        if op in ('BEQ','BNE'):
            if n==0 or inst[n-1].mnemonic!='CMP':
                errors.append(f'0x{i.address:08X}: conditional branch lacks immediately preceding CMP; flag lifetime unknown')
            constants.clear()
        elif op in ('B','BX'):constants.clear()
    return errors

def translate_safe(blob,base,offset,count):
    inst=inspect(blob,base,offset,count)
    errors=analyze_block(inst)
    if errors:return None,{'status':'blocked','reasons':errors,'instructions':[i.to_dict() for i in inst]}
    try:asm=generate(inst)
    except ValueError as e:
        return None,{'status':'blocked','reasons':[str(e)],'instructions':[i.to_dict() for i in inst]}
    return asm,{'status':'generated_research_only','reasons':[],'instructions':[i.to_dict() for i in inst]}

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
