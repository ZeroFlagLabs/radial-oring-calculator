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
        # v2.0 layout: six equal-width dropdowns, with method first.
        for control in ('calculation_method','application','configuration',
                        'groove_type','entry_mode_stack','ring_size'):
            self.assertEqual(int(widget(r,control).find('./property[@name="minimumSize"]/size/width').text),164)
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
        self.assertIn('status.setContentsMargins(40, 3, 0, 0)',main)
        self.assertIn('Static & Dynamic Radial O-Ring Calculator',(ROOT/'src/main.py').read_text(encoding='utf-8'))
        self.assertEqual(txt(widget(ET.parse(ROOT/'src/ui/forms/main_window.ui').getroot(),'setup_group'),'title'), 'Application setup')

@unittest.skipUnless(QT,'Requires PySide6; run with installed Windows venv')
class Stage952GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def test_method_selector_layout_preview(self):
        from PySide6.QtWidgets import QWidget
        from src.ui.main_window import MainWindow
        w=MainWindow();w.show()
        try:
            self.app.processEvents()
            names=('calculation_method','application','configuration',
                   'groove_type','entry_mode_stack','ring_size')
            controls=[w.findChild(QWidget,name) for name in names]
            self.assertTrue(all(controls))
            self.assertEqual([x.width() for x in controls],[164]*6)
            positions=[x.mapTo(w,x.rect().topLeft()) for x in controls]
            self.assertEqual([p.x() for p in positions],sorted(p.x() for p in positions))
            self.assertEqual(len({p.y() for p in positions}),1)
            ring=w.ring_size
            heading=w.findChild(QWidget,'selector_ring_size_label')
            info=w.guide_button
            self.assertEqual(ring.mapTo(w,ring.rect().topLeft()).x(),
                             heading.mapTo(w,heading.rect().topLeft()).x())
            self.assertEqual(info.mapTo(w,info.rect().topLeft()).x(),
                             ring.mapTo(w,ring.rect().topLeft()).x()+ring.width()+4)
            self.assertEqual(w.calculation_method.currentData(),'detailed')
            # Both methods now support results inspection and reporting.
            self.assertTrue(w.calculation_method.model().item(1).isEnabled())
        finally:w.close()

    def test_simplified_live_preview_preserves_inputs_and_reports(self):
        from src.ui.main_window import MainWindow
        from src.calculations.installed import calculate_installed
        from src.calculations.criteria import screen_rectangular
        w=MainWindow();seed_sample(w);w.show()
        try:
            self.app.processEvents()
            initial=w._collect()
            expected_detailed=calculate_installed(initial,method='detailed')
            expected_simple=calculate_installed(initial,method='simplified')
            self.assertEqual(w._last_result,expected_detailed.results)
            self.assertTrue(w.trace_button.isEnabled())
            self.assertTrue(w.snapshot_button.isEnabled())
            self.assertTrue(w.save_snapshot_button.isEnabled())
            w.calculation_method.setCurrentIndex(1)
            self.app.processEvents()
            self.assertEqual(w.calculation_method.currentData(),'simplified')
            self.assertEqual(w._collect(),initial)
            self.assertEqual(w._last_evaluation,expected_simple)
            self.assertEqual(w._last_result,expected_simple.results)
            self.assertNotEqual(w._last_result.squeeze_percent.nominal,
                                expected_detailed.results.squeeze_percent.nominal)
            self.assertEqual(w._last_result.stretch_percent,
                             expected_detailed.results.stretch_percent)
            self.assertNotEqual(w._last_result.gland_fill_percent,
                                expected_detailed.results.gland_fill_percent)
            self.assertEqual(w._last_result.cavity_area_sq_in,
                             expected_detailed.results.cavity_area_sq_in)
            self.assertEqual(w._last_screening.checks[1:],
                             screen_rectangular(expected_detailed.results,
                                                w.application.currentData()).checks[1:])
            self.assertTrue(w.trace_button.isEnabled())
            self.assertTrue(w.snapshot_button.isEnabled())
            self.assertTrue(w.save_snapshot_button.isEnabled())
            dialog=w._make_tolerance_trace_dialog()
            self.assertIsNotNone(dialog)
            self.assertIn('Simplified',dialog.windowTitle())
            dialog.close()
            self.assertIsNotNone(w._snapshot_pixmap())
            self.assertEqual(w.statusBar().currentMessage(),'')
            w.calculation_method.setCurrentIndex(0)
            self.app.processEvents()
            self.assertEqual(w._collect(),initial)
            self.assertEqual(w._last_evaluation,expected_detailed)
            self.assertTrue(w.trace_button.isEnabled())
            self.assertTrue(w.snapshot_button.isEnabled())
            self.assertTrue(w.save_snapshot_button.isEnabled())
            dialog=w._make_tolerance_trace_dialog()
            self.assertIsNotNone(dialog)
            dialog.close()
        finally:w.close()

    def test_equal_dimension_and_guide_frame_widths(self):
        from PySide6.QtWidgets import QGroupBox, QWidget
        from src.ui.main_window import MainWindow
        w=MainWindow();w.show()
        try:
            self.app.processEvents()
            names=('male_group','female_group','shared_group',
                   'ring_group','drawing_group')
            frames=[w.findChild(QGroupBox,name) for name in names]
            self.assertEqual([frame.width() for frame in frames],[520]*5)
            self.assertEqual(w.findChild(QWidget,'input_panel').width(),530)
            self.assertEqual(w.findChild(QWidget,'guide_panel').width(),520)
            self.assertEqual(w.minimumSize(),w.maximumSize())
            app_left=w.application.mapTo(w,w.application.rect().topLeft()).x()
            for name in ('spin_male_cylinder_id_nom','spin_shared_width_nom',
                         'spin_male_ring_id_nom'):
                field=w.findChild(QWidget,name)
                self.assertEqual(field.mapTo(w,field.rect().topLeft()).x(),app_left)
            self.assertEqual(w.findChild(QWidget,'spin_shared_width_tol').mapTo(
                w,w.findChild(QWidget,'spin_shared_width_tol').rect().topLeft()).x(),app_left+218)
            # Toggling male/female must retain the equal-column layout.
            w.configuration.setCurrentIndex(1)
            self.app.processEvents()
            self.assertEqual(w.findChild(QGroupBox,'female_group').width(),520)
            self.assertEqual(w.findChild(QGroupBox,'drawing_group').width(),520)
            female_tol=w.findChild(QWidget,'spin_female_rod_od_tol')
            female_frame=w.findChild(QGroupBox,'female_group')
            self.assertEqual(
                female_frame.mapTo(w,female_frame.rect().topLeft()).x()+female_frame.width(),
                female_tol.mapTo(w,female_tol.rect().topLeft()).x()+female_tol.width()+14)
        finally:w.close()

    def test_right_edges_and_symmetric_dimension_padding(self):
        from PySide6.QtWidgets import QGroupBox, QWidget
        from src.ui.main_window import MainWindow
        w=MainWindow();w.show()
        try:
            self.app.processEvents()
            def left(name):
                field=w.findChild(QWidget,name)
                return field.mapTo(w,field.rect().topLeft()).x()
            def right(name):
                field=w.findChild(QWidget,name)
                return left(name)+field.width()
            # All three right edges meet, without the extra width at the right.
            self.assertEqual(right('setup_group'),right('drawing_group'))
            self.assertEqual(right('overview_box'),right('drawing_group'))
            self.assertEqual(w.width(),1080)
            left_pad=left('calculation_method')-left('setup_group')
            right_pad=right('setup_group')-right('guide_button')
            self.assertEqual(left_pad,right_pad)
            self.assertEqual(left_pad,15)
            # Dimension labels and tolerance controls have the same edge inset.
            for label,field,group in (
                ('label_male_cylinder_id','spin_male_cylinder_id_tol','male_group'),
                ('label_shared_width','spin_shared_width_tol','shared_group'),
                ('label_male_ring_id','spin_male_ring_id_tol','ring_group'),
            ):
                self.assertEqual(left(label)-left(group), 14)
                # Both sides of each dimension group retain the same 14px inset.
                # The first nominal field remains anchored at its original X.
                self.assertEqual(right(group)-right(field), 14)
            self.assertEqual(w.height(),784)
        finally:w.close()

    def test_compact_screening_columns_and_status(self):
        from PySide6.QtWidgets import QLabel, QWidget
        from src.ui.main_window import MainWindow
        w=MainWindow();seed_sample(w);w.show()
        try:
            self.app.processEvents()
            def centre(name):
                widget=w.findChild(QWidget,name)
                return widget.mapTo(w,widget.rect().topLeft()).x()+widget.width()/2
            positions=[centre('overview_header_'+str(i)) for i in (1,2,3)]
            self.assertEqual(positions,[558,698,838])
            self.assertEqual([b-a for a,b in zip(positions,positions[1:])],[140,140])
            self.assertEqual(w.findChild(QWidget,'overview_box').height(),179)
            # The corrected compact 112px button width preserves the right
            # edge, while the Status column remains at its original centre.
            self.assertEqual(centre('overview_header_4'),994)
            save=w.findChild(QWidget,'save_snapshot_button')
            results=w.findChild(QWidget,'overview_box')
            self.assertEqual(save.mapTo(w,save.rect().topLeft()).x()+save.width(),
                             results.mapTo(w,results.rect().topLeft()).x()+results.width())
            self.assertEqual(save.width(),112)
            for name in ('overview_squeeze_4','overview_fit_4','overview_fill_4'):
                self.assertEqual(centre(name),centre('overview_header_4'))
            # Contents-only alignment: the actual rendered Status text is
            # centred under Save PNG, not the original 102px grid cell.
            def visible_centre(name):
                label=w.findChild(QLabel,name)
                rect=label.contentsRect()
                return label.mapTo(w,rect.topLeft()).x()+rect.width()/2
            self.assertEqual(visible_centre('overview_header_4'),centre('save_snapshot_button'))
            for name in ('overview_squeeze_4','overview_fit_4','overview_fill_4'):
                self.assertEqual(visible_centre(name),centre('save_snapshot_button'))
            # All three numeric text centres move together; original column
            # geometry and precisely 140px between headings remain intact.
            shifted=[visible_centre('overview_header_'+str(i)) for i in (1,2,3)]
            self.assertEqual([b-a for a,b in zip(shifted,shifted[1:])],[140,140])
            for name in ('overview_squeeze_name','overview_fit_name','overview_fill_name'):
                label=w.findChild(QLabel,name)
                self.assertLessEqual(label.sizeHint().height(),label.height())
                self.assertLessEqual(label.sizeHint().width(),label.width())
                self.assertFalse(label.wordWrap())
        finally:w.close()

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
