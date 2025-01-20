import pytest
from unittest.mock import Mock
import json

import httpx
import pytest_asyncio

from textbelt_utils.async_client import AsyncTextbeltClient
from textbelt_utils.models import SMSRequest
from textbelt_utils.exceptions import QuotaExceededError

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
        phone="+1234567890",
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

@pytest.mark.asyncio
async def test_send_sms_with_sender_name(client, respx_mock):
    request = SMSRequest(
        phone="+1234567890",
        message="Test message with custom sender",
        key="test_key",
        sender="MyCompany"
    )

    # Mock to ensure sender is included in the request
    route = respx_mock.post("https://textbelt.com/text").mock(
        return_value=httpx.Response(
            200,
            json={
                "success": True,
                "quotaRemaining": 100,
                "textId": "12345"
            }
        )
    )

    response = await client.send_sms(request)
    
    # Verify the sender was included in the request data
    assert b"sender=MyCompany" in route.calls.last.request.content
    assert response.success is True

@pytest.mark.asyncio
async def test_send_test_sms_with_sender_name(client, respx_mock):
    request = SMSRequest(
        phone="+1234567890",
        message="Test message with custom sender",
        key="test_key",
        sender="MyCompany"
    )

    # Mock to ensure sender is included in the request
    route = respx_mock.post("https://textbelt.com/text").mock(
        return_value=httpx.Response(
            200,
            json={
                "success": True,
                "quotaRemaining": 100,
                "textId": "test_12345"
            }
        )
    )

    response = await client.send_test(request)
    
    # Verify the sender was included in the request data
    assert b"sender=MyCompany" in route.calls.last.request.content
    assert response.success is True 