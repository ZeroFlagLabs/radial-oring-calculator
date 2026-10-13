"""Compact, print-friendly calculation snapshot for clipboard and PNG.

Unlike a capture of the UI, this is drawn as a fixed-size engineering summary
using the selected guide and the same calculated witness as the main window.
"""
from datetime import datetime

from src.app_info import APP_TITLE, APP_VERSION

from PySide6.QtCore import Qt, QRect, QRectF, QSize
from PySide6.QtGui import QColor, QFont, QFontMetrics, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication, QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QVBoxLayout,
)

REPORT_WIDTH = 966
REPORT_HEIGHT = 686
TITLE = APP_TITLE
INK = '#243D58'
MUTED = '#657A91'
BLUE = '#164F8A'
RULE = '#D8E1EA'
BG = '#F7FAFC'


def _font(point_size, bold=False):
    result = QFont('Segoe UI', point_size)
    result.setWeight(QFont.Weight.DemiBold if bold else QFont.Weight.Normal)
    return result


def _text(painter, x, baseline, value, *, size=9, bold=False,
          colour=INK, align='left', width=0):
    """Draw one concise line and prevent very long values from overlapping."""
    value = str(value)
    painter.setPen(QColor(colour))
    font = _font(size, bold)
    if width:
        metrics = QFontMetrics(font)
        if metrics.horizontalAdvance(value) > width:
            value = metrics.elidedText(value, Qt.TextElideMode.ElideRight, width)
    painter.setFont(font)
    if align == 'right':
        painter.drawText(QRect(int(x-width), int(baseline-19), int(width), 24),
                         Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, value)
    elif align == 'center':
        painter.drawText(QRect(int(x), int(baseline-19), int(width), 24),
                         Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, value)
    else:
        painter.drawText(int(x), int(baseline), value)


def _line(painter, y, x1=28, x2=938, *, colour=RULE):
    painter.setPen(QPen(QColor(colour), 1))
    painter.drawLine(x1, y, x2, y)


def _guide_on_white(sketch):
    """Return the selected guide with its uniform pale background replaced by white.

    This affects only the PNG/snapshot report. The main calculator keeps the
    original light blue guide panel exactly as approved.
    """
    if sketch is None or sketch.isNull():
        return sketch
    image = sketch.toImage().convertToFormat(QImage.Format.Format_ARGB32)
    bg = image.pixelColor(0, 0)
    for y in range(image.height()):
        for x in range(image.width()):
            colour = image.pixelColor(x, y)
            if (abs(colour.red() - bg.red()) <= 2 and
                    abs(colour.green() - bg.green()) <= 2 and
                    abs(colour.blue() - bg.blue()) <= 2):
                image.setPixelColor(x, y, QColor('white'))
    return QPixmap.fromImage(image)


def _render_image(description, rows, screening, inputs, *, sketch=None,
                  context=None, detail_rows=None, timestamp=None):
    """Return a single 966 × 686 px image, smaller than the main calculator UI.

    There are no boxes around individual figures. Only a subtle outside border,
    light table rules, and a modest section-heading colour are used.
    """
    image = QPixmap(REPORT_WIDTH, REPORT_HEIGHT)
    image.fill(QColor('white'))
    painter = QPainter(image)
    try:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setPen(QPen(QColor('#9FBBD5'), 1))
        painter.drawRect(5, 5, REPORT_WIDTH-11, REPORT_HEIGHT-11)

        _text(painter, 27, 40, TITLE, size=15, bold=True, colour=BLUE)
        if timestamp is None:
            timestamp = datetime.now()
        _text(painter, 937, 33, timestamp.strftime('%d %b %Y  %H:%M'),
              size=9, colour=MUTED, align='right', width=185)
        _text(painter, 937, 51, 'v' + APP_VERSION, size=8, colour=MUTED,
              align='right', width=185)
        _line(painter, 65)

        # Left column: selected application followed immediately by its inputs.
        _text(painter, 28, 91, 'APPLICATION CONFIGURATION', size=10,
              bold=True, colour=BLUE)
        items = context or [('Selected calculation', description)]
        for i, (name, value) in enumerate(items[:5]):
            y = 114 + i*20
            _text(painter, 29, y, name, size=9, colour=MUTED)
            _text(painter, 439, y, value, size=9, bold=True,
                  align='right', width=254)

        _line(painter, 214, 28, 442)
        _text(painter, 28, 238, 'INPUT DIMENSIONS', size=10,
              bold=True, colour=BLUE)
        for i, (name, value) in enumerate(inputs):
            y = 261 + i*22
            if y >= 463:
                # Nine entries is the supported arrangement for both gland types.
                raise ValueError('Input list exceeds the compact report area')
            _text(painter, 29, y, name, size=9, colour=MUTED)
            _text(painter, 439, y, value, size=9, bold=True,
                  align='right', width=190)

        # Right column: exact selected guide (same scaling rule for every case).
        _text(painter, 480, 91, 'DIMENSION GUIDE', size=10,
              bold=True, colour=BLUE)
        image_box = QRect(508, 111, 382, 355)
        painter.fillRect(image_box, QColor('white'))
        if sketch is not None and not sketch.isNull():
            # Keep the same common display envelope for every case, but make
            # the report-only background white so the guide sits naturally
            # within emails and pasted documents.
            fitted = _guide_on_white(sketch).scaled(345, 345,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
            x = image_box.x() + (image_box.width()-fitted.width())//2
            y = image_box.y() + (image_box.height()-fitted.height())//2
            painter.drawPixmap(x, y, fitted)
        else:
            _text(painter, image_box.x()+25, 295, 'Guide unavailable', colour=MUTED)
        _text(painter, image_box.x(), 479,
              'Indicative geometry only - not to scale',
              size=8, colour=MUTED, align='center', width=image_box.width())

        _line(painter, 494)
        _text(painter, 28, 517, 'DIMENSIONAL SCREENING RESULTS',
              size=10, bold=True, colour=BLUE)

        # Only a heading divider and row separators: never individual cell boxes.
        headings = [
            (29, 'CHECK', 'left', 0),
            (207, 'MINIMUM', 'center', 100),
            (308, 'NOMINAL', 'center', 100),
            (409, 'MAXIMUM', 'center', 100),
            (541, 'ACCEPTANCE CRITERION', 'left', 0),
            (852, 'STATUS', 'center', 82),
        ]
        for x, heading, align, width in headings:
            _text(painter, x, 541, heading, size=8, bold=True,
                  colour=MUTED, align=align, width=width)
        _line(painter, 547)

        centers = [257, 358, 459]
        for i, (name, values, check) in enumerate(rows[:3]):
            y = 571 + i*40
            label = str(name).replace(' (%)','')
            _text(painter, 29, y, label, size=10, bold=True, colour=INK)
            for j, value in enumerate(values):
                _text(painter, centers[j]-48, y, value, size=10, bold=True,
                      align='center', width=96)
                if detail_rows and i < len(detail_rows) and detail_rows[i]:
                    _text(painter, centers[j]-48, y+14, detail_rows[i][j],
                          size=8, colour=MUTED, align='center', width=96)
            _text(painter, 541, y, check.criterion, size=8, colour=MUTED)
            passed = check.within_limits
            _text(painter, 851, y, 'PASS' if passed else 'REVIEW',
                  size=10, bold=True, colour='#18744F' if passed else '#B42318',
                  align='center', width=84)
            if i < 2:
                _line(painter, y+20)
    finally:
        painter.end()
    return image


class ScreenshotCard(QFrame):
    """Compatibility widget for the previous preview dialog and GUI tests."""
    def __init__(self, description, rows, screening, inputs, parent=None,
                 sketch=None, context=None, detail_rows=None):
        super().__init__(parent)
        self._image = _render_image(description, rows, screening, inputs,
                         sketch=sketch, context=context, detail_rows=detail_rows)
        self.setFixedSize(REPORT_WIDTH, REPORT_HEIGHT)

    def sizeHint(self):
        return QSize(REPORT_WIDTH, REPORT_HEIGHT)

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.drawPixmap(0, 0, self._image)
        finally:
            painter.end()

    def capture(self):
        return self._image.copy()


class ScreenshotDialog(QDialog):
    """Preview compatible with the existing Stage 8/9 GUI smoke tests."""
    def __init__(self, description, rows, screening, inputs, parent=None,
                 sketch=None, context=None, detail_rows=None):
        super().__init__(parent)
        self.setWindowTitle('Snapshot | ' + TITLE)
        self.resize(1000, 790)
        layout = QVBoxLayout(self)
        heading = QLabel('Copy or save the calculation snapshot below.')
        layout.addWidget(heading)
        scroll = QScrollArea()
        self.card = ScreenshotCard(description, rows, screening, inputs,
                 sketch=sketch, context=context, detail_rows=detail_rows)
        scroll.setWidget(self.card)
        layout.addWidget(scroll, 1)
        buttons = QHBoxLayout()
        copy = QPushButton('Copy image')
        copy.clicked.connect(self.copy_image)
        save = QPushButton('Save PNG…')
        save.clicked.connect(self.save_image)
        close = QPushButton('Close')
        close.clicked.connect(self.accept)
        buttons.addWidget(copy)
        buttons.addWidget(save)
        buttons.addStretch()
        buttons.addWidget(close)
        layout.addLayout(buttons)

    def capture(self):
        return self.card.capture()

    def copy_image(self):
        QApplication.clipboard().setPixmap(self.capture())

    def save_image(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Save calculation image',
                                             'oring-calculation.png', 'PNG images (*.png)')
        if path:
            save_snapshot_to_png(self.capture(), path)


def render_snapshot(description, rows, screening, inputs, sketch=None,
                    context=None, detail_rows=None):
    """Both main-window actions use the identical compact rendering function."""
    return _render_image(description, rows, screening, inputs, sketch=sketch,
                         context=context, detail_rows=detail_rows)


def save_snapshot_to_png(image, path):
    if not path.lower().endswith('.png'):
        path += '.png'
    if not image.save(path, 'PNG'):
        raise OSError('Could not save calculation image: ' + path)
    return path
