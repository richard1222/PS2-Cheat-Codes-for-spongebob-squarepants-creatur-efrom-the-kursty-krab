#!/usr/bin/env python3
"""Read-only ISO9660 root scanner for PS2 ELF (SLUS_213.91).

Reports and optionally audits the boot executable in one invocation. Makes no
changes to the ISO; does not extract proprietary executable files by default.
Supports 2048-byte cooked-sector ISO9660 images with root-level boot executables.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from ps2_elf_audit import audit, ElfError
from ps2_mips_string_xrefs import analyze

SECTOR=2048
MAX_DIR_BYTES=4*1024*1024
MAX_ELF_BYTES=64*1024*1024

class ISOError(ValueError):pass

def _both32(data:bytes,at:int)->int:
    if len(data)<at+8:raise ISOError('truncated ISO directory extent')
    little=int.from_bytes(data[at:at+4],'little')
    big=int.from_bytes(data[at+4:at+8],'big')
    if little!=big:raise ISOError('ISO9660 little/big endian extent mismatch')
    return little

def _decode_record(rec:bytes)->dict:
    if len(rec)<34:raise ISOError('truncated directory record')
    length=rec[0]
    name_len=rec[32]
    if length<33+name_len or length>len(rec):raise ISOError('invalid directory record length')
    name=rec[33:33+name_len]
    if name==b'\x00':name='.'
    elif name==b'\x01':name='..'
    else:name=name.decode('ascii','replace')
    return {'name':name,'lba':_both32(rec,2),'size':_both32(rec,10),
            'directory':bool(rec[25]&2),'flags':rec[25]}

def _bounded_extent(lba:int,length:int,iso_size:int)->tuple[int,int]:
    begin=lba*SECTOR
    if lba<0 or length<0 or begin>iso_size or length>iso_size-begin:
        raise ISOError('record extent extends outside ISO')
    return begin,length

def _find_root_entries(f,size:int)->list[dict]:
    if size<(17*SECTOR):raise ISOError('too small for ISO9660 descriptor')
    f.seek(16*SECTOR)
    pvd=f.read(SECTOR)
    if len(pvd)!=SECTOR or pvd[:7]!=b'\x01CD001\x01':
        raise ISOError('unsupported image: expected ISO9660 PVD in 2048-byte sectors')
    root_length=pvd[156]
    if root_length<34:raise ISOError('missing root directory record')
    root=_decode_record(pvd[156:156+root_length])
    if not root['directory']:raise ISOError('root record is not directory')
    if root['size']>MAX_DIR_BYTES:raise ISOError('root directory too large for bounded scan')
    begin,amount=_bounded_extent(root['lba'],root['size'],size)
    f.seek(begin)
    directory=f.read(amount)
    if len(directory)!=amount:raise ISOError('truncated directory')
    out=[];pos=0
    while pos<len(directory):
        length=directory[pos]
        if length==0:
            pos=((pos//SECTOR)+1)*SECTOR
            continue
        if pos+length>len(directory) or pos%SECTOR+length>SECTOR:
            raise ISOError('invalid directory entry crosses extent/sector boundary')
        entry=_decode_record(directory[pos:pos+length])
        if entry['name'] not in ('.','..'):
            _bounded_extent(entry['lba'],entry['size'],size)
            out.append(entry)
        pos+=length
    return out

def inspect_iso(path:Path,boot_name='SLUS_213.91',enable_xrefs=True,max_file_bytes=MAX_ELF_BYTES)->dict:
    if not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}',boot_name):
        raise ISOError('boot name must be a simple root filename')
    path=Path(path)
    with path.open('rb') as f:
        f.seek(0,2);iso_size=f.tell()
        entries=_find_root_entries(f,iso_size)
        match=[x for x in entries if x['name'].split(';')[0].upper()==boot_name.upper() and not x['directory']]
        report={'image':path.name,'image_size':iso_size,'sector_bytes':SECTOR,
                'root_entries':entries,'boot_name':boot_name,'boot_found':bool(match),
                'read_only':True}
        if len(match)!=1:
            if len(match)>1:raise ISOError('ambiguous duplicate boot file entries')
            report['note']='Boot executable not found at ISO root; no executable analyzed'
            return report
        entry=match[0]
        if entry['size']>max_file_bytes:raise ISOError('boot ELF exceeds maximum read limit')
        begin,amount=_bounded_extent(entry['lba'],entry['size'],iso_size)
        f.seek(begin);blob=f.read(amount)
        if len(blob)!=amount:raise ISOError('boot executable truncated')
    report['boot_file']={'lba':entry['lba'],'iso_offset':begin,'bytes':len(blob),
                         'sha256':hashlib.sha256(blob).hexdigest()}
    try:
        report['elf_audit']=audit(blob)
        if enable_xrefs:report['mips_debug_string_xrefs']=analyze(blob)
    except (ValueError,ElfError) as exc:
        report['elf_analysis_error']=str(exc)
    report['note']='Read only. File offsets are image-specific; static string references do not prove reachable features.'
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('iso',type=Path)
    p.add_argument('--boot-name',default='SLUS_213.91')
    p.add_argument('--no-xrefs',action='store_true')
    p.add_argument('--json',type=Path)
    a=p.parse_args()
    try:report=inspect_iso(a.iso,a.boot_name,not a.no_xrefs)
    except (OSError,ISOError) as ex:p.exit(2,'ISO scan blocked: '+str(ex)+'\n')
    output=json.dumps(report,indent=2)+'\n'
    if a.json:a.json.write_text(output,encoding='utf-8')
    else:print(output,end='')
if __name__=='__main__':main()
