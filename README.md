# SpongeBob: Creature from the Krusty Krab — PS2 Debug Research & Toolkit

Research into recovering a **PS2 debug menu and other working developer features**,
with original Python analysis tools and documented evidence.

**Current status:** no working PS2 debug menu or finished debug ISO has been produced.
The published [v1.1.0 toolkit](../../releases/tag/v1.1.0) provides read-only scanners.
The repository also contains newer development tools described below.

## Findings so far

| Area | Verified result | Limit |
|---|---|---|
| May 25, 2006 DS prototype | Boots directly into its debug menu; three pages navigate; Engine Parts launches and responds to movement; Patrick GYM launches | Tested in DeSmuME, not on PS2 |
| Uploaded USA PS2 executable | ELF layout, SHA-256, debug strings, configuration consumers and native menu references inspected | Strings and static references do not prove a working debug menu |
| PS2 menu infrastructure | Variable Menu has construction and callback code in the pause-menu system | Its developer purpose is unconfirmed; it may be an ordinary menu component |
| Development frontend package | Executable requests Splash 640x480 from frontend_devpackage | Package name alone does not demonstrate a hidden interface |
| Earlier initflags experiment | Bit 0 is set by the exclusive option handler | Changing 0x204 to 0x205 is not an established debug-menu activation |

Free-camera and standalone level-selection patches are outside the current requested scope.
DS code, addresses and state identifiers cannot be applied directly to the PS2 game.

## Windows: collect menu evidence

Use Python 3.10 or newer. Download the repository ZIP using **Code → Download ZIP**,
then **extract it**. Open the extracted folder containing tools and double-click:

**Run-Menu-Collector.cmd**

Choose your original PS2 ISO and a new output ZIP filename in the file pickers.
The collector gathers selected pause/debug menu resources for private analysis.
The original ISO is opened read-only; existing output files are refused.
If a dialog reports an error, copy that exact message.

The command-line equivalent, run from the folder containing tools, is:

```powershell
py tools\collect_menu_evidence.py "C:\path\game.iso" "spongebob-menu-evidence.zip"
```

The collector has synthetic archive and ISO tests. Its retail PAKS compatibility
has not yet been verified here. Selected package bytes are capped at 64 MiB.
The resulting evidence ZIP contains game resources: share it privately, not in this repository.

## Analysis commands

The core tools need only the Python standard library. The file-picker launcher also
needs Tkinter, normally included with the Windows Python installer.

```powershell
py tools\spongebob.py doctor
py tools\spongebob.py scan-iso "C:\path\game.iso" --json ps2-report.json
py tools\spongebob.py scan-elf SLUS_213.91 --json elf-report.json
py tools\spongebob.py scan-nds prototype.nds --json prototype-report.json
py tools\spongebob.py inspect-address SLUS_213.91 --address 0x5138E4 --json data-refs.json
```

On Linux/macOS use python3 and local paths. Report filenames must not already
exist. These scanners do not modify their inputs.

| Command | Purpose |
|---|---|
| doctor | Report optional dependencies without installing them |
| scan-iso | Inspect a root-level PS2 boot ELF in a 2048-byte-sector ISO9660 image |
| scan-elf | Find debug strings and candidate MIPS address constructions |
| scan-arm9 | Inspect A32 literal references and nearby direct calls |
| scan-nds | Validate NDS ARM9 bounds and run the prototype scanner directly |
| inspect-address | Find aligned pointer slots and candidate MIPS memory accesses |

scan-nds, inspect-address and the evidence collector are development additions
beyond the published v1.1.0 archive. Legacy ARM-to-MIPS scripts are limited research
demonstrations; they do not port the DS engine or build PS2 debug menus.
Optional Capstone, Unicorn and LLVM tools are not required for the core scanners.

## Research notes

- [Original PS2 cheats and research guide](docs/PS2_CHEATS_RESEARCH_ARCHIVE.md)
- [DS prototype debug-menu trace and runtime tests](docs/NDS_PROTOTYPE_DEBUG_TRACE.md)
- [Uploaded PS2 executable audit](docs/PS2_UPLOADED_ELF_AUDIT.md)
- [PS2 configuration trace and corrected flag interpretation](docs/PS2_CONFIGURATION_TRACE.md)
- [PS2 debug-menu investigation and resource evidence](docs/PS2_DEBUG_MENU_INVESTIGATION.md)
- [Historical native camera research](docs/PS2_NATIVE_FREE_CAMERA_TRACE.md)
- [Published release notes](RELEASE_NOTES.md)

The original research archive preserves earlier hypotheses and unsuccessful patch
attempts. Use the newer evidence notes when assessing those claims.

## Validation and limits

```powershell
py -m unittest discover -s tests -v
```

Latest local suite: **110 tests ran, 109 passed, 1 skipped**. Scanner and collector
tests use synthetic fixtures; they are not PS2 hardware or debug-ISO validation.
The Windows GUI has been syntax-checked; it has not been interactively tested on Windows here.

Static matches are candidates, not proof of reachability. MIPS analysis does not
cover all R5900 instructions, indirect pointers or gp-relative accesses. The package
builder creates source-only archives with an embedded SHA-256 manifest.

Only original tools, tests and research documentation belong in this repository.
Game ISOs, ROMs, extracted executables/resources and private transfers stay outside it.
