#!/usr/bin/env python3
"""Collect a bounded PRIVATE PS2 menu-resource bundle from a local ISO, read-only.

PAKS layout inferred from prior project extractor; retail compatibility must be
verified on the supplied ISO. Bundles contain game data: do not publish to GitHub.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from ps2_iso_probe import _find_root_entries, _bounded_extent

MAX_NAMES=4*1024*1024
MAX_PACKAGE=32*1024*1024
MAX_TOTAL=64*1024*1024

def inventory(read,extent_size):
    def bounded(at,count):
        if at<0 or count<0 or at+count>extent_size:raise ValueError('PAKS extent outside archive')
        data=read(at,count)
        if len(data)!=count:raise ValueError('truncated PAKS data')
        return data
    h=struct.unpack('<13I',bounded(0,52))
    _,align,version,count,info_raw,_,_,_,_,_,names_raw,names_size,info_size=h
    if not 1<=align<=1048576 or not 1<=count<=10000 or not 1<=names_size<=MAX_NAMES:
        raise ValueError('unsupported PAKS header bounds')
    info=info_raw*align;names_at=names_raw*align
    method=int(count*32>info_size) if info_size else int(((count*32+info+align-1)//align)*align>names_at)
    stride=20 if method else 32
    records=bounded(info,count*stride);names=bounded(names_at,names_size)
    base2=struct.unpack('<I',bounded(0x140,4))[0]+info if info>0x140 else 0
    result=[]
    for i in range(count):
        raw,crc,size,name_off,flags=struct.unpack_from('<5I',records,i*stride)
        if flags==0xffffffff:continue
        if name_off>=len(names):raise ValueError('invalid PAKS name offset')
        end=names.find(b'\0',name_off)
        if end<0:raise ValueError('unterminated PAKS name')
        name=names[name_off:end].decode('ascii')
        offset=raw*align+(base2 if flags&0x10 else 0)
        if offset+size>extent_size:raise ValueError('PAKS member outside archive')
        result.append({'name':name,'offset':offset,'size':size})
    return {'version':version,'method':method,'entries':result}

def collect(source,output):
    source=Path(source);output=Path(output)
    if source.resolve()==output.resolve():raise ValueError('output must differ from ISO')
    with source.open('rb') as stream:
        stream.seek(0,2);size=stream.tell();root=_find_root_entries(stream,size)
        matches=[e for e in root if e['name'].split(';')[0].upper()=='ALLPAKS.PS2' and not e['directory']]
        if len(matches)!=1:raise ValueError('expected exactly one ALLPAKS.PS2 at ISO root')
        entry=matches[0];base,amount=_bounded_extent(entry['lba'],entry['size'],size)
        def read(at,count):
            stream.seek(base+at);return stream.read(count)
        listing=inventory(read,amount)
        chosen=[e for e in listing['entries'] if any(t in e['name'].lower() for t in
                ('pause','frontend_dev','debugpackage'))]
        if not chosen:raise ValueError('no relevant menu packages found; no bundle written')
        if len(chosen)>32 or any(e['size']>MAX_PACKAGE for e in chosen) or sum(e['size'] for e in chosen)>MAX_TOTAL:
            raise ValueError('menu selection exceeds bounded bundle limit')
        manifest={'private_game_data':True,'source_image_bytes':size,'root_entries':root,
                  'paks_version':listing['version'],'paks_method':listing['method'],
                  'inventory':listing['entries'],'selected':[]}
        with output.open('xb') as handle:
            try:
                with ZipFile(handle,'w',compression=ZIP_DEFLATED) as archive:
                    for i,e in enumerate(chosen):
                        data=read(e['offset'],e['size'])
                        if len(data)!=e['size']:raise ValueError('truncated selected package')
                        # Fixed generated member names avoid archive path injection.
                        member=f'packages/{i:03d}.ps2'
                        archive.writestr(member,data)
                        manifest['selected'].append({**e,'bundle_member':member,
                            'sha256':hashlib.sha256(data).hexdigest()})
                    archive.writestr('manifest.json',json.dumps(manifest,indent=2))
            except BaseException:
                handle.close();output.unlink();raise
    return {'bundle':output.name,'packages':len(chosen),'selected_bytes':sum(e['size'] for e in chosen),
            'source_modified':False,'private_game_data':True}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('iso',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args()
    try:print(json.dumps(collect(a.iso,a.output),indent=2))
    except (ValueError,OSError) as e:p.exit(2,f'Collection blocked: {e}\n')
if __name__=='__main__':main()
