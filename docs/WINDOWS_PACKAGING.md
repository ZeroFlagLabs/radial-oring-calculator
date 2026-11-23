# Windows packaging - v2.0.1

The official Windows download is **one ZIP containing one unsigned portable EXE**, retaining the v1.0.1 single-file packaging model.

## Build environment

- Windows 11 with Python 3.13.x.
- Qt for Python/PySide6 6.12.0, including Essentials, Addons and shiboken6.
- PyInstaller 6.22.3.

From the public source tree:

~~~powershell
py -3.13 -m venv venv
& '.\venv\Scripts\python.exe' -m pip install -r requirements-build.txt
& '.\venv\Scripts\python.exe' -m unittest discover -s tests -q
& '.\venv\Scripts\python.exe' .\tools\Build-OneFile-Portable.py --project (Get-Location).Path
~~~

This builder creates a PyInstaller one-file specification, removes two unused binaries (`Qt6VirtualKeyboard.dll` and `qtvirtualkeyboardplugin.dll`) after dependency analysis and validates their absence from the executable. The embedded inventory must contain all eight Dimension Guides, the three Qt Designer forms, icons and the AS568 reference JSON.

The output is:

- `Radial-ORing-Calculator-v2.0.1-Windows-Portable.zip` containing only `Static & Dynamic Radial O-Ring Calculator v2.0.1.exe`
- `Radial-ORing-Calculator-v2.0.1-Windows-Portable.zip.sha256` to verify the ZIP integrity

## Executable smoke testing

Launch the packaged EXE itself on Windows and verify the v2.0.1 version in the main window and Settings, Detail/Simplified switching, male/female examples, squeeze/fit/fill results, all eight guide pictures, Inspector calculations, clipboard/PNG reporting, keyboard navigation, reset, app icon and GitHub update status. Test actual Windows dark mode where available.

The one-file PyInstaller bootloader extracts its Qt DLLs temporarily at startup. No Python installation, `_internal` directory or installer is needed for normal users.

## Security, licences and source

This is an unsigned program. SmartScreen, Smart App Control or workplace policies may block it; do not disable security protections.

Qt/PySide6 and other libraries in the EXE retain independent licences. A one-file executable does not itself settle LGPL source/relink requirements. The tagged public source contains build scripts, LGPL/GPL/MIT notices, third-party attributions and compatible-library rebuild instructions. The existing v1.0.0 release retains distributor-hosted matching Qt and PySide6 source archives and checksum evidence.

See [Qt LGPL and rebuild guidance](ONEFILE_REBUILD_AND_LGPL.md), [third-party notices](THIRD_PARTY_NOTICES.md) and [third-party release checklist](THIRD_PARTY_RELEASE_CHECKLIST.md). Private engineering studies and proprietary reference publications must never be included in this ZIP or repository.
