# v1.0.1 - Single-EXE Windows portable release

This update changes **Windows packaging only**, from a folder-based portable
application to **one EXE inside one ZIP**. The calculator's engineering methods
and application behaviour have not been deliberately changed.

## Download for Windows

**Download only:** `Radial-ORing-Calculator-v1.0.1-Windows-Portable.zip`.

Extract the ZIP, then double-click `Static & Dynamic Radial O-Ring Calculator v1.0.1.exe`.
There is no `_internal` folder to keep with the EXE. No Python installation,
setup program or second download is required.

**First run:** This EXE is unsigned, so Windows SmartScreen may show an
"Unknown publisher" warning. If you obtained the ZIP from the official
ZeroFlagLabs repository and trust it, Windows may offer **More info > Run anyway**.
Do not turn off Windows security if it does not offer that option.

## What changed

- v1.0.1 version metadata and window/Settings version labels.
- Windows package changed to PyInstaller **one-file** format.
- Excluded two unneeded Qt Virtual Keyboard DLL/plugin binaries.
- Eight Dimension Guides, forms, icons and catalogue data remain embedded.

## Verification

- Single-EXE PyInstaller build and archive inventory: **passed**.
- All eight Dimension Guides and all three UI forms: **present**.
- Both unnecessary Qt Virtual Keyboard components: **absent**.
- ZIP inventory: **exactly one EXE**.
- The 231 Windows regression tests and earlier packaged smoke tests were performed for the
  underlying v1.0.0 application. **The v1.0.1 one-file executable was not
  independently launch-tested on a second Windows computer before publication.**

## Open-source components

The application is MIT licensed except separately licensed/attributed material.
Qt 6.12.0/PySide6 6.12.0 have LGPL and other third-party obligations.
See [one-file source and rebuild instructions](https://github.com/ZeroFlagLabs/radial-oring-calculator/blob/v1.0.1/docs/ONEFILE_REBUILD_AND_LGPL.md),
[third-party notices](https://github.com/ZeroFlagLabs/radial-oring-calculator/blob/v1.0.1/docs/THIRD_PARTY_NOTICES.md)
and the Qt/PySide6 source archives with hashes on the
[v1.0.0 release](https://github.com/ZeroFlagLabs/radial-oring-calculator/releases/tag/v1.0.0).
The older v1.0.0 folder-based release remains available.

## Verify the Windows download (optional)

SHA-256 of `Radial-ORing-Calculator-v1.0.1-Windows-Portable.zip`:

`b40e1c0b29c5b782c3d310ab872aa4322187c2f09b0c711236700297d0dac7ff`

## Licences and build resources

The distributed EXE contains Qt/PySide6 components. Their LGPL/GPL licence
texts and third-party attribution notices are provided with the tagged source:
[LGPLv3](https://github.com/ZeroFlagLabs/radial-oring-calculator/blob/v1.0.1/licenses/LGPL-3.0.txt) ·
[GPLv3](https://github.com/ZeroFlagLabs/radial-oring-calculator/blob/v1.0.1/licenses/GPL-3.0.txt) ·
[Third-party notices](https://github.com/ZeroFlagLabs/radial-oring-calculator/blob/v1.0.1/docs/THIRD_PARTY_NOTICES.md) ·
[Rebuild/relink instructions](https://github.com/ZeroFlagLabs/radial-oring-calculator/blob/v1.0.1/docs/ONEFILE_REBUILD_AND_LGPL.md).

The matching distributor-hosted Qt and PySide6 source archives remain on the
[v1.0.0 release](https://github.com/ZeroFlagLabs/radial-oring-calculator/releases/tag/v1.0.0).
None of those resources is needed to run the Windows EXE.
