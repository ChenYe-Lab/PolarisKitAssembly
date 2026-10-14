from unittest.mock import Mock, patch
from requests.cookies import RequestsCookieJar
from django.test import SimpleTestCase, RequestFactory, override_settings
from kitserver import views


@override_settings(API_LOGIN_URL='http://backend.test/WebDatabase/login',
                   API_LOGIN_USERNAME='service', API_LOGIN_PASSWORD='test-password')
class ServiceAuthenticationTests(SimpleTestCase):
    def login(self, post_payload, verified=True):
        session = Mock()
        session.cookies = RequestsCookieJar(); session.cookies.set('csrftoken', 'backend-token')
        session.get.side_effect = [Mock(status_code=200), Mock(status_code=200, json=lambda: {'authenticated': verified})]
        session.post.return_value = Mock(status_code=200, json=lambda: post_payload)
        with patch.object(views, 'ApiSession', return_value=session):
            result = getattr(views, '__create_session')(RequestFactory().get('/', HTTP_COOKIE='csrftoken=frontend-token'))
        return result, session

    def test_success_requires_post_and_session_verification(self):
        result, session = self.login({'success': True, 'authenticated': True})
        self.assertIs(result, session)
        self.assertEqual(session.post.call_args.kwargs['headers']['X-CSRFToken'], 'backend-token')
        self.assertEqual(session.post.call_args.kwargs['data']['username'], 'service')
        self.assertEqual(session.get.call_count, 2)

    def test_http_200_without_authenticated_payload_is_failure(self):
        for payload in ({}, {'success': True}, {'success': False, 'authenticated': False}):
            result, session = self.login(payload)
            self.assertIsNone(result); session.close.assert_called_once()

    def test_missing_persisted_session_is_failure(self):
        result, session = self.login({'success': True, 'authenticated': True}, verified=False)
        self.assertIsNone(result); session.close.assert_called_once()
