"""Eight reference drawings and single-purpose source citation contracts."""
from pathlib import Path
import unittest
from struct import unpack
ROOT=Path(__file__).resolve().parents[1]
class GuideSourceTests(unittest.TestCase):
    def test_all_eight_guide_assets(self):
        d=ROOT/'src/resources/guides'
        names=('piston_rectangular_od','piston_rectangular_depth',
               'piston_dovetail_od','piston_dovetail_depth',
               'cylinder_rectangular_id','cylinder_rectangular_depth',
               'cylinder_dovetail_id','cylinder_dovetail_depth')
        self.assertEqual(sorted(x.stem for x in d.glob('*.png')),sorted(names))
        for name in names:
            binary=(d/(name+'.png')).read_bytes()
            self.assertEqual(binary[:8],b'\x89PNG\r\n\x1a\n')
            width,height=unpack('>II',binary[16:24])
            self.assertGreater(width,700)
            self.assertGreater(height,500)
        source=(ROOT/'src/ui/main_window.py').read_text(encoding='utf-8')
        for name in names:self.assertIn(name+'.png',source)
        self.assertNotIn("title.setText('TBC')",source)
    def test_precision_footer_and_targeted_source_citation(self):
        source=(ROOT/'src/ui/inspect_results.py').read_text(encoding='utf-8')
        self.assertIn("step.title == 'Installed-section reduction'",source)
        self.assertIn('Fig. 3-3, p. 3-7',source)
        self.assertIn("get(QLabel,'trace_disclaimer')",source)
        self.assertIn("get(QLabel,'geometry_note')",source)
