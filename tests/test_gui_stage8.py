from gui_sample import seed_sample
"""Windows PySide6 smoke tests, run during guarded installation."""
import importlib.util
import unittest
QT_INSTALLED=importlib.util.find_spec('PySide6') is not None

@unittest.skipUnless(QT_INSTALLED,'PySide6 not installed')
class Stage8GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])
    def test_three_primary_results_and_detail_toggle(self):
        from src.ui.main_window import MainWindow
        window=MainWindow();seed_sample(window)
        try:
            self.assertIsNotNone(window._last_evaluation)
            self.assertFalse(hasattr(window,'details_group'))
            self.assertIn('>O-ring ID stretch</span>', window.overview_cells[('Fit',0)].text())
            self.assertIn('0–5%', window.overview_cells[('Fit',0)].text())
            self.assertIn('%',window.overview_cells[('Squeeze',2)].text())
            dialog=window._make_tolerance_trace_dialog()
            from PySide6.QtWidgets import QTabWidget
            self.assertEqual(dialog.findChild(QTabWidget,'result_tabs').count(),2)
            dialog.close()
            window.configuration.setCurrentIndex(1)
            self.assertIn('>O-ring OD interference</span>', window.overview_cells[('Fit',0)].text())
            self.assertIn('0–2%', window.overview_cells[('Fit',0)].text())
            self.assertEqual(window._last_screening.checks[1].name,'OD interference')
        finally:window.close()
    def test_screen_capture_card_has_full_result_and_png(self):
        from src.ui.main_window import MainWindow
        from src.ui.snapshot_view import ScreenshotDialog
        window=MainWindow();seed_sample(window)
        try:
            r=window._last_result;s=window._last_screening
            rows=[('Squeeze (%)',('10%','11%','12%'),s.checks[0]),
                  ('ID stretch (%)',('1%','2%','3%'),s.checks[1]),
                  ('Gland fill (%)',('60%','70%','80%'),s.checks[2])]
            dialog=ScreenshotDialog('Stage 8 test',rows,s,window._capture_inputs(),window)
            pixmap=dialog.capture()
            self.assertFalse(pixmap.isNull())
            self.assertGreater(pixmap.width(),500)
            self.assertGreater(pixmap.height(),150)
            dialog.close()
        finally:window.close()
    def test_normal_catalogue_349_entries_and_no_special_half(self):
        from src.ui.main_window import MainWindow
        from src.ui.size_guide import SizeGuide
        window=MainWindow();seed_sample(window)
        try:
            self.assertEqual(len(window.as568_sizes),349)
            guide=SizeGuide(window.as568_sizes,window)
            self.assertEqual(guide.table.item(0,0).text(),'AS568-001')
            self.assertEqual(guide.table.item(1,0).text(),'AS568-002')
            self.assertEqual(window.ring_size.findData('-001 1/2'),-1)
            guide.close()
        finally:window.close()
