#!/usr/bin/env python3
"""Check optional disassembly/emulation dependencies without downloading software."""
import importlib
import json
import sys


def check():
    out={}
    for name in ('capstone','unicorn'):
        try:
            mod=importlib.import_module(name)
            out[name]={'installed':True,'version':str(getattr(mod,'__version__','unknown'))}
        except ImportError as exc:
            out[name]={'installed':False,'detail':str(exc)}
    return out


if __name__=='__main__':
    result=check()
    print(json.dumps(result,indent=2))
    if not all(x['installed'] for x in result.values()):
        sys.exit(1)
