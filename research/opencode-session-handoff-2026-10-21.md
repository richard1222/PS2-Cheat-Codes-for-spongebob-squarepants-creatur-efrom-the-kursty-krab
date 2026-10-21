# OpenCode Research Handoff — 2026-10-21

## Provenance and limitations

These notes were distilled from a **user-supplied OpenCode conversation JSON export**, covering prior work on *SpongeBob SquarePants: Creature from the Krusty Krab* (PS2). The exported conversation contains task messages and many shell-tool inputs/outputs, **not** all files from the original Windows workspace. Observations below are reproduced from the recorded command outputs; the binaries and hardware tests have **not** been independently rerun for this handoff.

Do **not** commit the raw export. It also covers unrelated projects and local machine information.

## PS2 retail executable inspection

- Target executable: `SLUS_213.91` (NTSC-U).
- Recorded ISO9660 root directory read: root directory LBA **261**.
- Recorded `SLUS_213.91;1` directory entry: file LBA **832**, size **4,720,268 bytes**, ISO byte offset **0x1A0000** (832 × 2048). **Build-specific; validate against your own ISO**, do not hard-code globally.
- Searches of the extracted executable reportedly found strings `debugpad`, `showfps`, `debugCamera`, `debugfont`, `DebugPackage`, `Free Camera`, `debuginvertxaxis`, `debuginvertyaxis`, `debugswapsticks`, and `nodebugoutput`. A string's presence **does not prove** a reachable menu or working functionality.
- A series of string scans targeted file offset **0x429C30**, described as a possible debug/config name table. Multiple ad hoc parsers yielded inconsistent or garbled entries depending on assumed padding, so the claimed exact entry count / structure is **unverified**.
- Config/descriptor data were probed near file offset **0x414890**; a test changed a candidate `initflags` value near offset **0x4148E4** from `0x204` to `0x205` or `0x20F`. **The meaning and runtime activation behavior have not been established by a disassembly**.
- The string `nodebugoutput` was found at reported file offset **0x457F48** in one session; renaming it is not the same as toggling its controlling flag.

## Debug ISO attempts and observed results

The OpenCode record documents experimental changes made on local copies of the user's PS2 ISO, followed by user reports of **no visible FPS counter or usable debug menu**:

| Experiment | Recorded outcome |
|---|---|
| Alter `SYSTEM.CNF` boot entry to add `debugpad showfps` | No debug overlay; this is not a verified argument-passing mechanism for the game |
| Patch candidate `initflags` from `0x204` to `0x205` and later `0x20F` | No visible debug functions reported |
| Set candidate inverted-camera axis defaults | No visible debug functions reported |
| Rename `nodebugoutput` text to `xodebugoutput` | No visible debug functions reported |
| Set several descriptor defaults to 1 | No visible debug functions reported |

The ISO-edit script replaced the executable at its existing byte location without changing its length (4,720,268 bytes). This **preserves layout**, but is not a guarantee of a bootable or functional image. Some build/boot failures were reported elsewhere in the overall session; preserve known-good original dumps and verify each candidate before hardware testing.

**No working debug menu was established. Do not mark these experiments as confirmed patches.**

## ALLPAKS extraction evidence

The OpenCode transcript contains a Python extractor script creation event and an extraction log:

- A parser reported **672** archive entries.
- A later directory listing reported **673** output files: **669** `.ps2`, **3** `.txt`, **1** `.sys`. The difference could be generated indexes/reports rather than original archive entries; reconcile programmatically.
- Named artifacts included `bonuspak_plankton gangster.ps2`, `debugpackage.ps2`, and `frontend_devpackage.ps2`.
- The tool `allpaks_extractor.py` and `extracted_files_list.txt` already exist in this GitHub repository. Validate exact counts and size claims against an independently hashed original `ALLPAKS.PS2`.

## What can actually be reused

1. **Shell commands and heuristics** in the exported session provide reproducible starting points for ELF/ISO9660 table inspection, string scanning and archive extraction.
2. **Existing GitHub source** includes `allpaks_extractor.py` and our separate ARM-to-MIPS proof-of-concept tools.
3. The raw session export **does not include the proprietary PS2 executable, the local ISO, or a complete workspace ZIP**. It does not confer access to the local PC filesystem.
4. The DS May 25 prototype studied separately provides ARM9/ARM7 and debug-menu research, but the PS2 and DS games use different CPU architectures and implementations.

## Recommended next engineering work

1. Acquire a legitimate, user-supplied `SLUS_213.91` executable; record SHA-256, ELF segments, executable CRC, and compare with reported offsets.
2. Parse debug/config structures using ELF-aware addresses and a disassembler (Ghidra/Capstone), rather than arbitrary string splitting or pattern substitution.
3. Trace code references to `debugpad`, `showfps`, `debugCamera` and level transition handlers.
4. Verify which flags are parsed, what calls initialize debug rendering, and whether developer-only routines survive retail compilation.
5. Implement and test a *single* PS2-native menu action, then add features incrementally; never assume translating DS ARM startup code will yield a working PS2 interface.
6. Build patches with expected-original bytes, SHA-256 checks and reversible outputs. Keep complete retail images, copyrighted assets and private local-session exports **out of the public repository**.

## Collaboration

OpenCode's `/export` command exports a **conversation**, not its project directory. For actual tool integration, separately export or commit **original scripts, tests and documentation** to a shared GitHub branch or upload a source-only ZIP to connected Google Drive. Do not upload game ISOs or private application credentials.
