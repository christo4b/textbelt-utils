import unittest
from unittest.mock import Mock, patch

from textbelt_utils.client import TextbeltClient
from textbelt_utils.models import BulkSMSRequest, SMSResponse
from textbelt_utils.exceptions import (
    QuotaExceededError,
    InvalidRequestError,
    BulkSendError,
    RateLimitError,
)

class TestBulkSMS(unittest.TestCase):
    def setUp(self):
        self.client = TextbeltClient(api_key="test_key")
        self.base_request = BulkSMSRequest(
            phones=["+12025550108", "+12025550109"],  # Example E.164 formatted numbers
            message="Test bulk message",
            key="test_key"
        )

    def test_bulk_request_validation(self):
        # Test valid request with shared message
        request = BulkSMSRequest(
            phones=["+12025550108", "+12025550109"],  # Example E.164 formatted numbers
            message="Test message",
            key="test_key"
        )
        self.assertEqual(len(request.phones), 2)
        self.assertEqual(request.message, "Test message")

        # Test valid request with individual messages
        request = BulkSMSRequest(
            phones=["+12025550108", "+12025550109"],  # Example E.164 formatted numbers
            individual_messages={
                "+12025550108": "Message 1",
                "+12025550109": "Message 2"
            },
            key="test_key"
        )
        self.assertEqual(len(request.phones), 2)
        self.assertEqual(request.individual_messages["+12025550108"], "Message 1")

        # Test invalid phone number format
        with self.assertRaises(ValueError):
            BulkSMSRequest(
                phones=["12025550108"],  # Missing +
                message="Test message",
                key="test_key"
            )

        # Test empty phones list
        with self.assertRaises(ValueError):
            BulkSMSRequest(
                phones=[],
                message="Test message",
                key="test_key"
            )

        # Test missing messages for some phones
        with self.assertRaises(ValueError):
            BulkSMSRequest(
                phones=["+12025550108", "+12025550109"],
                individual_messages={"+12025550108": "Message 1"},
                key="test_key"
            )

        # Test invalid batch size
        with self.assertRaises(ValueError):
            BulkSMSRequest(
                phones=["+12025550108"],
                message="Test message",
                key="test_key",
                batch_size=0
            )

        # Test invalid delay
        with self.assertRaises(ValueError):
            BulkSMSRequest(
                phones=["+12025550108"],
                message="Test message",
                key="test_key",
                delay_between_messages=0.01
            )

    @patch('requests.post')
    def test_bulk_send_success(self, mock_post):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "success": True,
            "quotaRemaining": 100,
            "textId": "12345"
        }
        mock_post.return_value = mock_response

        response = self.client.send_bulk_sms(self.base_request)

        self.assertEqual(response.total_messages, 2)
        self.assertEqual(response.successful_messages, 2)
        self.assertEqual(response.failed_messages, 0)
        self.assertTrue(response.success)
        self.assertFalse(response.partial_success)

    @patch('requests.post')
    def test_bulk_send_partial_failure(self, mock_post):
        def mock_send(*args, **kwargs):
            data = kwargs.get('data', {})
            phone = data.get('phone')
            if phone == "+12025550108":
                return Mock(
                    ok=True,
                    json=lambda: {
                        "success": True,
                        "quotaRemaining": 100,
                        "textId": "12345"
                    }
                )
            return Mock(
                ok=True,
                json=lambda: {
                    "success": False,
                    "error": "Invalid number",
                    "quotaRemaining": 99
                }
            )

        mock_post.side_effect = mock_send

        response = self.client.send_bulk_sms(self.base_request)

        self.assertEqual(response.total_messages, 2)
        self.assertEqual(response.successful_messages, 1)
        self.assertEqual(response.failed_messages, 1)
        self.assertFalse(response.success)
        self.assertTrue(response.partial_success)
        self.assertEqual(len(response.errors), 1)
        self.assertIn("Invalid number", response.errors["+12025550109"])

    @patch('requests.post')
    def test_bulk_send_quota_exceeded(self, mock_post):
        def mock_send(*args, **kwargs):
            return Mock(
                ok=True,
                json=lambda: {
                    "success": False,
                    "quotaRemaining": 0,
                    "error": "Out of quota"
                }
            )

        mock_post.side_effect = mock_send

        with self.assertRaises(QuotaExceededError) as context:
            self.client.send_bulk_sms(self.base_request)
        self.assertIn("quota exceeded", str(context.exception))

    @patch('requests.post')
    def test_bulk_send_rate_limit(self, mock_post):
        def mock_send(*args, **kwargs):
            return Mock(
                ok=False,
                status_code=429,
                json=lambda: {
                    "success": False,
                    "error": "Rate limit exceeded",
                    "retryAfter": 60
                }
            )

        mock_post.side_effect = mock_send

        with self.assertRaises(RateLimitError) as context:
            self.client.send_bulk_sms(self.base_request)
        self.assertEqual(context.exception.retry_after, 60)

if __name__ == '__main__':
    unittest.main() 