import json
import requests

from .models import (
    SMSRequest,
    SMSResponse,
    StatusResponse,
    QuotaResponse,
)
from .exceptions import (
    QuotaExceededError,
    InvalidRequestError,
    APIError,
)

class TextbeltClient:
    """Client for interacting with the Textbelt API"""

    BASE_URL = "https://textbelt.com"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def send_sms(self, request: SMSRequest) -> SMSResponse:
        """Send an SMS using the Textbelt API"""
        payload = {
            "phone": request.phone,
            "message": request.message,
            "key": self.api_key,
        }

        if request.sender:
            payload["sender"] = request.sender
        if request.reply_webhook_url:
            payload["replyWebhookUrl"] = request.reply_webhook_url
        if request.webhook_data:
            payload["webhookData"] = request.webhook_data

        response = requests.post(f"{self.BASE_URL}/text", data=payload)

        try:
            data = response.json()
        except json.JSONDecodeError:
            raise APIError("Invalid JSON response from API")

        if not response.ok:
            raise APIError(f"API request failed: {data.get('error', 'Unknown error')}")

        if not data["success"]:
            if "quota" in data.get("error", "").lower():
                raise QuotaExceededError("SMS quota exceeded")
            raise InvalidRequestError(data.get("error", "Unknown error"))

        return SMSResponse(
            success=data["success"],
            quota_remaining=data["quotaRemaining"],
            text_id=data.get("textId"),
            error=data.get("error"),
        )

    def check_status(self, text_id: str) -> StatusResponse:
        """Check the delivery status of a sent message"""
        response = requests.get(f"{self.BASE_URL}/status/{text_id}")

        try:
            data = response.json()
        except json.JSONDecodeError:
            raise APIError("Invalid JSON response from API")

        if not response.ok:
            raise APIError(f"Failed to check status: {data.get('error', 'Unknown error')}")

        return StatusResponse(status=data["status"])

    def check_quota(self) -> QuotaResponse:
        """Check the remaining quota for the API key"""
        response = requests.get(f"{self.BASE_URL}/quota/{self.api_key}")

        try:
            data = response.json()
        except json.JSONDecodeError:
            raise APIError("Invalid JSON response from API")

        if not response.ok or not data["success"]:
            raise APIError("Failed to check quota")

        return QuotaResponse(
            success=data["success"],
            quota_remaining=data["quotaRemaining"]
        )

    def send_test(self, request: SMSRequest) -> SMSResponse:
        """Send a test SMS without using quota"""
        test_request = SMSRequest(
            phone=request.phone,
            message=request.message,
            key=f"{self.api_key}_test",
            sender=request.sender,
            reply_webhook_url=request.reply_webhook_url,
            webhook_data=request.webhook_data
        )
        return self.send_sms(test_request)
