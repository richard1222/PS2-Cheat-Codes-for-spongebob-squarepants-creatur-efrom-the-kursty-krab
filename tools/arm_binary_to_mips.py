#!/usr/bin/env python3
"""A32 little-endian machine code -> research-only MIPS assembly (strict subset)."""
from __future__ import annotations
import argparse
import json
import struct
from pathlib import Path
from dataclasses import dataclass

MAP = [f'$t{i}' for i in range(10)] + ['$s0','$s1','$s2','$sp','$ra']
OPS = {0:'AND',1:'EOR',2:'SUB',4:'ADD',10:'CMP',12:'ORR',13:'MOV'}
U32 = 0xffffffff

@dataclass
class Instruction:
    address: int
    word: int
    mnemonic: str
    operands: tuple
    reason: str = ''
    @property
    def supported(self): return not self.reason
    def to_dict(self):
        return {'address':f'0x{self.address:08X}', 'word':f'0x{self.word:08X}',
                'mnemonic':self.mnemonic, 'operands':list(self.operands),
                'supported':self.supported, 'reason':self.reason}

def ror(v,n):
    n%=32
    return ((v>>n)|(v<<(32-n)))&U32 if n else v

def err(addr,word,reason):
    return Instruction(addr,word,'UNSUPPORTED',(),reason)

def validregs(*items):
    return all(0<=n<=14 for n in items)

def decode(word,addr):
    cond=word>>28
    if (word&0x0FFFFFF0)==0x012FFF10 and cond==14:
        rm=word&15
        return Instruction(addr,word,'BX',('lr',)) if rm==14 else err(addr,word,'BX other than lr unsupported')
    if ((word>>25)&7)==5:
        if (word>>24)&1: return err(addr,word,'BL and function calls not supported')
        if cond not in (0,1,14): return err(addr,word,'unsupported conditional branch')
        imm24=word&0xffffff
        offset=(imm24<<8)&U32
        if offset&0x80000000: offset-=1<<32
        target=(addr+8+(offset>>6))&U32
        return Instruction(addr,word,{0:'BEQ',1:'BNE',14:'B'}[cond],(target,))
    if cond!=14: return err(addr,word,'conditional execution/flags unsupported')
    if ((word>>26)&3)==1:
        I,P,U,B,W,L=((word>>b)&1 for b in (25,24,23,22,21,20))
        rn,rd=(word>>16)&15,(word>>12)&15
        if I or not P or B or W or not validregs(rn,rd):
            return err(addr,word,'unsupported addressing, byte access or PC')
        delta=(word&0xfff)*(1 if U else -1)
        return Instruction(addr,word,'LDR' if L else 'STR',(rd,rn,delta))
    if ((word>>26)&3)==0:
        I=(word>>25)&1; opcode=(word>>21)&15; S=(word>>20)&1
        rn,rd=(word>>16)&15,(word>>12)&15
        if opcode not in OPS:return err(addr,word,'opcode not implemented')
        op=OPS[opcode]
        if S != (1 if op=='CMP' else 0):
            return err(addr,word,'CPSR flag writes unsupported except CMP')
        if I:
            rhs=('imm',ror(word&0xff,((word>>8)&15)*2))
        else:
            if ((word>>4)&255)!=0: return err(addr,word,'register shift unsupported')
            rm=word&15
            if not validregs(rm): return err(addr,word,'PC register unsupported')
            rhs=('reg',rm)
        check=(rd,) if op=='MOV' else (rn,) if op=='CMP' else (rd,rn)
        if not validregs(*check):return err(addr,word,'PC register unsupported')
        return Instruction(addr,word,op,(rn,rd,rhs))
    return err(addr,word,'unsupported class: coprocessor/stack/multiply/etc.')

def generate(instructions):
    if not instructions:raise ValueError('empty instruction region')
    bad=[i for i in instructions if not i.supported]
    if bad:
        raise ValueError(f'first unsupported at 0x{bad[0].address:08X}: {bad[0].reason}')
    addresses={i.address for i in instructions}
    targets={i.operands[0] for i in instructions if i.mnemonic in ('B','BEQ','BNE')}
    if not targets <= addresses:
        raise ValueError('branch targets outside selected region: '+', '.join(hex(a) for a in sorted(targets-addresses)))
    out=['# Experimental A32 -> MIPS: NOT a PS2 executable patch.',
         '# ARM r0-r9 => MIPS t0-t9, r10-r12 => s0-s2, r13 => sp, r14 => ra',
         '# ABI not preserved; $at scratch and $v0/$v1 compare snapshots.',
         '.set noreorder']
    has_cmp=False
    for i in instructions:
        if i.address in targets:out.append(f'L_{i.address:08X}:')
        op=i.mnemonic
        if op in OPS.values():
            rn,rd,rhs=i.operands
            dst=MAP[rd];a=MAP[rn]
            if rhs[0]=='imm':b=rhs[1];isimm=True
            else:b=MAP[rhs[1]];isimm=False
            if op=='CMP':
                out.append(f'move $v0, {a}')
                out.append(f'li $v1, {b}' if isimm else f'move $v1, {b}')
                has_cmp=True
            elif op=='MOV':
                out.append(f'li {dst}, {b}' if isimm else f'move {dst}, {b}')
            elif op in ('ADD','SUB'):
                if isimm and -32768 <= (b if op=='ADD' else -b) <= 32767:
                    out.append(f'addiu {dst}, {a}, {b if op=="ADD" else -b}')
                else:
                    if isimm:out.append(f'li $at, {b}');b='$at'
                    out.append(f'{"addu" if op=="ADD" else "subu"} {dst}, {a}, {b}')
            else:
                if isimm:out.append(f'li $at, {b}');b='$at'
                out.append(f'{"or" if op=="ORR" else op.lower()} {dst}, {a}, {b}')
        elif op in ('LDR','STR'):
            rd,rn,delta=i.operands
            if delta%4:raise ValueError(f'unaligned 32-bit access at 0x{i.address:08X}')
            out.append(f'{"lw" if op=="LDR" else "sw"} {MAP[rd]}, {delta}({MAP[rn]})')
        elif op in ('BEQ','BNE'):
            if not has_cmp:raise ValueError(f'0x{i.address:08X}: branch requires CMP')
            out.extend([f'{op.lower()} $v0, $v1, L_{i.operands[0]:08X}',
                        'nop  # MIPS delay slot'])
        elif op=='B':
            out.extend([f'b L_{i.operands[0]:08X}','nop  # MIPS delay slot'])
        elif op=='BX':
            out.extend(['jr $ra','nop  # MIPS delay slot'])
        else:raise AssertionError(op)
    return '\n'.join(out)+'\n'

def inspect(blob,base,offset,count):
    if offset<0 or count<=0 or offset%4 or offset+count*4>len(blob):
        raise ValueError('offset must be aligned and selected region must fit input')
    return [decode(struct.unpack_from('<I',blob,offset+i*4)[0],base+offset+i*4)
            for i in range(count)]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('arm9_bin',type=Path)
    p.add_argument('--base',type=lambda s:int(s,0),default=0x02000000)
    p.add_argument('--offset',type=lambda s:int(s,0),default=0)
    p.add_argument('--count',type=int,default=16)
    p.add_argument('--out',type=Path,help='write only if whole block supported')
    p.add_argument('--report',type=Path,help='JSON diagnostics, even on failure')
    a=p.parse_args()
    try:
        inst=inspect(a.arm9_bin.read_bytes(),a.base,a.offset,a.count)
        report={'base':f'0x{a.base:08X}','offset':f'0x{a.offset:X}',
                'complete':all(x.supported for x in inst),
                'instructions':[x.to_dict() for x in inst]}
        if a.report:a.report.write_text(json.dumps(report,indent=2)+'\n')
        code=generate(inst)
        if a.out:a.out.write_text(code)
        else:print(code,end='')
        return 0
    except (ValueError,OSError) as e:
        p.exit(2,f'Cannot translate: {e}\n')

if __name__=='__main__':raise SystemExit(main())
