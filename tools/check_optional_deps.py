#!/usr/bin/env python3
"""Check optional Capstone/Unicorn installations without downloading anything."""
import importlib,json,sys
result={}
for name in ('capstone','unicorn'):
    try:
        x=importlib.import_module(name)
        result[name]={'installed':True,'version':str(getattr(x,'__version__','unknown'))}
    except ImportError as e:
        result[name]={'installed':False,'error':str(e)}
print(json.dumps(result,indent=2))
sys.exit(0 if all(x['installed'] for x in result.values()) else 1)
