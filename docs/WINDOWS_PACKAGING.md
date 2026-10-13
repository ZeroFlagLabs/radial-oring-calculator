# Windows packaging and release notes

This app has a tested **one-folder** PyInstaller v1.0.0 build. Use the bundled Qt libraries and plugins with the executable, not the EXE by itself.

## Tested environment

- Windows 11, Python **3.13.16**
- PySide6 / Qt for Python / Shiboken6 **6.12.0**
- PyInstaller **6.22.3**
- **231** Windows regression tests passed.
- Standalone EXE tested outside the development folder, including all eight guides, Inspect Results, PNG export, Settings, About/GitHub, and update status.
- A separate copy of the one-folder build was reviewed against a **112-binary SHA-256 manifest**, then two unused Qt Virtual Keyboard binaries were excluded. All **110** remaining binary entries were verified, and the cleaned copy passed a Windows smoke test.

The original one-file EXE was also tested, but the chosen public format is the one-folder ZIP. A one-folder layout makes compatible Qt DLL replacement more practical; it does **not** independently satisfy Qt LGPLv3 obligations.

## Rebuild locally

```powershell
& '.\venv\Scripts\python.exe' -m pip install -r requirements-build.txt
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File '.\tools\Build-OneFolder-Portable.ps1' -ProjectRoot (Get-Location).Path
```

The `Build-OneFolder-Portable.ps1` script uses **absolute paths** for assets, because PyInstaller resolves resources relative to the emitted `.spec` file. Rebuilt binaries may not match the published manifest if the toolchain or environment differs; perform a fresh manifest and licence review for such builds.

The audited v1.0.0 bundle initially included unused Qt Virtual Keyboard components; the published candidate excluded exactly:

- `_internal/PySide6/Qt6VirtualKeyboard.dll`
- `_internal/PySide6/plugins/platforminputcontexts/qtvirtualkeyboardplugin.dll`

A historical review-only script and its manifest are under `tools/release-audit/`, provided for reproducibility for that precise build. They do not automatically establish redistribution compliance for any different build.

## Publication gate

Before making the ZIP public, include MIT, LGPLv3 and GPLv3 licence texts, Python and other applicable third-party notices, and a **genuine corresponding-source and compatible-library replacement arrangement for Qt/PySide6**. See [Third-party release checklist](THIRD_PARTY_RELEASE_CHECKLIST.md).

Do not upload the original private `references/` or `design-assets/` folders, the `venv/`, `.spec` files, build directories, or internal company/customer material.
