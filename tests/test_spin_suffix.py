from src.ui.main_window import AdaptiveSpinBox, MainWindow
from src.ui.spin_suffix import protect_suffix

import unittest
from PySide6.QtCore import Qt, QPoint
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDoubleSpinBox

class SuffixSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def test_numeric_selection(self):
        for spin,value,replacement in self.make_spins():
            with self.subTest(type=type(spin).__name__,suffix=spin.suffix()):
                protect_suffix(spin)
                spin.show()
                spin.activateWindow()
                spin.setValue(value)
                spin.setFocus()
                self.app.processEvents()
                edit=spin.lineEdit()
                numeric=spin.textFromValue(spin.value())
                self.assertTrue(spin.suffix())
                self.assertEqual(edit.text(),numeric+spin.suffix())
                edit.selectAll()
                self.assertEqual(edit.selectedText(),numeric)
                QTest.keyClick(edit,Qt.Key.Key_A,Qt.KeyboardModifier.ControlModifier)
                self.assertEqual(edit.selectedText(),numeric)
                edit.setCursorPosition(0)
                QTest.keyClick(edit,Qt.Key.Key_End,Qt.KeyboardModifier.ShiftModifier)
                self.assertEqual(edit.selectedText(),numeric)
                edit.setSelection(len(edit.text()),-len(edit.text()))
                self.assertEqual(edit.selectedText(),numeric)
                edit.setCursorPosition(len(edit.text()))
                self.assertEqual(edit.cursorPosition(),len(numeric))
                # Mouse drag from the first glyph through the suffix.
                edit.setCursorPosition(0)
                QTest.mousePress(edit,Qt.MouseButton.LeftButton,pos=QPoint(2,edit.height()//2))
                QTest.mouseMove(edit,QPoint(edit.width()-2,edit.height()//2))
                QTest.mouseRelease(edit,Qt.MouseButton.LeftButton,pos=QPoint(edit.width()-2,edit.height()//2))
                self.assertNotIn(spin.suffix().strip(),edit.selectedText())
                QTest.keyClick(edit,Qt.Key.Key_A,Qt.KeyboardModifier.ControlModifier)
                QTest.keyClicks(edit,replacement)
                QTest.keyClick(edit,Qt.Key.Key_Return)
                self.assertAlmostEqual(spin.value(),float(replacement))
                self.assertTrue(edit.text().endswith(spin.suffix()))
                spin.close()

    def make_spins(self):
        a=AdaptiveSpinBox(); a.setRange(-10000,10000); a.setDecimals(12); a.setSuffix(" in")
        a.resize(130,30)
        b=AdaptiveSpinBox(); b.setRange(-180,180); b.setDecimals(6); b.setSuffix("°"); b.resize(130,30)
        return [(a,6.125,"1.2345"),(b,-5,"-3.5")]



class DesignerSuffixSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.w=MainWindow()
        self.w.show()
        self.w.activateWindow()
        self.app.processEvents()
        self.addCleanup(self.w.close)

    def test_all_designer_fields(self):
        spins=[s for rows in (self.w.rows,self.w.female_rows,self.w.shared_rows)
               for row in rows.values() for s in
               (row.nominal,row.tolerance,row.limit_min,row.limit_max)]
        self.assertEqual(len(spins),68)
        for s in spins:
            with self.subTest(field=s.objectName()):
                e=s.lineEdit(); text=e.text(); suffix=s.suffix()
                self.assertTrue(suffix and text.endswith(suffix))
                n=text[:-len(suffix)]
                e.deselect(); e.selectAll()
                self.assertEqual(e.selectedText(),n)
                e.setCursorPosition(len(text))
                self.assertEqual(e.cursorPosition(),len(n))
                e.setSelection(len(n),len(suffix))
                self.assertEqual(e.selectedText(),"")
                self.assertEqual(e.cursorPosition(),len(n))
                e.setSelection(len(text),-len(text))
                self.assertEqual(e.selectedText(),n)
                e.deselect()

    def exercise_visible(self,s,value,replacement):
        self.assertTrue(s.isVisible() and s.isEnabled(),s.objectName())
        s.setValue(value); s.setFocus(); self.app.processEvents()
        e=s.lineEdit(); suffix=s.suffix(); text=e.text()
        n=text[:-len(suffix)]
        self.assertTrue(text.endswith(suffix))
        QTest.keyClick(e,Qt.Key.Key_A,Qt.KeyboardModifier.ControlModifier)
        self.assertEqual(e.selectedText(),n)
        # Clicking to the right of the number places the caret before the unit.
        QTest.mouseClick(e,Qt.MouseButton.LeftButton,pos=QPoint(e.width()-3,e.height()//2))
        self.assertEqual(e.cursorPosition(),len(n))
        self.assertEqual(e.selectedText(),"")
        QTest.keyClick(e,Qt.Key.Key_Delete)
        self.assertEqual(e.text(),text)
        # Every suffix-only selection is empty; Delete cannot corrupt the unit.
        for start in range(len(n),len(text)):
            for length in range(1,len(text)-start+1):
                e.setSelection(start,length)
                self.assertEqual(e.selectedText(),"")
                QTest.keyClick(e,Qt.Key.Key_Delete)
                self.assertEqual(e.text(),text)
        for x1,x2 in ((2,e.width()-2),(e.width()-2,2)):
            e.deselect(); y=e.height()//2
            QTest.mousePress(e,Qt.MouseButton.LeftButton,pos=QPoint(x1,y))
            QTest.mouseMove(e,QPoint(x2,y))
            QTest.mouseRelease(e,Qt.MouseButton.LeftButton,pos=QPoint(x2,y))
            self.assertEqual(e.selectedText(),n)
        QTest.mouseClick(e,Qt.MouseButton.LeftButton,pos=QPoint(3,e.height()//2))
        self.assertEqual(e.cursorPosition(),0)
        QTest.keyClick(e,Qt.Key.Key_A,Qt.KeyboardModifier.ControlModifier)
        QTest.keyClicks(e,replacement)
        QTest.keyClick(e,Qt.Key.Key_Return)
        self.assertTrue(e.text().endswith(suffix))
        self.assertAlmostEqual(s.value(),float(replacement))

    def test_live_mouse_keyboard_and_partial_delete(self):
        r=self.w.shared_rows["width"]
        self.exercise_visible(r.nominal,1.234,"0.125")
        self.exercise_visible(r.tolerance,.003,"0.002")
        r.mode_limits.click(); self.app.processEvents()
        self.exercise_visible(r.limit_min,.122,"0.121")
        self.exercise_visible(r.limit_max,.128,"0.129")
        r=self.w.shared_rows["rect_angle"]
        self.exercise_visible(r.nominal,-1.5,"-1.2")

if __name__=="__main__": unittest.main()
