# Version 1.0.0 — research toolkit release

**Date:** 2026-10-21

## Release contract

Version 1.0.0 means a stable, reproducible **read-only command-line research
interface**, not a feature-complete SpongeBob PS2 debug ISO. The release is
useful before any retail PS2 executable is uploaded.

## Delivered

- `tools/spongebob.py` with `doctor`, `scan-iso`, `scan-elf`, `scan-arm9`.
- Controlled executable/ARM9 input sizes and bounded analysis options.
- Exclusive-creation `--json` reports; never replace the input or an existing
  report; JSON output is deterministic for the same input/environment.
- Existing ELF/MIPS and ARM9 scanners with older detailed research entrypoints.
- `tools/build_release.py`: deterministic ZIP creation, SHA-256 manifest, source
  allowlist, fixed timestamps, no binaries.
- Synthetic fixture tests. Run `python -m unittest discover -s tests -v`.

## Pre-release bug fixes

- Corrected MIPS string-reference scanning around PS2 SPECIAL2, LL and SC
  register writes, which could otherwise produce false-positive xrefs.
- Corrected `loaded_occurrences` and `truncated` when a report hit limit was reached.
- Added four regression tests.
- Synchronized the GitHub ARM decoder with the locally tested version to
  resolve a CI assertion failure involving the `BL` diagnostic wording.

## Out of scope / still unverified

No PS2 debug-menu activation; no ISO patching or ISO building; no PS2 runtime test.
Game-specific candidate offset claims from historical OpenCode experiments require
independent verification. Capstone and Unicorn optional imports do not constitute
feature integration. ARM-to-MIPS code is a very limited research demonstration.

## Verification gates before publication

1. All unit tests pass from the local source tree.
2. The built ZIP reproduces byte-for-byte when rebuilt from the same tree.
3. All manifest SHA-256 entries match files inside the ZIP.
4. Freshly extracted ZIP passes the same test suite.
5. No `.iso`, `.elf`, `.nds`, executable ROM data, or private exports are bundled.

## Next milestone

Obtain a user-owned PS2 `SLUS_213.91`, generate JSON reports, establish
code xrefs in Ghidra, and verify exactly one debug functionality path.
