from gui_sample import seed_sample
"""Stage 9.1 Windows GUI-only checks for the compact usability refinement."""
import importlib.util
import unittest

QT_INSTALLED = importlib.util.find_spec('PySide6') is not None


@unittest.skipUnless(QT_INSTALLED, 'PySide6 unavailable')
class Stage91GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_setup_order_and_uniform_columns(self):
        from src.ui.main_window import MainWindow
        w=MainWindow();seed_sample(w)
        try:
            self.assertEqual(w.windowTitle(), 'Static & Dynamic Radial O-Ring Calculator')
            self.assertEqual(w.application.currentData(), 'static')
            self.assertEqual(w.configuration.currentData(), 'male')
            self.assertEqual(w.ring_size.currentData(), None)
            self.assertEqual(w.entry_mode_stack.currentWidget(), w.entry_mode)
            self.assertTrue(w.guide_button.isEnabled())
            self.assertFalse(hasattr(w, 'overall_status'))
            self.assertTrue(w.guide_placeholder.isEnabled())
        finally:
            w.close()

    def test_spinners_ignore_wheel_but_keep_step_buttons(self):
        from src.ui.main_window import MainWindow
        from PySide6.QtCore import Qt, QPoint, QPointF
        from PySide6.QtGui import QWheelEvent
        w=MainWindow();seed_sample(w)
        try:
            dimension = w.shared_rows['width'].nominal
            before = dimension.value()
            event = QWheelEvent(QPointF(5, 5), QPointF(5, 5), QPoint(0, 0),
                                QPoint(0, 120), Qt.MouseButton.NoButton,
                                Qt.KeyboardModifier.NoModifier,
                                Qt.ScrollPhase.ScrollUpdate, False)
            dimension.wheelEvent(event)
            self.assertAlmostEqual(dimension.value(), before)
            self.assertFalse(event.isAccepted())
            dimension.stepUp()
            self.assertAlmostEqual(dimension.value(), before + 0.001)
            self.assertAlmostEqual(w.shared_rows['rect_angle'].nominal.singleStep(), 0.1)
        finally:
            w.close()

    def test_catalogue_note_is_stable_and_locked_fields_are_styled(self):
        from src.ui.main_window import MainWindow
        w=MainWindow();seed_sample(w)
        try:
            note_height = w.match_slot.height()
            self.assertFalse(hasattr(w, "size_note"))
            self.assertTrue(w.match_note.isHidden())
            w.ring_size.setCurrentIndex(1)
            self.assertTrue(w.match_note.isHidden())
            self.assertFalse(w.rows['ring_id'].nominal.isEnabled())
            self.assertFalse(w.rows['section'].tolerance.isEnabled())
            self.assertEqual(w.match_slot.height(), note_height)
            self.assertIn('QDoubleSpinBox:disabled', w.styleSheet())
            w.ring_size.setCurrentIndex(0)
            self.assertTrue(w.rows['ring_id'].nominal.isEnabled())
            self.assertFalse(w.match_note.isHidden())
            self.assertEqual(w.match_slot.height(), note_height)
            w.rows['ring_id'].tolerance.setValue(0.006)
            w._recalculate()
            self.assertTrue(w.match_note.isHidden())
            self.assertEqual(w.match_slot.height(), note_height)
        finally:
            w.close()

    def test_detailed_geometry_values_are_centred(self):
        from src.ui.main_window import MainWindow
        from PySide6.QtCore import Qt
        w=MainWindow();seed_sample(w)
        try:
            from PySide6.QtWidgets import QTableWidget
            inspector=w._make_tolerance_trace_dialog()
            table=inspector.findChild(QTableWidget,'geometry_table')
            self.assertEqual(table.item(1,1).textAlignment(), Qt.AlignmentFlag.AlignCenter)
            self.assertEqual(table.item(table.rowCount()-1,3).textAlignment(), Qt.AlignmentFlag.AlignCenter)
            self.assertIsNotNone(w._last_result)
            inspector.close()
        finally:
            w.close()

    def test_automatic_input_precision_kept(self):
        from src.ui.main_window import MainWindow
        w=MainWindow();seed_sample(w)
        try:
            self.assertEqual(w.rows['section'].nominal.textFromValue(.103), '0.103')
            self.assertEqual(w.female_rows['groove_depth'].tolerance.textFromValue(.00025), '0.00025')
            self.assertEqual(w.shared_rows['rect_angle'].nominal.textFromValue(1.0), '1.0')
        finally:
            w.close()

if __name__ == '__main__':
    unittest.main()
