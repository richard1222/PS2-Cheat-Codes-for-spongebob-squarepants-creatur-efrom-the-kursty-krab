# GitHub ARM / MIPS Tools and Converter v0.2

Research date: 2026-10-21

## Compared projects (upstream source, not vendored code)

| GitHub repository | Role |
|---|---|
| https://github.com/capstone-engine/capstone | ARM/MIPS disassembler for reading real ARM9 binary and obtaining instruction operands |
| https://github.com/keystone-engine/keystone | Multi-architecture assembler (candidate for assembled MIPS output) |
| https://github.com/unicorn-engine/unicorn | ARM/MIPS emulator for differential instruction tests |
| https://github.com/NationalSecurityAgency/ghidra | Find debug menu xrefs, functions, memory/structure usage |
| https://github.com/ps2dev/ps2sdk | PS2-native controller and runtime libraries |
| https://github.com/ps2dev/ps2toolchain-ee | EE MIPS toolchain for actual PS2 builds |

These libraries are separate projects; check upstream licenses before embedding sources or redistributing binaries.

## New first-stage converter: tools/arm_binary_to_mips.py

Unlike the original arm_to_mips.py, this tool **reads little-endian A32 machine-code bytes** from a selected .bin region and produces *exploratory*, fail-closed MIPS assembly.

Supported (strict subset): unconditional MOV/ADD/SUB/AND/EOR/ORR/CMP, simple aligned LDR/STR immediate addressing, B/BEQ/BNE with in-region targets, BX LR. Supports ARM immediate rotation. CMP operand values are snapshotted before later registers can change.

Unsupported: Thumb, ADDS/CPSR flag side effects beyond equality, BL or function calls, shifts, other condition codes, coprocessor instructions, stack and engine APIs. These emit errors, not bogus patches. Uses a scratch/test register map, **not a compatible ABI**. The DS and PS2 have different memory maps and game implementations.

### Usage with legitimately obtained and locally extracted ARM9

```sh
python tools/arm_binary_to_mips.py arm9.bin --base 0x02000000 --offset 0x850 --count 2 --report report.json --out sample.mips.s
python tools/arm_binary_to_mips.py arm9.bin --base 0x02000000 --offset 0x850 --count 3 --report halted.json
python -m unittest discover -s tests -v
```

### Observed on the May 25, 2006 DS beta

The extracted ARM9 entry at `0x02000850` begins with ARM words:

- `0xE3A0C301` at `0x02000850`: MOV r12, #0x04000000
- `0xE58CC208` at `0x02000854`: STR r12, [r12, #0x208]
- `0xEB000093` at `0x02000858`: BL; **our translator correctly stops here**

This demonstrates real A32 input can be decoded, **not** that hardware-initialization code is suitable for PS2 execution. The address `0x04000208` is DS-specific and should not be used as a PS2 memory-mapped register.

Local v0.2 build passed **9 Python unit tests**; this commit includes a mirrored test suite. No Keystone assembling, Unicorn execution, MIPS ABI adaptation, or PS2 ISO patching has been performed yet.

## Next steps

1. Add Capstone-powered read-only disassembly and function window selection.
2. Construct a semantic intermediate representation covering ARM condition flags, load/store variants and function calls.
3. Differentially emulate ARM/MIPS code with Unicorn using matched virtual memory and constrained inputs.
4. Reimplement DS debug-menu behavior against verified PS2 level-loader/controller functions.
5. Build checked PS2 patches only after validating user-supplied `SLUS_213.91` hashes and runtime tests.

Do **not** check ROMs, ISOs or copyrighted proprietary source into this public repository.
