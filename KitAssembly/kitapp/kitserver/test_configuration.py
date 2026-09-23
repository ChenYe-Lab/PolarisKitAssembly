import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from django.test import SimpleTestCase, RequestFactory, override_settings

from kitapp.environment import build_configuration
from kitserver.http_client import ApiSession
from kitserver import views


class ConfigurationTests(SimpleTestCase):
    def configuration(self, **overrides):
        env = {'SECRET_KEY': 'isolated-test-secret',
               'WEBDATABASE_URL': 'https://example.test/WebDatabase',
               'LABDATABASE_URL': 'https://example.test/LabDatabase/'}
        env.update(overrides)
        return build_configuration(Path('/project'), env)

    def test_secure_defaults(self):
        config = self.configuration()
        self.assertFalse(config['DEBUG'])
        self.assertNotIn('*', config['ALLOWED_HOSTS'])
        self.assertEqual(config['CSRF_TRUSTED_ORIGINS'], [])
        for key in ('SESSION_COOKIE_SECURE', 'CSRF_COOKIE_SECURE', 'VISITOR_COOKIE_SECURE'):
            self.assertTrue(config[key])

    def test_explicit_development_settings(self):
        config = self.configuration(DEBUG='yes', ALLOWED_HOSTS='localhost, example.test',
                                    CSRF_TRUSTED_ORIGINS='https://example.test')
        self.assertTrue(config['DEBUG'])
        self.assertFalse(config['SESSION_COOKIE_SECURE'])
        self.assertEqual(config['ALLOWED_HOSTS'], ['localhost', 'example.test'])
        self.assertEqual(config['CSRF_TRUSTED_ORIGINS'], ['https://example.test'])

    def test_urls_normalize_and_empty_login_uses_default(self):
        config = self.configuration(API_LOGIN_URL='')
        self.assertEqual(config['WEBDATABASE_URL'], 'https://example.test/WebDatabase/')
        self.assertEqual(config['API_LOGIN_URL'], 'https://example.test/WebDatabase/login')

    def test_missing_secret_is_rejected(self):
        for value in ('', 'replace-with-your-secret-key'):
            with self.subTest(value=value), self.assertRaises(ImproperlyConfigured):
                self.configuration(SECRET_KEY=value)

    def test_invalid_urls_fail_without_echoing_credentials(self):
        for value in ('', '/relative', 'https://example.test:bad/', 'https://example.test/?q=1',
                      'https://user:private-password@example.test/', 'ftp://example.test', 'https://bad host/'):
            with self.subTest(value=value), self.assertRaises(ImproperlyConfigured) as error:
                self.configuration(WEBDATABASE_URL=value)
            self.assertNotIn('private-password', str(error.exception))

    def test_invalid_values_are_rejected(self):
        for name, value in [('DEBUG', 'typo'), ('API_REQUEST_TIMEOUT', '0'),
                            ('API_REQUEST_TIMEOUT', 'nan'), ('API_REQUEST_TIMEOUT', '-1'),
                            ('VISITOR_COOKIE_MAX_AGE', '1.5'), ('ALLOWED_HOSTS', ''),
                            ('CSRF_TRUSTED_ORIGINS', 'example.test'),
                            ('VISITOR_COOKIE_SAMESITE', 'invalid')]:
            with self.subTest(name=name, value=value), self.assertRaises(ImproperlyConfigured):
                self.configuration(**{name: value})

    def test_same_site_none_requires_secure(self):
        with self.assertRaises(ImproperlyConfigured):
            self.configuration(VISITOR_COOKIE_SAMESITE='None', VISITOR_COOKIE_SECURE='false')

    def test_credentials_must_be_paired(self):
        with self.assertRaises(ImproperlyConfigured):
            self.configuration(API_LOGIN_USERNAME='test')
        self.assertEqual(self.configuration(API_LOGIN_USERNAME='test', API_LOGIN_PASSWORD=' pass ')['API_LOGIN_PASSWORD'], ' pass ')

    def test_optional_paths_and_legacy_tutorial_name(self):
        base = Path('/project')
        self.assertIsNone(self.configuration()['TUTORIAL_ADDRESS'])
        self.assertEqual(self.configuration(TUROERIAL_ADDRESS='docs/old.pdf')['TUTORIAL_ADDRESS'], base / 'docs/old.pdf')
        self.assertEqual(self.configuration(TUTORIAL_ADDRESS='new.pdf', TUROERIAL_ADDRESS='old.pdf')['TUTORIAL_ADDRESS'], base / 'new.pdf')
        self.assertEqual(self.configuration(SQLITE_PATH='data/app.sqlite3')['SQLITE_PATH'], base / 'data/app.sqlite3')

    def test_dotenv_does_not_override_process_environment(self):
        from kitapp.settings import _load_env_file
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / '.env'
            path.write_text('DEBUG=True\nALLOWED_HOSTS=localhost\n', encoding='utf-8')
            with patch.dict(os.environ, {'DEBUG': 'False'}, clear=True):
                _load_env_file(path)
                self.assertEqual(os.environ['DEBUG'], 'False')
                self.assertEqual(os.environ['ALLOWED_HOSTS'], 'localhost')


class ConfigurationConsumerTests(SimpleTestCase):
    @override_settings(API_REQUEST_TIMEOUT=3.5)
    def test_all_session_requests_receive_timeout(self):
        with patch('requests.Session.request') as request:
            with ApiSession() as session:
                session.get('https://example.test/list')
                session.post('https://example.test/create', json={})
                session.get('https://example.test/file', stream=True)
            self.assertEqual([call.kwargs['timeout'] for call in request.call_args_list], [3.5, 3.5, 3.5])

    @override_settings(API_REQUEST_TIMEOUT=20)
    def test_explicit_timeout_is_preserved(self):
        with patch('requests.Session.request') as request:
            with ApiSession() as session:
                session.get('https://example.test', timeout=2)
            self.assertEqual(request.call_args.kwargs['timeout'], 2)

    def test_tutorial_and_zip_use_configured_files(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'file.bin'
            path.write_bytes(b'configured-download')
            with override_settings(TUTORIAL_ADDRESS=path, ZIP_ADDRESS=path):
                for view in (views.getTutorial, views.getZip):
                    response = view(RequestFactory().get('/'))
                    try:
                        self.assertEqual(b''.join(response.streaming_content), b'configured-download')
                    finally:
                        response.close()

    @override_settings(TUTORIAL_ADDRESS=None, ZIP_ADDRESS=None)
    def test_unconfigured_download_is_404(self):
        for view in (views.getTutorial, views.getZip):
            with self.assertRaises(Http404):
                view(RequestFactory().get('/'))

    def test_tutorial_site_uses_configured_root_and_rejects_sibling(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'site'
            root.mkdir()
            (root / 'index.html').write_text('tutorial', encoding='utf-8')
            sibling = Path(folder) / 'site-private'
            sibling.mkdir()
            (sibling / 'private.txt').write_text('private', encoding='utf-8')
            with override_settings(TUTORIAL_SITE_ROOT=root):
                response = views.getTutorialTest(RequestFactory().get('/'))
                try:
                    self.assertEqual(b''.join(response.streaming_content), b'tutorial')
                finally:
                    response.close()
                with self.assertRaises(Http404):
                    views.getTutorialTest(RequestFactory().get('/'), '../site-private/private.txt')
