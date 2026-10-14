"""Exercise the frontend's real requests session against the backend HTTP server."""
import hashlib
import sys
from pathlib import Path
from django.test import LiveServerTestCase, RequestFactory, override_settings
from WebDatabase.models import CustomUser


@override_settings(API_REQUEST_TIMEOUT=5, ALLOWED_HOSTS=['localhost', '127.0.0.1', 'testserver'])
class ServiceSessionIntegrationTests(LiveServerTestCase):
    def test_frontend_logs_in_and_csrf_protected_write_succeeds(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'KitAssembly/kitapp'))
        from kitserver import views
        user = CustomUser(username='service-test', uname='service-test', role='editor', is_staff=False)
        user.set_password(hashlib.md5(b'service-test-password').hexdigest()); user.save()
        base = self.live_server_url + '/WebDatabase/'
        with override_settings(WEBDATABASE_URL=base, API_LOGIN_URL=base+'login',
                               API_LOGIN_USERNAME=user.username, API_LOGIN_PASSWORD='service-test-password'):
            session = getattr(views, '__create_session')(RequestFactory().get('/'))
        self.assertIsNotNone(session)
        try:
            response = session.post(base+'createRepo', json={'Name': 'service-test-repository'})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertTrue(response.json()['success'])
            self.assertEqual(session.get(base+'getrepos').status_code, 200)
        finally:
            session.close()
