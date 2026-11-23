"""Regression tests for v2.1.2 public GitHub update checks."""
import unittest
from pathlib import Path
from PySide6.QtCore import QCoreApplication, QObject, QUrl
from PySide6.QtNetwork import QNetworkReply
from src.ui.update_checker import UpdateChecker

ROOT = Path(__file__).resolve().parents[1]


class FakeReply(QObject):
    def __init__(self, url, http_status=200, error=QNetworkReply.NetworkError.NoError):
        super().__init__()
        self._url = QUrl(url)
        self._http_status = http_status
        self._error = error

    def url(self):
        return self._url

    def error(self):
        return self._error

    def attribute(self, attr):
        return self._http_status


class UpdateRedirectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def check_result(self, url, status=200, error=QNetworkReply.NetworkError.NoError):
        checker = UpdateChecker()
        reply = FakeReply(url, status, error)
        checker._reply = reply
        checker._finished(reply)
        return checker

    def test_latest_release_is_compared_without_github_rest_api(self):
        c = self.check_result('https://github.com/ZeroFlagLabs/radial-oring-calculator/releases/tag/v9.2.3')
        self.assertEqual(c.status, 'v9.2.3 available. Open GitHub to download.')
        self.assertEqual(c.release_version, 'v9.2.3')
        self.assertEqual(c.release_url, 'https://github.com/ZeroFlagLabs/radial-oring-calculator/releases/tag/v9.2.3')

    def test_current_or_older_version_is_up_to_date(self):
        for tag in ('v2.1.2', 'v2.1.1', 'v1.9.0'):
            c = self.check_result('https://github.com/ZeroFlagLabs/radial-oring-calculator/releases/tag/'+tag)
            self.assertEqual(c.status, 'Up to date.')
            self.assertIsNone(c.release_url)

    def test_no_release_redirect_is_distinguished_from_offline(self):
        c = self.check_result('https://github.com/ZeroFlagLabs/radial-oring-calculator/releases')
        self.assertEqual(c.status, 'No published GitHub release found yet.')

    def test_rate_limiting_is_not_reported_as_offline(self):
        c = self.check_result('https://github.com/ZeroFlagLabs/radial-oring-calculator/releases/latest',
                              403, QNetworkReply.NetworkError.ContentAccessDenied)
        self.assertIn('limiting update checks', c.status)
        self.assertNotIn('online', c.status.lower())

    def test_connection_failure_is_identified_separately(self):
        c = self.check_result('https://github.com/ZeroFlagLabs/radial-oring-calculator/releases/latest',
                              None, QNetworkReply.NetworkError.HostNotFoundError)
        self.assertIn('internet connection', c.status)

    def test_invalid_tag_and_wrong_domain_cannot_be_offered(self):
        for url in (
            'https://github.com/ZeroFlagLabs/radial-oring-calculator/releases/tag/invalid',
            'https://evil.example/ZeroFlagLabs/radial-oring-calculator/releases/tag/v99.0.0',
        ):
            c = self.check_result(url)
            self.assertIsNone(c.release_url)
            self.assertIsNone(c.release_version)

    def test_packager_requires_windows_tls_backend(self):
        builder = (ROOT/'tools/Build-OneFile-Portable.py').read_text(encoding='utf-8')
        self.assertIn('qschannelbackend.dll', builder)
        self.assertIn('--add-binary', builder)
        self.assertIn('Windows Schannel TLS backend missing', builder)

    def test_updater_uses_head_redirect_without_api_quota(self):
        updater = (ROOT/'src/ui/update_checker.py').read_text(encoding='utf-8')
        self.assertIn('self.network.head(request)', updater)
        self.assertIn('QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy', updater)
        self.assertNotIn('RELEASE_API_URL', updater)


if __name__ == '__main__':
    unittest.main()
