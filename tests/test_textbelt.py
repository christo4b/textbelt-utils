import unittest
from unittest.mock import patch, Mock
import json

from textbelt_utils.client import TextbeltClient
from textbelt_utils.models import SMSRequest, SMSResponse, StatusResponse, QuotaResponse
from textbelt_utils.exceptions import QuotaExceededError, InvalidRequestError, APIError, WebhookVerificationError
from textbelt_utils.utils import verify_webhook, is_valid_e164

class TestTextbeltClient(unittest.TestCase):
    def setUp(self):
        self.client = TextbeltClient(api_key="test_key")
        self.base_request = SMSRequest(
            phone="+1234567890",
            message="Test message",
            key="test_key"
        )

    @patch('requests.post')
    def test_send_sms_success(self, mock_post):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "success": True,
            "quotaRemaining": 100,
            "textId": "12345"
        }
        mock_post.return_value = mock_response

        response = self.client.send_sms(self.base_request)

        self.assertTrue(response.success)
        self.assertEqual(response.quota_remaining, 100)
        self.assertEqual(response.text_id, "12345")

    @patch('requests.post')
    def test_send_sms_quota_exceeded(self, mock_post):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "success": False,
            "quotaRemaining": 0,
            "error": "Out of quota"
        }
        mock_post.return_value = mock_response

        with self.assertRaises(QuotaExceededError):
            self.client.send_sms(self.base_request)

    @patch('requests.get')
    def test_check_status(self, mock_get):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": "DELIVERED"}
        mock_get.return_value = mock_response

        response = self.client.check_status("12345")
        self.assertEqual(response.status, "DELIVERED")

    @patch('requests.get')
    def test_check_quota(self, mock_get):
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "success": True,
            "quotaRemaining": 50
        }
        mock_get.return_value = mock_response

        response = self.client.check_quota()
        self.assertTrue(response.success)
        self.assertEqual(response.quota_remaining, 50)

class TestUtils(unittest.TestCase):
    def test_valid_e164(self):
        valid_numbers = [
            "+1234567890",
            "+441234567890",
            "+6591234567"
        ]
        invalid_numbers = [
            "1234567890",  # No plus
            "+123",        # Too short
            "+12345678901234567",  # Too long
            "+1234abcd",   # Non-digits
            "",           # Empty
            None,         # None
        ]

        for number in valid_numbers:
            self.assertTrue(is_valid_e164(number))

        for number in invalid_numbers:
            self.assertFalse(is_valid_e164(number) if number is not None else False)

    def test_webhook_verification(self):
        import time
        
        api_key = "test_key"
        timestamp = str(int(time.time()))  # Current timestamp
        payload = json.dumps({"test": "data"})
        
        # Generate a valid signature
        import hmac
        import hashlib
        valid_signature = hmac.new(
            api_key.encode('utf-8'),
            (timestamp + payload).encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Test valid signature
        self.assertTrue(verify_webhook(api_key, timestamp, valid_signature, payload))
        
        # Test invalid signature
        self.assertFalse(verify_webhook(api_key, timestamp, "invalid_signature", payload))
        
        # Test expired timestamp
        old_timestamp = str(int(time.time()) - 1000)
        old_signature = hmac.new(
            api_key.encode('utf-8'),
            (old_timestamp + payload).encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        with self.assertRaises(WebhookVerificationError):
            verify_webhook(api_key, old_timestamp, old_signature, payload)

if __name__ == '__main__':
    unittest.main()