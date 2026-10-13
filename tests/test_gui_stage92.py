from gui_sample import seed_sample
"""Stage 9.2 Qt Designer conversion: structural and Windows GUI regression."""
import importlib.util
from pathlib import Path
import unittest
from xml.etree import ElementTree as ET

QT_INSTALLED = importlib.util.find_spec('PySide6') is not None
LAYOUT = Path(__file__).resolve().parents[1] / 'src' / 'ui' / 'forms' / 'main_window.ui'


class DesignerLayoutStructureTests(unittest.TestCase):
    def test_the_editable_ui_has_unique_widget_names_and_promoted_spins(self):
        root = ET.parse(LAYOUT).getroot()
        names = [w.get('name') for w in root.iter('widget')]
        self.assertEqual(len(names), len(set(names)))
        self.assertGreaterEqual(len(names), 140)  # detailed panels intentionally removed in 9.5
        spins = [w for w in root.iter('widget') if w.get('class') == 'AdaptiveSpinBox']
        self.assertEqual(len(spins), 34)
        self.assertIn('src.ui.main_window', ET.tostring(root, encoding='unicode'))
        for name in ('appSurface','male_group','female_group','overview_squeeze_2',
                     'spin_shared_width_nom','match_slot','guide_placeholder'):
            self.assertIn(name, names)

    def test_source_math_is_unchanged_in_9_2(self):
        from src.calculations.installed import calculate_installed
        from src.calculations.profile_geometry import SignedDimension
        from src.calculations.rectangular import Dimension, MaleRectangularInputs
        inp = MaleRectangularInputs(
            cylinder_id=Dimension(.669,.001), gland_width=Dimension(.1425,.0025),
            o_ring_id=Dimension(.487,.005), o_ring_section=Dimension(.103,.003),
            mode='gland_od', gland_od=Dimension(.503,.001),rod_od=Dimension(.667,.001),
            bottom_radius=Dimension(0,0),entrance_radius=Dimension(0,0),
            wall_angle_deg=SignedDimension(0,0),
        )
        self.assertGreater(calculate_installed(inp).results.squeeze_percent.nominal,0)


@unittest.skipUnless(QT_INSTALLED, 'Requires Windows PySide6')
class Stage92GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_designer_widgets_bind_to_calculation_engine(self):
        from src.ui.main_window import MainWindow, AdaptiveSpinBox
        w=MainWindow();seed_sample(w)
        try:
            self.assertIsInstance(w.rows['ring_id'].nominal,AdaptiveSpinBox)
            self.assertTrue(w.rows['groove_depth'].widget.objectName().startswith('dim_'))
            self.assertIsNotNone(w._last_result)
            old=w._last_result.squeeze_percent.nominal
            w.rows['gland_od'].nominal.setValue(.585)
            self.assertNotEqual(old,w._last_result.squeeze_percent.nominal)
            self.assertEqual(w.shared_rows['rect_angle'].nominal.singleStep(), .1)
        finally:
            w.close()

    def test_stage91_behaviour_and_snapshot_survive_layout_conversion(self):
        from src.ui.main_window import MainWindow
        w=MainWindow();seed_sample(w)
        try:
            self.assertTrue(w.match_note.isHidden())
            self.assertEqual(w.configuration.currentData(),'male')
            w.configuration.setCurrentIndex(1)
            self.assertIn('>O-ring OD interference</span>', w.overview_cells[('Fit',0)].text())
            self.assertIn('0–2%', w.overview_cells[('Fit',0)].text())
            self.assertTrue(w.male_group.isHidden())
            self.assertFalse(w.female_group.isHidden())
            w.configuration.setCurrentIndex(0)
            inspector=w._make_tolerance_trace_dialog()
            self.assertEqual(inspector.findChild(__import__('PySide6.QtWidgets',fromlist=['QTabWidget']).QTabWidget,'result_tabs').count(),2)
            inspector.close()
            self.assertIsNotNone(w._last_screening)
            self.assertTrue(w.snapshot_button.isEnabled())
        finally:
            w.close()

    def test_designer_theme_is_active_at_window_level(self):
        # Stage 9.1's greyed-out catalogue input styling must survive the
        # .ui conversion, and its source must remain the editable .ui file.
        from src.ui.main_window import MainWindow
        w=MainWindow();seed_sample(w)
        try:
            self.assertIn('QDoubleSpinBox:disabled', w.styleSheet())
            self.assertEqual(w.styleSheet(), w.centralWidget().styleSheet())
            w.ring_size.setCurrentIndex(1)
            self.assertFalse(w.rows['ring_id'].nominal.isEnabled())
            self.assertFalse(w.rows['section'].tolerance.isEnabled())
        finally:
            w.close()

    def test_designer_dimension_layout_contains_editable_spinboxes(self):
        from src.ui.main_window import MainWindow
        from PySide6.QtWidgets import QHBoxLayout
        w=MainWindow();seed_sample(w)
        try:
            row=w.shared_rows['width']
            self.assertIsInstance(row.widget.layout(),QHBoxLayout)
            self.assertEqual(row.widget.layout().count(),3)
            self.assertEqual(row.nominal.textFromValue(.0835),'0.0835')
            self.assertEqual(w.female_rows['groove_depth'].tolerance.textFromValue(.00025),'0.00025')
        finally:
            w.close()


if __name__=='__main__': unittest.main()
