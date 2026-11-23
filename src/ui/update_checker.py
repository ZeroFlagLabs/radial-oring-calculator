"""Non-blocking, opt-out update notifications for the portable application.

Only GitHub's public latest-release redirect is requested. No personal data,
credentials, software downloads or installation actions are involved. Checking
the public release redirect avoids the unauthenticated GitHub REST API rate limit.
"""
import re

from PySide6.QtCore import QObject, QSettings, QTimer, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from src.app_info import APP_TITLE, APP_VERSION, GITHUB_URL, RELEASES_URL


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
        request = QNetworkRequest(QUrl(RELEASES_URL))
        request.setRawHeader(b'User-Agent', b'ZeroFlagLabs-ORing-Calculator')
        # HEAD follows GitHub's /releases/latest -> /releases/tag/vX.Y.Z
        # without downloading a release page or consuming REST API quota.
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
        )
        self._reply = self.network.head(request)
        reply = self._reply
        reply.finished.connect(lambda: self._finished(reply))
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(reply.abort)
        reply.finished.connect(timer.stop)
        reply.finished.connect(timer.deleteLater)
        timer.start(10000)

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
                if http_status in (403, 429):
                    self.status = 'GitHub is limiting update checks. Try again later.'
                elif http_status:
                    self.status = f'GitHub update check failed (HTTP {http_status}).'
                else:
                    self.status = 'Unable to reach GitHub. Check your internet connection.'
            else:
                latest = reply.url()
                prefix = QUrl(GITHUB_URL).path() + '/releases/tag/'
                if (latest.scheme() != 'https' or
                        latest.host().lower() != 'github.com' or
                        not latest.path().startswith(prefix)):
                    # A repository without stable releases can redirect to its
                    # general Releases page rather than a specific version.
                    self.status = 'No published GitHub release found yet.'
                else:
                    tag = latest.path()[len(prefix):]
                    version = self._parse_version(tag)
                    current = self._parse_version(APP_VERSION)
                    if version is None or current is None:
                        self.status = 'GitHub release version could not be read.'
                    elif version > current:
                        # The version tag is strictly numeric and safe to
                        # construct as a canonical, query-free release URL.
                        self.release_url = GITHUB_URL + '/releases/tag/' + tag
                        self.release_version = tag
                        self.status = f'{tag} available. Open GitHub to download.'
                    else:
                        self.status = 'Up to date.'
        finally:
            reply.deleteLater()
            self.state_changed.emit()

    @staticmethod
    def _parse_version(value):
        match = re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)', value)
        return tuple(map(int, match.groups())) if match else None
