# Uploaded PS2 executable: first verified audit

Input: SLUS_213.91, 4,720,268 bytes.
SHA-256: cd1c65efe630fa23b9ddfbe3525d703a5ba2d4cb548e3c37c5beda42a04c1783

ELF32 little-endian MIPS, entry 0x00100008. PT_LOAD maps file offset
0x1000 to virtual 0x00100000 (file-backed size 4,611,916).
For this segment only: virtual address = file offset + 0xFF000.
The uploaded input was analyzed read-only; no game executable is published.

## Verified string locations
| String | File offset | Virtual address |
|---|---|---|
| debugpad | 0x429D68 | 0x00528D68 |
| showfps | 0x429D80 | 0x00528D80 |
| debugCamera | 0x42A140 | 0x00529140 |
| debugfont | 0x42A100 | 0x00529100 |
| DebugPackage | 0x42A110 | 0x00529110 |
| frontend_devpackage | 0x42E868 | 0x0052D868 |

## Code references
Toolkit found a Free Camera string address construction at 0x003C2888 /
0x003C288C, referring to 0x00556E10. Disassembly shows a small string-copy
routine, not a demonstrated camera activation function.
frontend_devpackage has address-construction candidates at 0x001E18A4,
0x001E18E4, 0x001E19F8, 0x001E1A64 and 0x001E1C38.
At 0x001E18B8 the code calls 0x003AF310 after loading that package name;
the result is stored at object offset 0x150. Resource-loader semantics remain
an inference pending callee inspection.
At 0x001E1894 a call targets 0x003C2918, which is just jr ra / nop.
Several adjacent routines from 0x003C2910 through 0x003C2950 are also returns.
Their names/purpose are not established; do not label them debug activation
functions solely from proximity.

## Configuration table correction
At file offset 0x414890 there are value / abbreviation / name triples.
Verified entries include:
- 0x4148E4: initflags default 0x204.
- 0x4148F0: fps default 60.
- 0x4148FC: minfps default 30.
- 0x41492C: debugswapsticks default 1.
- 0x414938: debuginvertxaxis default 0.
- 0x414944: debuginvertyaxis default 0.

Following rows mix small integers with absolute string pointers. Their meaning
must be established from the table-reading code before editing. Earlier notes
that imply a uniform pointer table or assign all following values directly to
debug options are not sufficient evidence for patches.
Changing axis inversion is not evidence of enabling a debug menu.
The existing 0x204 initflags value does not establish what bit 0 controls.

## Limits and next analysis
No patch has been selected and no PS2/PS3 runtime test performed.
Trace consumers of the configuration table and the native development frontend,
then choose one independently verified feature for an isolated experiment.
The DS prototype's state 0 and ARM addresses do not transfer to this executable.
