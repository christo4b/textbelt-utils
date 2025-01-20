import pytest
from unittest.mock import Mock
import json

import httpx
import pytest_asyncio

from textbelt_utils.async_client import AsyncTextbeltClient
from textbelt_utils.models import (
    SMSRequest,
    OTPGenerateRequest,
    OTPVerifyRequest,
)
from textbelt_utils.exceptions import QuotaExceededError, InvalidRequestError

@pytest_asyncio.fixture
async def client():
    client = AsyncTextbeltClient(api_key="test_key")
    try:
        yield client
    finally:
        await client._client.aclose()

@pytest.fixture
def base_request():
    return SMSRequest(
        phone="+1234567890"Add support for bulk SMS sending,
        message="Test message",
        key="test_key"
    )

def test_sms_request_validation():
    # Test valid phone number
    request = SMSRequest(
        phone="+1234567890",
        message="Test message",
        key="test_key"
    )
    assert request.phone == "+1234567890"

    # Test invalid phone number format
    with pytest.raises(ValueError, match="Phone number must be in E.164 format"):
        SMSRequest(
            phone="1234567890",  # Missing +
            message="Test message",
            key="test_key"
        )

    # Test empty message
    with pytest.raises(ValueError, match="Message cannot be empty"):
        SMSRequest(
            phone="+1234567890",
            message="",
            key="test_key"
        )

    # Test message too long
    with pytest.raises(ValueError, match="Message length exceeds maximum"):
        SMSRequest(
            phone="+1234567890",
            message="x" * (SMSRequest.MAX_MESSAGE_LENGTH + 1),
            key="test_key"
        )

@pytest.mark.asyncio
async def test_send_sms_success(client, base_request, respx_mock):
    respx_mock.post("https://textbelt.com/text").mock(
        return_value=httpx.Response(
            200,
            json={
                "success": True,
                "quotaRemaining": 100,
                "textId": "12345"
            }
        )
    )

    response = await client.send_sms(base_request)

    assert response.success is True
    assert response.quota_remaining == 100
    assert response.text_id == "12345"

@pytest.mark.asyncio
async def test_send_sms_quota_exceeded(client, base_request, respx_mock):
    respx_mock.post("https://textbelt.com/text").mock(
        return_value=httpx.Response(
            200,
            json={
                "success": False,
                "quotaRemaining": 0,
                "error": "Out of quota"
            }
        )
    )

    with pytest.raises(QuotaExceededError):
        await client.send_sms(base_request)

@pytest.mark.asyncio
async def test_check_status(client, respx_mock):
    respx_mock.get("https://textbelt.com/status/12345").mock(
        return_value=httpx.Response(
            200,
            json={"status": "DELIVERED"}
        )
    )

    response = await client.check_status("12345")
    assert response.status == "DELIVERED"

@pytest.mark.asyncio
async def test_check_quota(client, respx_mock):
    respx_mock.get("https://textbelt.com/quota/test_key").mock(
        return_value=httpx.Response(
            200,
            json={
                "success": True,
                "quotaRemaining": 50
            }
        )
    )

    response = await client.check_quota()
    assert response.success is True
    assert response.quota_remaining == 50

@pytest.mark.asyncio
async def test_send_test_sms(client, base_request, respx_mock):
    respx_mock.post("https://textbelt.com/text").mock(
        return_value=httpx.Response(
            200,
            json={
                "success": True,
                "quotaRemaining": 100,
                "textId": "test_12345"
            }
        )
    )

    response = await client.send_test(base_request)
    assert response.success is True
    assert response.text_id == "test_12345"

def test_otp_request_validation():
    # Test valid OTP generate request
    request = OTPGenerateRequest(
        phone="+1234567890",
        userid="user123",
        key="test_key",
        lifetime=60,
        length=6
    )
    assert request.phone == "+1234567890"
    assert request.lifetime == 60
    assert request.length == 6

    # Test invalid phone number
    with pytest.raises(ValueError, match="Phone number must be in E.164 format"):
        OTPGenerateRequest(
            phone="1234567890",  # Missing +
            userid="user123",
            key="test_key"
        )

    # Test empty userid
    with pytest.raises(ValueError, match="userid cannot be empty"):
        OTPGenerateRequest(
            phone="+1234567890",
            userid="",
            key="test_key"
        )

    # Test invalid lifetime
    with pytest.raises(ValueError, match="lifetime must be between"):
        OTPGenerateRequest(
            phone="+1234567890",
            userid="user123",
            key="test_key",
            lifetime=10  # Too short
        )

    # Test invalid length
    with pytest.raises(ValueError, match="length must be between"):
        OTPGenerateRequest(
            phone="+1234567890",
            userid="user123",
            key="test_key",
            length=2  # Too short
        )

def test_otp_verify_request_validation():
    # Test valid OTP verify request
    request = OTPVerifyRequest(
        otp="123456",
        userid="user123",
        key="test_key"
    )
    assert request.otp == "123456"

    # Test empty OTP
    with pytest.raises(ValueError, match="otp cannot be empty"):
        OTPVerifyRequest(
            otp="",
            userid="user123",
            key="test_key"
        )

    # Test non-digit OTP
    with pytest.raises(ValueError, match="otp must contain only digits"):
        OTPVerifyRequest(
            otp="12a456",
            userid="user123",
            key="test_key"
        )

    # Test empty userid
    with pytest.raises(ValueError, match="userid cannot be empty"):
        OTPVerifyRequest(
            otp="123456",
            userid="",
            key="test_key"
        )

@pytest.mark.asyncio
async def test_generate_otp_success(client, respx_mock):
    request = OTPGenerateRequest(
        phone="+1234567890",
        userid="user123",
        key="test_key",
        message="Your code is $OTP",
        lifetime=60,
        length=6
    )

    respx_mock.post("https://textbelt.com/otp/generate").mock(
        return_value=httpx.Response(
            200,
            json={
                "success": True,
                "quotaRemaining": 100,
                "textId": "12345",
                "otp": "123456"  # Only returned in test mode
            }
        )
    )

    response = await client.generate_otp(request)
    assert response.success is True
    assert response.quota_remaining == 100
    assert response.text_id == "12345"
    assert response.otp == "123456"

@pytest.mark.asyncio
async def test_generate_otp_quota_exceeded(client, respx_mock):
    request = OTPGenerateRequest(
        phone="+1234567890",
        userid="user123",
        key="test_key"
    )

    respx_mock.post("https://textbelt.com/otp/generate").mock(
        return_value=httpx.Response(
            200,
            json={
                "success": False,
                "quotaRemaining": 0,
                "error": "Out of quota"
            }
        )
    )

    with pytest.raises(QuotaExceededError):
        await client.generate_otp(request)

@pytest.mark.asyncio
async def test_verify_otp_success(client, respx_mock):
    request = OTPVerifyRequest(
        otp="123456",
        userid="user123",
        key="test_key"
    )

    respx_mock.get("https://textbelt.com/otp/verify").mock(
        return_value=httpx.Response(
            200,
            json={
                "success": True,
                "isValidOtp": True
            }
        )
    )

    response = await client.verify_otp(request)
    assert response.success is True
    assert response.is_valid_otp is True

@pytest.mark.asyncio
async def test_verify_otp_invalid(client, respx_mock):
    request = OTPVerifyRequest(
        otp="123456",
        userid="user123",
        key="test_key"
    )

    respx_mock.get("https://textbelt.com/otp/verify").mock(
        return_value=httpx.Response(
            200,
            json={
                "success": True,
                "isValidOtp": False
            }
        )
    )

    response = await client.verify_otp(request)
    assert response.success is True
    assert response.is_valid_otp is False
