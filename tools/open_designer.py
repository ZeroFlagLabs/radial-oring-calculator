"""Open the editable main window in Qt Designer on Windows."""
from pathlib import Path
import shutil
import subprocess
import sys

project = Path(__file__).resolve().parents[1]
ui = project / 'src' / 'ui' / 'forms' / 'main_window.ui'


def main() -> int:
    if not ui.is_file():
        print(f'Cannot find layout file: {ui}')
        return 1

    candidates = [project / 'venv' / 'Scripts' / 'pyside6-designer.exe']
    try:
        import PySide6
        home = Path(PySide6.__file__).resolve().parent
        candidates += [home / 'designer.exe', home / 'Qt' / 'bin' / 'designer.exe']
    except ImportError:
        pass

    for command_name in ('pyside6-designer.exe', 'designer.exe', 'designer'):
        found = shutil.which(command_name)
        if found:
            candidates.append(Path(found))

    for binary in candidates:
        if binary.is_file():
            try:
                subprocess.Popen([str(binary), str(ui)], cwd=str(project))
            except OSError as exc:
                print(f'Unable to start Qt Designer: {exc}')
                return 1
            print(f'Opened Qt Designer with: {ui}')
            return 0

    print('Qt Designer was not found.')
    print('Try installing the PySide6 Addons package in the project environment:')
    print(r'  .\venv\Scripts\python.exe -m pip install PySide6-Addons')
    print('Then double-click tools/Edit_Layout.cmd again.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
