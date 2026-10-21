#!/usr/bin/env python3
"""Disassemble small ARM9 A32 code windows using installed Clang and LLVM objdump.

ARM instructions are wrapped in a temporary .o with .inst directives; this
preserves their exact bytes but does not recreate the game's original sections
or prove a function start. Neither tool is bundled with this repository.
"""
import argparse
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

def disassemble(blob: bytes, base: int, offset: int, count: int,
                clang='clang', objdump='llvm-objdump') -> str:
    if base<0 or base>0xffffffff or offset<0 or offset%4 or count<1 or count>256:
        raise ValueError('base, aligned offset or count is invalid (max count: 256)')
    if base+offset+count*4 > 0x100000000 or offset+count*4>len(blob):
        raise ValueError('requested disassembly exceeds file or 32-bit space')
    for binary in (clang,objdump):
        if shutil.which(binary) is None:
            raise RuntimeError(f'required executable not found: {binary}')
    words=struct.unpack_from('<'+'I'*count,blob,offset)
    asm='\n'.join(['.syntax unified','.arm','.text','.global arm9_window','arm9_window:']+
                  [f'  .inst 0x{w:08X}' for w in words])+'\n'
    with tempfile.TemporaryDirectory(prefix='sb-arm9-') as td:
        source=Path(td)/'snippet.S'
        out=Path(td)/'snippet.o'
        source.write_text(asm,encoding='ascii')
        first=subprocess.run([clang,'--target=armv5te-none-eabi','-c',str(source),'-o',str(out)],
                             capture_output=True,text=True,timeout=15)
        if first.returncode!=0:
            raise RuntimeError('Clang assembly failed: '+first.stderr[:600])
        second=subprocess.run([objdump,'-d',f'--adjust-vma={base+offset}',str(out)],
                              capture_output=True,text=True,timeout=15)
        if second.returncode!=0:
            raise RuntimeError('LLVM disassembly failed: '+second.stderr[:600])
        return second.stdout

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('arm9',type=Path)
    parser.add_argument('--base',type=lambda x:int(x,0),default=0x02000000)
    parser.add_argument('--offset',type=lambda x:int(x,0),required=True)
    parser.add_argument('--count',type=int,default=16)
    parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    try:output=disassemble(args.arm9.read_bytes(),args.base,args.offset,args.count)
    except (ValueError,OSError,RuntimeError,subprocess.TimeoutExpired) as e:
        parser.exit(2,f'Cannot disassemble: {e}\n')
    if args.out:args.out.write_text(output,encoding='utf-8')
    else:print(output,end='')
if __name__=='__main__':main()
