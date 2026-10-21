# Native PS2 free camera: factory and object trace

Input SHA-256:
cd1c65efe630fa23b9ddfbe3525d703a5ba2d4cb548e3c37c5beda42a04c1783

Read-only static analysis. No executable patch or runtime test.

## Surviving named camera implementation
Registration sequence:
- 0x003A848C loads a0 = 0x00556D38, the string CFFlyAroundCamera.
- 0x003A8494 (delay slot) establishes a1 = 0x003A8140.
- 0x003A8490 calls 0x003A82E0 with those name/factory arguments.
- Factory 0x003A8140 allocates 0x140 bytes through 0x00441140 and
  calls constructor 0x003BD898 at 0x003A8164.
- Constructor passes CFFlyAroundCamera at 0x00557568 to base setup
  0x003BCA70 and stores 0x00557878 at object offset +0xC.
- The table at 0x00557878 includes method pointer 0x003C2888 at
  0x005578A8.
- Method 0x003C2888 copies the Free Camera name from 0x00556E10.

This establishes an internally consistent named-class, factory, constructor,
method-table and display-name chain. It is stronger evidence than unused text.
It does not establish that registration runs on the tested startup path or that
the class can safely replace the gameplay camera.

The neighboring registration loads CFPivotCamera from 0x00556D50 and factory
0x003A8178. That factory allocates 0x150 bytes and calls 0x003BDF48.
Its method-table name routine 0x003C28B8 copies Pivot Camera.
These separate object sizes and constructors show why swapping isolated names,
pointers or instruction immediates without matching object initialization risks
memory corruption.

## Controls/configuration
Fly-around constructor accesses the real debuginvertyaxis and debuginvertxaxis
table entries at 0x00513944 and 0x00513938, and default debugswapsticks at
0x0051392C. These are camera-control configuration, not menu activation.
Further input routine analysis is needed for actual button mapping.

## Next gate
Trace callers of factory lookup 0x003A83A0 / 0x003A83C8 and the point where a
camera object is selected into the active context. Verify context lifetime,
allocation size, virtual calls, player tracking and restoration before building
an isolated experimental patch. No working PS2 debug menu is claimed.
