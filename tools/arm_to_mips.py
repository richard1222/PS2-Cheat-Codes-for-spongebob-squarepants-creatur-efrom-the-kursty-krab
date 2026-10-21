#!/usr/bin/env python3
"""Conservative ARM assembly to MIPS assembly research translator.

Accepts assembly text, NOT DS ROM bytes. Unsupported ARM instructions fail.
"""
import argparse
import re
import sys
from pathlib import Path

REGS = {**{f"r{i}": r for i, r in enumerate(
    ["$t0","$t1","$t2","$t3","$t4","$t5","$t6","$t7","$t8","$t9","$s0","$s1","$s2"])},
    "sp":"$sp","r13":"$sp","lr":"$ra","r14":"$ra"}

class TranslationError(ValueError): pass

def reg(s, n):
    if s.strip().lower() not in REGS:
        raise TranslationError(f"line {n}: unsupported register {s}")
    return REGS[s.strip().lower()]

def operand(s, n):
    s=s.strip()
    if s.startswith("#"):
        try: num=int(s[1:],0)
        except ValueError: raise TranslationError(f"line {n}: invalid immediate {s}")
        if not -(1<<31)<=num<=(1<<32)-1:
            raise TranslationError(f"line {n}: immediate not 32-bit")
        return "$at",[f"li $at, {num}"]
    return reg(s,n),[]

def translate(source):
    output=["# Experimental ARM -> MIPS assembly; not a PS2 patch.",
            "# ARM r0-r12 -> MIPS t0-t9,s0-s2; ARM SP->sp LR->ra.",
            "# Not ABI safe; ARM flags/Thumb/memory instructions unsupported."]
    cmp_args=None
    for n,raw in enumerate(source.splitlines(),1):
        line=raw.split(";",1)[0].split("@",1)[0].strip()
        if not line: continue
        if line.endswith(":"):
            if not re.fullmatch(r"[A-Za-z_.$][\w.$]*:",line):
                raise TranslationError(f"line {n}: bad label")
            output.append(line); continue
        m=re.fullmatch(r"([A-Za-z][A-Za-z0-9]*)\s*(.*)",line)
        if not m: raise TranslationError(f"line {n}: unsupported syntax")
        op=m.group(1).upper()
        args=[a.strip() for a in m.group(2).split(",") if a.strip()]
        if op in ("MOV","ADD","SUB"):
            expected=2 if op=="MOV" else 3
            if len(args)!=expected: raise TranslationError(f"line {n}: wrong operand count")
            dst=reg(args[0],n)
            if op=="MOV":
                src,pre=operand(args[1],n)
                output.extend(pre+[f"move {dst}, {src}"])
            else:
                a=reg(args[1],n); b,pre=operand(args[2],n)
                output.extend(pre+[f'{"addu" if op=="ADD" else "subu"} {dst}, {a}, {b}'])
            continue
        if op=="CMP":
            if len(args)!=2: raise TranslationError(f"line {n}: CMP needs 2 operands")
            cmp_args=(reg(args[0],n),args[1],n)
            output.append("# CMP deferred for BEQ/BNE")
            continue
        if op in ("BEQ","BNE"):
            if len(args)!=1 or not re.fullmatch(r"[A-Za-z_.$][\w.$]*",args[0]):
                raise TranslationError(f"line {n}: invalid branch label")
            if cmp_args is None: raise TranslationError(f"line {n}: branch without CMP")
            a,b,bn=cmp_args
            rhs,pre=operand(b,bn)
            output.extend(pre+[f"{op.lower()} {a}, {rhs}, {args[0]}","nop  # branch delay slot"])
            continue
        if op=="B":
            if len(args)!=1 or not re.fullmatch(r"[A-Za-z_.$][\w.$]*",args[0]):
                raise TranslationError(f"line {n}: invalid branch")
            output.extend([f"b {args[0]}","nop  # branch delay slot"])
            continue
        if op=="BX" and len(args)==1 and args[0].lower() in ("lr","r14"):
            output.extend(["jr $ra","nop  # branch delay slot"])
            continue
        raise TranslationError(f"line {n}: unsupported {op}")
    return "\n".join(output)+"\n"

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("source",type=Path)
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    try: result=translate(a.source.read_text())
    except TranslationError as e: print(e,file=sys.stderr); sys.exit(2)
    if a.out: a.out.write_text(result)
    else: print(result,end="")
