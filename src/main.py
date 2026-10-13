"""Run from project root: python -m src.main"""

import sys
from pathlib import Path
from src import app_info
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ZeroFlagLabs Static & Dynamic Radial O-Ring Calculator")
    icon_path = Path(app_info.__file__).resolve().parent / "resources" / "icons" / "app-icon.png"
    if not icon_path.is_file():
        raise FileNotFoundError(f"Application icon is missing: {icon_path}")
    app_icon = QIcon(str(icon_path))
    if app_icon.isNull():
        raise RuntimeError(f"Application icon could not be loaded: {icon_path}")
    app.setWindowIcon(app_icon)
    window = MainWindow()
    window.setWindowIcon(app_icon)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
