from gui_sample import seed_sample
"""Stage 9 GUI regression checks; run on Windows with PySide6 installed."""
import importlib.util
import unittest

QT_INSTALLED = importlib.util.find_spec('PySide6') is not None


@unittest.skipUnless(QT_INSTALLED,'PySide6 unavailable')
class Stage9GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_gland_profiles_and_modes_update_diagram_and_preserve_engine(self):
        from src.ui.main_window import MainWindow
        w=MainWindow();seed_sample(w)
        try:
            self.assertIsNotNone(w._last_result)
            self.assertEqual(w.diagram.config,'male')
            for config in range(2):
                w.configuration.setCurrentIndex(config)
                for profile in range(2):
                    w.groove_type.setCurrentIndex(profile)
                    self.assertEqual(w.diagram.config,'female' if config else 'male')
                    self.assertEqual(w.diagram.groove,'dovetail' if profile else 'rectangular')
                    self.assertIsNotNone(w._last_result)
                    self.assertFalse(w.diagram.to_pixmap(720,420).isNull())
                if config == 0:
                    w.entry_mode.setCurrentIndex(1)
                    self.assertEqual(w.diagram.entry,'rod_and_depth')
                else:
                    w.female_entry_mode.setCurrentIndex(1)
                    self.assertEqual(w.diagram.entry,'cylinder_and_depth')
        finally:
            w.close()

    def test_field_focus_mapping_and_precision_without_selector(self):
        from src.ui.main_window import MainWindow
        from PySide6.QtCore import QEvent
        w=MainWindow();seed_sample(w)
        try:
            self.assertFalse(hasattr(w,'precision'))
            self.assertEqual(w.rows['section'].nominal.textFromValue(.103),'0.103')
            self.assertEqual(w.female_rows['groove_depth'].tolerance.textFromValue(.00025),'0.00025')
            target=w.shared_rows['width'].nominal
            w.eventFilter(target,QEvent(QEvent.Type.FocusIn))
            self.assertEqual(w.diagram.active_key,'width')
            target=w.rows['groove_depth'].nominal
            w.eventFilter(target,QEvent(QEvent.Type.FocusIn))
            self.assertEqual(w.diagram.active_key,'depth')
        finally:
            w.close()

    def test_screen_shot_with_schematic(self):
        from src.ui.main_window import MainWindow
        from src.ui.snapshot_view import ScreenshotDialog
        w=MainWindow();seed_sample(w)
        try:
            rows=[('Squeeze',('1%','2%','3%'),w._last_screening.checks[0]),
                  ('ID stretch',('1%','2%','3%'),w._last_screening.checks[1]),
                  ('Gland fill',('60%','70%','80%'),w._last_screening.checks[2])]
            dialog=ScreenshotDialog('Stage 9 test',rows,w._last_screening,
                         w._capture_inputs(),w,sketch=w.diagram.to_pixmap())
            pixmap=dialog.capture()
            self.assertFalse(pixmap.isNull())
            self.assertGreater(pixmap.height(),500)
            dialog.close()
        finally:
            w.close()

    def test_expanded_details_and_piston_label(self):
        from src.ui.main_window import MainWindow
        w=MainWindow();seed_sample(w)
        try:
            self.assertEqual(w.diagram.values['piston_od'],w.rows['direct_rod_od'].nominal.value())
            self.assertIn('Piston OD (in)',dict(w._capture_inputs()))
            from PySide6.QtWidgets import QTabWidget
            dialog=w._make_tolerance_trace_dialog()
            self.assertEqual(dialog.findChild(QTabWidget,'result_tabs').count(),2)
            dialog.close()
            w.configuration.setCurrentIndex(1)
            self.assertIn('Piston OD (in)',dict(w._capture_inputs()))
        finally:
            w.close()

if __name__=='__main__':unittest.main()
