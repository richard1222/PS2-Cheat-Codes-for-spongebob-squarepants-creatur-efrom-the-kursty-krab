# SpongeBob Creature from the Krusty Krab — Research Toolkit v1.1.0

**v1.1.0 is a stable read-only research toolkit**, not a PS2 debug ISO, a patcher,
or a complete ARM-to-MIPS translator. It cannot activate debug features without
verified game-specific reverse engineering.

The archive contains original Python utilities and synthetic tests only. **No
retail game files, binaries, copyrighted assets, or private OpenCode exports.**

## Windows quick start

Install Python 3.10 or newer. Extract the release ZIP to a folder. Open a terminal
in that folder. These commands need no third-party packages:

```powershell
py tools\spongebob.py doctor
py -m unittest discover -s tests -v
py tools\spongebob.py scan-iso "C:\path\to\your-own-SpongeBob.iso" --json ps2_report.json
```

For a standalone PS2 MIPS ELF or the extracted prototype ARM9:

```powershell
py tools\spongebob.py scan-elf "C:\path\to\SLUS_213.91" --json elf_report.json
py tools\spongebob.py scan-arm9 arm9.bin --term "DEBUG OPTIONS" --json arm9_report.json
```

On Linux or macOS replace `py` with `python3` and use standard local paths.

When using `--json`, the output filename must **not already exist** and cannot
be the input path. Omit `--json` for JSON printed to stdout. Input game files
are read-only and never modified. The ISO scanner supports 2048-byte-sector
ISO9660 images with a root-level `SLUS_213.91`. It does not follow other formats.

## Commands

| Command | Function | Limits |
|---|---|---|
| `doctor` | Detect optional Capstone, Unicorn, Clang and LLVM without installing | Standard library |
| `scan-iso` | Find boot executable in ISO and inspect debug strings and MIPS references | 4 MiB root directory, 64 MiB ELF |
| `scan-elf` | Inspect ELF32 MIPS segments and candidate `LUI + ADDIU/ORI` references | 64 MiB input, bounded hit count |
| `scan-arm9` | Analyze A32 literal-pool references and neighboring `BL` calls | 32 MiB input, bounded radius/hits |

The legacy scripts in `tools/` are included for compatibility and deeper manual
analysis, including a *restricted* ARM-to-MIPS prototype. Some support options
are research-only and do not provide runtime-equivalent MIPS or PS2 patches.

## Accuracy and limitations

- A string occurrence is not evidence that the feature is reachable.
- A static xref is only a candidate until verified in disassembly and execution.
- The MIPS scanner does not follow `$gp`-relative or all EE/R5900 instructions.
  It now conservatively stops when unmodeled instructions may overwrite
  pointer registers, trading completeness for fewer false matches.
- The ARM/DS and PS2 games differ in architecture, hardware, code and engine.
- Unit tests use synthetic ELF/ISO/ARM9 fixtures, **not the retail executable**.
- Optional Capstone and Unicorn packages are NOT required and are NOT yet wired
  into the converter. `doctor` reports presence, not actual emulation readiness.

For an original game executable, record its SHA-256 before interpreting offsets.
Keep game binaries private, and share only JSON research reports.

## Optional packages

```powershell
py -m pip install -r requirements-optional.txt
```

See `RELEASE_NOTES.md` for version-specific QA and release scope. The evidence-first
workflow follows deucebucket's public [No Tool, No Blocker](https://github.com/deucebucket/no-tool-no-blocker)
ideas without redistributing its code or installing its skill in ChatGPT.

## Earlier PS2 cheats and research

The repository also preserves its original PS2 cheat codes, developer-console
research and notes in [`docs/PS2_CHEATS_RESEARCH_ARCHIVE.md`](https://github.com/richard1222/PS2-Cheat-Codes-for-spongebob-squarepants-creatur-efrom-the-kursty-krab/blob/main/docs/PS2_CHEATS_RESEARCH_ARCHIVE.md).
That historical guide is not bundled in this small source-only release ZIP.

