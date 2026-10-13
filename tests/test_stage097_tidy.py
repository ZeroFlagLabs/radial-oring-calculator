from gui_sample import seed_sample
"""v0.9.7 main-window tidy: cosmetic labels, note and gap behaviour."""
from pathlib import Path
import unittest, importlib.util
ROOT=Path(__file__).resolve().parents[1]
QT=importlib.util.find_spec('PySide6') is not None

class TidySourceTests(unittest.TestCase):
    def test_no_calculation_changes_and_visible_wording(self):
        s=(ROOT/'src/ui/main_window.py').read_text(encoding='utf-8')
        self.assertIn("'O-ring squeeze'",s)
        self.assertIn("'O-ring ID stretch'",s)
        self.assertIn("'O-ring OD interference'",s)
        self.assertIn('note_font.setPixelSize(10)',s)
        self.assertIn('note_font.setStretch(88)',s)
        self.assertIn('self._root_layout.setAlignment(content, Qt.AlignmentFlag.AlignTop)',s)
        self.assertNotIn('max(680, minimum.height()',s)
        self.assertIn("'Gland fill'",s)

@unittest.skipUnless(QT,'Requires Windows PySide6')
class TidyGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])
    def test_screening_names_and_female_mode(self):
        from src.ui.main_window import MainWindow
        w=MainWindow();seed_sample(w);w.show()
        try:
            self.app.processEvents()
            self.assertIn('O-ring squeeze',w.overview_cells[('Squeeze',0)].text())
            self.assertIn('O-ring ID stretch',w.overview_cells[('Fit',0)].text())
            self.assertIn('Gland fill',w.overview_cells[('Gland fill',0)].text())
            self.assertEqual(w.shared_note.font().pixelSize(),10)
            w.configuration.setCurrentIndex(1);self.app.processEvents()
            self.assertIn('O-ring OD interference',w.overview_cells[('Fit',0)].text())
        finally:w.close()
