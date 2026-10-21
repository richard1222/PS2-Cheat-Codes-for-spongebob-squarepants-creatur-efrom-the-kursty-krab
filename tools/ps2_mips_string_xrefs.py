#!/usr/bin/env python3
"""Read-only MIPS32/PS2 ELF debug-string reference scanner.

Finds LUI + ORI/ADDIU register-address constructors in ELF executable PT_LOAD
segments, matching resulting addresses against case-insensitive ASCII strings.
These are *candidate* static references. No reachability/function claim, no
runtime memory analysis, no ISO/ELF modifications. Pure Python stdlib.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
from pathlib import Path
from ps2_elf_audit import parse_elf, DEFAULT_TERMS

MASK32 = (1 << 32) - 1
REGISTER_NAMES = ('zero','at','v0','v1','a0','a1','a2','a3',
                  't0','t1','t2','t3','t4','t5','t6','t7',
                  's0','s1','s2','s3','s4','s5','s6','s7',
                  't8','t9','k0','k1','gp','sp','fp','ra')


def _signed16(n: int) -> int:
    return n - 0x10000 if n & 0x8000 else n


def _writes_register(word: int, reg: int) -> bool:
    """Conservative clobber check; unknown encoding blocks a speculative match.

    Return true if encoding may alter the register. Branch/jump control-flow
    is checked by _flow_break separately.
    """
    op=(word >> 26) & 63
    rs=(word >> 21) & 31
    rt=(word >> 16) & 31
    rd=(word >> 11) & 31
    if word == 0:
        return False
    if op == 0:
        funct=word & 63
        # jr/jalr, mfhi, mflo, add/addu/sub/etc. All R-type writes use rd,
        # except special instructions with no GPR writes (false positives safe).
        return rd == reg or (funct == 9 and reg == 31)
    if op == 3: # JAL writes RA
        return reg == 31
    if op in (2,4,5,6,7,40,41,42,43,46,48,49,50,51,54,56,57,58,59,62,63):
        # j/branches/stores (some opcodes conservatively handled by flow breaker)
        return False
    if op in (16,17,18,19):
        return True  # coprocessors and transfers: unknown effect in this scanner
    return rt == reg  # I-type typical


def _flow_break(word: int) -> bool:
    op=word>>26
    if op in (1,2,3,4,5,6,7,20,21,22,23):return True
    if op==0 and (word&63) in (8,9,12,13):return True
    if op in (16,17,18,19):return True
    # MIPS likely branches, coprocessors, instructions not yet modeled
    return False


def address_from_pair(lui_word: int, low_word: int) -> tuple[int,int,str] | None:
    """Recognize LUI rt,hi ; ADDIU/ORI rt,rt,lo (also allows different dest).

    Returns (computed address, destination reg index, low mnemonic).
    MIPS ADDIU sign-extends the low immediate, whereas ORI zero-extends it.
    """
    if (lui_word>>26)!=15:return None
    base_reg=(lui_word>>16)&31
    if base_reg==0:return None
    op=low_word>>26
    if op not in (9,13):return None
    rs=(low_word>>21)&31
    if rs!=base_reg:return None
    dest=(low_word>>16)&31
    if dest==0:return None
    imm=low_word&0xffff
    lo=_signed16(imm) if op==9 else imm
    hi=(lui_word&0xffff)<<16
    return ((hi+lo)&MASK32,dest,'ADDIU' if op==9 else 'ORI')


def _scan_executable_pairs(blob:bytes,elf:dict,lookahead:int):
    endian='<' if elf['endian']=='little' else '>'
    for seg in elf['segments']:
        if not seg['executable']:continue
        start=seg['file_offset']; size=seg['filesz'];vaddr=seg['vaddr']
        for pos in range(0,size-3,4):
            high_off=start+pos
            hi_word=struct.unpack_from(endian+'I',blob,high_off)[0]
            if hi_word>>26!=15 or ((hi_word>>16)&31)==0:continue
            reg=(hi_word>>16)&31
            for steps in range(1,lookahead+1):
                next_pos=pos+4*steps
                if next_pos+4>size:break
                lo_word=struct.unpack_from(endian+'I',blob,start+next_pos)[0]
                pair=address_from_pair(hi_word,lo_word)
                if pair:
                    addr,dest,kind=pair
                    yield {'address':addr,'file_offset':high_off,
                           'lui_vaddr':vaddr+pos,'low_vaddr':vaddr+next_pos,
                           'low_file_offset':start+next_pos,
                           'lui_opcode':hi_word,'low_opcode':lo_word,
                           'low_kind':kind,'register':REGISTER_NAMES[dest],
                           'segment':seg['index']}
                    break
                if _flow_break(lo_word) or _writes_register(lo_word,reg):break


def analyze(blob:bytes,terms=DEFAULT_TERMS,lookahead:int=6,max_hits:int=250):
    if lookahead<1 or lookahead>64:raise ValueError('lookahead must be between 1 and 64')
    if max_hits<1:raise ValueError('max_hits must be positive')
    elf=parse_elf(blob)
    lower=blob.lower()
    candidates={}
    for pair in _scan_executable_pairs(blob,elf,lookahead):
        candidates.setdefault(pair['address'],[]).append(pair)
    strings=[]
    for term in terms:
        if not term or not term.isascii():raise ValueError('search terms must be nonempty ASCII')
        needle=term.lower().encode('ascii');off=0;total=0;hits=[]
        while (idx:=lower.find(needle,off))>=0:
            off=idx+1;total+=1
            for seg in elf['segments']:
                if not (seg['file_offset']<=idx<seg['file_offset']+seg['filesz']):continue
                va=seg['vaddr']+idx-seg['file_offset']
                refs=candidates.get(va,[])
                if len(hits)<max_hits:
                    hits.append({'string_file_offset':f'0x{idx:X}',
                                 'string_vaddr':f'0x{va:08X}',
                                 'references':[{'lui_address':f'0x{x["lui_vaddr"]:08X}',
                                                'low_address':f'0x{x["low_vaddr"]:08X}',
                                                'kind':x['low_kind'],
                                                'register':x['register'],
                                                'lui_word':f'0x{x["lui_opcode"]:08X}',
                                                'low_word':f'0x{x["low_opcode"]:08X}'} for x in refs]})
            # Never invent a VA for nonloaded strings.
        strings.append({'term':term,'total_file_occurrences':total,'loaded_occurrences':len(hits),
                        'truncated':total>max_hits,'hits':hits})
    return {'sha256':hashlib.sha256(blob).hexdigest(),'elf_endian':elf['endian'],
            'lookahead':lookahead,'strings':strings,
            'limitations':['Static executable-segment patterns only',
                           'Other pointer-building patterns and gp-relative references not covered',
                           'A match is not proof of runtime execution, string usage or a debug menu']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('elf',type=Path)
    p.add_argument('--term',dest='terms',action='append')
    p.add_argument('--lookahead',type=int,default=6)
    p.add_argument('--max-hits',type=int,default=250)
    p.add_argument('--json',type=Path)
    args=p.parse_args()
    try:
        result=analyze(args.elf.read_bytes(),args.terms or DEFAULT_TERMS,
                       args.lookahead,args.max_hits)
    except (ValueError,OSError) as exc:p.exit(2,f'Cannot analyze: {exc}\n')
    output=json.dumps(result,indent=2)+'\n'
    if args.json:args.json.write_text(output,encoding='utf-8')
    else:print(output,end='')
if __name__=='__main__':main()
