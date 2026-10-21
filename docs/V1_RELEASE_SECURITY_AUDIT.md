# v1.0.0 release security and provenance review

Audit date: 2026-10-21. Scope: the **source-only** `spongebob-toolkit-v1.0.0-reviewed.zip` produced locally using `tools/build_release.py`. This is a bounded pre-publication review, not a security certification or proof against unknown vulnerabilities.

## Reproducible checks

- 65 local Python `unittest` tests passed after README updates (`PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -q`).
- Two independent packaging runs produced the **same ZIP hash**.
- SHA-256 of reviewed ZIP: `5819c1bc86bab459344396b556ca82a95bf067bbb4da4e6f443cfedd68b90dc6`.
- The ZIP contains **21 entries**: 20 allowlisted text/source files and 1 `MANIFEST.sha256`.
- Every manifest SHA-256 matched the corresponding entry; every included file matched its local source.
- Every ZIP entry lives under the expected top-level folder, is marked as a regular file, and has no absolute path, traversal component, or symlink.
- No game `.iso`, `.nds`, `.elf`, `.bin`, `.exe`, `.prx` files, original game assets, private OpenCode conversation exports, local user directories, or credential-looking strings were found in the release ZIP.
- Search for network/import/export or shell capabilities found **no direct network requests** in the bundled toolkit. The optional `arm9_llvm_disasm.py` helper invokes locally installed `clang` and `llvm-objdump` with fixed argv, a temporary working directory, bounded count, and subprocess timeouts; these executables are **not included** in the ZIP.
- The supported unified CLI `tools/spongebob.py` reads input files without writing changes and uses exclusive create mode for `--json` reports. **Important:** some older scripts included for backwards compatibility still use `write_text` for a user-chosen report path, potentially overwriting existing reports; prefer the unified CLI.

## Documentation preservation

The original 867-line PS2 cheats and research README would otherwise be replaced by the compact toolkit landing page. It has been preserved in `docs/PS2_CHEATS_RESEARCH_ARCHIVE.md`, with a link in the new README. That historical research document is not included in the source-only ZIP.

## Known limits

- The program is **not** a PS2 patcher, ISO builder, cheat activator, or complete ARM-to-MIPS translation system.
- Unit tests use synthetic data; no real retail `SLUS_213.91` or PS2 hardware was tested as part of this audit.
- Libraries Capstone and Unicorn are **optional, not bundled, not installed** or integrated in this release.
- No dynamic malware sandboxing or formal penetration test was conducted.
- No software license was added on behalf of the project owner; before encouraging outside reuse or contributions, the owner should choose an explicit license.

## Recheck

```sh
python -m unittest discover -s tests -q
python tools/build_release.py ../release-a.zip
python tools/build_release.py ../release-b.zip
sha256sum ../release-a.zip ../release-b.zip
```

The builder never overwrites an existing archive. Compare the produced hash with the reviewed hash only when building from **this exact reviewed source tree**.
