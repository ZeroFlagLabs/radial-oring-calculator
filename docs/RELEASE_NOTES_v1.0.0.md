# v1.0.0 - Initial Windows Release

First public release of **Static & Dynamic Radial O-Ring Calculator** by ZeroFlagLabs.

## Download for Windows

**Only one file is needed:** `Radial-ORing-Calculator-v1.0.0-Windows-Portable.zip` (about 52 MB).

1. Download that ZIP from the **Assets** section below.
2. Extract the complete ZIP to a folder of your choice.
3. Open the application folder and double-click **Static & Dynamic Radial O-Ring Calculator v1.0.0.exe**.

That's it. No installation or Python required. **Keep the EXE and the `_internal`
folder together.** The extra assets below are for optional checksum verification
or for third-party open-source licensing. They are **not** needed to run the app.

**First run on Windows:** v1.0.0 is not code-signed, so Microsoft Defender
SmartScreen may display “Windows protected your PC” or “Unknown publisher”.
If you obtained the application from this official ZeroFlagLabs page and trust
it, Windows may offer **More info > Run anyway**. Don't disable Windows
security if it doesn't offer that option; Smart App Control or organisation
policies may block unsigned apps. See Microsoft's
[SmartScreen guidance](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation).

The optional `Radial-ORing-Calculator-v1.0.0-Windows-Portable.zip.sha256` file lets you verify the archive before
extracting it. Ordinary users need only the Windows ZIP.

## Features

- Static and reciprocating dynamic radial O-ring dimensional screening.
- Piston (male) and cylinder (female) glands.
- Rectangular and symmetrical double-dovetail groove profiles.
- Minimum, nominal and maximum radial squeeze, ID stretch/OD interference and gland fill.
- AS568 reference catalogue and manual dimensions.
- Detailed **Inspect Results** calculations, eight Dimension Guides and PNG summary output.
- Two-dimensional (2D) gland geometry incorporating wall angles, base radii and opening radii.
- PASS/REVIEW indications and optional GitHub update checks.

## Testing and scope

v1.0.0 passed **231 Windows regression tests** and standalone application smoke
tests. The approved portable build's 110 bundled binaries have been checked
against their audited hashes, with two unused Qt Virtual Keyboard binaries
excluded. The app supports **dimensional screening**, not full seal design
qualification; independently assess pressure, extrusion, material, temperature,
chemical compatibility, dynamic duty and installation.

[Engineering scope](https://github.com/ZeroFlagLabs/radial-oring-calculator/blob/main/docs/ENGINEERING_SCOPE.md)

## Licence and source information

Original application code, documentation and original artwork are MIT licensed.
Qt 6.12.0, PySide6 6.12.0, Python and bundled third-party components retain their
own licences. The Windows ZIP includes `THIRD_PARTY_NOTICES.md`,
`THIRD_PARTY_COMPONENTS.md`, `QT_SOURCE_AND_REPLACEMENT.md` and `licenses/`.
The source archives below are provided for recipient rights and licence
compliance only, **not because users need to install them**.

- `qt-everywhere-src-6.12.0.tar.xz` (Qt corresponding source)
- `pyside-setup-everywhere-src-6.12.0.tar.xz` (PySide6/Shiboken6 corresponding source)
- `QT_SOURCE_SHA256SUMS.txt` (source archive hashes)

[Application source code](https://github.com/ZeroFlagLabs/radial-oring-calculator) | [Qt third-party licence attributions](https://doc.qt.io/qt-6/licenses-used-in-qt.html)
