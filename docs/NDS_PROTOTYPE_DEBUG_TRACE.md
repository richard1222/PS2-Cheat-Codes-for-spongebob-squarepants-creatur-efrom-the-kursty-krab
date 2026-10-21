# May 25, 2006 NDS prototype: debug activation trace

## Evidence and scope
Analyzed user-provided prototype read-only. ARM9 SHA-256:
dfb3bc48c9bfba2d2fdeb3567ec17e45e5eebdf716537636380d924212109b5f
ROM ARM9 offset 0x4000; load 0x02000000; entry 0x02000850; size 810552.
Addresses below are ARM9 virtual addresses, not PS2 offsets.
Static analysis with toolkit scanners and Capstone A32 disassembly.
No emulator or hardware execution was performed.

## Debug screen construction
- 0x02004468 loads the DEBUG OPTIONS text pointer through literal slot 0x0200542C.
- 0x02004478 calls entry initializer 0x02004234.
- Initializer writes entry ID at +0, copies 35 label bytes into +1,
  writes a byte at +0x24 and a word at +0x28.
- Its parent builder starts at 0x02004454.
- Constructor 0x020040E8 calls that builder at 0x02004204.
- Other labels include SpongeBob GYM, Patrick GYM, Plankton GYM,
  Test Driving, Test FLying, Debug Menu (this screen), and TEST INTRO UI.

## State selection chain
- Factory at 0x0200101C bounds the selector against 0x23 and dispatches
  through an inline branch table starting at 0x02001040.
- Selector 0 branches to 0x020010D0; its constructor call at 0x020010F4
  targets 0x020040E8, establishing the debug-screen constructor chain.
- State transition routine at 0x0204B9DC preserves selector in r4 and calls
  factory 0x0200101C at 0x0204BA50.
- At 0x02000C9C, a startup-path routine sets r0 to 0.
  At 0x02000CA0 it calls 0x0204B9DC.
- Callback 0x02005C88 also sets selector 0 before tail-branching through a
  literal pointer to 0x0204B9DC.

## Conclusion
The prototype contains a static startup-path request for the debug-screen state.
This is stronger than a string occurrence and suggests no activation patch is
needed for this DS prototype. It does not prove startup reachability or successful
rendering at runtime. No button combination has been established.
The next validation is to boot the unchanged prototype and observe state 0.

## PS2 implications
This DS menu uses DS graphics hardware (for example accesses in the 0x04000000
range). Neither this state ID nor its ARM addresses can be used as PS2 patches.
A PS2 executable or PS2 prototype is still required to establish a native path.


## Runtime verification — 2026-10-21
Booted the unchanged user-provided NDS image in DeSmuME 0.9.12,
interpreter CPU, software rendering, headless SDL. After 180 frames the rendered
screen visibly shows:
- SpongeBob DS: Debug Menu
- Thu May 25 18:20:43 PDT 2006
- Page 1 of 3
- LEVEL 01: Tutorial - License Chase, Engine Parts
- LEVEL 02: Hot Rodding (Race)
- LEVEL 03: Train Training
- LEVEL 04: Money Bags, Thieves, Hostages
- LEVEL 05: Krusty Krumb
- LEVEL 06: Bull Worm - TOUCH
- LEVEL 07: Bull Worm - FLYING
- LEVEL 08: Rocket - FLYING

This confirms automatic debug-menu rendering without an activation patch on
this DS prototype in this emulator. It supersedes the earlier uncertainty about
whether the menu renders at startup. It does not establish PS2 compatibility.

Attempted scripted right/left/A input, but the captured final screen remained
on page 1. Navigation and level launch are NOT verified; no successful launch
is claimed. No game ROM or extracted executable is published.


## Follow-up runtime verification — navigation and level launch
Repeated tests with DeSmuME 0.9.12 using cycle(with_joystick=False), so the
headless harness does not poll joystick state during scripted keypad input.
The earlier unsuccessful input attempt did not demonstrate broken game controls.

Observed:
- Down changes the selected entry. Scrolling reaches pages 2 and 3 and wraps.
- Page 2 includes levels 09–15.
- Page 3 includes TEST INTRO UI, START MENU, MAIN MENU, LANGUAGE SELECT,
  OPTIONS MENU, SpongeBob GYM, Patrick GYM, Plankton GYM, Test Screen Link,
  Test Driving, Test Flying and Debug Menu (this screen).
- From fresh boot, Down once selects Engine Parts. A launches a rendered scene
  with SpongeBob on a platform. After 600 frames it remains rendered.
- Holding Right for 90 frames changes SpongeBob/camera position, demonstrating
  response to movement input. This does not constitute a full level test.
- In a separate fresh boot, 15 Down taps selected Patrick GYM (selection was
  visually checked). A launched a rendered test scene with Patrick, visible
  terrain and a red object. Scene was checked after 600 frames.
- No long-duration stability, completion, all-option, PS2 or PS3 tests performed.

Boot and basic interaction now work without a ROM patch in this emulator.
The prototype can supply verified menu structure and test-scene behavior as
research references. A native PS2 implementation still needs PS2 executable
analysis; these DS routines cannot be used as PS2 patch addresses.
