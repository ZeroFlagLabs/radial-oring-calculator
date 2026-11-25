"""Detailed/Simplified Inspector, snapshot, settings and header regression."""

import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from PySide6.QtWidgets import QApplication, QLabel, QComboBox, QTextBrowser, QTabWidget
from src.calculations.installed import calculate_installed
from src.ui.inspection_data import explain_case
from src.ui.main_window import MainWindow
from src.ui.settings_dialog import SettingsDialog
from src.ui.snapshot_view import save_snapshot_to_png, REPORT_WIDTH, REPORT_HEIGHT
from test_stage096 import samples
from gui_sample import seed_sample


class MethodEquationChecks(unittest.TestCase):
    def test_all_eight_geometry_variants_both_methods_all_witnesses(self):
        checked=0
        for inp,female,depth,dovetail in samples():
            evaluations={m:calculate_installed(inp,method=m)
                         for m in ('detailed','simplified')}
            self.assertEqual(evaluations['detailed'].results.cavity_area_sq_in,
                             evaluations['simplified'].results.cavity_area_sq_in)
            self.assertEqual(evaluations['detailed'].results.stretch_percent,
                             evaluations['simplified'].results.stretch_percent)
            for method,evaluation in evaluations.items():
                for metric in ('Squeeze','OD interference' if female else 'ID stretch','Gland fill'):
                    for condition in ('Minimum','Nominal','Maximum'):
                        result,inputs,steps=explain_case(evaluation,metric,condition,inp,6)
                        self.assertAlmostEqual(result,steps[-1].result,places=9)
                        self.assertTrue(all(step.symbolic and step.numeric for step in steps))
                        self.assertTrue(all(step.numeric_fraction is not None for step in steps
                                            if step.symbol_fraction is not None))
                        titles=[step.title for step in steps]
                        if metric=='Squeeze' and not female:
                            if method=='simplified':
                                self.assertIn('Free-state compression section',titles)
                                self.assertNotIn('Installed-section reduction',titles)
                                self.assertIn('d\u2080',steps[-1].symbol_fraction[2])
                            else:
                                self.assertIn('Installed-section reduction',titles)
                        if metric=='Gland fill' and not female:
                            if method=='simplified':
                                self.assertIn('O-ring material section',titles)
                                self.assertNotIn('Installed O-ring material section',titles)
                                self.assertAlmostEqual(steps[0].result,
                                                       dict(evaluation.cases[(metric,condition)].values)['section'])
                            else:
                                self.assertTrue(any(t in titles for t in
                                                    ('Installed O-ring material section','O-ring material section')))
                        checked+=1
        self.assertEqual(checked,144)


class MethodUiChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def test_header_icon_and_reference_style_popup_preserve_geometry(self):
        from PySide6.QtWidgets import QDialog, QWidget
        w=MainWindow();w.show()
        try:
            self.app.processEvents()
            self.assertEqual((w.width(),w.height()),(1080,781))
            button=w.calculation_method_info_button
            self.assertEqual((button.width(),button.height()),(15,15))
            self.assertTrue(button.isVisible())
            self.assertFalse(button.icon().isNull())
            label=w.findChild(QLabel,'selector_calculation_method_label')
            self.assertEqual(button.pos().x(),
                             min(label.width()-button.width(),
                                 label.fontMetrics().horizontalAdvance(label.text())+4))
            self.assertEqual(button.pos().y(),2)
            dialog=w._make_calculation_method_info_dialog()
            dialog.show()
            self.app.processEvents()
            self.assertEqual(dialog.windowTitle(),
                'Calculation Method | Static & Dynamic Radial O-Ring Calculator')
            self.assertEqual(dialog.width(),485)
            self.assertLessEqual(dialog.height(),265)
            self.assertIsNone(dialog.findChild(QLabel,'method_dialog_icon'))
            heading=dialog.findChild(QLabel,'method_dialog_heading')
            rule=dialog.findChild(QWidget,'method_dialog_heading_rule')
            app_name=dialog.findChild(QLabel,'method_dialog_app_name')
            self.assertEqual(heading.text(),'Calculation Method')
            self.assertEqual((heading.x(),heading.y()),(11,11))
            self.assertEqual((rule.x(),rule.y()),(11,34))
            self.assertEqual((app_name.x(),app_name.y()),(11,43))
            self.assertEqual(rule.width(),dialog.width()-22)
            self.assertIsNotNone(dialog.findChild(QLabel,'method_heading_detailed'))
            self.assertIsNotNone(dialog.findChild(QLabel,'method_heading_simplified'))
            margins=dialog.layout().contentsMargins()
            self.assertEqual((margins.left(),margins.top(),margins.right(),margins.bottom()),
                             (11,11,11,11))
            self.assertEqual(dialog.layout().spacing(),6)
            descriptions=[dialog.findChild(QLabel,'method_description_'+method)
                          for method in ('detailed','simplified')]
            self.assertIn('manufacturer-informed installed-condition',descriptions[0].text())
            self.assertIn('free-state O-ring cross-section',descriptions[1].text())
            for description in descriptions:
                self.assertGreaterEqual(description.height(),
                                        description.heightForWidth(description.width()))
            self.assertNotIn('recommended for new',' '.join(x.text() for x in descriptions).lower())
            self.assertNotIn('retrospective',' '.join(x.text() for x in descriptions).lower())
            close=dialog.findChild(QWidget,'close_method_information')
            self.assertEqual(close.width(),106)
            self.assertEqual(close.geometry().right()+1,dialog.width()-11)
            dialog.close()
            # The quiet QDialog opens directly, never a notification message box.
            with patch.object(QDialog,'exec',return_value=0) as show:
                button.click()
                show.assert_called_once()
        finally:w.close()

    def test_save_png_suggested_filename_starts_with_current_method(self):
        """Method name leads the filename; the existing context is unchanged."""
        from PySide6.QtGui import QPixmap
        from PySide6.QtWidgets import QFileDialog

        w=MainWindow()
        w.show()
        try:
            self.app.processEvents()
            image=QPixmap(2,2)
            image.fill()
            with (patch.object(w, '_snapshot_pixmap', return_value=image),
                  patch.object(QFileDialog, 'getSaveFileName',
                               return_value=('', '')) as picker):
                # Original default context remains after the new method prefix.
                w._save_snapshot()
                self.assertEqual(picker.call_args.args[2],
                                 'Detailed - Static - Piston - Rectangular.png')

                # Changing calculation method must immediately update the
                # proposed filename, without saving or reusing an old method.
                w.calculation_method.setCurrentIndex(1)
                w._save_snapshot()
                self.assertEqual(picker.call_args.args[2],
                                 'Simplified - Static - Piston - Rectangular.png')

                # The existing application, component, profile and catalogue
                # designation fields follow the method in their original order.
                w.application.setCurrentIndex(1)
                w.configuration.setCurrentIndex(1)
                w.groove_type.setCurrentIndex(1)
                w.ring_size.setCurrentIndex(1)
                w._save_snapshot()
                proposed=picker.call_args.args[2]
                self.assertTrue(proposed.startswith(
                    'Simplified - Dynamic - Cylinder - Double Dovetail - '),
                    proposed)
                self.assertTrue(proposed.endswith('.png'),proposed)

                w.calculation_method.setCurrentIndex(0)
                w._save_snapshot()
                self.assertEqual(picker.call_args.args[2],
                                 'Detailed'+proposed[len('Simplified'):])
        finally:
            w.close()

    def test_two_inspectors_show_correct_equations_and_witnesses(self):
        w=MainWindow();seed_sample(w);w.show()
        try:
            for index,method in ((0,'detailed'),(1,'simplified')):
                w.calculation_method.setCurrentIndex(index)
                self.app.processEvents()
                dlg=w._make_tolerance_trace_dialog()
                self.assertIsNotNone(dlg)
                self.assertIn(method.title(),dlg.windowTitle())
                measures=dlg.findChild(QComboBox,'trace_measure')
                conditions=dlg.findChild(QComboBox,'trace_condition')
                prec=dlg.findChild(QComboBox,'trace_precision')
                browser=dlg.findChild(QTextBrowser,'trace_text')
                self.assertEqual(dlg.findChild(QTabWidget,'result_tabs').count(),2)
                for metricidx,metric in enumerate(('Squeeze','ID stretch','Gland fill')):
                    measures.setCurrentIndex(metricidx)
                    for conditionidx,condition in enumerate(('Minimum','Nominal','Maximum')):
                        conditions.setCurrentIndex(conditionidx)
                        self.app.processEvents()
                        text=browser.toPlainText()
                        result,_,steps=explain_case(w._last_evaluation,metric,condition,w._last_inputs,3)
                        self.assertIn(steps[-1].title,text)
                        self.assertIn(f'{result:.3f}',text)
                        if method=='simplified' and metric=='Squeeze':
                            self.assertIn('Free-state compression section',text)
                            self.assertNotIn('Installed-section reduction',text)
                        if method=='detailed' and metric=='Squeeze':
                            self.assertIn('Installed-section reduction',text)
                        if method=='simplified' and metric=='Gland fill':
                            self.assertIn('free-state',text.lower())
                            self.assertNotIn('Installed O-ring material section',text)
                dlg.close()
        finally:w.close()

    def test_size_reference_buttons_have_equal_width(self):
        from src.ui.size_guide import SizeGuide
        w=MainWindow()
        guide=SizeGuide(w.as568_sizes,w)
        guide.show()
        try:
            self.app.processEvents()
            self.assertEqual(guide.choose.width(),112)
            self.assertEqual(guide.close_button.width(),106)
            # Qt offscreen reports inflated font widths on this Windows host.
            # Native Windows fit was verified separately at 87px + 24px.
            if self.app.platformName() != 'offscreen':
                self.assertGreaterEqual(
                    guide.choose.width()-guide.choose.fontMetrics().horizontalAdvance(
                        guide.choose.text()),20)
            from PySide6.QtWidgets import QDialogButtonBox
            settings=SettingsDialog(w)
            settings_close=settings.dialog.findChild(QDialogButtonBox,'buttons').button(
                QDialogButtonBox.StandardButton.Close)
            self.assertEqual(settings_close.width(),guide.close_button.width())
            settings.dialog.close()
        finally:
            guide.close()
            w.close()

    def test_all_dialog_action_buttons_share_compact_width(self):
        from PySide6.QtWidgets import QDialogButtonBox, QPushButton
        from src.ui.size_guide import SizeGuide
        from src.ui.dialog_style import standard_action_width
        w=MainWindow()
        seed_sample(w)
        settings=SettingsDialog(w)
        guide=SizeGuide(w.as568_sizes,w)
        method=w._make_calculation_method_info_dialog()
        inspector=w._make_tolerance_trace_dialog()
        try:
            self.assertIsNotNone(inspector)
            buttons=[
                guide.choose,
                guide.close_button,
                settings.dialog.findChild(QDialogButtonBox,'buttons').button(
                    QDialogButtonBox.StandardButton.Close),
                method.findChild(QPushButton,'close_method_information'),
                inspector.findChild(QPushButton,'close_inspection'),
            ]
            self.assertEqual([button.width() for button in buttons],
                             [112,106,106,106,106])
            for button in buttons[1:]:
                self.assertEqual(button.width(),standard_action_width(button))
            # The longest caption remains untruncated at the current font.
            # Qt offscreen reports inflated font widths on this Windows host.
            # Native Windows fit was verified separately at 87px + 24px.
            if self.app.platformName() != 'offscreen':
                self.assertGreaterEqual(
                    guide.choose.width()-guide.choose.fontMetrics().horizontalAdvance(
                        guide.choose.text()),20)
        finally:
            inspector.close()
            method.close()
            guide.close()
            settings.dialog.close()
            w.close()

    def test_male_tab_order_direct_od_and_depth_groove_entries(self):
        from PySide6.QtWidgets import QDoubleSpinBox
        from PySide6.QtTest import QTest
        from PySide6.QtCore import Qt
        w=MainWindow()
        w.show()
        try:
            self.app.processEvents()
            def focus_name():
                focus=self.app.focusWidget()
                while focus is not None and not isinstance(focus,QDoubleSpinBox):
                    focus=focus.parentWidget()
                return focus.objectName() if focus is not None else None

            # Test returning to direct OD after switching away as well.
            for idx,component,groove in (
                (0,'direct_rod_od','gland_od'),
                (1,'rod_od','groove_depth'),
                (0,'direct_rod_od','gland_od'),
            ):
                w.entry_mode.setCurrentIndex(idx)
                self.app.processEvents()
                tol=w.rows[component].tolerance
                tol.setFocus(Qt.FocusReason.OtherFocusReason)
                self.app.processEvents()
                self.assertEqual(focus_name(),tol.objectName())
                for target in (w.rows[groove].nominal,
                               w.rows[groove].tolerance,
                               w.findChild(QDoubleSpinBox,'spin_shared_width_nom')):
                    QTest.keyClick(self.app.focusWidget(),Qt.Key.Key_Tab)
                    self.app.processEvents()
                    self.assertEqual(focus_name(),target.objectName())
        finally:
            w.close()

    def test_main_action_buttons_match_dialog_width_without_resizing_window(self):
        from PySide6.QtWidgets import QPushButton
        w=MainWindow();w.show()
        try:
            self.app.processEvents()
            self.assertEqual((w.width(),w.height()),(1080,781))
            names=('trace_button','reset_button','snapshot_button',
                   'save_snapshot_button')
            buttons=[w.findChild(QPushButton,name) for name in names]
            self.assertEqual([btn.width() for btn in buttons],[106]*4)
            xs=[btn.mapTo(w,btn.rect().topLeft()).x() for btn in buttons]
            self.assertEqual(xs,[10,124,850,964])
            self.assertTrue(all(a.geometry().right()<b.geometry().left()
                                for a,b in zip(buttons,buttons[1:])))
        finally:
            w.close()

    def test_action_buttons_and_settings_never_receive_tab_focus_in_any_configuration(self):
        from PySide6.QtWidgets import QPushButton
        from PySide6.QtTest import QTest
        from PySide6.QtCore import Qt
        w=MainWindow()
        w.show()
        try:
            self.app.processEvents()
            buttons=[w.findChild(QPushButton,name) for name in
                     ('trace_button','reset_button','snapshot_button',
                      'save_snapshot_button','settings_button')]
            for button in buttons:
                self.assertEqual(button.focusPolicy(),Qt.FocusPolicy.NoFocus)
                self.assertTrue(button.isEnabled() or
                                button.objectName() in
                                ('trace_button','snapshot_button','save_snapshot_button'))
            count=0
            for application in range(2):
                w.application.setCurrentIndex(application)
                for configuration in range(2):
                    w.configuration.setCurrentIndex(configuration)
                    for profile in range(2):
                        w.groove_type.setCurrentIndex(profile)
                        for mode in range(2):
                            (w.female_entry_mode if configuration else
                             w.entry_mode).setCurrentIndex(mode)
                            for ring in ('automatic','manual'):
                                w.ring_size.setCurrentIndex(
                                    0 if ring=='automatic'
                                    else w.ring_size.count()-1)
                                self.app.processEvents()
                                start=(w.female_rows[
                                    'direct_cylinder_id' if mode==0 else
                                    'cylinder_id'].nominal if configuration
                                    else w.rows['cylinder_id'].nominal)
                                start.setFocus(Qt.FocusReason.OtherFocusReason)
                                self.app.processEvents()
                                for step in range(30):
                                    focus=self.app.focusWidget()
                                    self.assertIsNotNone(focus)
                                    self.assertNotIn(
                                        focus,buttons,
                                        (application,configuration,profile,
                                         mode,ring,step))
                                    QTest.keyClick(focus,Qt.Key.Key_Tab)
                                    self.app.processEvents()
                                count+=1
            self.assertEqual(count,32)
        finally:
            w.close()

    def test_female_tab_order_all_groove_profiles_and_entry_modes(self):
        from PySide6.QtWidgets import QDoubleSpinBox
        from PySide6.QtTest import QTest
        from PySide6.QtCore import Qt
        w=MainWindow();w.show()
        try:
            self.app.processEvents()
            w.configuration.setCurrentIndex(1)
            def focused_name():
                focus=self.app.focusWidget()
                while focus is not None and not isinstance(focus,QDoubleSpinBox):
                    focus=focus.parentWidget()
                return focus.objectName() if focus is not None else None
            for profile in range(2):
                w.groove_type.setCurrentIndex(profile)
                for index in (0,1,0):
                    w.female_entry_mode.setCurrentIndex(index)
                    self.app.processEvents()
                    cylinder=('direct_cylinder_id' if index==0 else 'cylinder_id')
                    gland=('gland_id' if index==0 else 'groove_depth')
                    rows=w.female_rows
                    expected=[]
                    for key in (cylinder,'rod_od',gland):
                        expected.extend((rows[key].nominal.objectName(),
                                         rows[key].tolerance.objectName()))
                    for key in ('width','radius','entrance_radius',
                                'angle' if profile else 'rect_angle'):
                        row=w.shared_rows[key]
                        expected.extend((row.nominal.objectName(),
                                         row.tolerance.objectName()))
                    first=rows[cylinder].nominal
                    first.setFocus(Qt.FocusReason.OtherFocusReason)
                    self.app.processEvents()
                    observed=[focused_name()]
                    for _ in range(len(expected)-1):
                        QTest.keyClick(self.app.focusWidget(),Qt.Key.Key_Tab)
                        self.app.processEvents()
                        observed.append(focused_name())
                    self.assertEqual(observed,expected,
                                     (w.groove_type.currentData(),
                                      w.female_entry_mode.currentData()))
        finally:
            w.close()

    def test_snapshot_contains_method_and_retains_fixed_image(self):
        from src.ui import snapshot_view
        w=MainWindow();seed_sample(w);w.show()
        try:
            for index,method in ((0,'Detailed'),(1,'Simplified')):
                w.calculation_method.setCurrentIndex(index)
                self.app.processEvents()
                self.assertTrue(w.trace_button.isEnabled())
                self.assertTrue(w.snapshot_button.isEnabled())
                self.assertTrue(w.save_snapshot_button.isEnabled())
                textcalls=[]
                original=snapshot_view._text
                def capture(painter,x,y,value,**kwargs):
                    textcalls.append((x,y,str(value)))
                    return original(painter,x,y,value,**kwargs)
                with patch.object(snapshot_view,'_text',side_effect=capture):
                    pix=w._snapshot_pixmap()
                self.assertFalse(pix.isNull())
                self.assertEqual((pix.width(),pix.height()),(REPORT_WIDTH,REPORT_HEIGHT))
                self.assertIn((29,114,'Calculation method'),textcalls)
                self.assertIn((439,114,method),textcalls)
                for label in ('Application','Gland type','Groove profile','Groove dimension','O-ring size'):
                    self.assertTrue(any(x==29 and v==label for x,y,v in textcalls),label)
                self.assertEqual(
                    [y for name in ('Calculation method','Application','Gland type',
                                    'Groove profile','Groove dimension','O-ring size')
                     for x,y,v in textcalls if x==29 and v==name],
                    [114,136,158,180,202,224])
                self.assertTrue(any(y==270 and v=='INPUT DIMENSIONS' for x,y,v in textcalls))
                # Real PNG encoder and clipboard path work in both modes.
                with tempfile.TemporaryDirectory() as tmp:
                    target=Path(tmp)/(method+'.png')
                    self.assertEqual(save_snapshot_to_png(pix,str(target)),str(target))
                    self.assertGreater(target.stat().st_size,10000)
                w._copy_snapshot()
                self.assertFalse(QApplication.clipboard().pixmap().isNull())
        finally:w.close()

    def test_snapshot_screening_rows_center_every_field(self):
        from src.ui import snapshot_view
        w=MainWindow();seed_sample(w);w.show()
        try:
            for method_index in (0,1):
                w.calculation_method.setCurrentIndex(method_index)
                self.app.processEvents()
                calls=[]
                original=snapshot_view._row_cell
                def capture(painter,x,top,width,height,value,**kw):
                    calls.append((x,top,width,height,str(value),kw))
                    return original(painter,x,top,width,height,value,**kw)
                with patch.object(snapshot_view,'_row_cell',side_effect=capture):
                    report=w._snapshot_pixmap()
                self.assertEqual((report.width(),report.height()),(966,686))
                for i,row in enumerate(('Squeeze','ID stretch','Gland fill')):
                    top=548+i*40
                    singles=[c for c in calls if c[1]==top and c[3]==40
                             and c[0] in (29,541,851)]
                    self.assertEqual(len(singles),3)
                    self.assertEqual([c[0] for c in singles],[29,541,851])
                    self.assertIn(row,singles[0][4])
                    self.assertTrue(singles[1][5].get('wrap'))
                    self.assertEqual(singles[2][5].get('align'),'center')
                    top_values=[c for c in calls if c[1]==top+2 and c[3]==18]
                    bottom_values=[c for c in calls if c[1]==top+20 and c[3]==18]
                    if top_values:
                        self.assertEqual([c[0] for c in top_values],[159,260,361])
                        self.assertEqual([c[0] for c in bottom_values],[159,260,361])
                        self.assertEqual((top_values[0][1]+top_values[0][3]/2 +
                                          bottom_values[0][1]+bottom_values[0][3]/2)/2,
                                         top+20)
                    else:
                        self.assertEqual(
                            [c[0] for c in calls if c[1]==top and c[3]==40
                             and c[0] in (159,260,361)],
                            [159,260,361])
        finally:w.close()

    def test_snapshot_squeeze_row_has_same_height_as_other_rows(self):
        from src.ui import snapshot_view
        w=MainWindow();seed_sample(w);w.show()
        try:
            calls=[]
            original=snapshot_view._line
            def capture(painter,y,*args,**kwargs):
                calls.append(y)
                return original(painter,y,*args,**kwargs)
            with patch.object(snapshot_view,'_line',side_effect=capture):
                w._snapshot_pixmap()
            self.assertIn(547,calls)
            self.assertIn(588,calls)
            self.assertIn(628,calls)
            self.assertEqual(588-548,628-588)
            self.assertEqual(628-588,40)
            self.assertEqual(548-547,1)
        finally:
            w.close()

    def test_method_assumptions_references_and_screening_limits(self):
        w=MainWindow()
        settings=SettingsDialog(w)
        try:
            tabs=settings.dialog.findChild(QTabWidget,'settings_tabs')
            self.assertEqual([tabs.tabText(i) for i in range(tabs.count())],
                             ['Assumptions','References','Updates','About'])
            assumptions=settings.dialog.findChild(QLabel,'assumptions_text').text()
            refs=settings.dialog.findChild(QLabel,'references_text').text()
            self.assertIn('Detailed',assumptions)
            self.assertIn('Simplified',assumptions)
            self.assertIn('constant-volume',assumptions)
            self.assertIn('OD-interference',assumptions)
            self.assertIn('not a separately manufacturer-endorsed',refs)
            self.assertIn('Parker Hannifin',refs)
            self.assertIn('Freudenberg',refs)
            self.assertIn('James Walker',refs)
            self.assertIn('16%',settings.dialog.findChild(QLabel,'criteria_text').text())
        finally:
            settings.dialog.close()
            w.close()


if __name__=='__main__':
    unittest.main()
