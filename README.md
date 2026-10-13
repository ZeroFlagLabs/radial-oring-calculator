# Static & Dynamic Radial O-Ring Calculator

**ZeroFlagLabs** · Windows desktop application · v1.0.0

A desktop application for **dimensional screening of static and reciprocating dynamic radial O-ring seals**. Supports piston (male) and cylinder (female) arrangements with rectangular and symmetrical double-dovetail gland profiles.

> **Publication preparation:** v1.0.0 has passed 231 Windows regression tests and standalone tests in both one-file and one-folder configurations. The recommended **public download is the one-folder ZIP**, after third-party redistribution compliance is completed. A GitHub Release is not available until the owner publishes it.

## Features

- Static and reciprocating dynamic radial O-ring configurations.
- Piston/male and cylinder/female gland types.
- Rectangular and symmetrical double-dovetail grooves, with supported depth or diameter entry modes.
- AS568 reference-size catalogue and manual O-ring dimensions.
- Minimum, nominal and maximum dimensional checks for radial squeeze, ID stretch or OD interference, and gland fill.
- Two-dimensional (2D) gland geometry using wall angles, opening radii and base radii.
- **Inspect Results** with equations, numerical substitutions and intermediate results.
- Eight purpose-made **Dimension Guides** and compact **PNG summary reporting**.
- **PASS**, **REVIEW** and invalid-input indications.
- Optional GitHub update checks; the application does not auto-install releases.

## Download and run

When published, the recommended Windows download will appear on [GitHub Releases](https://github.com/ZeroFlagLabs/radial-oring-calculator/releases).

1. Download the **v1.0.0 Windows portable ZIP**.
2. Extract the entire ZIP to a folder you can write to.
3. Run **Static & Dynamic Radial O-Ring Calculator v1.0.0.exe** inside the extracted application folder.
4. **Keep the EXE and its `_internal` folder together.** Python need not be installed.

Check the SHA-256 file supplied with the release to verify the archive. There is no installer or automatic update installation. The application intentionally starts with zero-valued numeric inputs rather than a sample design.

## Screenshots

A populated screen capture and example PNG report will be added when available. No proprietary customer drawings are distributed.

## Run from source (Windows)

Install Python and use PowerShell at the repository root:

```powershell
py -3 -m venv venv
& '.\venv\Scripts\python.exe' -m pip install -r requirements.txt
& '.\venv\Scripts\python.exe' -m src.main
```

Run the regression tests:

```powershell
& '.\venv\Scripts\python.exe' -m unittest discover -s tests -q
```

The app uses **PySide6** (Qt for Python), not PyQt6. Qt Designer `.ui` source files are included for all three application dialogs.

## Build (Windows, developer use)

The approved **one-folder** Windows candidate was generated with PyInstaller 6.22.3 and PySide6 6.12.0. See [development/release guidance](docs/DEVELOPMENT.md) and [Windows packaging](docs/WINDOWS_PACKAGING.md). A separate, older one-file build script remains available for development; **do not treat that as the approved public distribution format**.

## Engineering scope

This is **dimensional screening**, not full seal design qualification. **PASS** means selected screening criteria are satisfied for the evaluated conditions. **REVIEW** means further engineering assessment is needed, not automatic rejection. Available gland area uses a two-dimensional (2D) representation of the groove section and radial-clearance strip; see [Engineering scope and limitations](docs/ENGINEERING_SCOPE.md) and the application's Assumptions and References tabs.

## Licence, data and third-party components

Original application code, documentation and project-owned artwork are released under [MIT](LICENSE), **except where separately attributed**. The AS568 dataset is included with the project owner's stated redistribution permission; this does not license the source manufacturers' manuals or standards. The original reference publications are not included.

Qt/PySide6, Python and other bundled components are separately licensed. Read [third-party notices](docs/THIRD_PARTY_NOTICES.md), [redistribution checklist](docs/THIRD_PARTY_RELEASE_CHECKLIST.md) and the licence texts in `licenses/`. Publication of a Windows binary is subject to fulfilling the corresponding-source and replacement obligations of the applicable Qt licences.

## Project layout

| Path | Purpose |
|---|---|
| `src/calculations/` | Geometry, dimensional checks and tolerance machinery |
| `src/catalog/`, `src/resources/data/` | O-ring catalogue/reference dimensions |
| `src/ui/`, `src/ui/forms/` | Application interface and Qt Designer layouts |
| `src/resources/guides/` | Eight approved Dimension Guides |
| `src/resources/icons/` | Original project artwork and application icon |
| `tests/` | Current and historical regression coverage |
| `tools/` | Developer commands and packaging tools |
| `docs/`, `licenses/` | Engineering methods, guidance and legal notices |

Private CAD masters, proprietary reference PDFs, local development environments and generated executable builds are not distributed as source.
