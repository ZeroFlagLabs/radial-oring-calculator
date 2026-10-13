"""Release-integration checks for the GitHub identity and application icons."""
from pathlib import Path
from xml.etree import ElementTree as ET
import importlib.util
import unittest

from src.app_info import APP_VERSION, GITHUB_REPOSITORY, GITHUB_URL, RELEASES_URL, RELEASE_API_URL

ROOT = Path(__file__).resolve().parents[1]
QT = importlib.util.find_spec('PySide6') is not None


class ReleaseIntegrationSourceTests(unittest.TestCase):
    def test_github_identity(self):
        self.assertEqual(GITHUB_REPOSITORY, 'ZeroFlagLabs/radial-oring-calculator')
        self.assertEqual(GITHUB_URL, 'https://github.com/' + GITHUB_REPOSITORY)
        self.assertEqual(RELEASES_URL, GITHUB_URL + '/releases/latest')
        self.assertTrue(RELEASE_API_URL.endswith('/repos/' + GITHUB_REPOSITORY + '/releases/latest'))
        self.assertRegex(APP_VERSION, r'^\d+\.\d+\.\d+$')

    def test_icon_assets_exist_and_packaging_enforces_them(self):
        for name in ('icon.ico', 'app-icon.png'):
            self.assertGreater((ROOT / 'src/resources/icons' / name).stat().st_size, 1000)
        png = (ROOT / 'src/resources/icons/app-icon.png').read_bytes()
        self.assertEqual(png[:8], b'\x89PNG\r\n\x1a\n')
        ico = (ROOT / 'src/resources/icons/icon.ico').read_bytes()
        self.assertEqual(ico[:4], b'\x00\x00\x01\x00')
        builder = (ROOT / 'tools/package_app.sh').read_text(encoding='utf-8')
        self.assertIn('--icon "src/resources/icons/icon.ico"', builder)
        self.assertIn('src/resources/icons;src/resources/icons', builder)
        self.assertIn('Approved Windows/runtime application icons are missing', builder)
        src = (ROOT / 'src/main.py').read_text(encoding='utf-8')
        self.assertIn('app.setWindowIcon(app_icon)', src)
        self.assertIn('Path(app_info.__file__).resolve().parent', src)
        self.assertIn('window.setWindowIcon(app_icon)', src)

    def test_designer_about_matches_public_link(self):
        root = ET.parse(ROOT / 'src/ui/forms/settings_dialog.ui').getroot()
        label = root.find('.//widget[@name="github_link"]/property[@name="text"]/string')
        self.assertEqual(label.text, 'Project on GitHub')
        code = (ROOT / 'src/ui/settings_dialog.py').read_text(encoding='utf-8')
        self.assertIn('Project on GitHub</a>', code)
        self.assertNotIn('(once published)', code)


@unittest.skipUnless(QT, 'PySide6 GUI required')
class ReleaseIntegrationGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_main_app_icon_and_settings_link(self):
        from PySide6.QtGui import QIcon
        from PySide6.QtWidgets import QLabel
        from src.ui.main_window import MainWindow
        from src.ui.settings_dialog import SettingsDialog
        icon = QIcon(str(ROOT / 'src/resources/icons/app-icon.png'))
        self.assertFalse(icon.isNull())
        self.app.setWindowIcon(icon)
        w = MainWindow()
        try:
            w.setWindowIcon(icon)
            self.assertFalse(w.windowIcon().isNull())
            settings = SettingsDialog(w)
            self.assertIn(GITHUB_URL, settings.dialog.findChild(QLabel, 'github_link').text())
            settings.dialog.close()
        finally:
            w.close()


if __name__ == '__main__':
    unittest.main()
