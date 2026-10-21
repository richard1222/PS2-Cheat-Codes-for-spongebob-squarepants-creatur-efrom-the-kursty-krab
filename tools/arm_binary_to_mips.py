#!/usr/bin/env python3
"""A32 binary -> research-only MIPS assembly subset translator.

Fails closed on unsupported instructions. No game patching, DS SDK/PS2 hardware
compatibility or equivalence of different game engines is implied.
"""
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
    def supported(self):return not self.reason
    def to_dict(self):
        return {'address':f'0x{self.address:08X}', 'word':f'0x{self.word:08X}',
                'mnemonic':self.mnemonic, 'operands':list(self.operands),
                'supported':self.supported, 'reason':self.reason}

def ror(v,n):
    n%=32
    return ((v>>n)|(v<<(32-n)))&U32 if n else v

def err(addr,word,reason):return Instruction(addr,word,'UNSUPPORTED',(),reason)

def validregs(*items):return all(0<=n<=14 for n in items)

def decode(word,addr):
    cond=word>>28
    if (word&0x0FFFFFF0)==0x012FFF10 and cond==14:
        rm=word&15
        return Instruction(addr,word,'BX',('lr',)) if rm==14 else err(addr,word,'BX register other than lr not supported')
    if ((word>>25)&7)==5:
        if (word>>24)&1:return err(addr,word,'BL and function calls not supported')
        if cond not in (0,1,14):return err(addr,word,'unsupported conditional branch')
        imm24=word&0xffffff
        offset=((imm24<<8)&0xffffffff)
        if offset&0x80000000:offset-=1<<32
        target=(addr+8+(offset>>6))&U32 # signext imm24 << 2
        return Instruction(addr,word,{0:'BEQ',1:'BNE',14:'B'}[cond],(target,))
    if cond!=14:return err(addr,word,'conditional execution/flags not yet modeled')
    # Immediate-offset, aligned LDR/STR (no writeback/PC/register-shift)
    if ((word>>26)&3)==1:
        I,P,U,B,W,L=((word>>b)&1 for b in (25,24,23,22,21,20))
        rn,rd=(word>>16)&15,(word>>12)&15
        if I or not P or B or W or not validregs(rn,rd):
            return err(addr,word,'unsupported addressing mode, byte access or PC register')
        delta=(word&0xfff)*(1 if U else -1)
        return Instruction(addr,word,'LDR' if L else 'STR',(rd,rn,delta))
    if ((word>>26)&3)==0:
        I=(word>>25)&1; opcode=(word>>21)&15; S=(word>>20)&1
        rn,rd=(word>>16)&15,(word>>12)&15
        if opcode not in OPS:return err(addr,word,'data-processing opcode not implemented')
        op=OPS[opcode]
        if S != (1 if op=='CMP' else 0):return err(addr,word,'CPSR flags writes not supported except CMP')
        if I:
            imm=ror(word&0xff,((word>>8)&15)*2)
            rhs=('imm',imm)
        else:
            if ((word>>4)&255)!=0:return err(addr,word,'register shift / nonzero shifter fields unsupported')
            rm=word&15
            if not validregs(rm):return err(addr,word,'PC operand unsupported')
            rhs=('reg',rm)
        check=(rd,) if op=='MOV' else (rn,) if op=='CMP' else (rd,rn)
        if not validregs(*check):return err(addr,word,'PC operand unsupported')
        return Instruction(addr,word,op,(rn,rd,rhs))
    return err(addr,word,'instruction class unsupported (coprocessor/stack/multiply/etc.)')

def generate(instructions):
    """Translate full block or raise. Only local control flow allowed."""
    if not instructions:raise ValueError('empty instruction region')
    bad=[i for i in instructions if not i.supported]
    if bad:raise ValueError(f'first unsupported at 0x{bad[0].address:08X}: {bad[0].reason}')
    addresses={i.address for i in instructions}
    targets={i.operands[0] for i in instructions if i.mnemonic in ('B','BEQ','BNE')}
    if not targets <= addresses:raise ValueError('branch targets outside selected region: '+', '.join(hex(a) for a in sorted(targets-addresses)))
    out=['# A32 -> MIPS exploratory translation, NOT a PS2 executable patch',
         '# Assumes a 32-bit, little-endian, private scratch RAM calling context.',
         '# Register mappings do not follow either platform ABI.',
         '# ARM r0-r9=>MIPS t0-t9, r10-r12=>s0-s2, r13=>sp, r14=>ra',
         '# Reserved scratch: $at (immediates), $v0/$v1 (CMP snapshot)',
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
            elif op=='MOV':out.append(f'li {dst}, {b}' if isimm else f'move {dst}, {b}')
            elif op in ('ADD','SUB'):
                if isimm and -32768<= (b if op=='ADD' else -b) <=32767:
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
            if not has_cmp:raise ValueError(f'0x{i.address:08X}: conditional branch requires a preceding CMP')
            out.extend([f'{op.lower()} $v0, $v1, L_{i.operands[0]:08X}','nop  # delay slot'])
        elif op=='B':out.extend([f'b L_{i.operands[0]:08X}','nop  # delay slot'])
        elif op=='BX':out.extend(['jr $ra','nop  # delay slot'])
        else:raise AssertionError(op)
    return '\n'.join(out)+'\n'

def inspect(blob,base,offset,count):
    if offset<0 or count<=0 or offset%4 or offset+count*4>len(blob):
        raise ValueError('offset must be 4-byte aligned and requested region must fit input')
    return [decode(struct.unpack_from('<I',blob,offset+i*4)[0],base+offset+i*4) for i in range(count)]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('arm9_bin',type=Path)
    p.add_argument('--base',type=lambda s:int(s,0),default=0x02000000)
    p.add_argument('--offset',type=lambda s:int(s,0),default=0)
    p.add_argument('--count',type=int,default=16)
    p.add_argument('--out',type=Path,help='Only writes when every instruction is supported')
    p.add_argument('--report',type=Path,help='Write JSON diagnostics even when conversion fails')
    args=p.parse_args()
    try:
        inst=inspect(args.arm9_bin.read_bytes(),args.base,args.offset,args.count)
        report={'base':f'0x{args.base:08X}','offset':f'0x{args.offset:X}',
                'complete':all(i.supported for i in inst),
                'instructions':[i.to_dict() for i in inst]}
        if args.report:args.report.write_text(json.dumps(report,indent=2)+'\n')
        code=generate(inst)
        if args.out:args.out.write_text(code)
        else:print(code,end='')
        return 0
    except (ValueError,OSError) as ex:
        p.exit(2,f'Cannot translate: {ex}\n')

if __name__=='__main__':raise SystemExit(main())
