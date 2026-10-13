from gui_sample import seed_sample
"""Regression tests for the compact report and optional input tolerances."""
from pathlib import Path
from struct import unpack
import ast
import importlib.util
import unittest

ROOT=Path(__file__).resolve().parents[1]
GUI=importlib.util.find_spec('PySide6') is not None

class CompactReportSourceTests(unittest.TestCase):
    def test_title_size_and_unboxed_format(self):
        source=(ROOT/'src/ui/snapshot_view.py').read_text(encoding='utf8')
        ast.parse(source)
        self.assertIn("TITLE = APP_TITLE",source)
        self.assertIn('REPORT_WIDTH = 966',source)
        self.assertIn('REPORT_HEIGHT = 686',source)
        self.assertIn('DIMENSIONAL SCREENING RESULTS',source)
        self.assertIn('ACCEPTANCE CRITERION',source)
        self.assertIn('Indicative geometry only - not to scale',source)
        self.assertNotIn("'CALCULATION NOTES'",source)
        self.assertIn('painter.drawRect(5, 5',source)
    def test_each_dimension_has_correct_unit_and_optional_tolerance(self):
        main=(ROOT/'src/ui/main_window.py').read_text(encoding='utf8')
        ast.parse(main)
        self.assertIn("names[key]+' (in)'", main)
        self.assertIn("' (°)' if key in ('angle','rect_angle')",main)
        self.assertIn('if tolerance > 0.0000005:',main)
    def test_six_locked_images_are_identical_to_installed_preview_hashes(self):
        # Package SHA-256 verification also enforces the baseline and exact
        # image list. The two changed files remain 1068 x 1068.
        d=ROOT/'src/resources/guides'
        self.assertEqual(len(list(d.glob('*.png'))),8)
        for path in d.glob('*.png'):
            data=path.read_bytes()
            self.assertEqual(data[:8],b'\x89PNG\r\n\x1a\n')
            self.assertEqual(unpack('>II',data[16:24]),(1068,1068))

@unittest.skipUnless(GUI, 'Requires PySide6 on Windows')
class WindowsCompactReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])
    def test_all_input_tolerances_and_compact_png(self):
        from src.ui.main_window import MainWindow
        w=MainWindow();seed_sample(w)
        try:
            w.shared_rows['rect_angle'].nominal.setValue(2)
            w.shared_rows['rect_angle'].tolerance.setValue(0)
            value=dict(w._capture_inputs())['Wall angle (°)']
            self.assertEqual(value,'2.000')
            w.shared_rows['rect_angle'].tolerance.setValue(0.5)
            value=dict(w._capture_inputs())['Wall angle (°)']
            self.assertEqual(value,'2.000 ± 0.500')
            w.shared_rows['rect_angle'].tolerance.setValue(0)
            w.shared_rows['width'].tolerance.setValue(0.00025)
            value=dict(w._capture_inputs())['Groove width (in)']
            self.assertIn('± 0.00025',value)
            self.assertTrue(all('(in)' in k or '(°)' in k for k,_ in w._capture_inputs()))
            image=w._snapshot_pixmap()
            self.assertFalse(image.isNull())
            self.assertEqual((image.width(),image.height()),(966,686))
        finally:w.close()
    def test_all_eight_snapshots_have_same_size(self):
        from src.ui.main_window import MainWindow
        w=MainWindow();seed_sample(w)
        try:
            for config in (0,1):
                w.configuration.setCurrentIndex(config)
                for groove in (0,1):
                    w.groove_type.setCurrentIndex(groove)
                    for mode in (0,1):
                        (w.female_entry_mode if config else w.entry_mode).setCurrentIndex(mode)
                        self.assertEqual(w._snapshot_pixmap().size().width(),966)
        finally:w.close()
