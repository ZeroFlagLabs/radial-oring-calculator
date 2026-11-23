"""v2.1.0 per-input real Limits mode, units, geometry and retention tests."""
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from dataclasses import replace
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QAbstractSpinBox, QStyle, QStyleOptionSpinBox
from PySide6.QtTest import QTest
from src.ui.main_window import MainWindow
from src.calculations.rectangular import Dimension
from src.calculations.installed import calculate_installed
from gui_sample import seed_sample


class ToleranceModeFunctionalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def window(self):
        w=MainWindow()
        seed_sample(w)
        w.show()
        self.app.processEvents()
        self.addCleanup(w.close)
        return w

    def equal_envelopes(self, actual, expected):
        for name in ('squeeze_in', 'squeeze_percent', 'stretch_percent',
                     'gland_fill_percent', 'cavity_area_sq_in'):
            a=getattr(actual,name)
            b=getattr(expected,name)
            for case in ('minimum','nominal','maximum'):
                self.assertAlmostEqual(getattr(a,case),getattr(b,case),places=9,
                    msg=f'{name}.{case}')

    def test_disabled_steppers_blend_into_rounded_field(self):
        """Disabled steppers must not paint a square over rounded input corners."""
        ui = Path(__file__).resolve().parents[1] / 'src/ui/forms/main_window.ui'
        root = ET.parse(ui).getroot()
        surface = next(w for w in root.iter('widget')
                       if w.get('name') == 'appSurface')
        style = surface.find("./property[@name='styleSheet']/string").text
        self.assertIn('QDoubleSpinBox:disabled { background: #e3e8ee;', style)
        self.assertIn('border-radius: 4px;', style)
        self.assertIn('QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {', style)
        self.assertIn('background: transparent;', style)
        self.assertIn('QDoubleSpinBox::up-arrow:disabled', style)
        self.assertIn('QDoubleSpinBox::down-arrow:disabled', style)
        self.assertNotIn('QDoubleSpinBox::up-button:disabled', style)
        self.assertNotIn('QDoubleSpinBox::down-button:disabled', style)
        w=self.window()
        w.ring_size.setCurrentIndex(w.ring_size.findData('-113'))
        for row in (w.rows['ring_id'], w.rows['section']):
            row.mode_limits.click()
            self.app.processEvents()
            for field in (row.limit_min, row.limit_max):
                self.assertFalse(field.isEnabled())
                self.assertEqual(field.buttonSymbols(),
                    QAbstractSpinBox.ButtonSymbols.UpDownArrows)
                self.assertEqual(field.width(), 106)
        self.assertTrue(w.rows['ring_id'].mode_limits.isEnabled())

    def test_all_17_rows_retain_geometry_and_have_matching_11px_labels(self):
        w=self.window()
        self.assertEqual(w.width(),1080)
        # Native Windows is 801 px; offscreen Qt uses shorter font metrics.
        self.assertIn(w.height(),(784,801))
        controls=[r for group in (w.rows,w.female_rows,w.shared_rows) for r in group.values()]
        self.assertEqual(len(controls),17)
        for row in controls:
            self.assertEqual(row.nominal.width(),106)
            self.assertEqual(row.tolerance.width(),106)
            self.assertEqual(row.limit_min.width(),106)
            self.assertEqual(row.limit_max.width(),106)
            self.assertEqual(row.nominal_stack.width(),106)
            self.assertEqual(row.mode_stack.width(),106)
            self.assertEqual((row.mode_sym.width(),row.mode_limits.width()),(46,46))
            self.assertEqual((row.nominal_stack.currentIndex(),row.mode_stack.currentIndex()),(0,0))
            self.assertEqual(row.mode_sym.text(),chr(177))
            self.assertEqual(row.mode_limits.text(),'Limits')
            self.assertEqual(row.mode_sym.focusPolicy(),Qt.FocusPolicy.NoFocus)
            self.assertEqual(row.mode_limits.focusPolicy(),Qt.FocusPolicy.NoFocus)
            self.assertFalse(row.limit_mode)
            self.assertEqual(row.limit_min.suffix(),row.nominal.suffix())
            self.assertEqual(row.limit_max.suffix(),row.nominal.suffix())
            self.assertEqual(row.limit_min.buttonSymbols(),QAbstractSpinBox.ButtonSymbols.UpDownArrows)
            self.assertEqual(row.limit_max.buttonSymbols(),QAbstractSpinBox.ButtonSymbols.UpDownArrows)
            stem=row.nominal.objectName().removeprefix('spin_').removesuffix('_nom')
            for which in ('min','max'):
                label=w.findChild(QLabel,'limit_tag_'+stem+'_'+which)
                self.assertEqual(label.text(),which.upper())
                self.assertEqual(label.font().pixelSize(),11)
                self.assertEqual(label.x(),59)
                self.assertTrue(label.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents))
            if row.widget.isVisible():
                self.assertEqual(row.nominal_stack.mapTo(w,QPoint()).x(),192)
                self.assertEqual(row.mode_sym.mapTo(w,QPoint()).x(),308)
                self.assertEqual(row.mode_stack.mapTo(w,QPoint()).x(),410)

    def test_symmetrical_equivalent_limits_match_both_methods_exactly(self):
        w=self.window()
        for method in ('simplified','detailed'):
            w.calculation_method.setCurrentIndex(0 if method=='detailed' else 1)
            original=w._last_result
            row=w.shared_rows['width']
            row.mode_limits.click()
            self.app.processEvents()
            self.assertIsNotNone(w._last_result)
            self.equal_envelopes(w._last_result,original)
            self.assertTrue(w.save_snapshot_button.isEnabled())
            self.assertTrue(w.trace_button.isEnabled())
            self.assertTrue(w.snapshot_button.isEnabled())
            self.assertIn('midpoint',w.statusBar().currentMessage())
            row.mode_sym.click()
            self.app.processEvents()
            self.equal_envelopes(w._last_result,original)
            self.assertFalse(w._has_active_limits())

    def test_asymmetric_width_limits_derive_midpoint_and_feed_both_methods(self):
        w=self.window()
        for method in ('simplified','detailed'):
            w.calculation_method.setCurrentIndex(0 if method=='detailed' else 1)
            original_inputs=w._collect()
            row=w.shared_rows['width']
            row.mode_limits.click()
            row.limit_min.setValue(.141)
            row.limit_max.setValue(.1485)
            self.app.processEvents()
            expected_dim=Dimension((.141+.1485)/2,(.1485-.141)/2)
            expected=calculate_installed(
                replace(original_inputs,gland_width=expected_dim),method=method)
            self.assertAlmostEqual(w._collect().gland_width.minimum,.141,places=12)
            self.assertAlmostEqual(w._collect().gland_width.maximum,.1485,places=12)
            self.assertAlmostEqual(w._collect().gland_width.nominal,.14475,places=12)
            self.equal_envelopes(w._last_result,expected.results)
            self.assertIsNotNone(w._last_evaluation)
            self.assertEqual(len(w._last_evaluation.cases),9)
            snapshot=dict(w._capture_inputs())
            self.assertIn('Groove width (in)',snapshot)
            self.assertIn(chr(177),snapshot['Groove width (in)'])
            row.mode_sym.click()
            self.app.processEvents()

    def test_limits_survive_toggling_and_invalid_order_blocks_outputs(self):
        w=self.window()
        row=w.shared_rows['width']
        row.mode_limits.click()
        row.limit_min.setValue(.14125)
        row.limit_max.setValue(.14975)
        self.app.processEvents()
        self.assertIsNotNone(w._last_result)
        row.mode_sym.click()
        self.assertAlmostEqual(row.nominal.value(),.1455,places=9)
        self.assertAlmostEqual(row.tolerance.value(),.00425,places=9)
        row.mode_limits.click()
        self.assertAlmostEqual(row.limit_min.value(),.14125,places=6)
        self.assertAlmostEqual(row.limit_max.value(),.14975,places=6)
        row.limit_min.setValue(.151)
        self.app.processEvents()
        self.assertIsNone(w._last_result)
        self.assertFalse(w.save_snapshot_button.isEnabled())
        self.assertFalse(w.snapshot_button.isEnabled())
        self.assertIn('minimum limit exceeds maximum',w.statusBar().currentMessage().lower())
        row.limit_max.setValue(.152)
        self.app.processEvents()
        self.assertIsNotNone(w._last_result)
        self.assertTrue(w.save_snapshot_button.isEnabled())

    def test_inches_and_degrees_have_real_clickable_steppers(self):
        w=self.window()
        for key,value,delta,suffix in (('width',.1415,.001,' in'),
                                       ('rect_angle',3.0,.1,' deg')):
            row=w.shared_rows[key]
            row.mode_limits.click()
            for editor in (row.limit_min,row.limit_max):
                editor.setValue(value)
                self.assertEqual(editor.suffix(),suffix)
                self.assertTrue(editor.text().endswith(suffix))
                option=QStyleOptionSpinBox()
                editor.initStyleOption(option)
                rect=editor.style().subControlRect(
                    QStyle.ComplexControl.CC_SpinBox,option,
                    QStyle.SubControl.SC_SpinBoxUp,editor)
                self.assertGreater(rect.width(),0)
                QTest.mouseClick(editor,Qt.MouseButton.LeftButton,pos=rect.center())
                self.app.processEvents()
                self.assertAlmostEqual(editor.value(),value+delta,places=6)
            row.mode_sym.click()

    def test_reset_restores_zero_and_symmetrical_for_every_row(self):
        w=self.window()
        w.shared_rows['width'].mode_limits.click()
        w.shared_rows['width'].limit_min.setValue(.138)
        w.rows['section'].mode_limits.click()
        w._reset_dimensions()
        for group in (w.rows,w.female_rows,w.shared_rows):
            for row in group.values():
                self.assertEqual((row.nominal.value(),row.tolerance.value(),
                                  row.limit_min.value(),row.limit_max.value()),
                                 (0.0,0.0,0.0,0.0))
                self.assertFalse(row.limit_mode)
                self.assertFalse(row.limits_initialized)
                self.assertTrue(row.mode_sym.isChecked())
        self.assertIsNone(w._last_result)

    def test_as568_catalogue_dimensions_are_locked_but_modes_can_be_selected(self):
        w=self.window()
        ring=w.rows['ring_id']
        section=w.rows['section']
        # Manual asymmetric data must not leak into the catalogue values.
        ring.mode_limits.click()
        ring.limit_min.setValue(.550)
        ring.limit_max.setValue(.578)
        selection=w.ring_size.findData('-113')
        self.assertGreater(selection,0)
        w.ring_size.setCurrentIndex(selection)
        self.app.processEvents()
        catalogue=next(x for x in w.as568_sizes if x.dash=='-113')
        self.assertTrue(ring.limit_mode)
        self.assertFalse(section.limit_mode)
        for key,nom,tol in (('ring_id',catalogue.id_in,catalogue.id_tol_in),
                            ('section',catalogue.cs_in,catalogue.cs_tol_in)):
            row=w.rows[key]
            self.assertTrue(row.mode_limits.isEnabled())
            self.assertTrue(row.mode_sym.isEnabled())
            self.assertFalse(row.nominal.isEnabled())
            self.assertFalse(row.tolerance.isEnabled())
            self.assertFalse(row.limit_min.isEnabled())
            self.assertFalse(row.limit_max.isEnabled())
            self.assertAlmostEqual(row.nominal.value(),nom,places=9)
            self.assertAlmostEqual(row.tolerance.value(),tol,places=9)
            self.assertAlmostEqual(row.limit_min.value(),nom-tol,places=9)
            self.assertAlmostEqual(row.limit_max.value(),nom+tol,places=9)
            self.assertTrue(row.limits_initialized)
        self.assertTrue(ring.mode_limits.isChecked())
        self.assertTrue(section.mode_sym.isChecked())
        self.assertTrue(w._last_result is not None)
        first_result=w._last_result
        section.mode_limits.click()
        self.app.processEvents()
        self.assertTrue(section.limit_mode)
        self.assertFalse(section.limit_min.isEnabled())
        self.assertFalse(section.limit_max.isEnabled())
        self.assertTrue(w._last_result is not None)
        self.equal_envelopes(w._last_result,first_result)
        ring.mode_sym.click()
        section.mode_sym.click()
        self.app.processEvents()
        self.equal_envelopes(w._last_result,first_result)
        self.assertFalse(ring.limit_mode)
        self.assertFalse(section.limit_mode)
        # Manual re-selection unlocks all fields and both independent toggles.
        w.ring_size.setCurrentIndex(0)
        self.app.processEvents()
        for row in (ring,section):
            self.assertTrue(row.nominal.isEnabled())
            self.assertTrue(row.tolerance.isEnabled())
            self.assertTrue(row.limit_min.isEnabled())
            self.assertTrue(row.limit_max.isEnabled())
            self.assertTrue(row.mode_sym.isEnabled())
            self.assertTrue(row.mode_limits.isEnabled())

    def test_as568_catalogue_changes_refresh_both_limit_fields_in_selected_mode(self):
        w=self.window()
        first=w.ring_size.findData('-113')
        second=w.ring_size.findData('-114')
        self.assertGreater(first,0)
        self.assertGreater(second,0)
        w.ring_size.setCurrentIndex(first)
        self.app.processEvents()
        ring=w.rows['ring_id']
        section=w.rows['section']
        ring.mode_limits.click()
        section.mode_limits.click()
        self.app.processEvents()
        self.assertTrue(ring.limit_mode)
        self.assertTrue(section.limit_mode)
        w.ring_size.setCurrentIndex(second)
        self.app.processEvents()
        catalogue=next(x for x in w.as568_sizes if x.dash=='-114')
        for row,nom,tol in ((ring,catalogue.id_in,catalogue.id_tol_in),
                            (section,catalogue.cs_in,catalogue.cs_tol_in)):
            self.assertTrue(row.limit_mode)
            self.assertTrue(row.mode_limits.isChecked())
            self.assertEqual(row.nominal_stack.currentIndex(),1)
            self.assertEqual(row.mode_stack.currentIndex(),1)
            self.assertAlmostEqual(row.limit_min.value(),nom-tol,places=9)
            self.assertAlmostEqual(row.limit_max.value(),nom+tol,places=9)
            self.assertAlmostEqual(row.dimension().minimum,nom-tol,places=9)
            self.assertAlmostEqual(row.dimension().maximum,nom+tol,places=9)
            self.assertFalse(row.limit_min.isEnabled())
            self.assertFalse(row.limit_max.isEnabled())
            self.assertTrue(row.mode_sym.isEnabled())
            self.assertTrue(row.mode_limits.isEnabled())
        # Toggle back without changing the actual catalogue dimensions.
        section.mode_sym.click()
        self.app.processEvents()
        self.assertFalse(section.limit_mode)
        self.assertTrue(ring.limit_mode)
        self.assertAlmostEqual(section.dimension().minimum,
                               catalogue.cs_in-catalogue.cs_tol_in,places=9)
        self.assertAlmostEqual(ring.dimension().maximum,
                               catalogue.id_in+catalogue.id_tol_in,places=9)

    def test_switching_components_carries_first_use_exact_limits(self):
        w=self.window()
        # Female rod is already populated in seed_sample, clear to model a
        # first-time configuration where the counterpart has no existing input.
        target=w.female_rows['rod_od']
        target.nominal.setValue(0)
        target.tolerance.setValue(0)
        source=w.rows['direct_rod_od']
        source.mode_limits.click()
        source.limit_min.setValue(.7465)
        source.limit_max.setValue(.7495)
        w.configuration.setCurrentIndex(1)
        self.app.processEvents()
        self.assertTrue(target.limit_mode)
        self.assertEqual(target.nominal_stack.currentIndex(),1)
        self.assertAlmostEqual(target.limit_min.value(),.7465,places=7)
        self.assertAlmostEqual(target.limit_max.value(),.7495,places=7)

    def test_hidden_unused_limits_do_not_block_active_calculation(self):
        w=self.window()
        row=w.female_rows['gland_id']
        row.mode_limits.click()
        row.limit_min.setValue(0.8)
        row.limit_max.setValue(0.7)
        self.app.processEvents()
        self.assertIsNotNone(w._last_result)
        self.assertTrue(w.save_snapshot_button.isEnabled())
        self.assertFalse(w._has_active_limits())
        w.configuration.setCurrentIndex(1)
        self.app.processEvents()
        self.assertIsNone(w._last_result)
        self.assertFalse(w.save_snapshot_button.isEnabled())

if __name__=='__main__':
    unittest.main()
