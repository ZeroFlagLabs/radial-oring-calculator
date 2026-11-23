# v2.0.0 - Detailed and Simplified calculation methods

## Windows download

**Radial-ORing-Calculator-v2.0.0-Windows-Portable.zip** contains a single executable:
`Static & Dynamic Radial O-Ring Calculator v2.0.0.exe`.

Extract and run the EXE. No installer, Python environment or additional runtime folder is needed. The executable is unsigned and may trigger Windows SmartScreen or corporate security restrictions; do not disable security protections.

## What's new

- **Switchable calculation method** in Application setup without changing entered dimensions.
  - **Detailed (default):** Manufacturer-informed installed-condition calculations. For stretched male O-rings, radial squeeze uses an empirical installed compression cross-section, and gland fill uses a separate constant-volume material-area correction.
  - **Simplified:** Uses the **free-state O-ring cross-section** for radial squeeze and the free-state O-ring material area for gland fill, with **no stretch-related reduction**.
- **Shared geometry and criteria:** Both methods use exactly the same available gland area, tolerance inputs and extrema, ID stretch or OD interference calculation and PASS/REVIEW limits. Female results are identical in both methods.
- **Inspect Results** presents the calculation-method-specific equations and controlling tolerance inputs.
- **Copy Snapshot** and **Save PNG** identify the method used.
- A concise **Calculation Method information** popup and updated Settings explanations.

## Interface and compatibility

- Refined application selectors, dimensional inputs, Dimension Guides and result/report alignment.
- Consistent, compact button sizes and improved keyboard Tab traversal through input dimensions.
- Settings cog and footer actions excluded from Tab focus, while remaining clickable.
- Windows dark-mode readability fixed without changing the system theme.

## Unchanged screening rules

Minimum squeeze >=0.007 in; maximum squeeze <=30% (static) or <=16% (reciprocating dynamic); male installed ID stretch 0-5%; female installed OD interference 0-2%; gland fill 60-85%. These are inclusive dimensional screening limits. **REVIEW does not automatically mean the O-ring design is unsuitable.**

## Packaging and licences

- Retains the single-EXE Windows ZIP format introduced in v1.0.1.
- Eight guides, three Qt forms, the AS568 catalogue and application icons remain embedded.
- Excludes the two unused Qt Virtual Keyboard binaries.
- Includes a separate SHA-256 ZIP checksum. Build and Qt relinking/source guidance, independent third-party notices and licence texts are provided with the tagged source; matching distributor-hosted Qt/PySide6 source archives remain on the earlier v1.0.0 release.
- Original project code is MIT licensed except independently licensed or attributed components. No proprietary engineering documents or private development data are distributed.

## Verification

**264 automated numerical and GUI regression tests passed.** The one-file archive/resource verification passed, and the packaged executable was extracted, launched on Windows and confirmed to display v2.0.0. Both unused Qt Virtual Keyboard components were absent. A separate-machine test is not claimed.

**ZIP SHA-256:** `43da88a4ed505d489850954abd0e8f282b9642e61453d45be686a9cc5a5b1d6e`. A matching checksum file accompanies the download.

See [engineering scope](ENGINEERING_SCOPE.md), [Windows packaging](WINDOWS_PACKAGING.md), [third-party notices](THIRD_PARTY_NOTICES.md) and [one-file rebuild and LGPL instructions](ONEFILE_REBUILD_AND_LGPL.md).
