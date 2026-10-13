from gui_sample import seed_sample
"""Windows-only UI smoke tests for passive recognition and trace window."""
import importlib.util
import unittest
QT_INSTALLED = importlib.util.find_spec('PySide6') is not None


@unittest.skipUnless(QT_INSTALLED, 'PySide6 is not installed')
class Stage7GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_manual_match_note_does_not_select_or_disable(self):
        from src.ui.main_window import MainWindow
        window=MainWindow();seed_sample(window)
        try:
            self.assertIsNone(window.ring_size.currentData())
            for key, nom, tol in (('ring_id', .487, .005), ('section', .103, .003)):
                row = window.rows[key]
                row.nominal.setValue(nom)
                row.tolerance.setValue(tol)
            window._recalculate()
            self.assertIn('AS568-112', window.match_note.text())
            self.assertFalse(window.match_note.isHidden())
            self.assertIsNone(window.ring_size.currentData())
            self.assertTrue(window.rows['ring_id'].nominal.isEnabled())
            self.assertTrue(window.rows['section'].tolerance.isEnabled())
            window.rows['ring_id'].tolerance.setValue(.006)
            window._recalculate()
            self.assertTrue(window.match_note.isHidden())
        finally:
            window.close()

    def test_catalogue_selected_then_manual_retains_values_and_notes(self):
        from src.ui.main_window import MainWindow
        window=MainWindow();seed_sample(window)
        try:
            i=window.ring_size.findData('-112')
            window.ring_size.setCurrentIndex(i)
            self.assertTrue(window.match_note.isHidden())
            self.assertFalse(window.rows['ring_id'].nominal.isEnabled())
            window.ring_size.setCurrentIndex(0)
            self.assertTrue(window.rows['ring_id'].nominal.isEnabled())
            self.assertAlmostEqual(window.rows['ring_id'].nominal.value(),.487)
            self.assertIn('AS568-112',window.match_note.text())
        finally:
            window.close()

    def test_stage7_witness_button_enabled_on_valid_result(self):
        from src.ui.main_window import MainWindow
        window=MainWindow();seed_sample(window)
        try:
            self.assertTrue(window.trace_button.isEnabled())
            self.assertIsNotNone(window._last_inputs)
            self.assertEqual(len(window._last_result.gland_fill_percent.__dict__),3)
        finally:
            window.close()


if __name__ == '__main__':
    unittest.main()
