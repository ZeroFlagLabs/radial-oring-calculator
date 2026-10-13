from gui_sample import seed_sample
"""GUI regression tests; these run on Windows when PySide6 is installed."""

import importlib.util
import unittest

QT_INSTALLED = importlib.util.find_spec('PySide6') is not None


@unittest.skipUnless(QT_INSTALLED, 'PySide6 not available in this Python environment')
class Stage5GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_shared_width_keeps_user_value_when_switching_gender(self):
        from src.ui.main_window import MainWindow
        window=MainWindow();seed_sample(window)
        window.shared_rows['width'].nominal.setValue(.146)
        window.shared_rows['width'].tolerance.setValue(.005)
        window.configuration.setCurrentIndex(1)
        self.assertAlmostEqual(window.shared_rows['width'].nominal.value(), .146)
        self.assertAlmostEqual(window.shared_rows['width'].tolerance.value(), .005)
        self.assertAlmostEqual(window._collect().gland_width.nominal, .146)
        window.configuration.setCurrentIndex(0)
        self.assertAlmostEqual(window._collect().gland_width.nominal, .146)
        window.close()

    def test_dovetail_direct_and_depth_modes_connect(self):
        from src.ui.main_window import MainWindow
        from src.calculations.dovetail import MaleDovetailInputs, FemaleDovetailInputs
        window=MainWindow();seed_sample(window)
        window.groove_type.setCurrentIndex(1)
        self.assertIsInstance(window._collect(), MaleDovetailInputs)
        self.assertIsNotNone(window._last_result)
        window.entry_mode.setCurrentIndex(1)
        self.assertIsInstance(window._collect(), MaleDovetailInputs)
        window.configuration.setCurrentIndex(1)
        self.assertIsInstance(window._collect(), FemaleDovetailInputs)
        window.female_entry_mode.setCurrentIndex(1)
        self.assertIsInstance(window._collect(), FemaleDovetailInputs)
        window.close()

    def test_size_guide_starts_numeric_ascending_with_half(self):
        from src.ui.main_window import MainWindow
        from src.ui.size_guide import SizeGuide
        window=MainWindow();seed_sample(window)
        guide = SizeGuide(window.as568_sizes, window)
        self.assertEqual(
            [guide.table.item(i, 0).text() for i in range(5)],
            ['AS568-001', 'AS568-002', 'AS568-003', 'AS568-004', 'AS568-005'],
        )
        from PySide6.QtCore import Qt
        self.assertEqual(guide.table.item(0, 1).textAlignment(), Qt.AlignmentFlag.AlignCenter)
        guide.table.sortItems(1, Qt.SortOrder.DescendingOrder)
        ids = [float(guide.table.item(row, 1).text()) for row in range(guide.table.rowCount())]
        # Different AS568 sizes can share the same ID (e.g. -395 and -475).
        # Compare the complete ordered sequence rather than requiring strict inequality.
        self.assertEqual(ids, sorted(ids, reverse=True))
        self.assertGreater(ids[0], ids[-1])
        guide.close()
        window.close()

    def test_application_still_switches_and_inputs_format_automatically(self):
        from src.ui.main_window import MainWindow
        window=MainWindow();seed_sample(window)
        self.assertEqual(window.application.currentData(), 'static')
        window.application.setCurrentIndex(1)
        self.assertEqual(window._last_screening.application, 'dynamic')
        self.assertFalse(hasattr(window,'precision'))
        self.assertEqual(window.shared_rows['angle'].nominal.minimum_display_decimals,1)
        self.assertEqual(window.female_rows['groove_depth'].tolerance.textFromValue(.00025),'0.00025')
        window.close()


if __name__ == '__main__':
    unittest.main()
