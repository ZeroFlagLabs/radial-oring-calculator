from gui_sample import seed_sample
"""Stage 9.4 layout and correlated screening figure regressions."""
from pathlib import Path
from src.app_info import APP_VERSION
from xml.etree import ElementTree as ET
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
LAYOUT = ROOT / 'src/ui/forms/main_window.ui'
QT_INSTALLED = importlib.util.find_spec('PySide6') is not None


class Stage94LayoutTests(unittest.TestCase):
    def test_editable_settings_button_compact_results_without_copy_button(self):
        root = ET.parse(LAYOUT).getroot()
        names = [x.get('name') for x in root.iter('widget')]
        for name in ('settings_button', 'overview_table',
                     'guide_button', 'match_slot', 'match_note'):
            self.assertIn(name, names)
        self.assertIn('overview_grid',[x.get('name') for x in root.iter('layout')])
        self.assertNotIn('copy_button', names)
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(
            root.find('.//widget[@name="version_label"]/property[@name="text"]/string').text,
            'v' + APP_VERSION)
        self.assertTrue((ROOT / 'src/ui/forms/settings_dialog.ui').is_file())
        self.assertTrue((ROOT / 'src/resources/icons/settings-gear.png').is_file())

    def test_calculations_still_independent_of_gui(self):
        from src.calculations.installed import calculate_installed
        from src.calculations.rectangular import Dimension, MaleRectangularInputs
        from src.calculations.profile_geometry import SignedDimension
        inp = MaleRectangularInputs(
            cylinder_id=Dimension(.669,.001),gland_width=Dimension(.1425,.0025),
            o_ring_id=Dimension(.487,.005),o_ring_section=Dimension(.103,.003),
            mode='gland_od',gland_od=Dimension(.503,.001),rod_od=Dimension(.667,.001),
            bottom_radius=Dimension(0,0),entrance_radius=Dimension(0,0),
            wall_angle_deg=SignedDimension(0,0),
        )
        self.assertGreater(calculate_installed(inp).results.squeeze_percent.nominal,0)


@unittest.skipUnless(QT_INSTALLED, 'Requires PySide6')
class Stage94GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_settings_form_and_button(self):
        from src.ui.main_window import MainWindow
        from src.ui.settings_dialog import SettingsDialog
        from PySide6.QtWidgets import QTabWidget
        w=MainWindow();seed_sample(w)
        try:
            self.assertTrue(w.settings_button.isEnabled())
            self.assertFalse(hasattr(w,'copy_button'))
            settings=SettingsDialog(w)
            self.assertEqual(settings.dialog.findChild(QTabWidget,'settings_tabs').count(),4)
        finally:
            w.close()

    def test_correlated_physical_dimensions_match_witnesses(self):
        from src.ui.main_window import MainWindow
        w=MainWindow();seed_sample(w)
        try:
            for female in (False,True):
                w.configuration.setCurrentIndex(1 if female else 0)
                if w._last_evaluation is None:
                    continue
                for condition,col in (('Minimum',1),('Nominal',2),('Maximum',3)):
                    witness=w._last_evaluation.cases[('Squeeze', condition)]
                    self.assertAlmostEqual(w._correlated_physical_value('Squeeze',condition),
                                           witness.squeeze_in)
                    for name in ('Squeeze','Fit'):
                        self.assertIn(' in',w.overview_cells[(name,col)].text())
                        self.assertIn('%',w.overview_cells[(name,col)].text())
                self.assertNotIn(' in',w.overview_cells[('Gland fill',2)].text())
        finally:
            w.close()

    def test_match_slot_is_not_in_dimensions_layout(self):
        from src.ui.main_window import MainWindow
        w=MainWindow();seed_sample(w)
        try:
            self.assertEqual(w.match_slot.parentWidget(),w.findChild(type(w.ring_group),'setup_group'))
            self.assertEqual(w.ring_group.layout().indexOf(w.match_slot),-1)
            before=w.match_slot.height()
            w.rows['ring_id'].nominal.setValue(.487)
            w.rows['ring_id'].tolerance.setValue(.005)
            w.rows['section'].nominal.setValue(.103)
            w.rows['section'].tolerance.setValue(.003)
            self.assertFalse(w.match_note.isHidden())
            self.assertEqual(before,w.match_slot.height())
        finally:
            w.close()


if __name__=='__main__':
    unittest.main()
