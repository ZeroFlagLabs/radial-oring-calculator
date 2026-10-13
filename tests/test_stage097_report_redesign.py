from gui_sample import seed_sample
"""Regression checks for source-owned guide scale and exported PNG summary."""
import ast
import importlib.util
from pathlib import Path
from struct import unpack
import unittest
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
GUI=importlib.util.find_spec('PySide6') is not None

class PreviewSourceTests(unittest.TestCase):
    def test_references_have_separate_section_gap(self):
        root=ET.parse(ROOT/'src/ui/forms/settings_dialog.ui').getroot()
        gap=root.find('.//spacer[@name="referencesSectionGap"]')
        self.assertIsNotNone(gap)
        self.assertEqual(gap.find('./property[@name="sizeHint"]/size/height').text,'20')
    def test_guide_scale_and_footer_and_replacement(self):
        main=(ROOT/'src/ui/main_window.py').read_text(encoding='utf-8')
        self.assertIn('Indicative geometry only - not to scale',main)
        self.assertIn('self._reference_pixmaps[state]',main)
        directory=ROOT/'src/resources/guides'
        self.assertEqual(len(list(directory.glob('*.png'))),8)
        for image in directory.glob('*.png'):
            data=image.read_bytes()
            self.assertEqual(data[:8],b'\x89PNG\r\n\x1a\n')
            self.assertEqual(unpack('>II',data[16:24]),(1068,1068))
    def test_report_is_independent_of_windows_chrome(self):
        source=(ROOT/'src/ui/snapshot_view.py').read_text(encoding='utf-8')
        ast.parse(source)
        main=(ROOT/'src/ui/main_window.py').read_text(encoding='utf-8')
        self.assertIn('sketch=sketch, context=context, detail_rows=details',main)
        self.assertIn('DIMENSION GUIDE',source)
        self.assertIn('INPUT DIMENSIONS',source)
        self.assertIn('DIMENSIONAL SCREENING RESULTS',source)
        self.assertNotIn("'CALCULATION NOTES'",source)
        self.assertIn('TITLE = APP_TITLE',source)
        self.assertIn('painter.drawPixmap(x, y, fitted)',source)
        self.assertIn('REPORT_WIDTH = 966',source)

@unittest.skipUnless(GUI,'Requires PySide6 on Windows')
class WindowsReportSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])
    def test_guides_embedded_and_case_results(self):
        from src.ui.main_window import MainWindow
        w=MainWindow();seed_sample(w)
        try:
            img=w._snapshot_pixmap()
            self.assertFalse(img.isNull())
            self.assertEqual(img.width(),966)
            self.assertEqual(img.height(),686)
            for state in range(2):
                w.configuration.setCurrentIndex(state)
                w.groove_type.setCurrentIndex(1)
                image=w._snapshot_pixmap()
                self.assertFalse(image.isNull())
                self.assertEqual(img.width(),image.width())
        finally: w.close()

if __name__=='__main__':unittest.main()
