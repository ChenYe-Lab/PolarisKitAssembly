import json
from unittest.mock import Mock, patch

from django.test import Client, TestCase


class FeedbackSubmissionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.client.cookies["kitapp_visitor_id"] = "12345"

    @patch("kitserver.views._post_webdatabase_json")
    @patch("kitserver.views.__create_session")
    def test_submit_feedback_forwards_payload_to_webdatabase(self, mock_create_session, mock_post):
        mock_create_session.return_value = object()
        mock_post.return_value = (
            Mock(status_code=201),
            {
                "success": True,
                "data": {
                    "id": 9,
                    "visitor_id": 12345,
                    "feedback_type": "issue",
                    "title": "Homepage button overlaps",
                },
            },
        )

        response = self.client.post(
            "/kitserver/submit_feedback",
            data=json.dumps(
                {
                    "feedback_type": "issue",
                    "title": "Homepage button overlaps",
                    "content": "The submit button overlaps on small screens.",
                    "contact_email": "alice@example.com",
                    "page_path": "/kitserver/index",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        mock_post.assert_called_once_with(
            mock_create_session.return_value,
            "createVisitorFeedback",
            {
                "visitor_id": "12345",
                "feedback_type": "issue",
                "title": "Homepage button overlaps",
                "content": "The submit button overlaps on small screens.",
                "contact_email": "alice@example.com",
                "page_path": "/kitserver/index",
            },
        )

    def test_submit_feedback_rejects_missing_title_or_content(self):
        response = self.client.post(
            "/kitserver/submit_feedback",
            data=json.dumps(
                {
                    "feedback_type": "suggestion",
                    "title": "",
                    "content": "",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    @patch("kitserver.views.__create_session")
    def test_submit_feedback_requires_api_login(self, mock_create_session):
        mock_create_session.return_value = None

        response = self.client.post(
            "/kitserver/submit_feedback",
            data=json.dumps(
                {
                    "feedback_type": "issue",
                    "title": "Need help",
                    "content": "The homepage is unclear.",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
