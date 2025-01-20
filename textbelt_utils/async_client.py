import httpx

from .models import (
    SMSRequest,
    SMSResponse,
    StatusResponse,
    QuotaResponse,
    OTPGenerateRequest,
    OTPGenerateResponse,
    OTPVerifyRequest,
    OTPVerifyResponse,
)
from .exceptions import (
    QuotaExceededError,
    InvalidRequestError,
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
        response.raise_for_status()
        
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
