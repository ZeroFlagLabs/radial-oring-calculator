"""Regression coverage for units as separate, display-only labels."""
import unittest
from PySide6.QtCore import Qt,QPoint
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.ui.spin_suffix import unit_suffix

class InlineUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.w=MainWindow()
        self.w.show()
        self.w.activateWindow()
        self.app.processEvents()
        self.addCleanup(self.w.close)

    def fields(self):
        return [s for rows in (self.w.rows,self.w.female_rows,self.w.shared_rows)
                for row in rows.values() for s in
                (row.nominal,row.tolerance,row.limit_min,row.limit_max)]

    def test_all_68_units_outside_native_editor(self):
        fields=self.fields()
        self.assertEqual(len(fields),68)
        for s in fields:
            with self.subTest(field=s.objectName()):
                e=s.lineEdit(); unit=s._inline_unit
                self.assertIn(unit_suffix(s),(" in"," deg"))
                self.assertEqual(s.suffix(),"")
                self.assertEqual(unit.label.text(),unit_suffix(s))
                self.assertTrue(unit.label.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents))
                self.assertEqual(unit.label.textInteractionFlags(),Qt.TextInteractionFlag.NoTextInteraction)
                self.assertNotIn(unit_suffix(s).strip(),e.text())
                e.selectAll()
                self.assertEqual(e.selectedText(),e.text())
                e.deselect()

    def exercise_first_click(self,s):
        # No setValue or setFocus on the target: real first click of an untouched editor.
        self.w.configuration.setFocus()
        self.app.processEvents()
        e=s.lineEdit()
        unit=s._inline_unit
        original=e.text()
        suffix=unit.label.text()
        label_rect=unit.label.geometry()
        self.assertTrue(unit.label.isVisible())
        self.assertFalse(s.hasFocus())
        # Both direct unit hit and blank region to its right.
        for x in (label_rect.center().x(),e.width()-3):
            self.w.configuration.setFocus();self.app.processEvents()
            QTest.mouseClick(e,Qt.MouseButton.LeftButton,pos=QPoint(x,e.height()//2))
            self.assertEqual(e.cursorPosition(),len(original),(s.objectName(),x,original,e.cursorPosition()))
            self.assertEqual(e.selectedText(),"")
            QTest.keyClick(e,Qt.Key.Key_Delete)
            self.assertEqual(e.text(),original)
            self.assertEqual(unit.label.text(),suffix)
        QTest.keyClick(e,Qt.Key.Key_Backspace)
        self.assertEqual(e.text(),original[:-1])
        self.assertEqual(unit.label.text(),suffix)
        # Restore through real numeric editing, then test both selection directions.
        QTest.keyClick(e,Qt.Key.Key_A,Qt.KeyboardModifier.ControlModifier)
        QTest.keyClicks(e,original)
        QTest.keyClick(e,Qt.Key.Key_Return)
        self.app.processEvents()
        text=e.text()
        for x1,x2 in ((2,e.width()-3),(e.width()-3,2)):
            e.deselect()
            y=e.height()//2
            QTest.mousePress(e,Qt.MouseButton.LeftButton,pos=QPoint(x1,y))
            QTest.mouseMove(e,QPoint(x2,y))
            QTest.mouseRelease(e,Qt.MouseButton.LeftButton,pos=QPoint(x2,y))
            self.assertEqual(e.selectedText(),text)
        QTest.keyClick(e,Qt.Key.Key_C,Qt.KeyboardModifier.ControlModifier)
        self.assertEqual(self.app.clipboard().text(),text)
        self.assertEqual(unit.label.text(),suffix)
        e.deselect()

    def test_first_click_all_visible_field_families_and_modes(self):
        w=self.w
        seen=set()
        for female in (0,1):
            w.configuration.setCurrentIndex(female)
            for groove in (0,1):
                w.groove_type.setCurrentIndex(groove)
                for depth in (0,1):
                    (w.female_entry_mode if female else w.entry_mode).setCurrentIndex(depth)
                    w._reset_dimensions()
                    self.app.processEvents()
                    for limits in (False,True):
                        for rows in (w.rows,w.female_rows,w.shared_rows):
                            for row in rows.values():
                                if row.nominal.isVisible() or row.limit_min.isVisible():
                                    (row.mode_limits if limits else row.mode_sym).click()
                        self.app.processEvents()
                        for s in self.fields():
                            if s.isVisible() and s.isEnabled() and s.objectName() not in seen:
                                with self.subTest(field=s.objectName()):
                                    self.exercise_first_click(s)
                                    seen.add(s.objectName())
        self.assertEqual(len(seen),68,sorted(set(s.objectName() for s in self.fields())-seen))

    def test_signed_and_precise_values(self):
        w=self.w
        for key,value,replacement in (("rect_angle",-1.5,"-1.25"),("width",.141001,"0.148500")):
            r=w.shared_rows[key]
            for s in (r.nominal,r.limit_min):
                (r.mode_limits if s is r.limit_min else r.mode_sym).click()
                s.setValue(value)
                self.app.processEvents()
                e=s.lineEdit();unit=s._inline_unit
                self.assertEqual(e.text(),s.textFromValue(s.value()))
                w.configuration.setFocus();self.app.processEvents()
                QTest.mouseClick(e,Qt.MouseButton.LeftButton,pos=unit.label.geometry().center())
                self.assertEqual(e.cursorPosition(),len(e.text()))
                QTest.keyClick(e,Qt.Key.Key_A,Qt.KeyboardModifier.ControlModifier)
                QTest.keyClicks(e,replacement)
                QTest.keyClick(e,Qt.Key.Key_Return)
                self.app.processEvents()
                self.assertAlmostEqual(s.value(),float(replacement))
                self.assertEqual(unit.label.text(),unit_suffix(s))

if __name__=="__main__":unittest.main()
