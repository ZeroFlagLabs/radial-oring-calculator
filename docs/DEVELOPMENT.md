# Development and release guidance - v2.1.0

## Code and resource architecture

- `src/calculations/` contains geometry, tolerance evaluation, installed-condition calculation methods and screening criteria.
- `src/ui/forms/` contains the three Qt Designer .ui files. Preserve widget object names.
- `src/ui/inspection_data.py` contains method-specific explanations and tolerance witnesses; `src/ui/snapshot_view.py` renders the clipboard/PNG report.
- `src/app_info.py` is the authoritative application version and public repository identity.
- The eight approved Dimension Guide images in `src/resources/guides/` and their underlying artwork are not changed during packaging.

## Windows development

~~~powershell
py -3.13 -m venv venv
& '.\venv\Scripts\python.exe' -m pip install -r requirements-build.txt
& '.\venv\Scripts\python.exe' -m unittest discover -s tests -q
& '.\venv\Scripts\python.exe' -m src.main
~~~

`tools/Run_Calculator.cmd` and `tools/Edit_Layout.cmd` are local development launchers. The current GUI uses a light colour scheme, including under Windows dark mode.

## Release verification

1. Complete the full Python regression suite, including Detailed/Simplified arithmetic and GUI tests.
2. Verify both calculation methods for the eight supported application/gland/profile combinations, including diameter/depth entry, tolerance extrema and optional radii/angles.
3. Check Inspect Results, clipboard and PNG report agree on selected method and displayed figures.
4. Check light/dark Windows palettes, all eight Dimension Guides, O-ring catalogue/manual entry, update checks, resets and mouse/keyboard controls.
5. Build the actual executable and run it on Windows, not just from source. Test startup, output, guides, dialogs and basic calculations without a development source dependency.
6. Inspect PyInstaller archives, ensure the two unused Virtual Keyboard components are absent, and verify the EXE-only ZIP and SHA-256 checksum.
7. Review required Qt/Python third-party notices and the source/rebuild materials before publishing.

## Single-EXE release builder

The preferred v2.1.0 builder is the published v1.0.1 `tools/Build-OneFile-Portable.py` mechanism:

~~~powershell
& '.\venv\Scripts\python.exe' .\tools\Build-OneFile-Portable.py --project (Get-Location).Path
~~~

The builder creates a standalone executable, EXE-only ZIP and .sha256 file in `dist-onefile/`. It checks embedded guides, forms, icons and catalogue data and excludes unused Qt Virtual Keyboard components.

The older `tools/package_app.sh` launcher is retained for older local workflows only. Do not use it to prepare the official release: it lacks the explicit audited Virtual Keyboard exclusion.

## GitHub publication and privacy

- Publish **on top of the existing repository history**, never via an unrelated reinitialised local Git directory or force push.
- Stage reviewed source/test files and public documentation only. Review staged paths, changed file contents and licences.
- Exclude proprietary reference PDFs, original CAD, local development files, engineering comparison records, screenshots of private material, secrets, virtual environments, build intermediates and audit folders.
- Recheck the release ZIP file list and published GitHub assets after upload.
- Keep LGPL/GPL/MIT/Python licence texts and component attribution consistent with the exact packaged versions. The source and rebuild/relink instructions support recipients in exercising Qt licence rights.

See [engineering scope](ENGINEERING_SCOPE.md), [Windows packaging](WINDOWS_PACKAGING.md), [Qt rebuilding](ONEFILE_REBUILD_AND_LGPL.md) and [third-party notices](THIRD_PARTY_NOTICES.md).
