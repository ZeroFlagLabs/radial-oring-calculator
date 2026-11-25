"""ZeroFlagLabs fixed-size, optically centred status bar."""
from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QStatusBar


class CenteredStatusBar(QStatusBar):
    """Retain Qt message signals and timeout handling; centre only the paint."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizeGripEnabled(False)
        self.setFixedHeight(21)
        self.setStyleSheet("QStatusBar {background:#f0f0f0;color:#243d58;font: 9pt 'Segoe UI';}")

    def paintEvent(self, event):
        # All current calculators use transient messages, not permanent widgets.
        # Centre a representative ascender/descender ink box rather than the
        # font line box; keep a fixed baseline so messages never jump vertically.
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.palette().window())
        painter.setPen(self.palette().windowText().color())
        painter.setFont(self.font())
        box = painter.fontMetrics().tightBoundingRect("Agjpqy")
        baseline = round((self.height() - 1 - box.top() - box.bottom()) / 2)
        painter.setClipRect(QRect(6, 0, max(0, self.width() - 12), self.height()))
        painter.drawText(QPoint(6, baseline), self.currentMessage())
        painter.end()
