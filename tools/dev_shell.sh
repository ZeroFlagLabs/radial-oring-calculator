#!/usr/bin/env bash
# Git Bash development shell for the O-Ring Calculator (Windows).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"
VENV="$PROJECT_ROOT/venv"
PYTHON="$VENV/Scripts/python.exe"
ACTIVATE="$VENV/Scripts/activate"

if [[ ! -f "$PYTHON" || ! -f "$ACTIVATE" ]]; then
    if [[ -e "$VENV" ]]; then
        echo "An incomplete venv already exists. Nothing was deleted."
        echo "Inspect it before retrying: $VENV"
        exit 1
    fi
    echo "No venv found at: $VENV"
    read -r -p "Create it and install requirements? (y/n): " answer
    if [[ "${answer,,}" != "y" ]]; then
        echo "Cancelled."
        exit 1
    fi
    if command -v py.exe >/dev/null 2>&1; then
        py.exe -3 -m venv "$VENV"
    elif command -v python >/dev/null 2>&1; then
        python -m venv "$VENV"
    else
        echo "Python 3 is not available. Install Python first."
        exit 1
    fi
    "$PYTHON" -m pip install -r "$PROJECT_ROOT/requirements.txt"
fi

# Git Bash activation sets PATH and VIRTUAL_ENV for the interactive child shell.
# shellcheck disable=SC1090
source "$ACTIVATE"
python -c 'import PySide6; import src.main' || {
    echo "The environment is missing dependencies."
    echo "Run: python -m pip install -r requirements.txt"
    exit 1
}

# Keep the user's convenient per-environment Designer shortcut where possible.
# The tools/Edit_Layout.cmd launcher also works without this optional shortcut.
if command -v cygpath >/dev/null 2>&1 && command -v powershell.exe >/dev/null 2>&1; then
    designer="$VENV/Scripts/pyside6-designer.exe"
    if [[ -f "$designer" ]]; then
        designer_win="$(cygpath -w "$designer")"
        root_win="$(cygpath -w "$PROJECT_ROOT")"
        link_win="$(cygpath -w "$SCRIPT_DIR/Qt Designer (venv specific shortcut).lnk")"
        # Environment variables avoid quoting user paths inside PowerShell source.
        ORING_DESIGNER_EXE="$designer_win" ORING_PROJECT_ROOT="$root_win" \
        ORING_DESIGNER_LINK="$link_win" \
        powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
          '$ErrorActionPreference="Stop"; $shell=New-Object -ComObject WScript.Shell; $link=$shell.CreateShortcut($env:ORING_DESIGNER_LINK); $link.TargetPath=$env:ORING_DESIGNER_EXE; $link.WorkingDirectory=$env:ORING_PROJECT_ROOT; $link.IconLocation=$env:ORING_DESIGNER_EXE + ",0"; $link.Save()' \
          >/dev/null 2>&1 || true
    fi
fi

echo ""
echo "O-Ring Calculator — Dev Shell"
echo "Project: $PROJECT_ROOT"
echo "Python: $(python --version 2>&1)"
echo "Environment: venv"
echo "Run: python -m src.main"
echo "Tests: python -m unittest discover -s tests -v"
echo ""

# Use a new interactive shell; its inherited PATH and VIRTUAL_ENV remain active.
export PS1='(venv) \W $ '
exec bash --noprofile --norc -i
