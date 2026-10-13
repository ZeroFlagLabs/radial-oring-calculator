from gui_sample import seed_sample
"""Stage 9.5: direct snapshot, two-tab inspection and fixed footprint tests."""
from pathlib import Path
from xml.etree import ElementTree as ET
import importlib.util
import unittest

ROOT=Path(__file__).resolve().parents[1]
QT=importlib.util.find_spec('PySide6') is not None

class Stage95SourceTests(unittest.TestCase):
    def test_main_window_only_contains_live_designer_controls(self):
        ui=ET.parse(ROOT/'src/ui/forms/main_window.ui').getroot()
        names=[x.get('name') for x in ui.iter('widget')]
        self.assertEqual(len(names),len(set(names)))
        for key in ('trace_button','snapshot_button','save_snapshot_button','settings_button'):
            self.assertIn(key,names)
        for removed in ('details_group','criteria_group','details_button','copy_button'):
            self.assertNotIn(removed,names)
        self.assertEqual(ui.find('.//widget[@name="overview_header_0"]/property[@name="text"]/string').text or '', '')
    def test_input_column_has_no_expanding_gap_below_frames(self):
        """Surplus panel height must not appear between input groups."""
        ui=ET.parse(ROOT/'src/ui/forms/main_window.ui').getroot()
        layout=ui.find('.//layout[@name="inputLayout"]')
        self.assertIsNotNone(layout)
        last_item=layout.findall('item')[-1]
        spacer=last_item.find('spacer[@name="input_bottom_stretch"]')
        self.assertIsNotNone(spacer)
        self.assertEqual(spacer.find('./property[@name="sizeType"]/enum').text,
                         'QSizePolicy::Fixed')
    def test_results_inspector_designer_tabs_and_precision(self):
        ui=ET.parse(ROOT/'src/ui/forms/inspect_results.ui').getroot()
        names=[x.get('name') for x in ui.iter('widget')]
        self.assertEqual(len(names),len(set(names)))
        for name in ('result_tabs','geometry_table','trace_precision','trace_condition','trace_measure','trace_text'):
            self.assertIn(name,names)
        tabs=ui.findall('.//widget[@name="result_tabs"]/widget')
        self.assertEqual([x.get('name') for x in tabs],['tolerance_tab','geometry_tab'])
    def test_invalid_geometry_cannot_unhide_layout_changing_footer(self):
        main=(ROOT/'src/ui/main_window.py').read_text()
        self.assertNotIn('self.overview_note.show()',main)
        self.assertIn('self.statusBar().showMessage(message)',main)
        self.assertIn("status.setText('INVALID')",main)
        self.assertIn('title_label.setToolTip(check.criterion)',main)

    def test_snapshot_uses_explicit_qt6_painter_offset(self):
        snapshot=(ROOT/'src/ui/snapshot_view.py').read_text()
        self.assertIn('painter.drawPixmap(x, y, fitted)',snapshot)

    def test_main_window_is_non_scrolling_and_fixed_size_in_code(self):
        main=(ROOT/'src/ui/main_window.py').read_text()
        self.assertIn('self.setCentralWidget(surface)',main)
        self.assertIn('self.setFixedSize(width, height)',main)
        self.assertIn('self._stabilise_input_heights()',main)
        self.assertIn('stack.setFixedHeight(height)',main)
        self.assertIn("self.findChild(QWidget, 'input_panel')", main)
        self.assertIn("self.findChild(QGroupBox, 'overview_box')", main)
        self.assertIn('group.setFixedHeight(height)',main)
        self.assertNotIn('scroll.setWidget(surface)',main)
        # This label belonged to the removed Detailed Geometry panel. It must
        # not be accessed when the male/female setup changes at startup.
        self.assertNotIn('self.gland_label', main)
        self.assertIn('self.save_snapshot_button.clicked.connect(self._save_snapshot)',main)

@unittest.skipUnless(QT,'PySide6 unavailable; executed on Windows')
class Stage95GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])
    def test_inspector_tabs_and_geometry_display(self):
        from PySide6.QtWidgets import QTabWidget,QTableWidget,QComboBox
        from src.ui.main_window import MainWindow
        w=MainWindow();seed_sample(w)
        try:
            dlg=w._make_tolerance_trace_dialog()
            tabs=dlg.findChild(QTabWidget,'result_tabs')
            self.assertEqual(tabs.count(),2)
            self.assertEqual(tabs.tabText(0),'Tolerance cases')
            self.assertEqual(tabs.tabText(1),'Calculated geometry')
            table=dlg.findChild(QTableWidget,'geometry_table')
            self.assertGreaterEqual(table.rowCount(),5)
            self.assertIn('sealing area',table.item(table.rowCount()-1,0).text())
            prec=dlg.findChild(QComboBox,'trace_precision')
            self.assertEqual(prec.currentText(),'3 DP')
            self.assertRegex(table.item(table.rowCount()-1,2).text(),r'^-?\d+\.\d{3}$')
            prec.setCurrentIndex(6)
            self.assertRegex(table.item(table.rowCount()-1,2).text(),r'^-?\d+\.\d{6}$')
            dlg.close()
        finally:w.close()
    def test_fixed_main_and_direct_snapshot(self):
        from PySide6.QtWidgets import QScrollArea,QApplication
        from src.ui.main_window import MainWindow
        w=MainWindow();seed_sample(w)
        try:
            self.assertFalse(isinstance(w.centralWidget(),QScrollArea))
            self.assertEqual(w.minimumSize(),w.maximumSize())
            self.assertTrue(w.save_snapshot_button.isEnabled())
            pixmap=w._snapshot_pixmap()
            self.assertFalse(pixmap.isNull())
            self.assertGreater(pixmap.width(),500)
            self.assertGreater(pixmap.height(),300)
            w._copy_snapshot()
            self.assertFalse(QApplication.clipboard().pixmap().isNull())
            for config in (1,0):
                w.configuration.setCurrentIndex(config)
                w.ring_size.setCurrentIndex(1)
                self.app.processEvents()
                self.assertEqual(w.minimumSize(),w.maximumSize())
        finally:w.close()
    def test_invalid_as568_does_not_move_panels_or_add_result_row(self):
        from src.ui.main_window import MainWindow
        from PySide6.QtWidgets import QGroupBox
        w=MainWindow();seed_sample(w)
        w.show()
        try:
            self.app.processEvents()
            initial=(w.ring_group.y(),w.findChild(QGroupBox,'shared_group').y(),
                     w.findChild(QGroupBox,'overview_box').height())
            # A tiny AS568 ring is physically incompatible with the startup gland;
            # it must display INVALID without making a formerly hidden note visible.
            w.ring_size.setCurrentIndex(1)
            self.app.processEvents()
            self.assertEqual((w.ring_group.y(),w.findChild(QGroupBox,'shared_group').y(),
                              w.findChild(QGroupBox,'overview_box').height()),initial)
            self.assertTrue(w.overview_note.isHidden())
            self.assertEqual(w.overview_cells[('Squeeze',4)].text(),'INVALID')
            self.assertIn('Cannot evaluate geometry:',w.statusBar().currentMessage())
            w.ring_size.setCurrentIndex(0)
            self.app.processEvents()
            self.assertTrue(w.overview_note.isHidden())
        finally:w.close()

    def test_screening_subtitles_use_actual_check_criteria(self):
        from src.ui.main_window import MainWindow
        w=MainWindow();seed_sample(w)
        try:
            for kind in (0,1):
                w.application.setCurrentIndex(kind)
                for female in (0,1):
                    w.configuration.setCurrentIndex(female)
                    # Some initial male/female input combinations are invalid
                    # until the user enters suitable gland dimensions.
                    if w._last_screening is None: continue
                    for name, check in zip(('Squeeze','Fit','Gland fill'), w._last_screening.checks):
                        label=w.overview_cells[(name,0)]
                        self.assertIn(check.criterion,label.text())
                        self.assertEqual(label.toolTip(),check.criterion)
        finally:w.close()

    def test_size_guide_no_redundant_intro(self):
        from src.ui.size_guide import SizeGuide
        from src.ui.main_window import MainWindow
        from PySide6.QtWidgets import QLabel
        w=MainWindow();seed_sample(w)
        try:
            guide=SizeGuide(w.as568_sizes,w)
            self.assertFalse(any('nominal actual ID' in label.text() for label in guide.findChildren(QLabel)))
            guide.close()
        finally:w.close()

if __name__=='__main__': unittest.main()
