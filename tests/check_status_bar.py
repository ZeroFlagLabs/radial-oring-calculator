"""Native rendered status bar, stable baseline and timeout regression."""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication,QStatusBar
from PySide6.QtGui import QFontInfo,QPalette
from PySide6.QtCore import QPoint
from PySide6.QtTest import QTest
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
sys.path.insert(0,str(root/'src'))
from src.ui.main_window import MainWindow
app=QApplication([]);w=MainWindow()

w.show();app.processEvents()
bar=w.statusBar()
font=QFontInfo(bar.font())
assert (font.family(),font.pointSize(),font.bold())==("Segoe UI",9,False)
assert isinstance(bar,QStatusBar)
assert bar.height()==21 and bar.width()==w.width()
assert bar.mapTo(w,QPoint()).y()+bar.height()==w.height()
assert not bar.isSizeGripEnabled()
assert bar.palette().color(QPalette.ColorRole.WindowText).name()=="#243d58"
assert bar.palette().color(QPalette.ColorRole.Window).name()=="#f0f0f0"
def ink(text):
    bar.showMessage(text);app.processEvents();im=bar.grab().toImage()
    assert im.pixelColor(im.width()-15,10).name()=="#f0f0f0"
    pix=[]
    for y in range(21):
        for x in range(4,min(im.width()-20,240)):
            c=im.pixelColor(x,y)
            if c.red()<170 and c.green()<180 and c.blue()<200:pix.append((x,y))
    return min(x for x,y in pix),min(y for x,y in pix),max(y for x,y in pix)
for message in ("Ready","Calculation complete.","Agjpqy"):
    x,t,b=ink(message)
    assert x in (6,7) and abs((t+b)/2-10)<=1,(message,x,t,b)
    print("Centered:",message,"ink",t,b,flush=True)
_,t,b=ink("Calculated")
assert t in (4,5,6) and b<t+12,(t,b)
seen=[]
bar.messageChanged.connect(seen.append)
bar.showMessage("Temporary message",50)
assert bar.currentMessage()=="Temporary message"
QTest.qWait(100)
assert not bar.currentMessage() and seen==["Temporary message",""],seen
print("PASS centered native status, stable baseline and timeout",w.size().toTuple(),flush=True)
w.close()
