"""Position application-owned modal dialogs relative to the visible parent frame."""
from PySide6.QtCore import QTimer, QPoint
from PySide6.QtGui import QGuiApplication

def center_dialog(dialog, parent):
    """Center the complete dialog frame and constrain it to the parent's screen."""
    parent = parent.window()
    p = parent.frameGeometry()
    f = dialog.frameGeometry()
    screen = QGuiApplication.screenAt(p.center()) or parent.screen()
    bounds = screen.availableGeometry()
    x = p.x() + (p.width()-f.width())//2
    y = p.y() + (p.height()-f.height())//2
    x = max(bounds.left(), min(x, bounds.right()+1-f.width()))
    y = max(bounds.top(), min(y, bounds.bottom()+1-f.height()))
    dialog.move(dialog.pos() + QPoint(x-f.x(), y-f.y()))

def exec_centered(dialog, parent):
    """Apply placement before exec and once native frame geometry is available."""
    dialog.ensurePolished()
    if dialog.layout(): dialog.layout().activate()
    dialog.winId()
    center_dialog(dialog, parent)
    def settle():
        if dialog.isVisible(): center_dialog(dialog, parent)
    QTimer.singleShot(0, dialog, settle)
    return dialog.exec()
