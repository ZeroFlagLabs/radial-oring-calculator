"""Presentation and version consistency regression checks (no engine changes)."""
from pathlib import Path
from xml.etree import ElementTree as ET
from html import unescape
from src.app_info import APP_VERSION
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
QT = importlib.util.find_spec('PySide6') is not None

class PresentationSourceTests(unittest.TestCase):
    def test_app_version_matches_designer_defaults_and_update_version(self):
        self.assertRegex(APP_VERSION, r'^\d+\.\d+\.\d+$')
        main = ET.parse(ROOT/'src/ui/forms/main_window.ui').getroot()
        settings = ET.parse(ROOT/'src/ui/forms/settings_dialog.ui').getroot()
        self.assertEqual(main.find('.//widget[@name="version_label"]/property[@name="text"]/string').text, 'v' + APP_VERSION)
        self.assertIn('v' + APP_VERSION, settings.find('.//widget[@name="about_text"]/property[@name="text"]/string').text)
        checker=(ROOT/'src/ui/update_checker.py').read_text(encoding='utf8')
        self.assertIn('from src.app_info import APP_TITLE, APP_VERSION',checker)

    def test_assumptions_three_blue_groupings_and_transition_bullets(self):
        root=ET.parse(ROOT/'src/ui/forms/settings_dialog.ui').getroot()
        node=root.find('.//widget[@name="assumptions_text"]')
        self.assertEqual(node.find('./property[@name="textFormat"]/enum').text,'Qt::TextFormat::RichText')
        html=node.find('./property[@name="text"]/string').text
        for header in ('Scope and tolerance evaluation',
                       'Groove geometry and O-ring behaviour',
                       'Screening interpretation and design responsibility'):
            self.assertIn(header,html)
        self.assertEqual(html.count('color:#164f8a'),3)
        self.assertEqual(html.count('• '),8)
        for phrase in ('two-dimensional (2D) representation', 'opening radii',
                       'actual groove opening width','constant-volume model',
                       'PASS indicates','REVIEW indicates','INVALID indicates',
                       'complete seal design approval'):
            self.assertIn(phrase,unescape(html))
        self.assertNotIn('approximation',html.lower())
        self.assertNotIn('entrance radii',html.lower())

    def test_assumptions_section_spacing_matches_reference_presentation(self):
        root=ET.parse(ROOT/'src/ui/forms/settings_dialog.ui').getroot()
        html=root.find('.//widget[@name="assumptions_text"]/property[@name="text"]/string').text
        self.assertEqual(html.count('margin:28px 0 7px 0; color:#164f8a; font-weight:600;'),2)
        self.assertIn('Scope and tolerance evaluation',html)
        self.assertEqual(html.count('• '),8)
        self.assertEqual(html.count('margin:0 0 10px 0;'),8)
        # Both subsequent headings have the larger vertical gap; the initial
        # heading and the individual bullet spacing are preserved.
        self.assertIn('margin:0 0 7px 0; color:#164f8a;',html)
        self.assertEqual(root.find('.//spacer[@name="referencesSectionGap"]/.//height').text,'20')

    def test_references_bullets_use_assumptions_spacing(self):
        root=ET.parse(ROOT/'src/ui/forms/settings_dialog.ui').getroot()
        assumptions=root.find('.//widget[@name="assumptions_text"]/property[@name="text"]/string').text
        self.assertIn('margin:0 0 10px 0;',assumptions)
        for label in ('references_text','criteria_text'):
            node=root.find(f'.//widget[@name="{label}"]')
            self.assertEqual(node.find('./property[@name="textFormat"]/enum').text,'Qt::TextFormat::RichText')
            html=node.find('./property[@name="text"]/string').text
            self.assertEqual(html.count('margin:0 0 10px 0;'),4)
            self.assertEqual(html.count('• '),3)
        self.assertEqual(root.find('.//spacer[@name="referencesSectionGap"]/.//height').text,'20')
        self.assertEqual(root.find('.//spacer[@name="referencesClosingNoteGap"]/.//height').text,'20')
        ending=root.find('.//widget[@name="references_note"]/property[@name="text"]/string').text
        self.assertIn('The reference publications are not distributed with the application.',ending)

    def test_assumptions_explains_three_percent_boundary(self):
        root=ET.parse(ROOT/'src/ui/forms/settings_dialog.ui').getroot()
        html=root.find('.//widget[@name="assumptions_text"]/property[@name="text"]/string').text
        self.assertIn('Piston squeeze additionally checks both sides of the 3% ID-stretch transition',html)
        for phrase in (
            "Parker's published empirical relationships",
            'one equation for 0–3% ID stretch',
            'The equations do not meet exactly at 3%',
            'calculated squeeze can change abruptly',
            'minimum and nominal are identical despite dimensional tolerances',
            'the calculator evaluates both sides of the transition',
        ):
            self.assertIn(phrase,html)
        self.assertEqual(html.count('• '),8)

    def test_updates_native_layout_spacers_preserve_every_control(self):
        root=ET.parse(ROOT/'src/ui/forms/settings_dialog.ui').getroot()
        layout=root.find('.//layout[@name="updatesLayout"]')
        parts=[]
        for item in layout.findall('item'):
            child=next(iter(item))
            parts.append(child.get('name'))
        self.assertEqual(parts,[
            'current_version','updates_version_to_checkbox_gap','check_on_launch',
            'updates_checkbox_to_information_gap','update_information',
            'updates_information_to_status_gap','update_status',
            'updates_status_to_buttons_gap','updateButtonLayout','updatesSpacer'])
        for name,height in (
            ('updates_version_to_checkbox_gap','12'),
            ('updates_checkbox_to_information_gap','12'),
            ('updates_information_to_status_gap','8'),
            ('updates_status_to_buttons_gap','14')):
            sp=layout.find(f'./item/spacer[@name="{name}"]')
            self.assertIsNotNone(sp)
            self.assertEqual(sp.find('./property[@name="sizeType"]/enum').text,'QSizePolicy::Fixed')
            self.assertEqual(sp.find('.//size/height').text,height)
        self.assertEqual(root.find('.//widget[@name="current_version"]/property[@name="text"]/string').text,'Current version:')
        self.assertIn('remains portable',root.find('.//widget[@name="update_information"]/property[@name="text"]/string').text)
        self.assertEqual(root.find('.//widget[@name="check_now_button"]/property[@name="text"]/string').text,'Check for updates')

    def test_about_full_line_gap_and_public_github_link(self):
        root=ET.parse(ROOT/'src/ui/forms/settings_dialog.ui').getroot()
        layout=root.find('.//layout[@name="aboutLayout"]')
        items=layout.findall('item')
        self.assertEqual(items[1].find('./spacer').get('name'),'about_github_section_gap')
        self.assertEqual(items[1].find('.//size/height').text,'16')
        self.assertEqual(items[2].find('./widget').get('name'),'github_link')
        self.assertEqual(root.find('.//widget[@name="github_link"]/property[@name="text"]/string').text, 'Project on GitHub')
        self.assertIn('third-party components retain their own licences',
                      (ROOT/'src/ui/settings_dialog.py').read_text(encoding='utf8'))

@unittest.skipUnless(QT,'PySide6 GUI required')
class PresentationGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def test_settings_visible_text_and_version(self):
        from src.ui.settings_dialog import SettingsDialog
        from src.ui.main_window import MainWindow
        from PySide6.QtWidgets import QLabel
        w=MainWindow()
        try:
            settings=SettingsDialog(w)
            dlg=settings.dialog
            assumptions=dlg.findChild(QLabel,'assumptions_text')
            self.assertIsNotNone(assumptions)
            self.assertIn('color:#164f8a',assumptions.text())
            self.assertIn('opening radii',assumptions.text())
            self.assertIn('v' + APP_VERSION,dlg.findChild(QLabel,'current_version').text())
            dlg.close()
        finally:w.close()

if __name__=='__main__': unittest.main()
