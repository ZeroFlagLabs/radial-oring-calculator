"""Regression tests for live, two-way tolerance representation conversion."""
import unittest
from decimal import Decimal

from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from gui_sample import seed_sample


class LiveToleranceConversionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def make_window(self):
        w = MainWindow()
        seed_sample(w)
        w.show()
        self.app.processEvents()
        self.addCleanup(w.close)
        return w

    def test_status_bar_explains_both_tolerance_representations(self):
        w = self.make_window()
        row = w.shared_rows['width']
        self.assertIn('Symmetrical:', w.statusBar().currentMessage())
        row.mode_limits.click()
        self.assertIn('Limits:', w.statusBar().currentMessage())
        row.mode_sym.click()
        self.assertIn('Symmetrical:', w.statusBar().currentMessage())

    def test_all_17_fields_roundtrip_unchanged_without_input_edits(self):
        w = self.make_window()
        rows = [r for group in (w.rows,w.female_rows,w.shared_rows)
                for r in group.values()]
        self.assertEqual(len(rows),17)
        for row in rows:
            a,b = row.nominal.value(),row.tolerance.value()
            row.mode_limits.click()
            self.assertTrue(row.limit_mode)
            self.assertAlmostEqual(row.limit_min.value(),a-b,places=9)
            self.assertAlmostEqual(row.limit_max.value(),a+b,places=9)
            row.mode_sym.click()
            self.assertFalse(row.limit_mode)
            self.assertAlmostEqual(row.nominal.value(),a,places=9)
            self.assertAlmostEqual(row.tolerance.value(),b,places=9)

    def test_three_thou_and_zero_tolerance(self):
        w = self.make_window()
        row = w.rows['gland_od']
        row.nominal.setValue(1.0)
        row.tolerance.setValue(.003)
        row.mode_limits.click()
        self.assertAlmostEqual(row.limit_min.value(),.997,places=9)
        self.assertAlmostEqual(row.limit_max.value(),1.003,places=9)
        row.mode_sym.click()
        self.assertAlmostEqual(row.nominal.value(),1,places=9)
        self.assertAlmostEqual(row.tolerance.value(),.003,places=9)
        row.tolerance.setValue(0)
        row.mode_limits.click()
        self.assertEqual(row.limit_min.value(),1.0)
        self.assertEqual(row.limit_max.value(),1.0)
        row.mode_sym.click()
        self.assertEqual(row.tolerance.value(),0)

    def test_partial_limits_all_positive_only_rows(self):
        w = self.make_window()
        groups = (
            (w.rows, ('gland_od', 'direct_rod_od', 'rod_od', 'groove_depth',
                      'cylinder_id', 'ring_id', 'section')),
            (w.female_rows, ('gland_id', 'direct_cylinder_id', 'cylinder_id',
                             'groove_depth', 'rod_od')),
            (w.shared_rows, ('width',)),
        )
        for group, keys in groups:
            for key in keys:
                row = group[key]
                for low, high, expected in (
                        (1.0, 0.0, (1.0, 0.0)),
                        (0.0, 1.0, (1.0, 0.0)),
                        (0.0, 0.0, (0.0, 0.0)),
                        (1.0, 1.0, (1.0, 0.0)),
                        (.997, 1.003, (1.0, .003))):
                    with self.subTest(key=key, low=low, high=high):
                        row.mode_limits.click()
                        row.limit_min.setValue(low)
                        row.limit_max.setValue(high)
                        self.assertTrue(row.limit_mode)
                        row.mode_sym.click()
                        self.assertFalse(row.limit_mode)
                        self.assertEqual((row.nominal.value(),
                                          row.tolerance.value()), expected)
                        row.mode_limits.click()
                        self.assertEqual(row.limit_min.value(),
                                         expected[0] - expected[1])
                        self.assertAlmostEqual(row.limit_max.value(),
                                               expected[0] + expected[1], places=12)
                        row.mode_sym.click()

    def test_zero_endpoint_radii_and_angles_remain_literal(self):
        w = self.make_window()
        for key in ('radius', 'entrance_radius', 'angle', 'rect_angle'):
            row = w.shared_rows[key]
            with self.subTest(key=key):
                row.mode_limits.click()
                row.limit_min.setValue(0)
                row.limit_max.setValue(.004)
                row.mode_sym.click()
                self.assertFalse(row.limit_mode)
                self.assertEqual((row.nominal.value(), row.tolerance.value()),
                                 (.002, .002))
                row.mode_limits.click()
                self.assertEqual((row.limit_min.value(), row.limit_max.value()),
                                 (0, .004))
                row.limit_min.setValue(.004)
                row.limit_max.setValue(0)
                row.mode_sym.click()
                self.assertTrue(row.limit_mode)
        row = w.shared_rows['rect_angle']
        row.limit_min.setValue(-2)
        row.limit_max.setValue(0)
        row.mode_sym.click()
        self.assertEqual((row.nominal.value(), row.tolerance.value()), (-1, 1))
        row.mode_limits.click()
        self.assertEqual((row.limit_min.value(), row.limit_max.value()), (-2, 0))

    def test_partial_limits_not_substituted_during_calculation(self):
        w = self.make_window()
        row = w.shared_rows['width']
        row.mode_limits.click()
        row.limit_min.setValue(0)
        row.limit_max.setValue(.146)
        self.assertEqual(row.dimension().minimum, 0)
        self.assertEqual(row.effective_nominal(), .073)
        self.assertIsNone(w._last_result)
        row.limit_min.setValue(.146)
        row.limit_max.setValue(0)
        with self.assertRaisesRegex(ValueError, 'minimum limit exceeds maximum'):
            row.dimension()
        self.assertIsNone(w._last_result)
        row.mode_sym.click()
        self.assertEqual((row.nominal.value(), row.tolerance.value()), (.146, 0))
        self.assertIsNotNone(w._last_result)

    def test_partial_limits_preserve_precision_over_repeated_conversions(self):
        w = self.make_window()
        row = w.shared_rows['width']
        for low, high in ((.141000000001, 0), (0, .141000000001)):
            row.mode_limits.click()
            for editor in (row.limit_min, row.limit_max):
                editor.setDecimals(12)
            row.limit_min.setValue(low)
            row.limit_max.setValue(high)
            for _ in range(5):
                row.mode_sym.click()
                self.assertEqual(row.nominal.value(), .141000000001)
                self.assertEqual(row.tolerance.value(), 0)
                row.mode_limits.click()
                self.assertEqual((row.limit_min.value(), row.limit_max.value()),
                                 (.141000000001, .141000000001))
            row.mode_sym.click()

    def test_new_symmetrical_values_reconvert_not_old_stale_limits(self):
        w = self.make_window()
        row = w.shared_rows['width']
        row.mode_limits.click()
        row.limit_min.setValue(.140)
        row.limit_max.setValue(.160)
        row.mode_sym.click()
        self.assertAlmostEqual(row.nominal.value(),.150,places=9)
        self.assertAlmostEqual(row.tolerance.value(),.010,places=9)
        row.nominal.setValue(.147)
        row.tolerance.setValue(.002)
        row.mode_limits.click()
        self.assertAlmostEqual(row.limit_min.value(),.145,places=9)
        self.assertAlmostEqual(row.limit_max.value(),.149,places=9)

    def test_new_limit_values_reconvert_not_old_stale_symmetry(self):
        w = self.make_window()
        row = w.shared_rows['width']
        row.mode_limits.click()
        row.limit_min.setValue(.141)
        row.limit_max.setValue(.1485)
        row.mode_sym.click()
        self.assertAlmostEqual(row.nominal.value(),.14475,places=9)
        self.assertAlmostEqual(row.tolerance.value(),.00375,places=9)
        row.mode_limits.click()
        row.limit_min.setValue(.139)
        row.limit_max.setValue(.153)
        row.mode_sym.click()
        self.assertAlmostEqual(row.nominal.value(),.146,places=9)
        self.assertAlmostEqual(row.tolerance.value(),.007,places=9)

    def test_six_decimal_limits_roundtrip_without_one_microinch_loss(self):
        w = self.make_window()
        row = w.shared_rows['width']
        row.mode_limits.click()
        row.limit_min.setValue(.141001)
        row.limit_max.setValue(.148500)
        for n in range(5):
            row.mode_sym.click()
            self.assertEqual(row.nominal.decimals(),7)
            self.assertEqual(row.tolerance.decimals(),7)
            self.assertAlmostEqual(row.nominal.value(),.1447505,delta=1e-12)
            self.assertAlmostEqual(row.tolerance.value(),.0037495,delta=1e-12)
            self.assertIn('0.1447505',row.nominal.text())
            self.assertIn('0.0037495',row.tolerance.text())
            row.mode_limits.click()
            self.assertAlmostEqual(row.limit_min.value(),.141001,delta=1e-12)
            self.assertAlmostEqual(row.limit_max.value(),.148500,delta=1e-12)
        self.assertEqual(w.width(),1080)
        self.assertIn(w.height(),(784,801))  # offscreen Qt vs native Windows font metrics

    def test_signed_wall_angle_negative_min_max_and_zero_tolerance(self):
        w = self.make_window()
        row = w.shared_rows['rect_angle']
        row.nominal.setValue(-1.0)
        row.tolerance.setValue(2.0)
        row.mode_limits.click()
        self.assertEqual(row.limit_min.value(),-3.0)
        self.assertEqual(row.limit_max.value(),1.0)
        self.assertTrue(row.limit_min.text().endswith(' deg'))
        row.mode_sym.click()
        self.assertEqual(row.nominal.value(),-1.0)
        self.assertEqual(row.tolerance.value(),2.0)
        row.tolerance.setValue(0)
        row.mode_limits.click()
        self.assertEqual(row.limit_min.value(),-1)
        self.assertEqual(row.limit_max.value(),-1)

    def test_reversed_limits_remain_visible_without_bad_conversion(self):
        w = self.make_window()
        row = w.shared_rows['width']
        row.mode_limits.click()
        row.limit_min.setValue(.151)
        row.limit_max.setValue(.141)
        self.assertIsNone(w._last_result)
        row.mode_sym.click()
        self.assertTrue(row.limit_mode)
        self.assertTrue(row.mode_limits.isChecked())
        self.assertEqual(row.nominal_stack.currentIndex(),1)
        self.assertAlmostEqual(row.limit_min.value(),.151,places=9)
        self.assertAlmostEqual(row.limit_max.value(),.141,places=9)
        self.assertFalse(w.save_snapshot_button.isEnabled())
        row.limit_max.setValue(.153)
        row.mode_sym.click()
        self.assertFalse(row.limit_mode)
        self.assertAlmostEqual(row.nominal.value(),.152,places=9)
        self.assertAlmostEqual(row.tolerance.value(),.001,places=9)

    def test_infeasible_nonnegative_endpoint_does_not_silently_clamp(self):
        w = self.make_window()
        row = w.shared_rows['radius']
        row.nominal.setValue(.001)
        row.tolerance.setValue(.003)
        row.mode_limits.click()
        self.assertFalse(row.limit_mode)
        self.assertTrue(row.mode_sym.isChecked())
        self.assertAlmostEqual(row.nominal.value(),.001,places=9)
        self.assertAlmostEqual(row.tolerance.value(),.003,places=9)
        self.assertIn('outside the permitted input range',
                      w.statusBar().currentMessage())

    def test_overprecision_conversion_is_rejected_atomically(self):
        w = self.make_window()
        row = w.shared_rows['width']
        row.mode_limits.click()
        for editor in (row.limit_min,row.limit_max):
            editor.setDecimals(12)
        row.limit_min.setValue(.141000000001)
        row.limit_max.setValue(.148500000002)
        original=(row.nominal.value(),row.tolerance.value())
        row.mode_sym.click()
        self.assertTrue(row.limit_mode)
        self.assertTrue(row.mode_limits.isChecked())
        self.assertEqual((row.nominal.value(),row.tolerance.value()),original)
        self.assertAlmostEqual(row.limit_min.value(),.141000000001,delta=1e-13)
        self.assertAlmostEqual(row.limit_max.value(),.148500000002,delta=1e-13)
        self.assertIn('requires more than 12 decimal places',
                      w.statusBar().currentMessage())

    def test_reset_and_as568_selection_restore_standard_six_place_precision(self):
        w = self.make_window()
        row = w.shared_rows['width']
        row.mode_limits.click()
        row.limit_min.setValue(.141001)
        row.limit_max.setValue(.148500)
        row.mode_sym.click()
        self.assertEqual(row.nominal.decimals(),7)
        w._reset_dimensions()
        self.assertEqual(row.nominal.decimals(),6)
        self.assertEqual(row.tolerance.decimals(),6)
        self.assertEqual(row.limit_min.decimals(),6)
        self.assertEqual(row.limit_max.decimals(),6)
        self.assertEqual(row.nominal.value(),0)
        ring=w.rows['ring_id']
        ring.mode_limits.click()
        ring.limit_min.setValue(.548001)
        ring.limit_max.setValue(.555500)
        ring.mode_sym.click()
        self.assertEqual(ring.nominal.decimals(),7)
        w.ring_size.setCurrentIndex(w.ring_size.findData('-113'))
        for editor in (ring.nominal,ring.tolerance,ring.limit_min,ring.limit_max):
            self.assertEqual(editor.decimals(),6)
            self.assertFalse(editor.isEnabled())

    def test_as568_catalogue_stays_locked_and_reconverts_both_ways(self):
        w = self.make_window()
        ix = w.ring_size.findData('-113')
        self.assertGreater(ix,0)
        w.ring_size.setCurrentIndex(ix)
        for key in ('ring_id','section'):
            row = w.rows[key]
            original=(row.nominal.value(),row.tolerance.value())
            row.mode_limits.click()
            self.assertTrue(row.mode_limits.isEnabled())
            self.assertFalse(row.limit_min.isEnabled())
            self.assertFalse(row.limit_max.isEnabled())
            self.assertAlmostEqual(row.limit_min.value(),original[0]-original[1],places=9)
            self.assertAlmostEqual(row.limit_max.value(),original[0]+original[1],places=9)
            row.mode_sym.click()
            self.assertFalse(row.nominal.isEnabled())
            self.assertFalse(row.tolerance.isEnabled())
            self.assertEqual((row.nominal.value(),row.tolerance.value()),original)

if __name__ == '__main__':
    unittest.main()
