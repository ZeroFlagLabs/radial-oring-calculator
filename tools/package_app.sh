#!/usr/bin/env bash
# Git Bash one-file PyInstaller build for the portable Windows application.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"
PYTHON="$PROJECT_ROOT/venv/Scripts/python.exe"

fail() { echo "ERROR: $*" >&2; exit 1; }
[[ -f "$PYTHON" ]] || fail "venv is missing. Run tools/dev_shell.sh first."
[[ -f src/main.py && -f src/ui/forms/main_window.ui && \
   -f src/ui/forms/settings_dialog.ui && \
   -f src/ui/forms/inspect_results.ui && \
   -f src/resources/data/as568_reference.json ]] || \
    fail "Required Python, Designer layouts or AS568 data is missing."
[[ -d src/resources/guides ]] || fail "Dimension Guide PNG directory missing."
[[ -s src/resources/icons/icon.ico && -s src/resources/icons/app-icon.png ]] || \
    fail "Approved Windows/runtime application icons are missing."
[[ "$(find src/resources/guides -maxdepth 1 -type f -name '*.png' | wc -l | tr -d ' ')" == 8 ]] || \
    fail "Expected exactly eight processed Dimension Guide PNGs."

# Never include references or your private CAD drawings in the executable.
# The only explicitly bundled assets below are the editable layout, catalogue
# and optional public artwork; source references/ are not copied.
"$PYTHON" -c 'import PySide6, src.main' || fail "PySide6/application imports failed."
"$PYTHON" -m PyInstaller --version >/dev/null 2>&1 || \
    fail "PyInstaller missing. Install once: python -m pip install -r requirements-build.txt"

echo "Static & Dynamic Radial O-Ring Calculator - Portable Build"
# Read both identifiers from the application's single authoritative source.
app_name="$("$PYTHON" -c 'from src.app_info import APP_TITLE; print(APP_TITLE)')"
version="$("$PYTHON" -c 'from src.app_info import APP_VERSION; print(APP_VERSION)')"
[[ -n "$app_name" && "$app_name" != *[\\/:\*\?\"\<\>\|]* ]] || fail "Invalid application name in src/app_info.py"
[[ "$version" =~ ^[0-9]+(\.[0-9]+){1,3}$ ]] || fail "Invalid version in src/app_info.py"
name="$app_name v$version"
# Verify tests before packaging: an engineering app should not ship on a failed run.
"$PYTHON" -m unittest discover -s tests -q || fail "Regression tests failed. Build cancelled."

args=(--noconfirm --clean --onefile --windowed --paths "$PROJECT_ROOT" --name "$name")
args+=(--add-data "src/ui/forms/main_window.ui;src/ui/forms")
args+=(--add-data "src/ui/forms/settings_dialog.ui;src/ui/forms")
args+=(--add-data "src/ui/forms/inspect_results.ui;src/ui/forms")
args+=(--add-data "src/resources/data/as568_reference.json;src/resources/data")
args+=(--add-data "src/resources/guides;src/resources/guides")
if [[ -d src/resources/images ]]; then
    args+=(--add-data "src/resources/images;src/resources/images")
fi
if [[ -d src/resources/icons ]]; then
    args+=(--add-data "src/resources/icons;src/resources/icons")
fi
args+=(--icon "src/resources/icons/icon.ico")

echo "Building $name.exe (this does not include references/)."
"$PYTHON" -m PyInstaller "${args[@]}" src/main.py
exe="dist/$name.exe"
[[ -s "$exe" ]] || fail "PyInstaller returned, but the expected executable was not created."
sha256="$("$PYTHON" -c 'import hashlib,sys;h=hashlib.sha256();f=open(sys.argv[1],"rb");[h.update(c) for c in iter(lambda:f.read(1048576),b"")];print(h.hexdigest())' "$exe")"
printf '%s  %s\n' "$sha256" "$name.exe" > "dist/$name.sha256"
echo "Build complete: $PROJECT_ROOT/$exe"
echo "SHA-256 saved beside EXE. Test this EXE on Windows before publishing a Release."
if command -v explorer.exe >/dev/null 2>&1 && command -v cygpath >/dev/null 2>&1; then
    explorer.exe "$(cygpath -w "$PROJECT_ROOT/dist")" >/dev/null 2>&1 || true
fi
