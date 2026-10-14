# One-file Windows build, LGPL source and rebuild instructions (v1.0.1)

## Ordinary Windows users

Download **only** `Radial-ORing-Calculator-v1.0.1-Windows-Portable.zip` from the
[v1.0.1 release](https://github.com/ZeroFlagLabs/radial-oring-calculator/releases/tag/v1.0.1).
The ZIP has one EXE. Extract it and double-click the EXE. No Python installation
or additional downloads are required to run it. The program may take a little
longer to start because PyInstaller extracts libraries to a temporary directory.
The unsigned app may trigger Windows SmartScreen; do not disable Windows security.

## Source and licences

The original application's source is at this repository, tagged `v1.0.1`, MIT
licensed except separately attributed material. The executable includes
PySide6/Qt 6.12.0 and other independently licensed components. The repository
contains the MIT, LGPLv3 and GPLv3 texts under `licenses/`, and component
attributions in `docs/THIRD_PARTY_NOTICES.md` and `docs/THIRD_PARTY_RELEASE_CHECKLIST.md`.
Matching distributor-hosted archives of the unmodified Qt and PySide6/Shiboken6
source, plus their SHA-256 checksums, were published as release assets of
[v1.0.0](https://github.com/ZeroFlagLabs/radial-oring-calculator/releases/tag/v1.0.0).
These are **licensing and rebuild resources, not run-time dependencies**.

Qt's [LGPL obligations](https://www.qt.io/development/open-source-lgpl-obligations)
require allowing recipients to modify and relink/recombine compatible libraries.
The single EXE uses PyInstaller's one-file format, which unpacks Qt dynamic
libraries at run time; they are *not* separately replaceable alongside the EXE.
Accordingly, the application source and a rebuild path are offered here.

## Rebuild/recombine on Windows

Use Windows, Python **3.13.16**, PySide6 **6.12.0**, PySide6-Essentials and
PySide6-Addons **6.12.0**, shiboken6 **6.12.0**, and PyInstaller **6.22.3**.
Start from the v1.0.1 tag and use a fresh environment; do not alter the public
release asset. For the published unmodified build, run:

```powershell
py -3.13 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install PySide6==6.12.0 PyInstaller==6.22.3
& .\.venv\Scripts\python.exe .\tools\Build-OneFile-Portable.py --project (Get-Location).Path
```

The program regenerates a PyInstaller one-file spec, removes the two unused
GPL-only Qt Virtual Keyboard binaries after Analysis, checks the complete
archive inventory for required resources and exclusions, then creates an
EXE-only ZIP and a *separate, optional* SHA-256 verification file.

To **recombine with modified LGPL Qt/PySide6 libraries**, obtain the source
archives linked above, build the modified Qt and, as needed, PySide6/Shiboken6
binaries that remain ABI-compatible with the application, then arrange for
those replacement libraries to be the versions imported from your selected
Python environment before invoking the same builder. For example, a developer
may replace the compatible DLLs in an isolated copy of the PySide6 runtime
inside that build environment. The packager collects the environment's runtime
libraries into the new one-file EXE. No software signing key or publisher-only
installation permission is required to build and run the modified EXE.

This is a method and source-availability description, **not** a claim that a
modified Qt rebuild was separately demonstrated in the v1.0.1 release process.
Users are free to debug their library modifications and rebuild the package
under the applicable licences. Preserve all required component attributions.

See also [PyInstaller spec-file documentation](https://pyinstaller.org/en/stable/spec-files.html),
[the LGPLv3 text](https://www.gnu.org/licenses/lgpl-3.0.html), and
[the Qt module licence list](https://doc.qt.io/qt-6/licenses-used-in-qt.html).
