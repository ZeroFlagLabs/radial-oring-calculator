# v2.1.1 - Tolerance status-bar consistency and report alignment

A presentation-focused maintenance release following v2.1.0. No engineering
calculations, dimensional tolerances, screening criteria, AS568 data, selected
geometry, or calculation-method assumptions have changed.

## Changes

- **Symmetrical tolerance status:** When the active input dimensions all use
  symmetrical (+/-) tolerances, the status bar now explains that nominal
  results use the entered dimensions and tolerance extrema use nominal
  +/- tolerance. The existing **Limits** explanation remains available when
  an active dimension is set to Min/Max, including mixed-mode configurations.
- **PNG and clipboard snapshot alignment:** The Minimum, Nominal and Maximum
  headings and their associated numerical results move **50 pixels left**
  relative to v2.1.0. The three columns maintain their **101-pixel centre
  spacing**, and the fixed **966 x 686-pixel** report, acceptance criteria,
  status column, text content and geometry diagram are unchanged.
- Both **Detailed** and **Simplified** methods use this same snapshot renderer.
  The PNG and clipboard retain the existing symmetrical representation for
  displayed dimensional inputs.

## Download

The Windows asset `Radial-ORing-Calculator-v2.1.1-Windows-Portable.zip`
contains a single `Static & Dynamic Radial O-Ring Calculator v2.1.1.exe`.
Extract and run it on supported Windows systems, without installing Python or
requiring a separate `_internal` directory. The executable is unsigned,
so Windows SmartScreen or workplace security policies may restrict it.

## Verification

- **295 automated regression tests passed** on the v2.1.1 public release source,
  including GUI, engineering calculations, tolerance conversion and report checks.
- A fresh Windows single-file EXE was built using Python 3.13.16,
  PyInstaller 6.22.3 and PySide6 6.12.0.
- The PyInstaller archive inventory verified all required embedded forms,
  eight Dimension Guides, icons and AS568 catalogue data, and confirmed that
  both unused Qt Virtual Keyboard DLL/plugin files were excluded.
- The portable ZIP passed CRC/integrity verification, contains exactly one EXE,
  and has a matching external SHA-256 checksum file. The EXE was extracted to
  an independent folder and launched successfully with a visible native
  Windows application window.

**Portable ZIP SHA-256:** `9daae19bb933ba6dd943025115db49db42371b724c4ec936c2291c17bf2e79e0`

The calculator is a dimensional screening tool, **not seal qualification**.
Refer to [engineering methods and limitations](ENGINEERING_SCOPE.md).

## Source and third-party obligations

The public tag retains application source, the Windows rebuild tool, relevant
licence texts, third-party notices and Qt rebuild/relinking guidance. The
package and repository exclude private engineering publications, internal
audit records and Mathcad reference material. See
[Windows packaging](WINDOWS_PACKAGING.md) and
[Qt/LGPL guidance](ONEFILE_REBUILD_AND_LGPL.md).

Previous releases are available separately:
[v2.1.0](RELEASE_NOTES_v2.1.0.md) and
[v2.0.1](RELEASE_NOTES_v2.0.1.md).
