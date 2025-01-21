import json
import time
from typing import Dict

import requests

from .models import (
    SMSRequest,
    SMSResponse,
    StatusResponse,
    QuotaResponse,
    BulkSMSRequest,
    BulkSMSResponse,
)
from .exceptions import (
    QuotaExceededError,
    InvalidRequestError,
    APIError,
    RateLimitError,
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

        # Handle rate limiting
        if response.status_code == 429:
            data = response.json()
            retry_after = data.get("retryAfter", 60)
            raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds", retry_after)

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

    def send_bulk_sms(self, request: BulkSMSRequest) -> BulkSMSResponse:
        """Send multiple SMS messages in bulk with rate limiting.
        
        Args:
            request: A BulkSMSRequest object containing the messages to send
            
        Returns:
            A BulkSMSResponse object containing the results of the bulk send operation
            
        Raises:
            QuotaExceededError: If the quota is exceeded during sending
            InvalidRequestError: If any of the messages are invalid
            APIError: If there is an error communicating with the API
            RateLimitError: If rate limit is exceeded
        """
        results: dict[str, SMSResponse] = {}
        errors: dict[str, str] = {}
        
        # Create batches of phone numbers
        phone_batches = [
            request.phones[i:i + request.batch_size]
            for i in range(0, len(request.phones), request.batch_size)
        ]
        
        for batch in phone_batches:
            for phone in batch:
                try:
                    # Create individual SMS request
                    message = request.message if request.message is not None else request.individual_messages[phone]
                    sms_request = SMSRequest(
                        phone=phone,
                        message=message,
                        key=request.key or self.api_key,
                        sender=request.sender,
                        reply_webhook_url=request.reply_webhook_url,
                        webhook_data=request.webhook_data
                    )
                    
                    # Send the message
                    response = self.send_sms(sms_request)
                    results[phone] = response
                    
                    # Apply rate limiting delay
                    if request.delay_between_messages > 0:
                        time.sleep(request.delay_between_messages)
                        
                except (QuotaExceededError, RateLimitError) as e:
                    # Propagate critical errors immediately
                    raise
                except Exception as e:
                    errors[phone] = str(e)
        
        # Calculate statistics
        total_messages = len(request.phones)
        successful_messages = len([r for r in results.values() if r.success])
        failed_messages = total_messages - successful_messages
        
        return BulkSMSResponse(
            total_messages=total_messages,
            successful_messages=successful_messages,
            failed_messages=failed_messages,
            results=results,
            errors=errors
        )
