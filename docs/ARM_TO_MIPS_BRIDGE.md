# ARM-to-MIPS bridge v0.1

An experimental, deliberately limited **ARM assembly-text to MIPS assembly-text translator** for the *Creature from the Krusty Krab* debug investigation.

## Usage

```bash
python tools/arm_to_mips.py examples/arm-menu-sample.arm --out out.s
python -m unittest discover -s tests -v
```

### Supported instructions
`MOV`, `ADD`, `SUB`, `CMP` followed by `BEQ`/`BNE`, `B`, and `BX lr`; labels and simple register or immediate operands. Uses MIPS pseudo-instructions and inserts branch-delay NOPs. Unsupported inputs fail explicitly.

### Limitations

- This translates *assembly text*, not ARM9/ARM7 binaries or an entire DS ROM.
- The mapping is **not ABI safe**; ARM/PS2 calling conventions are different.
- CMP is only treated as a deferred equality comparison; CPSR flags are not reproduced.
- No ARM Thumb mode, conditionally executed instructions, memory accesses, load/store, function calls, PC-relative addressing, interrupt code, shifts, or hardware register emulation.
- No native PS2 ISO modification is performed. Generated code has not been assembled or run on a PS2.
- DS prototypes (WayForward/ARM) and PS2 executable (Blitz/MIPS) are separate implementations. The goal is to reuse *behavioral understanding*, not presume code compatibility.

## Known research targets
The local May 25, 2006 beta report identifies ARM9 load `0x02000000` and entry `0x02000850`, ARM7 load/entry `0x02380000`, and menu resource strings including `levelselect` and `stageselect`. ARM7 contains an `IS-NITRO-DEBUGGER` library string, which by itself is **not** an executable debug-menu entry point.

## Next development stages
1. Disassemble selected ARM9 functions (with Ghidra or Capstone) and annotate their actual behavior.
2. Build an intermediate representation modeling condition flags, memory, control flow, calls and return values.
3. Add differential execution tests for small translated functions.
4. Create a PS2 MIPS runtime interface for controllers, menus, and level transitions.
5. Only then make version-checked executable patches and separately validate experimental ISO builds.

No commercial ROMs, ISO images, or extracted proprietary binaries should be checked into this public repository.
