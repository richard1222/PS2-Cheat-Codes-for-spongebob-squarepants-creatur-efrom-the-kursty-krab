# DS Prototype Archive Search — 2026-10-21 (follow-up)

## Confirmed public catalog information
The [Hidden Palace WayForward lot](https://hiddenpalace.org/w/index.php?title=WayForward_lot) catalogs the following DS prototypes of *SpongeBob SquarePants: Creature from the Krusty Krab*:

| Build | Timestamp | Research purpose |
|---|---|---|
| May 25, 2006 | 18:20:43 | Earliest documented debug-menu frontend; original filename `parent.srl` |
| June 8, 2006 | 17:47:32 | Closest subsequent comparison |
| June 15, 2006 | 12:07:42 | Look for surviving debug strings/functions |
| July 5, 2006 | 19:02:48 | Mid-development comparison |
| August 13, 2006 | 20:10:30 | Late-stage comparison; filename `20060813.srl` |

The May 25 page says it boots to a developer-facing menu, including `GAME SELECT` and `TEST INTRO UI`, but that is documentation, **not** proof that the binary was acquired or analyzed in this project.

## Archive access status
- Hidden Palace catalog pages: indexed and documented.
- Internet Archive item `cftkk-ds-src`: named in this repository's existing README, but direct page and metadata retrieval failed from the research environment. Its contents, authenticity, and distribution permissions are **unverified**.
- Planet Emulation May 25 beta listing: previous research located a listing, but retrieval of the actual file was not confirmed.
- Wayback CDX and direct snapshot queries: unsuccessful from the research environment.
- **No DS prototype ROM has been acquired, extracted, or disassembled yet.**

## Actionable next steps
1. Obtain a legitimately shareable ROM from an authorized source; record full SHA-256, CRC32, filename, and NDS header build metadata.
2. Run local NDS extraction on the copy to extract ARM9 and ARM7, map offsets to load addresses, and search strings.
3. Compare at least two adjacent dates (May 25 and June 8 are ideal) and trace `GAME SELECT` references in Ghidra.
4. Independently reverse-engineer PS2 `SLUS_213.91` to implement equivalent features using PS2-native MIPS patches.

Research archive only: do not add copyrighted ROM dumps or unlicensed proprietary source to this public repository.
