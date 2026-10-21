#!/usr/bin/env python3
"""ARM9 literal-pool xref scanner for a legitimately held DS ARM9 binary.

Finds ASCII strings, pointer words, and candidate PC-relative ARM LDRs.
A match is a candidate reference, NOT a verified executable code path.
"""
import argparse, csv, hashlib, json, struct
from pathlib import Path

DEFAULT_TERMS=('DEBUG OPTIONS','game_select_','levelselect','stageselect','debug','TEST INTRO UI','free camera')

def pc_relative_ldr_target(word,address):
    if word>>28==15:return None
    if (word&0x0F7F0000)!=0x051F0000:return None
    displacement=(word&0xFFF)*(1 if word&(1<<23) else -1)
    return (((address+8)&~3)+displacement)&0xFFFFFFFF

def locate(blob,base,terms=DEFAULT_TERMS,limit=250):
    if base%4:raise ValueError('base must be aligned')
    if not 0<=base<=0xffffffff or base+len(blob)>0x100000000:
        raise ValueError('data outside 32-bit address space')
    if limit<1:raise ValueError('limit must be positive')
    words=[(off,struct.unpack_from('<I',blob,off)[0]) for off in range(0,len(blob)-3,4)]
    ptrs={}
    ldrs={}
    for off,word in words:
        ptrs.setdefault(word,[]).append(base+off)
        t=pc_relative_ldr_target(word,base+off)
        if t is not None and base<=t<=base+len(blob)-4:
            ldrs.setdefault(t,[]).append((base+off,word))
    results=[];summary={};folded=blob.lower()
    for term in terms:
        if not term or not term.isascii():raise ValueError('terms must be ASCII')
        needle=term.encode('ascii').lower();offset=0;hits=[]
        while (idx:=folded.find(needle,offset))>=0:
            hits.append(idx);offset=idx+1
        summary[term]=len(hits)
        for idx in hits[:limit]:
            addr=base+idx
            slots=ptrs.get(addr,[])
            refs=[{'instruction_address':f'0x{pc:08X}',
                   'opcode':f'0x{opcode:08X}',
                   'literal_slot_address':f'0x{slot:08X}'}
                  for slot in slots for pc,opcode in ldrs.get(slot,[])]
            results.append({'term':term,'string_address':f'0x{addr:08X}',
                            'file_offset':f'0x{idx:X}',
                            'literal_pointer_addresses':[f'0x{slot:08X}' for slot in slots],
                            'candidate_ldr_xrefs':refs})
    return {'sha256':hashlib.sha256(blob).hexdigest(),'base':f'0x{base:08X}',
            'bytes':len(blob),'occurrences':summary,'entries':results,
            'disclaimer':'Static candidate matches; verify instruction execution and function reachability in Ghidra.'}

def save_csv(report,path):
    with Path(path).open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f)
        w.writerow(['term','string_address','file_offset','literal_slot','candidate_ldr','opcode'])
        for e in report['entries']:
            if not e['candidate_ldr_xrefs']:
                w.writerow([e['term'],e['string_address'],e['file_offset'],
                            ';'.join(e['literal_pointer_addresses']),'',''])
            for x in e['candidate_ldr_xrefs']:
                w.writerow([e['term'],e['string_address'],e['file_offset'],
                            x['literal_slot_address'],x['instruction_address'],x['opcode']])

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('arm9',type=Path)
    p.add_argument('--base',type=lambda s:int(s,0),default=0x02000000)
    p.add_argument('--term',action='append',dest='terms')
    p.add_argument('--limit',type=int,default=250)
    p.add_argument('--json',type=Path)
    p.add_argument('--csv',type=Path)
    a=p.parse_args()
    r=locate(a.arm9.read_bytes(),a.base,a.terms or DEFAULT_TERMS,a.limit)
    if a.json:a.json.write_text(json.dumps(r,indent=2)+'\n')
    if a.csv:save_csv(r,a.csv)
    if not a.json and not a.csv:print(json.dumps(r,indent=2))
    print('Terms:',r['occurrences'])
    print('Code reference candidates:',sum(len(e['candidate_ldr_xrefs']) for e in r['entries']))
if __name__=='__main__':main()
