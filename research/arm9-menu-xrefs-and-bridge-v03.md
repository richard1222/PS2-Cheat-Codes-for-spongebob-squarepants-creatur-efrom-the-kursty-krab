# ARM9 Debug-Menu Reference Research + Bridge v0.3

**Research date:** October 21, 2026. **Target:** WayForward DS *Creature from the Krusty Krab* prototype, May 25, 2006.

## Reproducible inputs

The user's extracted ARM9 binary loads at `0x02000000`, entry `0x02000850`, size 810,552 bytes, SHA-256:

`dfb3bc48c9bfba2d2fdeb3567ec17e45e5eebdf716537636380d924212109b5f`

No ROMs, extracted game binaries, copyrighted data, or private OpenCode export is committed.

## Verified static reference chains

| String | ARM9 RAM address | Literal pointer slot | Candidate LDR instruction |
|---|---|---|---|
| `DEBUG OPTIONS` | `0x020BD98C` | `0x0200542C` | `0x02004468` (`0xE59F2FBC`) |
| `TEST INTRO UI` | `0x020BDC50` | `0x0200597C` | `0x02005730` (`0xE59F2244`) |

These are verified **byte-level** chains: exact string bytes, little-endian pointer words containing the loaded address, and PC-relative A32 LDR instruction patterns resolving to the pointer-slot address. They are **not** verified menu activation functions or evidence of dynamic execution; Ghidra must determine code vs data and call context.

The prototype also contains resource names `game_select_`, `levelselect` and `stageselect`. The basic pointer scanner found no direct static LDR-to-absolute-pointer chains for these particular filenames, so search asset loading/relative structures next.

## v0.3 tool usage

```sh
python tools/arm9_string_xrefs.py path/to/arm9.bin --base 0x02000000 --json xrefs.json --csv xrefs.csv
python tools/arm_binary_to_mips_v03.py path/to/arm9.bin --base 0x02000000 --offset 0x850 --count 3 --report blocked.json
python -m unittest discover -s tests -v
python tools/check_optional_deps.py
```

The report CSV includes only string offsets, literal slots, and candidate opcode addresses—not original game code bytes.

### New fail-closed translator gate

The v0.2 converter can produce MIPS for a basic A32 instruction subset, but identical-looking loads/stores can have incompatible hardware effects on PS2. v0.3 forbids all `LDR`/`STR` until explicit PS2-side memory semantics exist, detects obvious DS MMIO addresses from basic constant propagation, and blocks ambiguous CMP/branch flag lifetime.

The real ARM9 startup block illustrates the need:

- `0x02000850`: `MOV r12, #0x04000000`
- `0x02000854`: `STR r12, [r12, #0x208]` → **DS hardware address `0x04000208`**
- `0x02000858`: a `BL` function call, unsupported

v0.3 refuses these operations. **Even successfully generated register-only assembly is research output, not a PS2 patch**: calling convention, memory, controller, menu, and level-loading APIs differ between WayForward DS and Blitz PS2.

### External libraries

- [Capstone](https://github.com/capstone-engine/capstone) for more accurate disassembly.
- [Unicorn](https://github.com/unicorn-engine/unicorn) for differential CPU emulation.

They are **not installed** in the current execution environment: pip could not resolve the package-index host. The two tools above require only Python's standard library and the repository's existing `tools/arm_binary_to_mips.py`. On a connected Windows machine, install optional packages with `py -m pip install -r requirements-optional.txt` and check them with `python tools/check_optional_deps.py`. Neither has yet been integrated into code translation.

### Ghidra investigation targets

1. Load extracted `arm9.bin` as ARM little-endian, image base `0x02000000` and entry `0x02000850`.
2. Navigate to `0x02004468`; confirm A32 LDR points through `0x0200542C` to `DEBUG OPTIONS`.
3. Navigate to `0x02005730`; confirm A32 LDR points through `0x0200597C` to `TEST INTRO UI`.
4. Trace the containing functions, caller cross-references, and menu-control paths. Compare with existing `levelselect` resource loading.
5. Analyze `SLUS_213.91` **independently**, then design MIPS-native menu behavior after validating its game-specific APIs.

**Status:** static debug-menu pointer leads identified; 11 new local tests passed; no PS2 debug menu has been activated or built.
