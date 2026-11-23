# v2.0.1 - Results alignment and method-aware PNG filenames

A small maintenance release based on v2.0.0. **No changes to the engineering calculation methods, gland geometry, tolerances or dimensional screening limits.**

## Changes

- **Status alignment:** The Status heading and all PASS/REVIEW indicators are centred directly above the Save PNG button.
- **Numerical headings:** The start of Nominal aligns with the left edge of the Dimension Guide frame. Minimum, Nominal and Maximum headings and values move consistently, retaining the original 140 px centre-to-centre spacing.
- **PNG filename:** The suggested filename begins with **Detailed** or **Simplified** according to the active calculation method. The existing application, component, groove profile and optional O-ring size follow in their previous order.

Example suggested names:

- Detailed - Static - Piston - Rectangular.png
- Simplified - Dynamic - Cylinder - Double Dovetail - [selected O-ring size].png

Filenames remain editable in the Windows Save dialog. The saved PNG contents, calculations and settings have not changed.

## Download

**Radial-ORing-Calculator-v2.0.1-Windows-Portable.zip** contains one executable: **Static & Dynamic Radial O-Ring Calculator v2.0.1.exe**. Extract the ZIP and run the EXE. No installer or Python installation is needed. The executable is unsigned and Windows or workplace security policies may restrict it.

The single-EXE format, Embedded Dimension Guides, AS568 data, Detailed/Simplified methods, Inspect Results, PNG and clipboard reporting, keyboard navigation and Windows dark-mode compatibility all remain as in v2.0.0.

## Verification

**266 automated regression tests passed** against the tagged release source, including method-prefixed PNG filename tests and native Windows alignment checks. PyInstaller archive checks confirmed embedded application resources and the exclusion of both unused Qt Virtual Keyboard components.

The packaged executable was extracted and launched independently on Windows, displayed **v2.0.1**, and closed normally. A separate clean-computer test has not been claimed.

**Portable ZIP SHA-256:** `854352d8d3ff04427e6056eacee42cf598d79fea4ad68883fe65f4672a5bc58d`. A matching .sha256 file accompanies the download.

## Source, documentation and licensing

The v2.0.1 tagged source contains [engineering scope](ENGINEERING_SCOPE.md), [Windows packaging](WINDOWS_PACKAGING.md), [rebuild and Qt LGPL guidance](ONEFILE_REBUILD_AND_LGPL.md), [third-party notices](THIRD_PARTY_NOTICES.md) and associated licence texts. Proprietary engineering publications and private development files are excluded.

For the full v2 feature changes, see [v2.0.0 release notes](RELEASE_NOTES_v2.0.0.md).
