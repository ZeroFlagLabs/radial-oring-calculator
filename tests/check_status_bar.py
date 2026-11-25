"""Native Windows status bar appearance regression."""
import sys
from pathlib import Path
from PySide6.QtCore import QPoint
from PySide6.QtGui import QFontInfo,QPalette
from PySide6.QtWidgets import QApplication,QStatusBar
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
sys.path.insert(0,str(root/'src'))
from src.ui.main_window import MainWindow
app=QApplication([])
w=MainWindow();w.show();app.processEvents()
bar=w.statusBar();bar.showMessage("Status bar reference");app.processEvents()
font=QFontInfo(bar.font())
assert (font.family(),font.pointSize(),font.bold())==("Segoe UI",9,False)
assert bar.height()==21 and bar.width()==w.width()
assert bar.mapTo(w,QPoint()).y()+bar.height()==w.height()
assert not bar.isSizeGripEnabled()
assert bar.palette().color(QPalette.ColorRole.WindowText).name()=="#243d58"
assert bar.palette().color(QPalette.ColorRole.Window).name()=="#f0f0f0"
im=bar.grab().toImage()
assert im.pixelColor(im.width()-15,im.height()//2).name()=="#f0f0f0"
assert w.findChildren(QStatusBar)==[bar]
print("Native status bar PASS",w.size().toTuple(),bar.size().toTuple())
w.close()
