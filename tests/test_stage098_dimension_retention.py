"""Regression protection for retaining component inputs across view switches.

The physical piston OD and cylinder ID are shown in different Qt Designer
widgets in alternative modes. No selector should discard a value already
entered, nor replace a value already deliberately set in the destination.
"""
from pathlib import Path
import ast
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
GUI = importlib.util.find_spec('PySide6') is not None


class DimensionRetentionSourceTests(unittest.TestCase):
    def test_selection_changes_copy_only_into_unused_dimensions(self):
        tree = ast.parse((ROOT/'src/ui/main_window.py').read_text(encoding='utf8'))
        names = {node.name for node in ast.walk(tree)
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for name in ('_fill_unused_dimension', '_fill_other_configuration',
                     '_change_mode', '_change_female_mode', '_change_configuration'):
            self.assertIn(name, names)


@unittest.skipUnless(GUI, 'Requires PySide6 GUI on Windows')
class DimensionRetentionWindowsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_mode_switches_copy_hardware_and_keep_original_values(self):
        from src.ui.main_window import MainWindow
        w = MainWindow()
        try:
            # Male OD mode -> depth mode must carry Piston OD and tolerance.
            w.rows['direct_rod_od'].nominal.setValue(0.745)
            w.rows['direct_rod_od'].tolerance.setValue(0.00025)
            w.rows['cylinder_id'].nominal.setValue(0.770)
            w.rows['cylinder_id'].tolerance.setValue(0.001)
            w.entry_mode.setCurrentIndex(1)
            self.assertAlmostEqual(w.rows['rod_od'].nominal.value(), 0.745)
            self.assertAlmostEqual(w.rows['rod_od'].tolerance.value(), 0.00025)
            self.assertAlmostEqual(w.rows['cylinder_id'].nominal.value(), 0.770)
            # Editing depth-mode piston OD must not erase entered OD-mode input.
            w.rows['rod_od'].nominal.setValue(0.744)
            w.entry_mode.setCurrentIndex(0)
            self.assertAlmostEqual(w.rows['direct_rod_od'].nominal.value(), 0.745)
            w.entry_mode.setCurrentIndex(1)
            self.assertAlmostEqual(w.rows['rod_od'].nominal.value(), 0.744)
        finally:
            w.close()

    def test_component_switch_copies_only_common_hardware_into_empty_fields(self):
        from src.ui.main_window import MainWindow
        w = MainWindow()
        try:
            w.rows['direct_rod_od'].nominal.setValue(0.625)
            w.rows['direct_rod_od'].tolerance.setValue(0.001)
            w.rows['cylinder_id'].nominal.setValue(0.650)
            w.rows['cylinder_id'].tolerance.setValue(0.0005)
            w.rows['gland_od'].nominal.setValue(0.570)
            w.configuration.setCurrentIndex(1)
            self.assertAlmostEqual(w.female_rows['rod_od'].nominal.value(), 0.625)
            self.assertAlmostEqual(w.female_rows['rod_od'].tolerance.value(), 0.001)
            self.assertAlmostEqual(w.female_rows['direct_cylinder_id'].nominal.value(), 0.650)
            self.assertAlmostEqual(w.female_rows['cylinder_id'].nominal.value(), 0.650)
            self.assertAlmostEqual(w.female_rows['cylinder_id'].tolerance.value(), 0.0005)
            # Male groove OD is not interchangeable with female groove ID.
            self.assertEqual(w.female_rows['gland_id'].nominal.value(), 0.0)
            # The cylinder configuration can use distinct previously entered
            # values without rewriting the original male configuration.
            w.female_rows['rod_od'].nominal.setValue(0.623)
            w.configuration.setCurrentIndex(0)
            self.assertAlmostEqual(w.rows['direct_rod_od'].nominal.value(), 0.625)
            self.assertAlmostEqual(w.rows['gland_od'].nominal.value(), 0.570)
            w.configuration.setCurrentIndex(1)
            self.assertAlmostEqual(w.female_rows['rod_od'].nominal.value(), 0.623)
        finally:
            w.close()

    def test_cylinder_depth_to_piston_depth_and_back_retains_tolerance(self):
        """Regression: female depth -> male depth must keep both numbers."""
        from src.ui.main_window import MainWindow
        w = MainWindow()
        try:
            w.configuration.setCurrentIndex(1)  # Cylinder groove
            w.female_entry_mode.setCurrentIndex(1)  # Depth
            w.entry_mode.setCurrentIndex(1)  # Piston Depth for when switched
            w.female_rows['groove_depth'].nominal.setValue(0.083)
            w.female_rows['groove_depth'].tolerance.setValue(0.002)
            w.configuration.setCurrentIndex(0)  # Piston groove, still Depth
            self.assertAlmostEqual(w.rows['groove_depth'].nominal.value(), 0.083)
            self.assertAlmostEqual(w.rows['groove_depth'].tolerance.value(), 0.002)
            # Once a destination has a different entered value, it is retained.
            w.rows['groove_depth'].nominal.setValue(0.087)
            w.rows['groove_depth'].tolerance.setValue(0.001)
            w.configuration.setCurrentIndex(1)
            self.assertAlmostEqual(w.female_rows['groove_depth'].nominal.value(), 0.083)
            self.assertAlmostEqual(w.female_rows['groove_depth'].tolerance.value(), 0.002)
            w.configuration.setCurrentIndex(0)
            self.assertAlmostEqual(w.rows['groove_depth'].nominal.value(), 0.087)
            self.assertAlmostEqual(w.rows['groove_depth'].tolerance.value(), 0.001)
        finally:
            w.close()

    def test_piston_depth_to_cylinder_depth_and_reset(self):
        from src.ui.main_window import MainWindow
        w = MainWindow()
        try:
            w.entry_mode.setCurrentIndex(1)  # Piston Depth
            w.female_entry_mode.setCurrentIndex(1)  # Cylinder Depth
            w.rows['groove_depth'].nominal.setValue(0.094)
            w.rows['groove_depth'].tolerance.setValue(0.0015)
            w.configuration.setCurrentIndex(1)
            self.assertAlmostEqual(w.female_rows['groove_depth'].nominal.value(), 0.094)
            self.assertAlmostEqual(w.female_rows['groove_depth'].tolerance.value(), 0.0015)
            # Reset remains the only action that clears both independent slots.
            w.reset_button.click()
            self.assertEqual(w.female_rows['groove_depth'].nominal.value(), 0.0)
            self.assertEqual(w.rows['groove_depth'].nominal.value(), 0.0)
            self.assertEqual(w.female_rows['groove_depth'].tolerance.value(), 0.0)
            self.assertEqual(w.rows['groove_depth'].tolerance.value(), 0.0)
        finally:
            w.close()

    def test_female_depth_switch_and_reset(self):
        from src.ui.main_window import MainWindow
        w = MainWindow()
        try:
            w.configuration.setCurrentIndex(1)
            w.female_rows['direct_cylinder_id'].nominal.setValue(0.750)
            w.female_rows['direct_cylinder_id'].tolerance.setValue(0.002)
            w.female_entry_mode.setCurrentIndex(1)
            self.assertAlmostEqual(w.female_rows['cylinder_id'].nominal.value(), 0.750)
            self.assertAlmostEqual(w.female_rows['cylinder_id'].tolerance.value(), 0.002)
            w.female_rows['cylinder_id'].nominal.setValue(0.751)
            w.female_entry_mode.setCurrentIndex(0)
            self.assertAlmostEqual(w.female_rows['direct_cylinder_id'].nominal.value(), 0.750)
            w.reset_button.click()
            for group in (w.rows, w.female_rows, w.shared_rows):
                for row in group.values():
                    self.assertEqual(row.nominal.value(), 0.0)
                    self.assertEqual(row.tolerance.value(), 0.0)
            self.assertEqual(w.female_entry_mode.currentData(), 'gland_id')
        finally:
            w.close()
