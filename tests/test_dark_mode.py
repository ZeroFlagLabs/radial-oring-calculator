"""Windows theme compatibility without changing the host OS theme.

The main UI is intentionally light. These tests run in a separate native
Windows Qt process because the offscreen Qt plugin cannot simulate the
Windows 11 QStyleHints dark colour scheme accurately.
"""
import os
from pathlib import Path
import subprocess
import sys
import unittest


@unittest.skipUnless(sys.platform == "win32", "Windows Qt palette tests")
class DarkModeRegression(unittest.TestCase):

    def _run_native(self, script):
        env = os.environ.copy()
        env["QT_QPA_PLATFORM"] = "windows"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "-B", "-c", script],
            cwd=root, env=env, capture_output=True, text=True,
            timeout=25, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_simulated_native_dark_scheme_shows_readable_main_and_dialogs(self):
        self._run_native(r"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QLabel, QComboBox
from src.ui.main_window import MainWindow
from src.ui.settings_dialog import SettingsDialog
from src.ui.size_guide import SizeGuide
app=QApplication([])
app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
assert app.styleHints().colorScheme()==Qt.ColorScheme.Dark
assert app.palette().color(QPalette.ColorRole.WindowText).lightness()>150

window=MainWindow()
window.show()
app.processEvents()
assert app.styleHints().colorScheme()==Qt.ColorScheme.Light
assert app.palette().color(QPalette.ColorRole.WindowText).lightness()<100

for name in (
    "selector_calculation_method_label", "selector_application_label",
    "selector_configuration_label", "selector_groove_type_label",
    "selector_entry_mode_stack_label", "selector_ring_size_label",
    "label_male_cylinder_id", "label_male_direct_rod_od",
    "label_male_gland_od", "label_shared_width", "label_male_section",
):
    label=window.findChild(QLabel,name)
    assert label is not None,name
    assert label.palette().color(label.foregroundRole()).lightness()<150,name

for name in (
    "calculation_method", "application", "configuration",
    "groove_type", "ring_size",
):
    combo=window.findChild(QComboBox,name)
    assert combo is not None,name
    combo.showPopup()
    app.processEvents()
    palette=combo.view().palette()
    assert palette.color(QPalette.ColorRole.Base).lightness()>200,name
    assert palette.color(QPalette.ColorRole.Text).lightness()<100,name
    combo.hidePopup()

settings=SettingsDialog(window)
guide=SizeGuide(window.as568_sizes,window)
for dialog in (settings.dialog,guide,window._make_calculation_method_info_dialog()):
    dialog.show()
    app.processEvents()
    assert dialog.palette().color(QPalette.ColorRole.WindowText).lightness()<100
    dialog.close()
assert guide.table.palette().color(QPalette.ColorRole.Base).lightness()>200
assert guide.table.palette().color(QPalette.ColorRole.Text).lightness()<100

# Inspector inherits the same readable palette.
import sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/"tests"))
from gui_sample import seed_sample
seed_sample(window)
inspector=window._make_tolerance_trace_dialog()
assert inspector is not None
assert inspector.palette().color(QPalette.ColorRole.WindowText).lightness()<100
inspector.close()
window.close()
""")

    def test_native_light_scheme_preserves_original_window_size_and_palette(self):
        self._run_native(r"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
app=QApplication([])
# Do not explicitly set Light here. The objective is to prove that a
# naturally light Windows session is completely untouched by the fix.
if app.styleHints().colorScheme()!=Qt.ColorScheme.Light:
    raise SystemExit(0)
before=[app.palette().color(role).name() for role in
        (QPalette.ColorRole.Window,QPalette.ColorRole.WindowText,
         QPalette.ColorRole.Base,QPalette.ColorRole.Text)]
window=MainWindow()
window.show()
app.processEvents()
after=[app.palette().color(role).name() for role in
       (QPalette.ColorRole.Window,QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Base,QPalette.ColorRole.Text)]
assert before==after,(before,after)
# Native Windows11 style has different chrome/text metrics from the
# offscreen test renderer. Compare the themed colours exactly and retain
# the established nominal window width, without a renderer-specific height.
assert window.width()==1080,window.width()
assert 780<=window.height()<=850,window.height()
window.close()
""")


if __name__ == "__main__":
    unittest.main()
