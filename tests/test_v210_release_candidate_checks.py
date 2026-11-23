"""v2.1.0 regression checks for tooltips, report integrity and input precision."""
import hashlib
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from xml.etree import ElementTree as ET

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QDoubleSpinBox, QWidget
from src.ui.main_window import MainWindow
from src.ui.snapshot_view import save_snapshot_to_png, REPORT_WIDTH, REPORT_HEIGHT
from gui_sample import seed_sample


ROOT=Path(__file__).resolve().parents[1]


class V210ReleaseCandidateChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def build_window(self):
        w=MainWindow()
        seed_sample(w)
        w.show()
        self.app.processEvents()
        self.addCleanup(w.close)
        return w

    def test_all_68_tooltips_are_truthful_and_no_preview_language_remains(self):
        ui=(ROOT/'src/ui/forms/main_window.ui').read_text(encoding='utf-8')
        self.assertNotIn('v2.1 UI preview',ui)
        self.assertNotIn('visual preview; not calculated yet',ui)
        tree=ET.fromstring(ui)
        widgets={v.get('name'):v for v in tree.iter('widget') if v.get('name')}
        w=self.build_window()
        for row in (r for g in (w.rows,w.female_rows,w.shared_rows)
                    for r in g.values()):
            base=row.nominal.objectName().removeprefix('spin_').removesuffix('_nom')
            for kind in ('sym','limits'):
                name='mode_'+base+'_'+kind
                widget=w.findChild(QPushButton,name)
                text=widget.toolTip()
                self.assertTrue(text,name)
                self.assertNotIn('preview',text.lower())
                self.assertNotIn('not used',text.lower())
                if kind=='limits':
                    self.assertIn('midpoint',text.lower())
                else:
                    self.assertIn('symmetrical',text.lower())
                self.assertIsNotNone(widgets[name])
            for kind in ('min','max'):
                name='limit_'+base+'_'+kind
                widget=w.findChild(QDoubleSpinBox,name)
                self.assertTrue(widget.toolTip())
                self.assertNotIn('preview',widget.toolTip().lower())
                self.assertIn('permitted dimension',widget.toolTip())
        self.assertEqual(w.width(),1080)
        # Native Windows is 801px; Qt's offscreen renderer uses 784px.
        self.assertIn(w.height(),(784,801))

    def test_limits_endpoints_are_preserved_to_six_place_input_resolution(self):
        w=self.build_window()
        row=w.shared_rows['width']
        row.mode_limits.click()
        row.limit_min.setValue(.141001)
        row.limit_max.setValue(.148500)
        self.app.processEvents()
        d=row.dimension()
        self.assertAlmostEqual(d.minimum,.141001,delta=1e-12)
        self.assertAlmostEqual(d.maximum,.148500,delta=1e-12)
        self.assertAlmostEqual(d.nominal,.1447505,delta=1e-12)
        self.assertAlmostEqual(d.tolerance,.0037495,delta=1e-12)
        self.assertIsNotNone(w._last_result)
        self.assertTrue(w.save_snapshot_button.isEnabled())
        row.limit_max.setValue(.141001)
        self.app.processEvents()
        self.assertAlmostEqual(row.dimension().tolerance,0,delta=1e-12)
        self.assertIsNotNone(w._last_result)
        # A reversed interval must never produce a PASS or an export.
        row.limit_min.setValue(.141002)
        self.app.processEvents()
        self.assertIsNone(w._last_result)
        self.assertFalse(w.snapshot_button.isEnabled())
        self.assertFalse(w.save_snapshot_button.isEnabled())
        self.assertIn('Invalid limits',w.statusBar().currentMessage())
        row.limit_max.setValue(.148500)
        self.app.processEvents()
        self.assertIsNotNone(w._last_result)

    def test_png_and_clipboard_use_unchanged_symmetric_report_layout(self):
        local=ROOT/'src/ui/snapshot_view.py'
        previous_v201_sha256='fe89c58f1b131649aa7a112d07fd28ff328d693c50f2f32026ed4c877342202a'
        self.assertEqual(hashlib.sha256(local.read_bytes()).hexdigest(),
                         previous_v201_sha256,
                         'The existing snapshot renderer must remain byte-for-byte unchanged')
        w=self.build_window()
        old=dict(w._capture_inputs())
        row=w.shared_rows['width']
        row.mode_limits.click()
        row.limit_min.setValue(.141)
        row.limit_max.setValue(.1485)
        self.app.processEvents()
        current=dict(w._capture_inputs())
        self.assertEqual(current['Groove width (in)'],
                         '0.14475 '+chr(177)+' 0.00375')
        self.assertEqual(old['Cylinder ID (in)'],current['Cylinder ID (in)'])
        self.assertEqual(old['Piston OD (in)'],current['Piston OD (in)'])
        self.assertEqual(len(current),9)
        report=w._snapshot_pixmap()
        self.assertIsNotNone(report)
        self.assertEqual((report.width(),report.height()),
                         (REPORT_WIDTH,REPORT_HEIGHT))
        with TemporaryDirectory() as temp:
            path=Path(temp)/'validate_snapshot.png'
            save_snapshot_to_png(report,str(path))
            self.assertTrue(path.is_file())
            self.assertGreater(path.stat().st_size,10000)
            with path.open('rb') as f:
                self.assertEqual(f.read(8),bytes.fromhex('89504e470d0a1a0a'))
        w._copy_snapshot()
        clipboard=QApplication.clipboard().pixmap()
        self.assertFalse(clipboard.isNull())
        self.assertEqual((clipboard.width(),clipboard.height()),
                         (REPORT_WIDTH,REPORT_HEIGHT))
        self.assertIsNotNone(w._make_tolerance_trace_dialog())
        self.assertTrue(w.trace_button.isEnabled())
        self.assertTrue(w.snapshot_button.isEnabled())
        self.assertTrue(w.save_snapshot_button.isEnabled())

    def test_as568_disabled_entry_still_reports_catalogue_endpoints_and_copies(self):
        w=self.build_window()
        dash=w.ring_size.findData('-113')
        self.assertGreater(dash,0)
        w.ring_size.setCurrentIndex(dash)
        size=next(s for s in w.as568_sizes if s.dash=='-113')
        for key,nom,tol in (('ring_id',size.id_in,size.id_tol_in),
                            ('section',size.cs_in,size.cs_tol_in)):
            row=w.rows[key]
            row.mode_limits.click()
            self.app.processEvents()
            self.assertFalse(row.limit_min.isEnabled())
            self.assertFalse(row.limit_max.isEnabled())
            self.assertTrue(row.mode_limits.isEnabled())
            self.assertAlmostEqual(row.dimension().minimum,nom-tol)
            self.assertAlmostEqual(row.dimension().maximum,nom+tol)
            self.assertAlmostEqual(row.dimension().nominal,nom)
        self.assertIsNotNone(w._last_result)
        self.assertIsNotNone(w._snapshot_pixmap())
        # A new designation must refresh the displayed endpoints without
        # making the disabled fields accidentally editable.
        idx=w.ring_size.findData('-114')
        self.assertGreater(idx,0)
        w.ring_size.setCurrentIndex(idx)
        self.app.processEvents()
        for key in ('ring_id','section'):
            row=w.rows[key]
            self.assertTrue(row.limit_mode)
            self.assertFalse(row.limit_min.isEnabled())
            self.assertFalse(row.limit_max.isEnabled())
        self.assertIsNotNone(w._last_result)


if __name__=='__main__':
    unittest.main()
