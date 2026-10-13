from gui_sample import seed_sample
"""Stage 6 Windows UI smoke checks; PySide6 needed on user's machine."""
import importlib.util
import unittest

QT_INSTALLED = importlib.util.find_spec('PySide6') is not None


@unittest.skipUnless(QT_INSTALLED, 'PySide6 is not installed')
class Stage6GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_rectangular_start_angle_zero_and_profile_results_displayed(self):
        from src.ui.main_window import MainWindow
        window=MainWindow();seed_sample(window)
        try:
            self.assertEqual(window.groove_type.currentData(),'rectangular')
            self.assertEqual(window.shared_rows['rect_angle'].nominal.value(),0)
            self.assertIsNotNone(window._last_result)
            self.assertIsNotNone(window._last_result.groove_area_sq_in)
            dialog=window._make_tolerance_trace_dialog()
            from PySide6.QtWidgets import QTableWidget
            table=dialog.findChild(QTableWidget,'geometry_table')
            self.assertGreaterEqual(table.rowCount(),5)
            self.assertIn('.',table.item(table.rowCount()-1,2).text())
            dialog.close()
        finally:
            window.close()

    def test_entrance_and_bottom_radii_update_area(self):
        from src.ui.main_window import MainWindow
        window=MainWindow();seed_sample(window)
        try:
            sharp=window._last_result.cavity_area_sq_in.nominal
            window.shared_rows['entrance_radius'].nominal.setValue(.005)
            self.assertGreater(window._last_result.cavity_area_sq_in.nominal,sharp)
            with_top=window._last_result.cavity_area_sq_in.nominal
            window.shared_rows['radius'].nominal.setValue(.010)
            self.assertLess(window._last_result.cavity_area_sq_in.nominal,with_top)
        finally:
            window.close()

    def test_signed_angle_and_groove_switching(self):
        from src.ui.main_window import MainWindow
        window=MainWindow();seed_sample(window)
        try:
            window.shared_rows['rect_angle'].nominal.setValue(-1)
            self.assertAlmostEqual(window._collect().wall_angle_deg.nominal,-1)
            self.assertIsNotNone(window._last_result)
            window.groove_type.setCurrentIndex(1)
            self.assertEqual(window._collect().angle_deg.nominal,24)
            self.assertIsNotNone(window._last_result)
            window.groove_type.setCurrentIndex(0)
            self.assertAlmostEqual(window._collect().wall_angle_deg.nominal,-1)
            self.assertEqual(window.shared_rows['entrance_radius'].nominal.value(),0)
        finally:
            window.close()

    def test_male_female_and_direct_depth_modes_with_radii(self):
        from src.ui.main_window import MainWindow
        window=MainWindow();seed_sample(window)
        try:
            window.entry_mode.setCurrentIndex(1)
            window.shared_rows['radius'].nominal.setValue(.005)
            window.shared_rows['entrance_radius'].nominal.setValue(.003)
            self.assertIsNotNone(window._last_result)
            window.configuration.setCurrentIndex(1)
            self.assertIsNotNone(window._last_result)
            window.female_entry_mode.setCurrentIndex(1)
            self.assertIsNotNone(window._last_result)
            window.groove_type.setCurrentIndex(1)
            self.assertIsNotNone(window._last_result)
        finally:
            window.close()


if __name__=='__main__':
    unittest.main()
