import hashlib
import io
from contextlib import redirect_stdout
from django.test import Client, TestCase, override_settings
from WebDatabase.models import CustomUser, Parttable
from WebDatabase.logger import DjangoLogger


class AccessTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(uname='reader', email='reader@example.test',
            password=hashlib.md5(b'test-password').hexdigest(), role='user', is_staff=False)

    def test_anonymous_and_forged_legacy_session_are_rejected(self):
        self.assertEqual(self.client.get('/WebDatabase/Part').status_code, 401)
        session = self.client.session
        session['info'] = {'uid': self.user.pk, 'uname': 'reader'}
        session.save()
        self.assertEqual(self.client.get('/WebDatabase/Part').status_code, 401)

    def test_reader_cannot_write_or_list_visitor_details(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.post('/WebDatabase/AddPartData', {}, content_type='application/json').status_code, 403)
        self.assertEqual(self.client.get('/WebDatabase/deletePart').status_code, 405)
        self.assertFalse(Parttable.objects.exists())

    def test_csrf_applies_to_legacy_exempt_write_view(self):
        self.user.role = 'editor'; self.user.save()
        client = Client(enforce_csrf_checks=True); client.force_login(self.user)
        self.assertEqual(client.post('/WebDatabase/createRepo', {}, content_type='application/json').status_code, 403)

    def test_login_is_post_csrf_protected_and_verifiable(self):
        client = Client(enforce_csrf_checks=True)
        path = '/WebDatabase/login'
        self.assertFalse(client.get(path, HTTP_ACCEPT='application/json').json()['authenticated'])
        credentials = {'username': 'reader', 'password': 'test-password'}
        self.assertEqual(client.post(path, credentials, HTTP_ACCEPT='application/json').status_code, 403)
        output = io.StringIO()
        with redirect_stdout(output):
            response = client.post(path, credentials, HTTP_ACCEPT='application/json',
                HTTP_X_CSRFTOKEN=client.cookies['csrftoken'].value)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.json()['authenticated'])
        self.assertTrue(client.get(path, HTTP_ACCEPT='application/json').json()['authenticated'])
        self.assertNotIn('test-password', output.getvalue())

    def test_wrong_password_and_inactive_account_are_rejected(self):
        for active, password in [(True, 'wrong'), (False, 'test-password')]:
            self.user.is_active = active; self.user.save()
            response = self.client.post('/WebDatabase/login', {'username': 'reader', 'password': password},
                                        HTTP_ACCEPT='application/json')
            self.assertEqual(response.status_code, 401)
            self.assertFalse(response.json()['authenticated'])

    @override_settings(DEBUG=True)
    def test_nested_log_redaction(self):
        logger = DjangoLogger()
        data = {'password1': 'secret-a', 'nested': [{'API_TOKEN': 'secret-b', 'name': 'safe'}]}
        result = logger._sanitize_data(data)
        self.assertNotIn('secret-a', str(result)); self.assertNotIn('secret-b', str(result))
        self.assertEqual(result['nested'][0]['name'], 'safe')
        self.assertEqual(data['password1'], 'secret-a')
