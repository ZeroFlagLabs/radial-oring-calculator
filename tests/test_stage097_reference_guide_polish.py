from gui_sample import seed_sample
"""References/source traceability and square guide image regression tests."""
import importlib.util
import unittest
from pathlib import Path
from struct import unpack
from xml.etree import ElementTree as ET
from src.calculations.criteria import screen_rectangular
from src.calculations.rectangular import Dimension as D, MaleRectangularInputs
from src.calculations.installed import calculate_installed

ROOT=Path(__file__).resolve().parents[1]
GUI=importlib.util.find_spec('PySide6') is not None
NAMES=('piston_rectangular_od','piston_rectangular_depth','piston_dovetail_od',
       'piston_dovetail_depth','cylinder_rectangular_id','cylinder_rectangular_depth',
       'cylinder_dovetail_id','cylinder_dovetail_depth')

class SourceReferenceGuideTests(unittest.TestCase):
    def setUp(self):
        self.ui=ET.parse(ROOT/'src/ui/forms/settings_dialog.ui').getroot()
    def text(self, name):
        return self.ui.find(f'.//widget[@name="{name}"]/property[@name="text"]/string').text
    def test_references_preserve_three_sources_and_locations(self):
        pubs=self.text('references_text')
        for content in ('Parker Hannifin','ORD 5700A/US','Sections 3.5–3.7',
                        'Freudenberg Sealing Technologies','pages 2–4',
                        "James Walker: 'O' Ring Guide, Issue 7",'pages 27–31'):
            self.assertIn(content,pubs)
    def test_displayed_criteria_match_engine_thresholds(self):
        limits=self.text('criteria_text')
        for content in ('0.007″','30%','16%','0–5%','0–2%','60–85%','75%'):
            self.assertIn(content, limits)
        sample=MaleRectangularInputs(rod_od=D(.667),cylinder_id=D(.669),
                     gland_od=D(.503),gland_width=D(.1425),o_ring_id=D(.487),
                     o_ring_section=D(.103),bottom_radius=D(0))
        # The screening names and numeric limits remain supplied by the engine.
        result=calculate_installed(sample)
        self.assertEqual(screen_rectangular(result.results,'static').max_squeeze_percent,30.0)
        self.assertEqual(screen_rectangular(result.results,'dynamic').max_squeeze_percent,16.0)
    def test_references_are_scrollable_not_resized(self):
        self.assertIsNotNone(self.ui.find('.//widget[@name="references_scroll"]'))
        self.assertIsNotNone(self.ui.find('.//widget[@name="references_content"]'))
        note=self.text('references_note')
        self.assertIn('not universal acceptance limits',note)
        self.assertIn('not distributed',note)
        self.assertEqual(self.ui.find('.//widget[@name="settingsDialog"]/property[@name="minimumSize"]/size/width').text,'510')
    def test_all_eight_matched_square_guides(self):
        directory=ROOT/'src/resources/guides'
        self.assertEqual(set(x.stem for x in directory.glob('*.png')),set(NAMES))
        for name in NAMES:
            data=(directory/(name+'.png')).read_bytes()
            self.assertEqual(data[:8],b'\x89PNG\r\n\x1a\n')
            self.assertEqual(unpack('>II',data[16:24]),(1068,1068))

@unittest.skipUnless(GUI, 'PySide6 unavailable')
class GuiReferenceGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])
    def test_references_tab_loads_and_scrolls(self):
        from PySide6.QtWidgets import QLabel,QScrollArea
        from src.ui.settings_dialog import SettingsDialog
        dialog=SettingsDialog(None)
        try:
            self.assertIsNotNone(dialog.dialog.findChild(QScrollArea,'references_scroll'))
            self.assertIn('30%',dialog.dialog.findChild(QLabel,'criteria_text').text())
        finally:dialog.dialog.close()
    def test_eight_guide_images_render(self):
        from PySide6.QtWidgets import QLabel
        from src.ui.main_window import MainWindow
        w=MainWindow();seed_sample(w)
        try:
            picture=w.findChild(QLabel,'guide_picture')
            for c in range(2):
                w.configuration.setCurrentIndex(c)
                for t in range(2):
                    w.groove_type.setCurrentIndex(t)
                    for mode in range(2):
                        (w.female_entry_mode if c else w.entry_mode).setCurrentIndex(mode)
                        self.assertFalse(picture.pixmap().isNull())
                        self.assertLessEqual(picture.pixmap().width(),408)
                        self.assertLessEqual(picture.pixmap().height(),405)
        finally:w.close()

if __name__=='__main__':unittest.main()
