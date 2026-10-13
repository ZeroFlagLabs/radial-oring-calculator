"""Non-blocking, opt-out update notifications for the portable application.

Only GitHub stable Releases metadata is requested. No software is downloaded
or installed. A missing/unpublished repository is a normal offline-style state.
"""
import json
import re

from PySide6.QtCore import QObject, QSettings, QTimer, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from src.app_info import APP_TITLE, APP_VERSION, RELEASE_API_URL, RELEASES_URL


class UpdateChecker(QObject):
    state_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.prefs = QSettings('ZeroFlagLabs', APP_TITLE)
        self.network = QNetworkAccessManager(self)
        self.status = 'Not checked yet'
        self.release_url = None
        self.release_version = None
        self._reply = None

    def enabled(self):
        return self.prefs.value('updates/check_on_launch', True, type=bool)

    def set_enabled(self, enabled):
        self.prefs.setValue('updates/check_on_launch', bool(enabled))
        self.prefs.sync()
        self.state_changed.emit()

    def check_on_launch(self):
        if self.enabled():
            self.check()

    def check(self):
        if self._reply is not None:
            return
        self.status = 'Checking GitHub Releases…'
        self.state_changed.emit()
        request = QNetworkRequest(QUrl(RELEASE_API_URL))
        request.setRawHeader(b'User-Agent', b'ZeroFlagLabs-ORing-Calculator')
        request.setRawHeader(b'Accept', b'application/vnd.github+json')
        self._reply = self.network.get(request)
        reply = self._reply
        reply.finished.connect(lambda: self._finished(reply))
        # A parent-owned timer is cancelled with this checker. Unlike a
        # singleShot closure it cannot call a reply after window destruction.
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(reply.abort)
        reply.finished.connect(timer.stop)
        reply.finished.connect(timer.deleteLater)
        timer.start(7000)

    def _finished(self, reply):
        if reply is not self._reply:
            return
        self._reply = None
        self.release_url = None
        self.release_version = None
        try:
            http_status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            if http_status == 404:
                self.status = 'No published GitHub release found yet.'
            elif reply.error() != QNetworkReply.NetworkError.NoError:
                self.status = 'Unable to check updates. Try again when online.'
            else:
                metadata = json.loads(bytes(reply.readAll()).decode('utf8'))
                if metadata.get('draft') or metadata.get('prerelease'):
                    self.status = 'No newer stable release found.'
                else:
                    tag = str(metadata.get('tag_name', ''))
                    version = self._parse_version(tag)
                    current = self._parse_version(APP_VERSION)
                    if version is None or current is None:
                        self.status = 'GitHub release version could not be read.'
                    elif version > current:
                        url = metadata.get('html_url', '')
                        if not (isinstance(url, str) and url.startswith('https://github.com/')):
                            url = RELEASES_URL
                        self.release_url = url
                        self.release_version = tag
                        self.status = f'{tag} available. Open GitHub to download.'
                    else:
                        self.status = 'Up to date.'
        except (ValueError, KeyError, TypeError, UnicodeError):
            self.status = 'Unable to read GitHub release information.'
        finally:
            reply.deleteLater()
            self.state_changed.emit()

    @staticmethod
    def _parse_version(value):
        match = re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)', value)
        return tuple(map(int, match.groups())) if match else None
