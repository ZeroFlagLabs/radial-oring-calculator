# v2.1.0 - Independent symmetrical and limit tolerance inputs

A feature release extending v2.0.1 with **per-dimension symmetrical or
absolute-limit input**, and a live two-way converter for each dimension.
The window layout, Detailed and Simplified engineering equations, screening
criteria, AS568 source data, Dimension Guides and existing snapshot/report
appearance are preserved.

## What's new

- **Individual tolerance mode:** every physical dimension has its own
  +/- / Limits selector. Groove diameter can be entered as nominal plus/minus
  tolerance while groove width and ring section use separate Min/Max limits.
- **Two-way conversion:** changing the selector converts the values currently
  visible, not an older stored version. Nominal +/- tolerance becomes
  Min/Max; Min/Max becomes the equivalent midpoint +/- half-range.
  1.000 +/- 0.003 in is equivalent to Min 0.997 in, Max 1.003 in.
- **Preserved precision:** six-place input limits may produce a seven-place
  calculated midpoint/half-range. The entry controls display and store the
  necessary precision to preserve the original endpoints on a round trip.
- **Validation:** reversed limits and out-of-range conversions are not
  silently accepted or clamped. Invalid dimensions disable results and
  snapshot exports until corrected.
- **AS568 catalogue:** the selected standard sizes remain fixed and
  read-only in both representations. Their ID and cross-section selectors
  remain usable to show calculated catalogue minimum and maximum limits.
- **Input appearance:** 106-pixel fields and compact 92-pixel toggle;
  full-height Min/Max fields retain inch/degree units and native increment
  arrows, with unobtrusive labels before the arrows. The disabled field
  styling retains rounded corners.

## Engineering interpretation

The nominal value of a limit pair is **the arithmetic midpoint of the
entered minimum and maximum**, even when this differs from a dimension's
drawing basic size. The calculation engine receives the exact physical
minimum and maximum through its pre-existing nominal/tolerance data model.
This does not change the geometric equations, Detailed/Simplified method
assumptions or screening criteria.

A zero tolerance converts to two equal endpoints. Signed wall angles are
supported in the applicable fields. For AS568 catalogue selections, both
representations derive from the same fixed reference data.

## Reports and unchanged features

**Copy Snapshot** and **Save PNG** continue to present dimensions in
symmetrical midpoint plus/minus half-range form, as in v2.0.1. Their
renderer, layout, result columns, inspection explanations and method-prefixed
PNG filename behaviour have not been modified. The report is for convenient
screening and may display fewer decimal places than the underlying
high-precision calculation values.

The interface still supports static/dynamic, male/female,
rectangular/double-dovetail, and diameter/depth entry methods.

## Download

**Radial-ORing-Calculator-v2.1.0-Windows-Portable.zip** contains only
**Static & Dynamic Radial O-Ring Calculator v2.1.0.exe**. Extract the ZIP
and launch the EXE on supported Windows systems. No separate Python runtime,
installer or internal folder is required. This executable is **unsigned**
and Windows SmartScreen/workplace policy may restrict it.

## Verification

**294 automated tests passed** against the release source, including
independent numerical checks of asymmetric limits across male/female,
rectangular/dovetail, direct/depth entry and both calculation methods, plus
the piecewise 3% installed ID-stretch transition.

The Windows one-file PyInstaller EXE was built and audited for required
embedded resources and exclusion of both unused Qt Virtual Keyboard
components. The packaged EXE was extracted to an independent folder, launched
without the development environment, and exercised using Windows UI
Automation. A real 0.145 +/- 0.003 in entry converted to Min 0.142 in /
Max 0.148 in and back to the original values. The ZIP passed integrity
checks and its external SHA-256 matched.

**Portable ZIP SHA-256:** 1c191142aacd957c580f25afa724d7835a260260ace79869a9bb774fd8256e1a

The calculator performs **dimensional screening**, not seal qualification.
For engineering limitations, see [Engineering scope](ENGINEERING_SCOPE.md).

## Source, licensing and previous releases

The v2.1.0 tagged source contains the code, test suite, Windows builder,
third-party notices, licences and Qt rebuild/relink guidance. No proprietary
reference publications, private engineering notes or development artefacts
are included. Qt/PySide6 and the Python runtime retain their applicable
third-party licences. Companion matching-source resources were published
with v1.0.0. See
[Qt and source rebuild guidance](ONEFILE_REBUILD_AND_LGPL.md) and
[third-party release checklist](THIRD_PARTY_RELEASE_CHECKLIST.md).

Previous versions remain accessible:
[v2.0.1](RELEASE_NOTES_v2.0.1.md),
[v2.0.0](RELEASE_NOTES_v2.0.0.md).
