import httpx
import asyncio
from typing import List, Dict

from .models import (
    SMSRequest,
    SMSResponse,
    StatusResponse,
    QuotaResponse,
    OTPGenerateRequest,
    OTPGenerateResponse,
    OTPVerifyRequest,
    OTPVerifyResponse,
    BulkSMSRequest,
    BulkSMSResponse,
)
from .exceptions import (
    QuotaExceededError,
    InvalidRequestError,
    RateLimitError,
    APIError,
)

class AsyncTextbeltClient:
    """Async client for interacting with the Textbelt API"""
    
    BASE_URL = "https://textbelt.com"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = httpx.AsyncClient()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()

    async def send_sms(self, request: SMSRequest) -> SMSResponse:
        """Send an SMS using the Textbelt API asynchronously"""
        payload = {
            "phone": request.phone,
            "message": request.message,
            "key": self.api_key,
            **({"sender": request.sender} if request.sender else {}),
            **({"replyWebhookUrl": request.reply_webhook_url} if request.reply_webhook_url else {}),
            **({"webhookData": request.webhook_data} if request.webhook_data else {})
        }

        response = await self._client.post(f"{self.BASE_URL}/text", data=payload)
        
        # Handle rate limiting
        if response.status_code == 429:
            data = response.json()
            retry_after = data.get("retryAfter", 60)
            raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds", retry_after)
            
        # Handle other HTTP errors
        try:
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise APIError(f"API request failed: {str(e)}")
        
        data = response.json()
        
        if not data["success"]:
            if "quota" in data.get("error", "").lower():
                raise QuotaExceededError("SMS quota exceeded")
            raise InvalidRequestError(data.get("error", "Unknown error"))

        return SMSResponse(
            success=data["success"],
            quota_remaining=data["quotaRemaining"],
            text_id=data.get("textId"),
            error=data.get("error")
        )

    async def check_status(self, text_id: str) -> StatusResponse:
        """Check the delivery status of a sent message asynchronously"""
        response = await self._client.get(f"{self.BASE_URL}/status/{text_id}")
        response.raise_for_status()
        data = response.json()
        return StatusResponse(status=data["status"])

    async def check_quota(self) -> QuotaResponse:
        """Check the remaining quota for the API key asynchronously"""
        response = await self._client.get(f"{self.BASE_URL}/quota/{self.api_key}")
        response.raise_for_status()
        data = response.json()
        return QuotaResponse(
            success=data["success"],
            quota_remaining=data["quotaRemaining"]
        )

    async def send_test(self, request: SMSRequest) -> SMSResponse:
        """Send a test SMS without using quota asynchronously"""
        test_request = SMSRequest(
            phone=request.phone,
            message=request.message,
            key=f"{self.api_key}_test",
            sender=request.sender,
            reply_webhook_url=request.reply_webhook_url,
            webhook_data=request.webhook_data
        )
        return await self.send_sms(test_request)

    async def generate_otp(self, request: OTPGenerateRequest) -> OTPGenerateResponse:
        """Generate and send a one-time password via SMS.
        
        Args:
            request: The OTP generation request containing phone, userid, and options
            
        Returns:
            OTPGenerateResponse containing success status and OTP details
            
        Raises:
            QuotaExceededError: If you've run out of message quota
            InvalidRequestError: If the request is invalid
        """
        payload = {
            "phone": request.phone,
            "userid": request.userid,
            "key": self.api_key,
        }
        
        if request.message:
            payload["message"] = request.message
        if request.lifetime:
            payload["lifetime"] = request.lifetime
        if request.length:
            payload["length"] = request.length

        response = await self._client.post(f"{self.BASE_URL}/otp/generate", data=payload)
        response.raise_for_status()
        
        data = response.json()
        
        if not data["success"]:
            if "quota" in data.get("error", "").lower():
                raise QuotaExceededError("SMS quota exceeded")
            raise InvalidRequestError(data.get("error", "Unknown error"))

        return OTPGenerateResponse(
            success=data["success"],
            quota_remaining=data["quotaRemaining"],
            text_id=data.get("textId"),
            otp=data.get("otp"),
            error=data.get("error")
        )

    async def verify_otp(self, request: OTPVerifyRequest) -> OTPVerifyResponse:
        """Verify a one-time password entered by a user.
        
        Args:
            request: The OTP verification request containing the code and userid
            
        Returns:
            OTPVerifyResponse indicating whether the code is valid
            
        Raises:
            InvalidRequestError: If the request is invalid
        """
        params = {
            "otp": request.otp,
            "userid": request.userid,
            "key": self.api_key,
        }

        response = await self._client.get(f"{self.BASE_URL}/otp/verify", params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if not data["success"]:
            raise InvalidRequestError(data.get("error", "Unknown error"))

        return OTPVerifyResponse(
            success=data["success"],
            is_valid_otp=data["isValidOtp"],
            error=data.get("error")
        )

    async def send_bulk_sms(self, request: BulkSMSRequest) -> BulkSMSResponse:
        """Send multiple SMS messages in bulk with concurrent sending and rate limiting.
        
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
        results: Dict[str, SMSResponse] = {}
        errors: Dict[str, str] = {}
        
        # Create batches of phone numbers
        phone_batches = [
            request.phones[i:i + request.batch_size]
            for i in range(0, len(request.phones), request.batch_size)
        ]
        
        async def send_message(phone: str) -> tuple[str, SMSResponse | Exception]:
            try:
                message = request.message if request.message is not None else request.individual_messages[phone]
                sms_request = SMSRequest(
                    phone=phone,
                    message=message,
                    key=request.key or self.api_key,
                    sender=request.sender,
                    reply_webhook_url=request.reply_webhook_url,
                    webhook_data=request.webhook_data
                )
                response = await self.send_sms(sms_request)
                return phone, response
            except (QuotaExceededError, RateLimitError) as e:
                # Propagate critical errors
                raise
            except Exception as e:
                return phone, e
        
        # Process each batch with concurrent sending
        for batch in phone_batches:
            # Create tasks for concurrent sending within the batch
            tasks = [send_message(phone) for phone in batch]
            
            try:
                # Wait for all messages in the batch to complete
                batch_results = await asyncio.gather(*tasks)
                
                # Process results
                for phone, result in batch_results:
                    if isinstance(result, Exception):
                        errors[phone] = str(result)
                    else:
                        results[phone] = result
                
                # Apply rate limiting delay between batches if there are more batches
                if request.delay_between_messages > 0 and batch != phone_batches[-1]:
                    await asyncio.sleep(request.delay_between_messages)
            except (QuotaExceededError, RateLimitError) as e:
                # Propagate critical errors
                raise
        
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
