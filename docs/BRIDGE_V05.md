# SpongeBob Creature from the Krusty Krab — Research Toolkit v0.5

**Read-only research. Not a PS2 debug ISO or a working ARM-to-MIPS game-porting system.** No game ISO, executable, copyrighted game asset, or private chat export is bundled.

## What's new

- **`tools/ps2_mips_string_xrefs.py`** scans executable PT_LOAD segments for candidate `LUI` + `ADDIU` / `ORI` address-construction pairs whose 32-bit result points to a debug-related ASCII string in the same ELF. Handles MIPS little-/big-endian encoding and the signed 16-bit ADDIU immediate; stops at jumps, branches, and register clobbers.
- **`tools/ps2_iso_probe.py`** reads ISO9660 PVD/root directory and locates `SLUS_213.91;1`; hashes and audits its executable **in memory** and reports the MIPS code-reference candidates. It does not patch, mount, extract, or rewrite the game image. It rejects malformed extents, oversized directories/executables, and ambiguous boot-file entries.
- **`tests/test_v05.py`** provides synthetic MIPS ELF and ISO9660 fixtures. All 47 suite tests passed locally (26 prior + 21 new) under Python 3.13 on 2026-10-21. No retail game image was used for these tests.

## Usage on Windows (Python 3.10+)

From the extracted toolkit directory in PowerShell:

```powershell
py -m unittest discover -s tests -v
py tools\ps2_iso_probe.py "C:\path\to\your-own-SpongeBob.iso" --json ps2_iso_audit.json
py tools\ps2_mips_string_xrefs.py "C:\path\to\SLUS_213.91" --json ps2_mips_xrefs.json
py tools\ps2_elf_audit.py "C:\path\to\SLUS_213.91" --json ps2_elf_audit.json
```

Only the JSON reports are written when `--json` is specified, to the chosen paths. Input ISO and executable are never modified. The ISO scanner expects a **2048-byte-sector ISO9660 image** containing `SLUS_213.91` at the disc root; other images or custom layouts can be inspected separately after extraction with an authorized local tool.

### Debugging from the DS prototype

```powershell
py tools\arm9_string_xrefs.py arm9.bin --base 0x02000000 --json arm9_xrefs.json --csv arm9_xrefs.csv
py tools\arm9_call_context.py arm9.bin --base 0x02000000 --radius 32 --json arm9_calls.json
py tools\arm_binary_to_mips_v03.py arm9.bin --base 0x02000000 --offset 0x850 --count 3 --report blocked.json
```

The ARM9 prototype's `DEBUG OPTIONS` string and `TEST INTRO UI` reference chains remain promising research leads, but the DS and PS2 have different developers, architectures, hardware addresses, engines and UI code. A valid pointer or function address in the DS binary is not a valid PS2 patch offset.

## Optional dependencies

```powershell
py -m pip install -r requirements-optional.txt
py tools\check_optional_deps.py
```

`capstone` and `unicorn` are optional and **not yet integrated** into these v0.5 scanners. Package resolution failed in our hosted execution environment; core v0.5 scanners need neither module. `arm9_llvm_disasm.py` optionally requires external Clang + `llvm-objdump`.

## What the results mean

- A **string occurrence** means its bytes are present in a file-backed ELF segment.
- A **static reference candidate** is a pair of instruction words which *looks like* it computes a string's virtual address. It does not establish that those bytes are reachable code, that the string is actively used, or that a debug menu is enabled.
- A **successful test** verifies the documented functions on controlled synthetic inputs. It is not confirmation of PCSX2/PS3 runtime behavior or of any retail game's debug features.
- Patterns outside our subset (e.g. `$gp`-relative loads, LUI+LW, additional arithmetic, MIPS64/R5900-specific instructions) are not yet covered. False negatives are expected; disassembly and function tracing in Ghidra remain essential.

## Suggested next step

Run `ps2_iso_probe.py` on an unmodified, locally owned `Creature from the Krusty Krab` NTSC-U PS2 image, then share **only the JSON report** with this chat. We can investigate which debug-flag string candidates have references, inspect function context, and make a targeted test plan without guessing executable offsets. Avoid committing ISOs, game executables, or private data to a public GitHub repo.

## Source attribution

Our project remains independent. We adopted an evidence-first tool-gap workflow inspired by deucebucket's public [No Tool, No Blocker](https://github.com/deucebucket/no-tool-no-blocker) Codex skill; we did not embed or install its code as a ChatGPT runtime extension.
