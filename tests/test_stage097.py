from gui_sample import seed_sample
"""v0.9.7 interface changes and audit witness validation."""
import importlib.util
import unittest
from pathlib import Path
from src.app_info import APP_VERSION
from xml.etree import ElementTree as ET
from src.ui.inspection_data import explain_case
from test_stage096 import samples
from src.calculations.installed import calculate_installed

ROOT=Path(__file__).resolve().parents[1]
QT=importlib.util.find_spec('PySide6') is not None

class Stage097SourceTests(unittest.TestCase):
    def test_layout_text_and_reference_asset(self):
        r=ET.parse(ROOT/'src/ui/forms/main_window.ui').getroot()
        def text(name):return r.find(f'.//widget[@name="{name}"]/property[@name="text"]/string').text
        self.assertEqual(text('version_label'),'v' + APP_VERSION)
        self.assertEqual(text('shared_note'),
          'Width is measured between theoretical sharp intersections (opening radii excluded where present).')
        self.assertTrue((ROOT/'src/resources/guides/piston_dovetail_od.png').stat().st_size>1000)
        s=(ROOT/'src/ui/main_window.py').read_text()
        self.assertIn("self.entry_mode.addItem('OD', 'gland_od')",s)
        self.assertIn("self.female_entry_mode.addItem('Depth', 'cylinder_and_depth')",s)
        self.assertIn('self._refresh_dimension_guide()',s)
        self.assertIn('self.overview_grid.setColumnMinimumWidth',s)
    def test_assumptions_references_about(self):
        r=ET.parse(ROOT/'src/ui/forms/settings_dialog.ui').getroot()
        def txt(name):return r.find(f'.//widget[@name="{name}"]/property[@name="text"]/string').text
        self.assertNotIn('current dimensional',txt('references_text'))
        self.assertNotIn('traceability review is planned',txt('references_text'))
        self.assertIn('The reference publications are not distributed',txt('references_note'))
        self.assertIn('dynamic (reciprocating) radial',txt('about_text'))
        self.assertNotIn('Pre-release development build',txt('about_text'))
        self.assertEqual(txt('assumptions_text').count('•'),8)
        self.assertIn('check_on_launch', [w.get('name') for w in r.iter('widget')])
        self.assertIn('background: white',ET.tostring(r,encoding='unicode'))
    def test_all_72_reconciled_formulas_and_formatted_values(self):
        tested=0
        for inp,female,depth,dovetail in samples():
            evaluation=calculate_installed(inp)
            for key in ('Squeeze','OD interference' if female else 'ID stretch','Gland fill'):
                for cond in ('Minimum','Nominal','Maximum'):
                    res,dims,steps=explain_case(evaluation,key,cond,inp,3)
                    self.assertAlmostEqual(res,steps[-1].result,places=8)
                    self.assertTrue(all(s.symbolic and s.numeric and s.note for s in steps))
                    self.assertTrue(all(s.numeric_fraction is not None for s in steps
                                        if s.symbol_fraction is not None))
                    self.assertEqual(steps[-1].unit,'%')
                    if key=='Gland fill':
                        names=[d[0] for d in dims]
                        self.assertLess(names.index('Groove width'),names.index('O-ring free ID'))
                        self.assertIn('Groove opening radius',names)
                        self.assertIn('Groove dovetail angle' if dovetail else 'Groove wall angle',names)
                        self.assertIn('Groove profile area',[s.title for s in steps])
                    if key=='Squeeze' and not female:
                        self.assertIn('Installed-section reduction',[s.title for s in steps])
                    tested+=1
        self.assertEqual(tested,72)
    def test_precision_does_not_change_witness_results(self):
        inp,*_=next(iter(samples()))
        evaln=calculate_installed(inp)
        for metric in ('Squeeze','ID stretch','Gland fill'):
            for c in ('Minimum','Nominal','Maximum'):
                x=explain_case(evaln,metric,c,inp,0)
                y=explain_case(evaln,metric,c,inp,6)
                self.assertEqual(x[0],y[0])
                self.assertEqual(tuple(s.result for s in x[2]),tuple(s.result for s in y[2]))

@unittest.skipUnless(QT,'Requires Windows PySide6')
class Stage097GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])
    def test_reference_guide_switching(self):
        from src.ui.main_window import MainWindow
        from PySide6.QtWidgets import QLabel
        w=MainWindow();seed_sample(w);w.show()
        try:
            self.app.processEvents()
            pic=w.findChild(QLabel,'guide_picture')
            self.assertIsNotNone(pic)
            self.assertEqual(len(w._reference_pixmaps),8)
            for configuration in (0,1):
                w.configuration.setCurrentIndex(configuration)
                for groove in (0,1):
                    w.groove_type.setCurrentIndex(groove)
                    selector=w.female_entry_mode if configuration else w.entry_mode
                    for mode in (0,1):
                        selector.setCurrentIndex(mode)
                        self.app.processEvents()
                        self.assertTrue(pic.isVisible(), (configuration,groove,mode))
                        self.assertIsNotNone(pic.pixmap())
                        self.assertFalse(pic.pixmap().isNull())
                        self.assertIn(selector.currentText(),pic.toolTip())
        finally:w.close()
