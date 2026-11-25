"""Native Windows regression for stationary fitting inline units.

Run separately from the offscreen calculation/UI suite, on the real desktop.
"""
import sys,os
from pathlib import Path
os.environ["QT_QPA_PLATFORM"]="windows"
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication,QStyle,QStyleOptionFrame
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt,QPoint
from src.ui.main_window import MainWindow
from src.ui.update_checker import UpdateChecker
UpdateChecker.check_on_launch=lambda *a:None
app=QApplication([])
w=MainWindow();w.show();w.activateWindow();QTest.qWait(100)
seen=set()
for female in (0,1):
    w.configuration.setCurrentIndex(female)
    for groove in (0,1):
        w.groove_type.setCurrentIndex(groove)
        for depth in (0,1):
            (w.female_entry_mode if female else w.entry_mode).setCurrentIndex(depth)
            w._reset_dimensions();QTest.qWait(20)
            rows=[row for group in (w.rows,w.female_rows,w.shared_rows) for row in group.values()]
            for limits in (False,True):
                for row in rows:
                    if row.nominal.isVisible() or row.limit_min.isVisible():
                        (row.mode_limits if limits else row.mode_sym).click()
                QTest.qWait(20)
                for row in rows:
                    for s in (row.nominal,row.tolerance,row.limit_min,row.limit_max):
                        if not s.isVisible() or not s.isEnabled() or s.objectName() in seen:continue
                        e=s.lineEdit();u=s._inline_unit
                        for v in (0,.625,6.125,1.234567):
                            s.setValue(v)
                            if not s.isEnabled():continue
                            w.configuration.setFocus();QTest.qWait(10)
                            u.update()
                            opt=QStyleOptionFrame();e.initStyleOption(opt)
                            area=e.style().subElementRect(QStyle.SubElement.SE_LineEditContents,opt,e)
                            # Long text in Limits fields has less clearance due to Min/Max overlays.
                            if e.fontMetrics().horizontalAdvance(e.text())+e.textMargins().left()+e.textMargins().right()+4>area.width():continue
                            start=u.label.mapTo(s,QPoint())
                            geom=e.geometry(); original=e.text(); before_margin=e.textMargins()
                            for pos in (0,len(e.text())//2,len(e.text())):
                                e.setCursorPosition(pos);QTest.qWait(5)
                                assert u.label.mapTo(s,QPoint())==start,(s.objectName(),v,pos,start,u.label.pos())
                            QTest.mouseClick(e,Qt.MouseButton.LeftButton,pos=QPoint(8,e.height()//2));QTest.qWait(10)
                            assert s.hasFocus(),s.objectName()
                            assert u.label.mapTo(s,QPoint())==start,(s.objectName(),v,start,u.label.pos(), original,e.text(),geom,e.geometry(),before_margin,e.textMargins())
                            assert e.geometry()==geom
                            w.configuration.setFocus();QTest.qWait(10)
                            assert u.label.mapTo(s,QPoint())==start
                        s.setValue(0)
                        seen.add(s.objectName())
assert len(seen)==68,len(seen)
w.close()
print("PASS: 68 fields, zero/nonzero/precision, cursor and focus positions, native Windows renderer")
