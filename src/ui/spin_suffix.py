"""Display units beside numeric text without including them in the editor."""
from PySide6.QtCore import QObject, QEvent, Qt, QTimer
from PySide6.QtWidgets import QLabel, QStyle, QStyleOptionFrame

class InlineUnit(QObject):
    def __init__(self, spin):
        super().__init__(spin)
        self.spin = spin
        self.editor = spin.lineEdit()
        self.suffix = spin.suffix()
        self.base = self.editor.textMargins()
        self.unit_drag_anchor = None
        spin.setSuffix("")
        self.label = QLabel(self.suffix, self.editor)
        self.label.setObjectName("inline_numeric_unit")
        self.label.setTextFormat(Qt.TextFormat.PlainText)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.label.setStyleSheet("QLabel#inline_numeric_unit { background: transparent; border: none; padding: 0; color: #243d58; font-weight: normal; } QLabel#inline_numeric_unit:disabled { color: #8190a1; }")
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.update)
        self.editor.textChanged.connect(self.schedule)
        self.editor.cursorPositionChanged.connect(self.schedule)
        self.editor.installEventFilter(self)
        spin.installEventFilter(self)
        self.update()

    def schedule(self, *_):
        self.timer.start(0)

    def eventFilter(self, obj, event):
        # Native positionAt can map a click in the reserved suffix area to
        # a partially visible digit when a precise value is scrolled.
        # Explicitly treat that display-only area as the numeric end.
        e = self.editor
        kind = event.type()
        if obj is e:
            if kind in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonDblClick):
                if event.button() == Qt.MouseButton.LeftButton:
                    self.unit_drag_anchor = None
                    if event.position().x() >= self.label.x():
                        e.setFocus(Qt.FocusReason.MouseFocusReason)
                        end = len(e.text())
                        anchor = end
                        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                            anchor = e.cursorPosition()
                            if e.hasSelectedText():
                                start = e.selectionStart()
                                stop = start + len(e.selectedText())
                                anchor = stop if anchor == start else start
                        self.unit_drag_anchor = anchor
                        e.setSelection(anchor, end-anchor)
                        self.update()
                        return True
            elif kind == QEvent.Type.MouseMove and self.unit_drag_anchor is not None:
                if event.buttons() & Qt.MouseButton.LeftButton:
                    pos = (len(e.text()) if event.position().x() >= self.label.x()
                           else e.cursorPositionAt(event.position().toPoint()))
                    e.setSelection(self.unit_drag_anchor, pos-self.unit_drag_anchor)
                    return True
            elif kind == QEvent.Type.MouseButtonRelease and self.unit_drag_anchor is not None:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.unit_drag_anchor = None
                    return True
        if kind in (QEvent.Type.Resize, QEvent.Type.Show, QEvent.Type.FocusIn,
                            QEvent.Type.FocusOut, QEvent.Type.FontChange, QEvent.Type.StyleChange,
                            QEvent.Type.EnabledChange, QEvent.Type.LayoutDirectionChange):
            self.schedule()
        return False

    def update(self):
        e = self.editor
        self.label.setFont(e.font())
        fm = e.fontMetrics()
        width = fm.horizontalAdvance(self.suffix) + 1
        margins = e.textMargins()
        target = (self.base.left(), self.base.top(), self.base.right()+width, self.base.bottom())
        if (margins.left(),margins.top(),margins.right(),margins.bottom()) != target:
            e.setTextMargins(*target)
        opt = QStyleOptionFrame()
        e.initStyleOption(opt)
        area = e.style().subElementRect(QStyle.SubElement.SE_LineEditContents,opt,e)
        # Cursor geometry incorporates native style, focus border and horizontal scrolling.
        caret = e.inputMethodQuery(Qt.InputMethodQuery.ImCursorRectangle)
        x = caret.x() + caret.width()//2 + fm.horizontalAdvance(e.text()[e.cursorPosition():])
        x = min(max(area.left()+self.base.left(),x),area.right()-self.base.right()-width+1)
        self.label.setGeometry(x,0,width,e.height())
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label.show()
        self.label.raise_()

def install_inline_unit(spin):
    if not getattr(spin,"_inline_unit",None):
        spin._inline_unit = InlineUnit(spin)

def unit_suffix(spin):
    controller = getattr(spin,"_inline_unit",None)
    return controller.suffix if controller else spin.suffix()
