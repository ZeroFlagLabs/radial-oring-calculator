from gui_sample import seed_sample
"""Stage 9.5.2 source checks and Windows UI regression tests."""
import importlib.util
import pathlib
from xml.etree import ElementTree as ET
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
QT=importlib.util.find_spec('PySide6') is not None
APP='Static & Dynamic Radial O-Ring Calculator'

def widget(root,name):
    x=root.find(f'.//widget[@name="{name}"]')
    if x is None: raise AssertionError(f'Missing {name}')
    return x

def txt(x,key='text'):
    n=x.find(f'./property[@name="{key}"]/string')
    return n.text if n is not None else None

class Stage952SourceTests(unittest.TestCase):
    def test_sentence_case_and_dimension_labels(self):
        r=ET.parse(ROOT/'src/ui/forms/main_window.ui').getroot()
        self.assertEqual(txt(widget(r,'window_title')),APP)
        for control in ('application','configuration','groove_type','entry_mode_stack','ring_size'):
            self.assertEqual(int(widget(r,control).find('./property[@name="minimumSize"]/size/width').text),184)
        self.assertEqual(int(r.find('.//layout[@name="mainLayout"]/property[@name="spacing"]/number').text),4)
        self.assertEqual(int(r.find('.//layout[@name="mainLayout"]/property[@name="bottomMargin"]/number').text),4)
        for n in ('male_group','female_group'):
            self.assertEqual(txt(widget(r,n),'title'),'Component dimensions')
        for n,label in {'label_male_ring_id':'ID','label_male_gland_od':'OD',
                        'label_female_gland_id':'ID','label_shared_width':'Width',
                        'label_male_groove_depth':'Depth','label_female_groove_depth':'Depth'}.items():
            self.assertEqual(txt(widget(r,n)),label)
        self.assertIn('theoretical sharp intersections',txt(widget(r,'shared_note')))
        self.assertNotIn('where applicable',txt(widget(r,'shared_note')))
    def test_inspector_toolbar_and_clarity(self):
        r=ET.parse(ROOT/'src/ui/forms/inspect_results.ui').getroot()
        self.assertEqual(txt(widget(r,'InspectResults'),'windowTitle'),f'Inspect Results | {APP}')
        self.assertEqual(int(r.find('.//widget[@name="InspectResults"]/property[@name="geometry"]/rect/width').text),700)
        layout=r.find('.//layout[@name="traceSelectorsLayout"]')
        self.assertEqual(len(layout.findall('item')),3)
        self.assertEqual(len(layout.findall('./item/layout[@class="QVBoxLayout"]')),3)
        for name in ('trace_disclaimer','geometry_note'):
            t=(txt(widget(r,name)) or '').lower()
            self.assertNotIn('endpoint',t)
            self.assertNotIn('parker',t)
            self.assertNotIn('approximate',t)
        src=(ROOT/'src/ui/inspect_results.py').read_text(encoding='utf-8')
        # The inspector now generates terminology from read-only engine
        # witness values, without the old replace-at-display mapping.
        detail=(ROOT/'src/ui/inspection_data.py').read_text(encoding='utf-8')
        for term in ('Piston OD','Groove OD','Groove opening radius','Groove base radius'):
            self.assertIn(term,detail)
        self.assertIn('setColumnWidth(col,135)',src)
    def test_names_status_and_reference_copy(self):
        r=ET.parse(ROOT/'src/ui/forms/settings_dialog.ui').getroot()
        self.assertIn(APP,txt(widget(r,'about_text')))
        self.assertIn('ORD 5700A/US',txt(widget(r,'references_text')))
        self.assertNotIn('approximation',txt(widget(r,'assumptions_text')).lower())
        self.assertNotIn('approximate',txt(widget(r,'assumptions_text')).lower())
        self.assertNotIn('Apple Rubber',txt(widget(r,'references_text')))
        self.assertNotIn('endpoints',txt(widget(r,'assumptions_text')))
        main=(ROOT/'src/ui/main_window.py').read_text(encoding='utf-8')
        self.assertIn("self._align_dimension_frames()",main)
        # Verify both valid and invalid cases use the shared two-line label.
        # The placeholder may be a non-breaking space or short explanatory text;
        # inspecting its exact Unicode spelling makes this test unnecessarily fragile.
        self.assertIn("label.setText(self._screening_label_markup(title,",main)
        self.assertIn("title_label.setText(self._screening_label_markup(title, check.criterion))",main)
        self.assertIn('suggested, \'PNG images (*.png)\'',main)
        self.assertIn('guide.setFixedHeight(panel.maximumHeight())',main)
        self.assertIn('status.setContentsMargins(0, 3, 0, 0)',main)
        self.assertIn('Static & Dynamic Radial O-Ring Calculator',(ROOT/'src/main.py').read_text(encoding='utf-8'))
        self.assertEqual(txt(widget(ET.parse(ROOT/'src/ui/forms/main_window.ui').getroot(),'setup_group'),'title'), 'Application setup')

@unittest.skipUnless(QT,'Requires PySide6; run with installed Windows venv')
class Stage952GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def test_status_and_frame_alignment(self):
        from PySide6.QtWidgets import QGroupBox, QWidget
        from src.ui.main_window import MainWindow
        w=MainWindow();seed_sample(w);w.show()
        try:
            self.app.processEvents()
            guide=w.findChild(QGroupBox,'drawing_group')
            panel=w.findChild(QWidget,'input_panel')
            self.assertEqual(guide.height(),panel.maximumHeight())
            self.assertEqual(w.minimumSize(),w.maximumSize())
            w.ring_size.setCurrentIndex(1)
            self.app.processEvents()
            self.assertNotIn('Parker',w.statusBar().currentMessage())
            self.assertNotIn('endpoint',w.statusBar().currentMessage().lower())
            cell=w.overview_cells[('Squeeze',1)]
            self.assertIn('<br/>',cell.text())
            w.ring_size.setCurrentIndex(0)
            self.app.processEvents()
            self.assertIn('<br/>',cell.text())
        finally:w.close()

    def test_inspector_names_and_equal_column_widths(self):
        from PySide6.QtWidgets import QComboBox,QTableWidget,QTextBrowser
        from src.ui.main_window import MainWindow
        w=MainWindow();seed_sample(w)
        try:
            d=w._make_tolerance_trace_dialog()
            self.assertIsNotNone(d)
            self.assertEqual([d.findChild(QComboBox,n).minimumWidth() for n in
                             ('trace_measure','trace_condition','trace_precision')],[140]*3)
            grid=d.findChild(QTableWidget,'geometry_table')
            self.assertEqual([grid.columnWidth(c) for c in (1,2,3)],[135]*3)
            text=d.findChild(QTextBrowser,'trace_text').toPlainText()
            for term in ('Rod OD','Gland OD','Entrance radius','tolerance endpoints'):
                self.assertNotIn(term,text)
            d.close()
        finally:w.close()

if __name__=='__main__': unittest.main()
