# PS2 configuration trace and toolkit update

Input SHA-256: cd1c65efe630fa23b9ddfbe3525d703a5ba2d4cb548e3c37c5beda42a04c1783.
Read-only static analysis; no PS2 runtime test or ISO patch.

## Toolkit
New inspect-address CLI reports mapped aligned pointer slots and candidate
LUI plus immediate loads/stores. Supports input ELF endianness, bounded
lookahead/hits, signed immediates, conservative register-clobber and control-flow
barriers. It does not follow derived pointers or gp references.
Counts retain totals when output is truncated.
104 repository tests ran: 103 passed, one skipped.
Fresh package: 78 tests ran, 77 passed, one skipped.

## Native configuration flow
0x003AB564 / 0x003AB568 loads the initflags default from virtual 0x005138E4.
0x003AB510 establishes s3 as 0x0051D5F4 and 0x003AB574 stores the selected
initflags value there. Earlier code tries long/short option names using
0x003AAF98 and converts a returned string through 0x004F3EE8; otherwise it
falls back to the executable default.

The code at 0x003AB2FC onward compares option names against:
- 0x00556F08: nonexclusive
- 0x00556F18: nex
and at 0x003AB360 onward against:
- 0x00556F30: exclusive
- 0x00556F40: ex

The nonexclusive handler clears bit 0 via mask 0xFFFFFFFE.
The exclusive handler sets bit 0 at 0x003AB3BC (ORI value, value, 1),
then stores the result to 0x0051D5F4 at 0x003AB3C4.
The nodebugoutput / nd option is handled separately and sets bit 3 (0x8)
at 0x003AB438. These are static handler mappings, not proof of downstream
PS2 behavior or successful runtime argument delivery.

Consequently the historical 0x204 -> 0x205 patch sets the exclusive option bit;
it is not a demonstrated debug-menu patch. Axis inversion is also not menu
activation. No speculative executable modifications are made.

The new scanner finds accesses to initflags storage at 0x003A8A64,
0x003AB354, 0x003AB3B8, 0x003AB3D0, 0x003AB434, 0x003AE630,
0x003AF030 (additional indirect/derived accesses are outside its scope).
At 0x003AE644 and 0x003AF040 the tested bit is 0x4000.

## Negative evidence, carefully scoped
No exact mapped pointer slots or supported LUI-memory access patterns were found
for the debugpad string address 0x00528D68 or debugCamera string address
0x00529140. This does not prove either feature was removed; indirect or alternate
address construction remains possible. A broad Cheat search matched
CHeatHazeParticleEffect, not a cheat menu.

## Next investigation
Follow the native frontend classes/package users and Free Camera object
construction/vtables. Obtain runtime evidence for a specific native feature
before selecting patch bytes. DS debug state 0 is not a PS2 state identifier.
