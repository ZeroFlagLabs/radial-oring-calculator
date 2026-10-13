"""Stage 9.3 housekeeping invariants (independent of Windows GUI availability)."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Stage93MaintenanceTests(unittest.TestCase):
    def test_calculation_layout_and_data_paths_remain_stable(self):
        for name in (
            'src/main.py', 'src/calculations/installed.py',
            'src/catalog/as568.py', 'src/resources/data/as568_reference.json',
            'src/ui/main_window.py', 'src/ui/forms/main_window.ui',
        ):
            with self.subTest(name=name):
                self.assertTrue((ROOT / name).is_file())

    def test_both_launchers_use_venv_not_old_dot_venv(self):
        for name in ('tools/Edit_Layout.cmd', 'tools/Run_Calculator.cmd'):
            text = (ROOT / name).read_text(encoding='utf-8')
            self.assertIn(r'venv\Scripts\python.exe', text)
            self.assertNotIn(r'.venv\Scripts\python.exe', text)
            self.assertIn('cd /d "%~dp0.."', text)
        opener = (ROOT / 'tools/open_designer.py').read_text(encoding='utf-8')
        self.assertIn("project / 'venv'", opener)
        self.assertNotIn("project / '.venv'", opener)

    def test_private_reference_ignore_and_tool_scripts(self):
        text = (ROOT / '.gitignore').read_text(encoding='utf-8')
        for item in ('/references/', '/design-assets/', '/venv/', '/.venv/', '/build/', '/dist/'):
            self.assertIn(item, text)
        for name in ('tools/dev_shell.sh', 'tools/package_app.sh',
                     'requirements.txt', 'requirements-build.txt'):
            self.assertTrue((ROOT / name).is_file())

    def test_packaged_runtime_resources_are_explicitly_included(self):
        builder = (ROOT / 'tools/package_app.sh').read_text(encoding='utf8')
        for data in ('src/ui/forms/main_window.ui',
                     'src/ui/forms/settings_dialog.ui',
                     'src/ui/forms/inspect_results.ui',
                     'src/resources/data/as568_reference.json',
                     'src/resources/guides;src/resources/guides'):
            with self.subTest(data=data):
                self.assertIn(data, builder)
        self.assertIn('from src.app_info import APP_VERSION', builder)
        self.assertTrue((ROOT / 'docs/ENGINEERING_SCOPE.md').is_file())
        self.assertTrue((ROOT / 'docs/DEVELOPMENT.md').is_file())
        self.assertFalse((ROOT / 'Run_Calculator.cmd').exists())
        self.assertFalse((ROOT / 'Edit_Layout.cmd').exists())


if __name__ == '__main__':
    unittest.main()
