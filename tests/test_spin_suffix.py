from src.ui.main_window import AdaptiveSpinBox

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

if __name__=="__main__": unittest.main()
