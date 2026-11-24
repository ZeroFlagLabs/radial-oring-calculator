"""Keyboard navigation must preserve dimension order with mixed tolerance inputs."""
import unittest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDoubleSpinBox
from src.ui.main_window import MainWindow


class MixedToleranceTabOrderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.w = MainWindow()
        self.w.show()
        self.app.processEvents()
        self.addCleanup(self.w.close)

    def active_rows(self, female, depth, dovetail):
        w = self.w
        if female:
            rows = [w.female_rows[key] for key in (
                'cylinder_id' if depth else 'direct_cylinder_id', 'rod_od',
                'groove_depth' if depth else 'gland_id')]
        else:
            rows = [w.rows[key] for key in (
                'cylinder_id', 'rod_od' if depth else 'direct_rod_od',
                'groove_depth' if depth else 'gland_od')]
        rows += [w.shared_rows[key] for key in (
            'width', 'radius', 'entrance_radius',
            'angle' if dovetail else 'rect_angle')]
        return rows + [w.rows['ring_id'], w.rows['section']]

    def focused(self):
        focus = self.app.focusWidget()
        if focus is not None and isinstance(focus.parentWidget(), QDoubleSpinBox):
            focus = focus.parentWidget()
        return focus

    def verify_cycle(self, rows, female, label):
        w = self.w
        expected = [w.calculation_method, w.application, w.configuration,
                    w.groove_type,
                    w.female_entry_mode if female else w.entry_mode,
                    w.ring_size, w.guide_button]
        for row in rows:
            pair = (row.limit_min, row.limit_max) if row.limit_mode else (
                row.nominal, row.tolerance)
            expected.extend(editor for editor in pair if editor.isEnabled())
        expected[0].setFocus()
        self.app.processEvents()
        for reverse in (False, True):
            targets = ([expected[0]] + list(reversed(expected[1:])) + [expected[0]]
                       if reverse else expected + [expected[0]])
            for i, target in enumerate(targets):
                focus = self.focused()
                self.assertIs(focus, target, (label, reverse, i,
                    focus.objectName() if focus else None, target.objectName()))
                if i != len(targets)-1:
                    QTest.keyClick(self.app.focusWidget(),
                                   Qt.Key.Key_Backtab if reverse else Qt.Key.Key_Tab,
                                   Qt.KeyboardModifier.ShiftModifier if reverse else Qt.KeyboardModifier.NoModifier)
                    self.app.processEvents()

    def test_all_geometries_and_mixed_modes_bidirectionally(self):
        w = self.w
        for female in (0, 1):
            w.configuration.setCurrentIndex(female)
            for dovetail in (0, 1):
                w.groove_type.setCurrentIndex(dovetail)
                for depth in (0, 1, 0):
                    (w.female_entry_mode if female else w.entry_mode).setCurrentIndex(depth)
                    w.ring_size.setCurrentIndex(0)
                    rows = self.active_rows(female, depth, dovetail)
                    # All symmetrical, all limits, alternating, and each
                    # individual row in limits while the others use +/-.
                    masks = [0, 511, 0b101010101, 0b010101010] + [1 << i for i in range(9)]
                    for mask in masks:
                        for i, row in enumerate(rows):
                            desired = bool(mask & (1 << i))
                            if desired != row.limit_mode:
                                (row.mode_limits if desired else row.mode_sym).click()
                            self.assertEqual(row.limit_mode, desired)
                        self.app.processEvents()
                        self.verify_cycle(rows, female, (female, dovetail, depth, mask))
                    # Locked catalogue dimensions must not become tab stops,
                    # even if their visible representation is Min/Max.
                    for row in rows[-2:]:
                        row.mode_limits.click()
                    w.ring_size.setCurrentIndex(1)
                    self.app.processEvents()
                    self.verify_cycle(rows, female, ('catalogue', female, dovetail, depth))
                    w._reset_dimensions()
                    self.app.processEvents()
                    self.assertTrue(all(not row.limit_mode for row in rows))
                    self.verify_cycle(rows, female, ('reset', female, dovetail, depth))
