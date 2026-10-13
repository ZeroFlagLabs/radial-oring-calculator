from gui_sample import seed_sample
"""Stage 9.4.1: layout-stability, display-only rounding and Designer regression."""
import importlib.util
from pathlib import Path
from src.app_info import APP_VERSION
import unittest
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
QT = importlib.util.find_spec('PySide6') is not None


class Stage941SourceTests(unittest.TestCase):
    def test_designer_header_and_full_width_results(self):
        root = ET.parse(ROOT/'src/ui/forms/main_window.ui').getroot()
        self.assertIsNotNone(root.find('.//layout[@name="oringHeaderLayout"]'))
        self.assertIsNotNone(root.find('.//layout[@name="oringHeaderLayout"]/item/widget[@name="match_slot"]'))
        self.assertIsNone(root.find('.//layout[@name="ringLayout"]/item/widget[@name="match_slot"]'))
        self.assertIsNone(root.find('.//widget[@name="method_note"]'))
        table=root.find('.//widget[@name="overview_table"]')
        self.assertEqual(table.find('./property[@name="maximumSize"]/size/width').text,'16777215')
        self.assertEqual(root.find('.//widget[@name="overview_box"]/property[@name="title"]/string').text,
                         'Dimensional screening results')
        self.assertEqual(root.find('.//widget[@name="version_label"]/property[@name="text"]/string').text,
                         'v' + APP_VERSION)
        names=[node.get('name') for node in root.iter('widget')]
        self.assertEqual(len(names),len(set(names)))

    def test_preserve_engine_unchanged(self):
        from src.calculations.installed import calculate_installed
        from src.calculations.rectangular import Dimension, MaleRectangularInputs
        from src.calculations.profile_geometry import SignedDimension
        inp=MaleRectangularInputs(
            cylinder_id=Dimension(.669,.001),gland_width=Dimension(.1425,.0025),
            o_ring_id=Dimension(.487,.005),o_ring_section=Dimension(.103,.003),
            mode='gland_od',gland_od=Dimension(.503,.001),rod_od=Dimension(.667,.001),
            bottom_radius=Dimension(0,0),entrance_radius=Dimension(0,0),
            wall_angle_deg=SignedDimension(0,0))
        self.assertGreater(calculate_installed(inp).results.squeeze_percent.nominal,0)


@unittest.skipUnless(QT,'Requires Windows PySide6')
class Stage941GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def test_as568_changes_dont_reflow_application_or_hardware(self):
        from src.ui.main_window import MainWindow
        w=MainWindow();seed_sample(w)
        w.show()
        try:
            self.app.processEvents()
            setup=w.findChild(type(w.ring_group),'setup_group')
            shared=w.findChild(type(w.ring_group),'shared_group')
            baseline=(setup.height(),w.gland_entry.height(),shared.y(),w.ring_group.y())
            for idx in (1,0,9,0):
                w.ring_size.setCurrentIndex(idx)
                self.app.processEvents()
                self.assertEqual((setup.height(),w.gland_entry.height(),shared.y(),w.ring_group.y()),baseline)
        finally:
            w.close()

    def test_header_matching_and_result_format(self):
        from src.ui.main_window import MainWindow
        from PySide6.QtWidgets import QGroupBox
        w=MainWindow();seed_sample(w)
        try:
            self.assertEqual(w.match_slot.parentWidget(),w.findChild(QGroupBox,'setup_group'))
            self.assertFalse(w.overview_note.isVisible())
            self.assertNotIn('method_note',[node.objectName() for node in w.findChildren(QGroupBox)])
            for key in ('Squeeze','Fit'):
                for col in (1,2,3):
                    cell=w.overview_cells[(key,col)]
                    self.assertIn('font-size:10px',cell.text())
                    self.assertIn(' in',cell.text())
            from PySide6.QtWidgets import QTableWidget
            inspector=w._make_tolerance_trace_dialog()
            table=inspector.findChild(QTableWidget,'geometry_table')
            self.assertRegex(table.item(table.rowCount()-1,2).text(),r'^-?\d+\.\d{3}$')
            self.assertRegex(table.item(3,2).text(),r'^-?\d+\.\d{3}$')
            inspector.close()
            for row in (1,2,3):
                self.assertEqual(w.overview_grid.rowMinimumHeight(row),39)
        finally:
            w.close()

    def test_designer_stack_initialises_and_tracks_selected_gland(self):
        """Designer may save a preview on the female page; runtime must agree with setup."""
        from src.ui.main_window import MainWindow
        w=MainWindow();seed_sample(w)
        try:
            self.assertEqual(w.configuration.currentData(), 'male')
            self.assertIs(w.entry_mode_stack.currentWidget(), w.entry_mode)
            # Simulate Qt Designer having previewed the other stack page.
            w.entry_mode_stack.setCurrentWidget(w.female_entry_mode)
            self.assertIs(w.entry_mode_stack.currentWidget(), w.female_entry_mode)
            w._change_configuration()
            self.assertIs(w.entry_mode_stack.currentWidget(), w.entry_mode)
            w.configuration.setCurrentIndex(1)
            self.assertIs(w.entry_mode_stack.currentWidget(), w.female_entry_mode)
            w.ring_size.setCurrentIndex(1)
            self.assertIs(w.entry_mode_stack.currentWidget(), w.female_entry_mode)
            w.configuration.setCurrentIndex(0)
            self.assertIs(w.entry_mode_stack.currentWidget(), w.entry_mode)
        finally:
            w.close()

    def test_precision_choices_for_tolerance_inspector(self):
        from src.ui.main_window import MainWindow
        from PySide6.QtWidgets import QComboBox
        w=MainWindow();seed_sample(w)
        try:
            dialog = w._make_tolerance_trace_dialog()
            self.assertIsNotNone(dialog)
            precision = dialog.findChild(QComboBox,'trace_precision')
            self.assertIsNotNone(precision)
            self.assertEqual(precision.count(),7)
            self.assertEqual(precision.currentText(),'3 DP')
            precision.setCurrentIndex(6)
            self.assertEqual(precision.currentText(),'6 DP')
        finally:
            w.close()

if __name__=='__main__': unittest.main()
