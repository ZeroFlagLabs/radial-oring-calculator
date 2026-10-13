from gui_sample import seed_sample
"""v0.9.6 engineering explanation and Qt layout contracts."""
import importlib.util
import unittest
from pathlib import Path
from src.app_info import APP_VERSION
from xml.etree import ElementTree as ET
from src.calculations.rectangular import (Dimension as D, MaleRectangularInputs,
                                          FemaleRectangularInputs)
from src.calculations.dovetail import MaleDovetailInputs, FemaleDovetailInputs
from src.calculations.profile_geometry import SignedDimension
from src.calculations.installed import calculate_installed
from src.ui.inspection_data import explain_case, geometry_records

ROOT=Path(__file__).resolve().parents[1]
QT=importlib.util.find_spec('PySide6') is not None


def samples():
    common=dict(gland_width=D(.1425,.001),o_ring_id=D(.487,.002),
                o_ring_section=D(.103,.0005), bottom_radius=D(.004),
                entrance_radius=D(.002))
    for female in (False,True):
        for depth_entry in (False,True):
            for dovetail in (False,True):
                angle={'angle_deg':D(14) if dovetail else SignedDimension(0)} if dovetail else {'wall_angle_deg':SignedDimension(0)}
                cls=(FemaleDovetailInputs if dovetail else FemaleRectangularInputs) if female else (MaleDovetailInputs if dovetail else MaleRectangularInputs)
                if female:
                    hw=dict(rod_od=D(.665,.0002),cylinder_id=D(.669,.0002),
                            mode='cylinder_and_depth' if depth_entry else 'gland_id',
                            groove_depth=D(.090,.001) if depth_entry else None,
                            gland_id=None if depth_entry else D(.849,.002))
                else:
                    hw=dict(rod_od=D(.667,.0002),cylinder_id=D(.669,.0002),
                            mode='rod_and_depth' if depth_entry else 'gland_od',
                            groove_depth=D(.082,.001) if depth_entry else None,
                            gland_od=None if depth_entry else D(.503,.002))
                inp=cls(**common,**hw,**angle)
                yield inp, female, depth_entry, dovetail


class Stage096SourceTests(unittest.TestCase):
    def test_all_engine_case_explanations_and_units(self):
        checked=0
        for inp,female,depth,dovetail in samples():
            evaluation=calculate_installed(inp)
            for measure in ('Squeeze','OD interference' if female else 'ID stretch','Gland fill'):
                for condition in ('Minimum','Nominal','Maximum'):
                    result, dims, steps=explain_case(evaluation,measure,condition)
                    self.assertTrue(steps)
                    self.assertAlmostEqual(result,steps[-1].result,places=8)
                    self.assertEqual(steps[-1].unit,'%')
                    self.assertTrue(all(x[2] in ('in','deg') for x in dims))
                    self.assertNotIn('Parker',str(steps))
                    checked += 1
            rows=geometry_records(inp,evaluation.results,female)
            self.assertEqual(len(rows),6 if inp.entrance_radius.maximum > 0 else 5)
            self.assertIn('Groove ID' if female else 'Groove OD',rows[0][0]) if depth else self.assertEqual(rows[0][0],'Groove depth (in)')
            self.assertIn('clearance',rows[1][0])
            self.assertIn('sealing area',rows[-1][0])
            for _,bounds,unit in rows:
                self.assertLessEqual(bounds.minimum,bounds.maximum)
                self.assertGreaterEqual(bounds.nominal,bounds.minimum-1e-9)
                self.assertLessEqual(bounds.nominal,bounds.maximum+1e-9)
        self.assertEqual(checked,72)

    def test_designer_texts_and_version(self):
        ui=ET.parse(ROOT/'src/ui/forms/main_window.ui').getroot()
        self.assertEqual(ui.find('.//widget[@name="version_label"]/property[@name="text"]/string').text,'v' + APP_VERSION)
        self.assertEqual(ui.find('.//widget[@name="selector_entry_mode_stack_label"]/property[@name="text"]/string').text,'Groove dimension')
        self.assertIn('opening radii excluded',ui.find('.//widget[@name="shared_note"]/property[@name="text"]/string').text)
        settings=ET.parse(ROOT/'src/ui/forms/settings_dialog.ui').getroot()
        about=settings.find('.//widget[@name="about_text"]/property[@name="text"]/string').text
        self.assertIn('MIT',about)
        ass=settings.find('.//widget[@name="assumptions_text"]/property[@name="text"]/string').text
        self.assertIn('complete seal design approval',ass)
        ref=settings.find('.//widget[@name="references_text"]/property[@name="text"]/string').text
        self.assertIn("James Walker: 'O' Ring Guide, Issue 7",ref)
        inspect=ET.parse(ROOT/'src/ui/forms/inspect_results.ui').getroot()
        self.assertEqual(inspect.find('.//widget[@name="trace_text"]').get('class'),'QTextBrowser')
        self.assertEqual(inspect.find('.//widget[@name="trace_disclaimer"]/property[@name="text"]/string').text or '','')


@unittest.skipUnless(QT, 'Requires Windows PySide6')
class Stage096GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def test_inspector_rendered_fractions_and_nominal_default(self):
        from PySide6.QtWidgets import QComboBox,QTextBrowser,QTableWidget
        from src.ui.main_window import MainWindow
        window=MainWindow();seed_sample(window)
        try:
            dlg=window._make_tolerance_trace_dialog()
            condition=dlg.findChild(QComboBox,'trace_condition')
            self.assertEqual([condition.itemText(i) for i in range(3)],['Minimum','Nominal','Maximum'])
            self.assertEqual(condition.currentText(),'Nominal')
            browser=dlg.findChild(QTextBrowser,'trace_text')
            self.assertIsNotNone(browser)
            self.assertIn('<table',browser.toHtml().lower())
            self.assertIn('calculation breakdown', browser.toPlainText().casefold())
            table=dlg.findChild(QTableWidget,'geometry_table')
            self.assertIn(table.rowCount(),(5,6))
            measure=dlg.findChild(QComboBox,'trace_measure')
            for i in range(3):
                measure.setCurrentIndex(i)
                self.assertGreater(len(browser.toPlainText()),120)
            condition.setCurrentIndex(2)
            self.assertIn('Maximum',browser.toPlainText())
            dlg.close()
        finally:window.close()

    def test_screening_spacing_and_groove_method(self):
        from src.ui.main_window import MainWindow
        from PySide6.QtWidgets import QGroupBox,QComboBox
        window=MainWindow();seed_sample(window);window.show()
        try:
            self.app.processEvents()
            self.assertEqual(window.entry_mode.itemText(0),'OD')
            self.assertEqual(window.entry_mode.itemText(1),'Depth')
            self.assertEqual(window.female_entry_mode.itemText(0),'ID')
            overview=window.findChild(QGroupBox,'overview_box')
            guide=window.findChild(QGroupBox,'drawing_group')
            from PySide6.QtCore import QPoint
            # Compare coordinates in the same parent space, not guide-local.
            guide_bottom = guide.mapTo(window.centralWidget(),QPoint(0,guide.height())).y()
            overview_top = overview.mapTo(window.centralWidget(),QPoint(0,0)).y()
            gap = overview_top - guide_bottom
            setup=window.findChild(QGroupBox,'setup_group')
            setup_bottom = setup.mapTo(window.centralWidget(),QPoint(0,setup.height())).y()
            guide_top = guide.mapTo(window.centralWidget(),QPoint(0,0)).y()
            reference_gap = guide_top - setup_bottom
            self.assertGreaterEqual(gap,0, f'Overlapping screening/guide frames: {gap}px')
            self.assertLessEqual(abs(gap-reference_gap),4,
                f'Frame gaps differ: setup/guide={reference_gap}px, '
                f'guide/results={gap}px, window={window.height()}px')
            self.assertLessEqual(
                gap,14,
                f'Screening/guide gap {gap}px (expected <=14px); '
                f'window height={window.height()}px, '
                f'guide bottom={guide_bottom}px, screening top={overview_top}px')
            self.assertEqual(window.minimumSize(),window.maximumSize())
        finally:window.close()

if __name__=='__main__':unittest.main()
