# Development and release safeguards

## Architecture

- Calculations live in `src/calculations/`; avoid unrelated engine changes during release preparation.
- The Qt Designer sources are `src/ui/forms/main_window.ui`, `settings_dialog.ui` and `inspect_results.ui`. Their `objectName` values are used by the Python bindings.
- `src/app_info.py` defines the app title, version and public GitHub repository. The public repository may have no stable GitHub Release yet.
- All eight processed Dimension Guide PNGs in `src/resources/guides/` are approved; don't modify without separate review.
- Preserve the separate `requirements.txt` and `requirements-build.txt` files.
- Retain historic stage-named tests as regression coverage. Don't delete or rename them solely because their stage numbers are old.

## Windows local development

```powershell
py -3 -m venv venv
& '.\venv\Scripts\python.exe' -m pip install -r requirements-build.txt
& '.\venv\Scripts\python.exe' -m unittest discover -s tests -q
& '.\venv\Scripts\python.exe' -m src.main
```

The `tools/Run_Calculator.cmd` and `tools/Edit_Layout.cmd` shortcuts use `venv/`. Git Bash also supports `bash tools/dev_shell.sh`.

## Icon and portable build

`src/resources/icons/app-icon.png` is the **runtime Qt window/taskbar icon**. `src/resources/icons/icon.ico` is the **Windows executable/Explorer icon**. `src/main.py` explicitly configures the app and main-window icons. The PyInstaller packaging script requires both assets.

In Git Bash, from the project root:

```bash
bash tools/package_app.sh
```

The legacy Git Bash script runs the test suite and creates a **one-file developer build**. The tested public release is a separate **one-folder** build; see [Windows packaging](WINDOWS_PACKAGING.md). It excludes original publications, private CAD and other data in `references/` and `design-assets/`.

The owner has already completed the v1.0.0 Windows checks. For any subsequent rebuild, test the **packaged EXE itself**, not just the Python source: startup zeros, all eight guides, Inspect Results, tolerance switching, Reset dimensions, Save PNG, Copy Snapshot, About GitHub URL, and both online/offline update checks. Verify icon in Explorer, taskbar and title bar. Ideally smoke-test on a clean Windows PC without Python installed.

## GitHub staging and privacy

- Public repo: `https://github.com/ZeroFlagLabs/radial-oring-calculator`.
- Private `references/` and `design-assets/`, `venv/`, backups, installers and generated `dist/` are excluded from staging.
- `.gitignore` does **not** remove files already tracked. Review the **explicit staging list** with `git status --short` and `git diff --cached --name-status` before every first push.
- The existing public GitHub repository has its own initial commits. **Clone/fetch and incorporate remote `main`**, then reconcile the README/docs changes; do not force-push from a separately initialised local history.
- Complete the [third-party review](THIRD_PARTY_RELEASE_CHECKLIST.md), verify licence notices and resource/data redistribution permission before source or binary publication.
- Do not tag, publish or upload v1.0.0 without explicit approval after the final smoke tests.
