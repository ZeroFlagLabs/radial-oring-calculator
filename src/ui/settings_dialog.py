"""Settings: Designer-owned tabs and non-blocking GitHub update controls."""
from pathlib import Path
from PySide6.QtCore import QFile, QIODevice, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QLabel, QPushButton
from PySide6.QtUiTools import QUiLoader

from src.app_info import APP_TITLE, APP_VERSION, GITHUB_URL
from src.ui.update_checker import UpdateChecker


class SettingsDialog:
    """Thin adapter around the Designer-owned QDialog."""
    def __init__(self, parent):
        path = Path(__file__).resolve().parent / 'forms' / 'settings_dialog.ui'
        form = QFile(str(path))
        if not form.open(QIODevice.OpenModeFlag.ReadOnly):
            raise RuntimeError(f'Cannot open Settings layout: {path}')
        try:
            self.dialog = QUiLoader().load(form, parent)
        finally:
            form.close()
        if not isinstance(self.dialog, QDialog):
            raise RuntimeError('Settings Designer form must be a QDialog')
        self.dialog.findChild(QDialogButtonBox, 'buttons').rejected.connect(self.dialog.reject)
        self.checker = parent.update_checker if parent is not None else UpdateChecker(self.dialog)
        self.check_on_launch = self.dialog.findChild(QCheckBox, 'check_on_launch')
        self.check_now = self.dialog.findChild(QPushButton, 'check_now_button')
        self.status = self.dialog.findChild(QLabel, 'update_status')
        self.release_button = self.dialog.findChild(QPushButton, 'open_release_button')
        self.version = self.dialog.findChild(QLabel, 'current_version')
        self.about = self.dialog.findChild(QLabel, 'about_text')
        self.link = self.dialog.findChild(QLabel, 'github_link')
        if any(x is None for x in (self.check_on_launch, self.check_now, self.status,
                                    self.release_button, self.version, self.about, self.link)):
            raise RuntimeError('Settings Designer form is missing an Updates/About control')
        self.version.setText('Current version: v' + APP_VERSION)
        self.about.setText('ZeroFlagLabs ' + APP_TITLE + '  ·  v' + APP_VERSION +
                           '\n\nDimensional screening for static and dynamic (reciprocating) radial O-ring seals.'+
                           '\n\nOriginal application code: MIT Licence.'+
                           '\nPySide6/Qt and other third-party components retain their own licences.')
        # The repository is public; stable releases are published separately.
        self.link.setText(f'<a href="{GITHUB_URL}">Project on GitHub</a>')
        self.link.setOpenExternalLinks(True)
        self.check_on_launch.setChecked(self.checker.enabled())
        self.check_on_launch.toggled.connect(self.checker.set_enabled)
        self.check_now.clicked.connect(self.checker.check)
        self.release_button.clicked.connect(self._open_release)
        self.checker.state_changed.connect(self._refresh)
        self.dialog.finished.connect(self._disconnect)
        self._refresh()

    def _refresh(self):
        self.status.setText(self.checker.status)
        self.release_button.setEnabled(self.checker.release_url is not None)
        self.check_now.setEnabled(self.checker._reply is None)

    def _open_release(self):
        if self.checker.release_url:
            QDesktopServices.openUrl(QUrl(self.checker.release_url))

    def _disconnect(self, *_):
        try:
            self.checker.state_changed.disconnect(self._refresh)
        except (RuntimeError, TypeError):
            pass

    def exec(self):
        return self.dialog.exec()
