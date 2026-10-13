# v1.0.0 — Initial public release (draft)

## Features

- Windows desktop calculator for static and reciprocating dynamic radial O-ring gland screening.
- Piston and cylinder glands, rectangular and double-dovetail profiles, with supported diameter and depth inputs.
- AS568 catalogue, tolerance-range checks, Inspect Results working, eight Dimension Guides, and PNG reporting.
- Optional in-app GitHub release checks, clear PASS/REVIEW indicators, and a polished application icon.

## Testing

The release candidate passed 231 Windows regression tests. Standalone one-file and one-folder executables passed smoke tests, including the guides, reporting and GitHub links. The recommended public format is a portable one-folder ZIP.

## Engineering scope

Results are dimensional screening, not full design qualification. Users must independently assess application pressure, extrusion, materials, temperature, chemical compatibility, dynamic duty and other application factors. See [Engineering scope](ENGINEERING_SCOPE.md).

## Distribution notes

The tested one-folder candidate excludes two unnecessary Qt Virtual Keyboard binaries and preserves the audited remaining binaries. Before release, confirm Qt/PySide6 corresponding-source arrangements, component notices and applicable licences. The AS568 compilation is included with the project owner's stated redistribution permission.
