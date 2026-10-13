from gui_sample import seed_sample
"""Lightweight Qt UI smoke checks. Skipped where PySide6 is unavailable.

These run on the user's normal Windows environment without showing a window.
"""

import importlib.util
import unittest

QT_INSTALLED = importlib.util.find_spec("PySide6") is not None


@unittest.skipUnless(QT_INSTALLED, "PySide6 not available in this Python environment")
class Stage4GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_switch_glands_and_depth_entry(self):
        from src.ui.main_window import MainWindow
        from src.calculations.rectangular import FemaleRectangularResults, MaleRectangularResults
        window=MainWindow();seed_sample(window)
        self.assertIsInstance(window._last_result, MaleRectangularResults)
        window.configuration.setCurrentIndex(1)
        self.assertIsInstance(window._last_result, FemaleRectangularResults)
        self.assertTrue(window.male_group.isHidden())
        self.assertFalse(window.female_group.isHidden())
        self.assertIs(window.entry_mode_stack.currentWidget(), window.female_entry_mode)
        self.assertEqual(window.female_entry_mode.currentText(), "ID")
        direct = window._last_result
        window.female_entry_mode.setCurrentIndex(1)
        self.assertIsInstance(window._last_result, FemaleRectangularResults)
        self.assertAlmostEqual(direct.gland_fill_percent.nominal,
                               window._last_result.gland_fill_percent.nominal)
        window.configuration.setCurrentIndex(0)
        self.assertIsInstance(window._last_result, MaleRectangularResults)
        self.assertFalse(window.male_group.isHidden())
        self.assertTrue(window.female_group.isHidden())
        self.assertIs(window.entry_mode_stack.currentWidget(), window.entry_mode)
        window.close()

    def test_guide_search_and_select(self):
        from src.ui.main_window import MainWindow
        from src.ui.size_guide import SizeGuide
        window=MainWindow();seed_sample(window)
        guide = SizeGuide(window.as568_sizes, window)
        guide.search.setText("AS568-112")
        visible = [row for row in range(guide.table.rowCount()) if not guide.table.isRowHidden(row)]
        self.assertEqual(len(visible), 1)
        guide.table.selectRow(visible[0])
        guide._choose()
        self.assertEqual(guide.chosen_dash, "-112")
        index = window.ring_size.findData(guide.chosen_dash)
        window.ring_size.setCurrentIndex(index)
        self.assertAlmostEqual(window.rows["ring_id"].nominal.value(), .487)
        window.ring_size.setCurrentIndex(0)
        self.assertTrue(window.rows["ring_id"].nominal.isEnabled())
        self.assertAlmostEqual(window.rows["ring_id"].nominal.value(), .487)
        window.close()


if __name__ == "__main__":
    unittest.main()
