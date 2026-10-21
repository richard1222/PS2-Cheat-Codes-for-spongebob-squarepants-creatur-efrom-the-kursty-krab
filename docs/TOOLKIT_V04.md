# SpongeBob Creature from the Krusty Krab — ARM / PS2 research toolkit v0.4

**Research-only tools; no game patcher, no game binaries bundled.**

## New in v0.4

- `tools/arm9_call_context.py`: follow statically located ARM9 string → literal-pointer → A32 PC-relative LDR relationships. Report nearby `BL` direct-call targets and nearby partial opcode classification. This is **not a control-flow proof**.
- `tools/arm9_llvm_disasm.py`: optional full A32 instruction disassembly of small windows using locally installed Clang + `llvm-objdump`. Does **not** need Capstone. Preserves original ARM words in a throwaway local object file; no game data is uploaded or patched.
- `tools/ps2_elf_audit.py`: read-only MIPS ELF32 endianness, entrypoint, PT_LOAD segment and file-offset-to-virtual-address analysis; find debug-related strings and per-build SHA-256. Will reject invalid, truncated or ambiguous ELF layouts.
- 15 new unit tests, plus 11 v0.3 tests (26 tests total locally).

## Current DS prototype menu investigation

ARM9 (May 25, 2006 DS prototype) image base `0x02000000`, SHA256:
`dfb3bc48c9bfba2d2fdeb3567ec17e45e5eebdf716537636380d924212109b5f`

| Label text | Text addr | Literal slot | LDR addr | Nearby BL target |
|---|---|---|---|---|
| `DEBUG OPTIONS` | `0x020BD98C` | `0x0200542C` | `0x02004468` | `0x02004234` (call at `0x02004478`) |
| `TEST INTRO UI` | `0x020BDC50` | `0x0200597C` | `0x02005730` | `0x02004234` (call at `0x02005750`) |

The same ARM function is reached by both calls. Its small disassembled body (at `0x02004234`) saves `r4`/`lr`, writes configuration bytes to offsets 0 and `0x24`, saves an additional word at `0x28`, copies **35 bytes** from the provided text pointer to destination+1 via a call to `0x0205ED10`, then returns the destination pointer. The target `0x0205ED10` starts with a zero-length check and byte-alignment/halfword copy logic, **consistent with memcpy-like behavior**; it has not been dynamically tested or fully labeled. This supports a **menu-entry initialization** hypothesis, **not debug menu activation**.

## Reproduce on local extraction of your own prototype

```powershell
py -m unittest discover -s tests -v
py tools/arm9_string_xrefs.py C:\path\to\arm9.bin --base 0x02000000 --json menu_refs.json
py tools/arm9_call_context.py C:\path\to\arm9.bin --term "DEBUG OPTIONS" --term "TEST INTRO UI" --radius 10 --json menu_context.json
py tools/arm_binary_to_mips_v03.py C:\path\to\arm9.bin --base 0x02000000 --offset 0x850 --count 3 --report blocked.json
```

If you have Clang with the ARM target plus LLVM `llvm-objdump`:

```powershell
py tools/arm9_llvm_disasm.py C:\path\to\arm9.bin --offset 0x4234 --count 13
```

To audit **your local, unmodified** PS2 executable (do not put it on public GitHub):

```powershell
py tools/ps2_elf_audit.py C:\path\to\SLUS_213.91 --file-offset 0x429C30 --file-offset 0x4148E4 --file-offset 0x457F48 --json ps2_audit.json
```

These are offsets *within SLUS_213.91*; they are **not ISO-sector offsets**, and they are unverified hypotheses until your ELF is inspected. The SHA-256 identifies exactly which executable was analyzed.

`Capstone` and `Unicorn` remain optional, unavailable in this environment due to package-index access restrictions. Try on an internet-connected Windows PC:

```powershell
py -m pip install -r requirements-optional.txt
py tools/check_optional_deps.py
```

**No PSP or Manhunt assets belong to this toolkit.** Future work: verify menu constructor's callers; trace debug option selection/activation; map PS2 debug strings to ELF virtual addresses; identify callable native PS2 engine routines; only then implement patch experiments with byte hashes and rollback.