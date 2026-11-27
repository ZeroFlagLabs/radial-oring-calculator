"""ZeroFlagLabs standard application-owned dialogue palette (workflow v2.34)."""
import re
from pathlib import Path
from shiboken6 import isValid
from PySide6.QtCore import Qt, QTimer, QObject, QEvent
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QLabel, QScrollBar, QComboBox, QStyleFactory, QStyledItemDelegate

DIALOG_STYLE = """
QDialog { background:#f0f0f0; color:#174675; }
QLabel { color:#174675; }
QCheckBox { color:#242424; spacing:6px; }
QCheckBox::indicator { width:14px; height:14px; border:1px solid #9ebfe2; border-radius:3px; background:white; }
QCheckBox::indicator:checked { background:#dcecfb; border-color:#83afd9; image:url(@CHECK_ICON@); }
QCheckBox::indicator:hover { border-color:#258aca; }
QCheckBox::indicator:disabled { background:#eff2f5; border-color:#c4cdd8; }
QCheckBox::indicator:checked:disabled { image:url(@CHECK_ICON@); }
QLabel:disabled, QCheckBox:disabled { color:#8190a1; }
QPushButton { background:#eaf3fc; color:#144b83; border:1px solid #9ebfe2; border-radius:5px; min-height:24px; padding:2px 8px; font-weight:600; }
QPushButton:hover { background:#d9ecff; }
QPushButton:pressed { background:#c6def7; }
QPushButton:disabled { color:#8795a5; background:#eff2f5; }
QTabWidget::pane { background:white; border:1px solid #e7e7e7; border-radius:4px; }
QTabBar::tab { background:#f1f1f1; border:1px solid #e5e5e5; border-top-left-radius:5px; border-top-right-radius:5px; padding:4px 11px; color:#344556; }
QTabBar::tab:selected { background:white; color:#1b3452; border-bottom-color:white; }
QTextBrowser, QTextBrowser:focus { background:white; border:1px solid #e7e7e7; border-radius:4px; color:#242424; }
QTableWidget, QTableWidget:focus { border:1px solid #e7e7e7; border-radius:4px; background:white; alternate-background-color:#f3f7fb; color:#242424; selection-background-color:#e5f1fc; selection-color:#242424; }
QHeaderView::section { color:#174675; }
QFrame#settings_heading_rule, QFrame#inspect_heading_rule, QFrame#heading_rule, QFrame#method_dialog_heading_rule { color:#858585; }
"""

SCROLLBAR_STYLE = """
QScrollBar:vertical { background:white; width:12px; margin:0; border:0; }
QScrollBar::handle:vertical { background:#909090; min-height:24px; margin:0 5px 0 4px; border-radius:1px; }
QScrollBar::handle:vertical:hover, QScrollBar::handle:vertical:pressed { background:#707070; margin:0 3px; border-radius:3px; }
QScrollBar:horizontal { background:white; height:12px; margin:0; border:0; }
QScrollBar::handle:horizontal { background:#909090; min-width:24px; margin:4px 0 5px 0; border-radius:1px; }
QScrollBar::handle:horizontal:hover, QScrollBar::handle:horizontal:pressed { background:#707070; margin:3px 0; border-radius:3px; }
QScrollBar::add-line, QScrollBar::sub-line { width:0; height:0; border:0; background:transparent; }
QScrollBar::add-page, QScrollBar::sub-page { background:white; }
QScrollBar::up-arrow, QScrollBar::down-arrow, QScrollBar::left-arrow, QScrollBar::right-arrow { image:none; width:0; height:0; }
"""


def apply_scrollbar_theme(bar):
    bar.setStyleSheet(SCROLLBAR_STYLE)


class _InspectorPopupFocus(QObject):
    """Release resting combo focus on selection or dismissal of its native popup."""
    def __init__(self, combo, panel):
        super().__init__(combo)
        self.combo = combo
        self.panel = panel
        self.popup = combo.view().window()
        self.popup.installEventFilter(self)
        combo.installEventFilter(self)
        self.dismiss_release = False
        combo.activated.connect(self.schedule)
        # Mouse interaction need not take persistent focus. Tab access remains.
        combo.setFocusPolicy(Qt.FocusPolicy.TabFocus)

    def eventFilter(self, watched, event):
        if not all(isValid(w) for w in (self.combo, self.panel, self.popup)):
            return False
        kind = event.type()
        if kind == QEvent.Type.MouseButtonPress and self.popup.isVisible():
            # The native popup grabs mouse events. A press over its owner must
            # dismiss it, not be replayed to reopen the combo immediately.
            local = self.combo.mapFromGlobal(event.globalPosition().toPoint())
            if self.combo.rect().contains(local):
                self.dismiss_release = watched is self.combo
                self.popup.setAttribute(Qt.WidgetAttribute.WA_NoMouseReplay, True)
                self.combo.hidePopup()
                self.schedule()
                return True
        if watched is self.combo:
            if kind == QEvent.Type.MouseButtonRelease and self.dismiss_release:
                self.dismiss_release = False
                return True
            if kind == QEvent.Type.MouseButtonPress:
                self.dismiss_release = False
        if watched is self.popup and kind == QEvent.Type.Hide:
            self.schedule()
        return False

    def schedule(self, *_):
        # Wait for Qt's native popup to finish restoring focus to its owner.
        if isValid(self) and isValid(self.panel):
            QTimer.singleShot(0, self, self.finish)

    def finish(self):
        combo, panel = self.combo, self.panel
        if not all(isValid(w) for w in (combo, panel, self.popup)):
            return
        if self.popup.isVisible() or not panel.isVisible() or not combo.isVisible():
            return
        focus = QApplication.focusWidget()
        # Do not steal focus from another control deliberately clicked by the user.
        if focus is not None and focus is not combo and not self.popup.isAncestorOf(focus) and focus is not panel:
            return
        pos = panel.verticalScrollBar().value()
        horizontal = panel.horizontalScrollBar().value()
        panel.setFocus(Qt.FocusReason.OtherFocusReason)
        panel.verticalScrollBar().setValue(pos)
        panel.horizontalScrollBar().setValue(horizontal)


def return_focus_after_selection(combo, panel):
    combo._inspector_popup_focus = _InspectorPopupFocus(combo, panel)


def set_settings_identity(dialog, title, version, description):
    """Use the same About format and live identity in every application."""
    dialog.findChild(QLabel, 'current_version').setText('Current version: v' + version)
    dialog.findChild(QLabel, 'about_text').setText(
        'ZeroFlagLabs ' + title + '  \u00b7  v' + version + '\n\n' + description
        + '\n\nPortable Windows application.\n\nOriginal application code: MIT Licence.\nPySide6/Qt and other third-party components retain their own licences. Any third-party reference datasets retain their respective rights and licences.')


def ensure_light_scheme():
    app=QApplication.instance()
    if app is not None and app.styleHints().colorScheme()==Qt.ColorScheme.Dark:
        app.styleHints().setColorScheme(Qt.ColorScheme.Light)

def apply_dialog_theme(dialog):
    """Preserve local layout, specialised editor rules and semantic result colours."""
    check_icon = (Path(__file__).resolve().parent / 'resources' / 'icons' / 'checkbox-tick.png').as_posix()
    dialog.setStyleSheet(dialog.styleSheet()+"\n"+DIALOG_STYLE.replace('@CHECK_ICON@', '"'+check_icon+'"'))
    palette=dialog.palette()
    for role,value in ((QPalette.ColorRole.WindowText,'#174675'),(QPalette.ColorRole.Text,'#243d58'),(QPalette.ColorRole.Link,'#176bc0'),(QPalette.ColorRole.LinkVisited,'#176bc0')):
        palette.setColor(role,QColor(value))
    dialog.setPalette(palette)
    # Explicit scrollbar rules on each widget take precedence over nested
    # Designer scroll-area styles and do not depend on the native Qt style.
    for bar in dialog.findChildren(QScrollBar):
        apply_scrollbar_theme(bar)
    combos = dialog.findChildren(QComboBox)
    # Match the O-ring's native Windows 11 popup, including selected-row marker,
    # row heights, chevron and popup placement. Do not change the main window's
    # style or replace the Qt selection/keyboard handling.
    native = QStyleFactory.create('windows11') if combos else None
    if native is not None:
        native.setParent(dialog)
        dialog._native_combo_style = native
    for combo in combos:
        if native is not None:
            combo.setStyle(native)
            view = combo.view()
            view.setStyle(native)
            view.viewport().setStyle(native)
            view.window().setStyle(native)
            combo.setItemDelegate(QStyledItemDelegate(combo))
        combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        apply_scrollbar_theme(combo.view().verticalScrollBar())
        apply_scrollbar_theme(combo.view().horizontalScrollBar())
    for label in dialog.findChildren(QLabel):
        style=label.styleSheet()
        # Keep existing heading sizes and weight, standardise only colour roles.
        for old,new in (('#71849a','#6c7e94'),('#657a91','#667c94')):
            style=style.replace(old,new)
        name=label.objectName()
        # Prose is charcoal; controls, headings, hyperlinks and secondary notes retain their own roles.
        if name.startswith(('assumptions_text','references_text','criteria_text','method_description_')) or name in ('about_text','current_version','update_information','update_status','geometry_help','dialog_intro'):
            style += '\ncolor:#242424;'
        elif name=='references_note':
            style += '\ncolor:#667c94;'
        if style!=label.styleSheet():label.setStyleSheet(style)
        # Rich-text links can bypass QWidget foreground rules. Explicitly style
        # the anchors without altering their target, caption or interaction.
        text=label.text()
        if re.search(r'<a\s+href=',text,re.I):
            label.setText(re.sub(r'<a\s+href=', '<a style="color:#176bc0;" href=',text,flags=re.I))
