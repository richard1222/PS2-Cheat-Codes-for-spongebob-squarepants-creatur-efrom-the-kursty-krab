# PS2 debug-menu investigation

## Current requested scope
Debug menu and other recoverable developer functionality.
Free-camera and standalone level-selection patches are excluded.
No PS2 debug menu has been activated. Do not describe the DS menu as a PS2 menu.

## Verified native menu infrastructure
Input ELF SHA-256:
cd1c65efe630fa23b9ddfbe3525d703a5ba2d4cb548e3c37c5beda42a04c1783

- String Variable Menu at virtual 0x0052DCC8 is used by constructor 0x001EE0F8.
- Constructor requests Variable Menu Set at 0x0052DCD8 through 0x003C92E8,
  then registers callback 0x001EE6C0 through 0x00399538.
- It checks parent/resource pointers before initialization and falls back to a
  failure path if missing. Renaming a string alone would not supply its resources.
- Menu dispatcher 0x001EB218 uses a 22-entry jump table at 0x0052DB20.
  State 0 allocates 0x1C bytes and constructs Variable Menu at 0x001EB2E0.
- Helper 0x001E9D30 installs the callback/user data and requests state 0.
  Direct callers include 0x001E6DF8, 0x001EA944 and 0x001EACE0.
- These paths belong to the pause-menu infrastructure. Variable Menu is not yet
  established as a developer interface; it may be a generic ordinary menu.
- frontend_devpackage references at 0x001E18E4 onward request the asset
  Splash 640x480 from 0x0052D880. Package loading alone does not establish a
  debug interface.
- DebugMessageEcho and faDebugEcho are named object types with deserialization
  and name-return methods. Their names do not establish an interactive menu.
- ConsoleWindow has a buffer/formatting constructor at 0x00415F68, but whether
  it renders in-game or serves diagnostics remains unverified.

## Necessary resource evidence
The executable looks up menu definitions in resources from the disc. We need the
pause/debug package data to inspect labels, choices and callback behavior.
The current Drive connector cannot download the 1.85 GB ISO (256 MiB cap).
The local collector avoids that transfer by reading selected package extents.

On the user's PC, from a checkout of this research branch:
```powershell
py tools\collect_menu_evidence.py "C:\path\game.iso" "spongebob-menu-evidence.zip"
```

Upload the resulting ZIP privately in chat or through Drive.
It contains menu-related game resources and a manifest. Do not publish it to
GitHub. Original ISO is opened read-only. Existing outputs are refused.
Collector chooses package names containing pause, frontend_dev or debugpackage,
caps individual packages at 32 MiB and total selected bytes at 64 MiB.
Generated numeric archive names prevent input names from creating unsafe paths.

PAKS parsing is based on the project's prior documented extractor layout;
retail compatibility has NOT been tested here. It validates extents and stops
rather than guessing when layout/bounds do not match.
Both 20- and 32-byte record layouts have synthetic checks.
An end-to-end synthetic ISO test verifies selected content, original preservation,
and refusal to overwrite an existing bundle.
110 repository tests ran: 109 passed, one skipped.

## Next step
Inspect actual menu package resources and distinguish normal pause settings from
developer controls before implementing a menu activation or restoration patch.
