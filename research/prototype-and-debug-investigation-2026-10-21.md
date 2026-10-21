# Prototype and Debug Research — 2026-10-21

## Scope
SpongeBob SquarePants: Creature from the Krusty Krab, focusing on PS2 NTSC-U `SLUS_213.91` and documented Nintendo DS prototypes. Research notes and analysis procedures only; no commercial ROMs or game assets.

## Leads and verification status

| Lead | Status | Follow-up |
|---|---|---|
| PS2 executable `SLUS_213.91` | Target identified | Verify SHA-256 and executable's actual MIPS symbols/strings from an owned copy |
| Strings `debugCamera`, `Free Camera`, `CFFlyAroundCamera`, `debugpad`, `debugfont`, `showfps`, `minfps` | Reported in repository README, offsets unverified here | Locate exact strings and cross-references in Ghidra |
| `debugpackage.ps2` and `frontend_devpackage.ps2` | Reported in extracted ALLPAKS inventory | Inspect contents; filenames alone do not prove a usable menu exists |
| DS May 25, 2006 prototype | Hidden Palace record describes debug-style frontend including `GAME SELECT` and `TEST INTRO UI` | Obtain a verifiable research copy and record checksum |
| DS June 8 / June 15, 2006 builds | Alternate documented prototype leads | Verify whether archive downloads work before claiming features |
| `SB06` / `40 Winks` | Historical development-name lead | Search early prototype press, unused retail title assets, and archived development material |
| PS2 emulator patch community | Widescreen and FPS-related patch discussion | Reproduce only against matching game/version CRC |

**Not yet accomplished:** no DS ARM9/ARM7 extraction from a verified prototype, no MIPS function-address validation, no functional PS2 developer menu, and no tested debug ISO.

## Research links

- [Hidden Palace May 25 DS prototype](https://hiddenpalace.org/SpongeBob_SquarePants%3A_Creature_from_the_Krusty_Krab_%28May_25%2C_2006_prototype%29)
- [Hidden Palace DS prototype catalog](https://hiddenpalace.org/Prototypes_by_system/Nintendo_DS)
- [Wayback snapshots of the May 25 page](https://web.archive.org/web/*/https://hiddenpalace.org/SpongeBob_SquarePants%3A_Creature_from_the_Krusty_Krab_%28May_25%2C_2006_prototype%29)
- [PCSX2 widescreen patch community](https://forums.pcsx2.net/Thread-PCSX2-Widescreen-Game-Patches)
- [GameHacking.org: PS2 entry](https://gamehacking.org/game/105013)
- [Blitz Games retrospective](https://www.blitzgames.com/games/spongebobcftkk)

## Tooling workflow

1. **Inventory:** hash all input files (SHA-256) and preserve the original ISO/ROM.
2. **PS2 data extraction:** use existing repository script `allpaks_extractor.py` or QuickBMS `blitz_games.bms` to list game packages and record offsets and lengths.
3. **Nintendo DS binary extraction (when a ROM is available):** parse the NDS header, identify ARM9/ARM7 binary file offsets, sizes, RAM load addresses, and entry points, and extract both binaries.
4. **DS menu analysis:** scan ASCII/UTF-16LE for `GAME SELECT`, `TEST INTRO UI`, `DEBUG`, `LEVEL`, `CAMERA`; in Ghidra map segments using actual load addresses and trace string references, controller input and dispatch functions.
5. **PS2 analysis:** load `SLUS_213.91` as a PS2 MIPS ELF in Ghidra; follow references to debug strings and investigate renderer, controller polling and level loader.
6. **Patching:** require exact input hashes and expected bytes at each patch site, fail closed on mismatches, emit a new modified executable rather than overwriting the source.
7. **Experimental ISO:** rebuild from properly extracted filesystem contents only after patch verification; test on emulator, then cautiously test on PS3 webMAN MOD. Track boot success, controller input and regression results.

## Important caveats

- WayForward developed the DS version; Blitz Games developed the PS2 version. DS ARM code cannot be transplanted into the PS2 MIPS binary. The DS debug interface is a design and behavior reference, not proven shared code.
- Hidden Palace documentation does not guarantee a currently downloadable binary.
- Community cheat addresses must be version-checked; reported CRC `82C46B7A` is not verified against the user's own executable.
- This public repository should contain **original tools, patch descriptions, tests, findings, and documentation only**. Do not commit proprietary ROMs, full game ISOs, extracted assets, or unreleased source.

## Next tasks

- [ ] Verify PS2 ELF executable and identify xrefs for debug strings.
- [ ] Test `allpaks_extractor.py` against a local legally obtained copy of `ALLPAKS.PS2`.
- [ ] Acquire and authenticate a DS prototype research copy.
- [ ] Produce ARM9/ARM7 address tables and Ghidra analysis notes.
- [ ] Document a minimal PS2 debug feature and patch validation test before ISO rebuilding.
