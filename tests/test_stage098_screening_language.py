"""Release candidate polish: screening wording, gland-area definition and spin hover."""
import ast
from pathlib import Path
from types import SimpleNamespace
import importlib.util
import unittest
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
QT = importlib.util.find_spec('PySide6') is not None


class ScreeningLanguageSourceTests(unittest.TestCase):
    def test_screening_language_does_not_modify_numeric_engine(self):
        main = (ROOT/'src/ui/main_window.py').read_text(encoding='utf8')
        snapshot = (ROOT/'src/ui/snapshot_view.py').read_text(encoding='utf8')
        inspector = (ROOT/'src/ui/inspect_results.py').read_text(encoding='utf8')
        ast.parse(main); ast.parse(snapshot); ast.parse(inspector)
        self.assertIn("cell.setText('PASS' if check.within_limits else 'REVIEW')",main)
        self.assertIn("'PASS' if passed else 'REVIEW'",snapshot)
        self.assertIn("status = 'PASS' if screening_check.within_limits else 'REVIEW'",inspector)
        self.assertIn('Full tolerance-range screening:',inspector)
        self.assertNotIn("else 'FAIL'",main)
        self.assertNotIn("else 'FAIL'",snapshot)

    def test_assumptions_capture_2d_area_and_review_distinction(self):
        root=ET.parse(ROOT/'src/ui/forms/settings_dialog.ui').getroot()
        item=root.find('.//widget[@name="assumptions_text"]/property[@name="text"]/string')
        self.assertIsNotNone(item)
        text=item.text
        for word in ('two-dimensional (2D) representation','opening radii',
                     'actual groove opening width','rectangular clearance area',
                     'perpendicularly','REVIEW','INVALID'):
            self.assertIn(word,text)
        self.assertNotIn('approximation',text.lower())
        self.assertNotIn('entrance radii',text.lower())

    def test_no_stepper_hover_fill_and_arrows_are_still_defined(self):
        root=ET.parse(ROOT/'src/ui/forms/main_window.ui').getroot()
        qss=root.find('.//widget[@name="appSurface"]/property[@name="styleSheet"]/string')
        if qss is None:  # style belongs to the outer QMainWindow for some layouts
            qss=root.find('.//widget[@name="MainWindow"]/property[@name="styleSheet"]/string')
        self.assertIsNotNone(qss)
        text=qss.text
        self.assertIn('QDoubleSpinBox::up-button, QDoubleSpinBox::down-button',text)
        self.assertIn('QDoubleSpinBox::up-arrow',text)
        self.assertIn('QDoubleSpinBox::down-arrow',text)
        self.assertNotIn('QDoubleSpinBox::up-button:hover',text)
        self.assertNotIn('QDoubleSpinBox::down-button:hover',text)

    def test_inspector_status_position_and_two_section_dividers(self):
        source = (ROOT/'src/ui/inspect_results.py').read_text(encoding='utf8')
        ast.parse(source)
        self.assertIn('Full tolerance-range screening:', source)
        self.assertEqual(source.count('_section_rule(),'), 2)
        self.assertIn('align="right" valign="middle"', source)
        self.assertIn("status = 'PASS' if screening_check.within_limits else 'REVIEW'", source)
        self.assertIn("colour = '#18805b' if screening_check.within_limits else '#bb2b23'", source)
        self.assertIn('color:#D8E1EA', source)

    def test_inspector_input_spacing_matches_section_dividers(self):
        # Qt's QTextBrowser can omit a paragraph's lower margin when the next
        # element is a table, so both table boundaries use explicit spacing.
        source = (ROOT/'src/ui/inspect_results.py').read_text(encoding='utf8')
        ast.parse(source)
        self.assertIn(
            'font-size:10pt;margin:13px 0 18px 0;color:#164f8a;',
            source,
        )
        spacer = "'<p style=\"font-size:1pt;margin:0 0 12px 0;\">&nbsp;</p>'"
        self.assertEqual(source.count(spacer), 2)
        # First spacer must occur *after* Input Values but *before* its table.
        self.assertLess(source.index('<b>Input Values</b></p>'), source.index(spacer))
        self.assertLess(source.index(spacer),
                        source.index('<table cellspacing="0" cellpadding="3" width="100%"'))
        # Second spacer must remain below the dimension table and above line 2.
        self.assertLess(source.index("'</table>',"), source.rindex(spacer))
        self.assertLess(source.rindex(spacer), source.rindex('_section_rule(),'))
        self.assertEqual(source.count('_section_rule(),'), 2)

    def test_reset_button_has_sentence_case_text(self):
        root = ET.parse(ROOT/'src/ui/forms/main_window.ui').getroot()
        button = root.find('.//widget[@name="reset_button"]')
        self.assertIsNotNone(button)
        label = button.find('./property[@name="text"]/string')
        self.assertIsNotNone(label)
        self.assertEqual(label.text, 'Reset dimensions')

    def test_inspector_typography_uses_uniform_10_point_working_text(self):
        source = (ROOT/'src/ui/inspect_results.py').read_text(encoding='utf8')
        self.assertIn('font-size:12pt', source)  # selected result and status
        self.assertIn('style="font-size:10pt;" align="right"', source)
        self.assertIn('style="font-size:10pt;padding:0 5px;"', source)
        self.assertIn('font-size:9pt', source)   # small explanatory notes
        self.assertNotIn('font-size:11pt', source)
        self.assertNotIn('font-size:8pt', source)



@unittest.skipUnless(QT, 'PySide6 GUI required')
class ScreeningLanguageWindowsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def test_outside_criteria_shows_red_review_in_main_and_inspector(self):
        from src.ui.main_window import MainWindow
        from gui_sample import seed_sample
        from PySide6.QtWidgets import QTextBrowser
        w=MainWindow()
        try:
            seed_sample(w)
            # Deliberately widen the cavity until gland fill falls below the
            # retained screening criterion; no engine or limit changes.
            w.shared_rows['width'].nominal.setValue(0.3)
            w._recalculate()
            self.assertIsNotNone(w._last_screening)
            self.assertFalse(w._last_screening.checks[2].within_limits)
            status = w.overview_cells[('Gland fill',4)]
            self.assertEqual(status.text(),'REVIEW')
            self.assertIn('#bb2b23',status.styleSheet())
            window=w._make_tolerance_trace_dialog()
            self.assertIsNotNone(window)
            try:
                measurement=window.findChild(type(w.application),'trace_measure')
                measurement.setCurrentIndex(2)
                self.app.processEvents()
                browser=window.findChild(QTextBrowser,'trace_text')
                self.assertIn('Full tolerance-range screening:',browser.toPlainText())
                self.assertIn('REVIEW',browser.toPlainText())
            finally:window.close()
            png=w._snapshot_pixmap()
            self.assertFalse(png.isNull())
        finally:w.close()

    def test_inspector_three_sections_preserve_calculation_content(self):
        from PySide6.QtGui import QTextDocument
        from src.ui.inspect_results import _html_breakdown
        dimensions = [('Cylinder ID', 0.669, 'in'),
                      ('Piston OD', 0.667, 'in'),
                      ('O-ring cross section', 0.103, 'in')]
        steps = [SimpleNamespace(title='Calculate clearance',
                                 symbolic='C = (D - d) / 2', symbol_fraction=None,
                                 numeric='C = (0.669 - 0.667) / 2',
                                 numeric_fraction=None,
                                 result=0.001, unit='in', note='')]
        for metric in ('Squeeze', 'ID stretch', 'Gland fill'):
            for passed in (True, False):
                with self.subTest(metric=metric, passed=passed):
                    check = SimpleNamespace(within_limits=passed,
                                            criterion='Selected screening criterion')
                    html = _html_breakdown(metric, 'Nominal', 12.5,
                                           dimensions, steps, 3, check)
                    document = QTextDocument()
                    document.setHtml(html)
                    text = document.toPlainText()
                    self.assertIn('PASS' if passed else 'REVIEW', text)
                    self.assertIn('Full tolerance-range screening:', text)
                    self.assertLess(text.index('Input Values'),
                                    text.index('Calculation Breakdown'))
                    self.assertIn('Cylinder ID', text)
                    self.assertIn('Calculate clearance', text)
                    self.assertIn('Result:', text)


if __name__=='__main__':unittest.main()
