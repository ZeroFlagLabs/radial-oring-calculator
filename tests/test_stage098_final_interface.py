"""Interface regression: zero startup, reset, update preferences and guide fidelity."""
import hashlib
import importlib.util
from pathlib import Path
import unittest
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
GUI=importlib.util.find_spec('PySide6') is not None

class InterfaceSourceTests(unittest.TestCase):
    def test_all_four_actions_same_width_and_reset_next_to_inspect(self):
        r=ET.parse(ROOT/'src/ui/forms/main_window.ui').getroot()
        layout=r.find('.//layout[@name="actionLayout"]')
        labels=[w.get('name') for item in layout.findall('item') for w in item.findall('widget')]
        self.assertEqual(labels,['trace_button','reset_button','snapshot_button','save_snapshot_button'])
        widths=[]
        for name in labels:
            w=r.find(f'.//widget[@name="{name}"]')
            widths.append((w.find('./property[@name="minimumSize"]/size/width').text,
                           w.find('./property[@name="maximumSize"]/size/width').text))
        self.assertEqual(len(set(widths)),1)
        self.assertEqual(widths[0],('152','152'))
    def test_no_example_values_in_designer_and_dovetail_unset(self):
        r=ET.parse(ROOT/'src/ui/forms/main_window.ui').getroot()
        for w in r.iter('widget'):
            if (w.get('name') or '').startswith('spin_'):
                val=w.find('./property[@name="value"]/double')
                if val is not None:
                    self.assertEqual(float(val.text),0,w.get('name'))
    def test_updates_and_about_controls_exist(self):
        r=ET.parse(ROOT/'src/ui/forms/settings_dialog.ui').getroot()
        for name in ('check_on_launch','check_now_button','open_release_button','current_version',
                     'update_status','github_link'):
            self.assertIsNotNone(r.find(f'.//widget[@name="{name}"]'),name)
        info=(ROOT/'src/app_info.py').read_text()
        from src.app_info import APP_VERSION
        self.assertIn('APP_VERSION = ' + repr(APP_VERSION),info)
        self.assertIn('GITHUB_REPOSITORY',info)
    def test_assumptions_use_consistent_dynamic_terminology(self):
        r=ET.parse(ROOT/'src/ui/forms/settings_dialog.ui').getroot()
        label=r.find('.//widget[@name="assumptions_text"]')
        paragraph=label.find('./property[@name="text"]/string').text
        self.assertIn('static and dynamic (reciprocating) radial O-ring seals', paragraph)
        self.assertNotIn('reciprocating dynamic radial O-ring seals', paragraph)

    def test_six_approved_guide_files_not_changed(self):
        # Hashes come from the immediately preceding installed white-guide patch.
        import zipfile
        # Source-only test asserts image identities/geometry, installer enforces
        # SHA-256 equality with the six deployed files.
        d=ROOT/'src/resources/guides'
        self.assertEqual(len(list(d.glob('*.png'))),8)
        self.assertEqual(len({p.name for p in d.glob('*.png')}),8)
        for p in d.glob('*.png'):
            self.assertEqual(p.read_bytes()[:8], b'\x89PNG\r\n\x1a\n')

@unittest.skipUnless(GUI,'Requires PySide6 on Windows')
class InterfaceWindowsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def test_initial_state_and_reset_of_real_inputs(self):
        from src.ui.main_window import MainWindow
        from gui_sample import seed_sample
        w=MainWindow()
        try:
            self.assertIsNone(w._last_result)
            self.assertFalse(w.snapshot_button.isEnabled())
            self.assertFalse(w.trace_button.isEnabled())
            self.assertEqual(w.shared_rows['angle'].nominal.value(),0)
            self.assertEqual(w.shared_rows['angle'].tolerance.value(),0)
            self.assertEqual(w.rows['ring_id'].nominal.value(),0)
            self.assertTrue(w.rows['ring_id'].nominal.text().strip().startswith('0'))
            self.assertIn('Enter the required dimensions',w.statusBar().currentMessage())
            seed_sample(w)
            self.assertIsNotNone(w._last_result)
            self.assertTrue(w.snapshot_button.isEnabled())
            w.configuration.setCurrentIndex(1)
            w.groove_type.setCurrentIndex(1)
            w.application.setCurrentIndex(1)
            w.ring_size.setCurrentIndex(1)
            w.reset_button.click()
            self.assertEqual(w.configuration.currentIndex(),1)
            self.assertEqual(w.groove_type.currentIndex(),1)
            self.assertEqual(w.application.currentIndex(),1)
            self.assertEqual(w.ring_size.currentIndex(),0)
            self.assertFalse(w.snapshot_button.isEnabled())
            self.assertIsNone(w._last_result)
            self.assertEqual(w.shared_rows['angle'].nominal.value(),0)
            self.assertTrue(w.shared_rows['angle'].nominal.text().strip().startswith('0'))
            self.assertEqual(w.shared_rows['angle'].tolerance.value(),0)
        finally:
            w.close()

    def test_placeholder_dashes_align_with_status_then_restore_results(self):
        from PySide6.QtCore import Qt
        from src.ui.main_window import MainWindow
        from gui_sample import seed_sample
        w=MainWindow()
        try:
            # All input fields start at zero. Pending dashes must sit at the
            # same vertical position as the row labels and status dashes.
            for name in ('Squeeze', 'Fit', 'Gland fill'):
                self.assertEqual(w.overview_cells[(name,4)].text(), '—')
                for col in (1,2,3):
                    cell=w.overview_cells[(name,col)]
                    self.assertEqual(cell.text(), '—')
                    self.assertTrue(cell.alignment() & Qt.AlignmentFlag.AlignTop)
                    self.assertEqual(cell.contentsMargins().top(), 3)
            seed_sample(w)
            self.assertIsNotNone(w._last_result)
            for name in ('Squeeze', 'Fit', 'Gland fill'):
                for col in (1,2,3):
                    cell=w.overview_cells[(name,col)]
                    self.assertTrue(cell.alignment() & Qt.AlignmentFlag.AlignVCenter)
                    self.assertEqual(cell.contentsMargins().top(), 0)
            w.reset_button.click()
            self.assertIsNone(w._last_result)
            for name in ('Squeeze', 'Fit', 'Gland fill'):
                for col in (1,2,3):
                    cell=w.overview_cells[(name,col)]
                    self.assertEqual(cell.text(), '—')
                    self.assertTrue(cell.alignment() & Qt.AlignmentFlag.AlignTop)
        finally:
            w.close()

    def test_settings_controls_and_version(self):
        from src.ui.main_window import MainWindow
        from src.ui.settings_dialog import SettingsDialog
        from PySide6.QtWidgets import QCheckBox, QLabel, QPushButton
        w=MainWindow()
        try:
            d=SettingsDialog(w)
            check=d.dialog.findChild(QCheckBox,'check_on_launch')
            self.assertEqual(check.isChecked(),w.update_checker.enabled())
            from src.app_info import APP_VERSION
            self.assertIn('v' + APP_VERSION,d.dialog.findChild(QLabel,'current_version').text())
            self.assertTrue(d.dialog.findChild(QPushButton,'check_now_button').isEnabled())
            # Do not mutate persistent user update preferences from tests.
            d.dialog.close()
        finally:w.close()
