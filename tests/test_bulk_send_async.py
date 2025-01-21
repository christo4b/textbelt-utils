import asyncio
from unittest.mock import Mock

import httpx
import pytest
import pytest_asyncio

from textbelt_utils.async_client import AsyncTextbeltClient
from textbelt_utils.models import BulkSMSRequest, SMSResponse
from textbelt_utils.exceptions import (
    QuotaExceededError,
    InvalidRequestError,
    BulkSendError,
    RateLimitError,
)

@pytest_asyncio.fixture
async def client():
    client = AsyncTextbeltClient(api_key="test_key")
    try:
        yield client
    finally:
        await client._client.aclose()

@pytest.fixture
def base_request():
    return BulkSMSRequest(
        phones=["+12025550108", "+12025550109"],  # Example E.164 formatted numbers
        message="Test bulk message",
        key="test_key"
    )

def test_bulk_request_validation():
    # Test valid request with shared message
    request = BulkSMSRequest(
        phones=["+12025550108", "+12025550109"],  # Example E.164 formatted numbers
        message="Test message",
        key="test_key"
    )
    assert len(request.phones) == 2
    assert request.message == "Test message"

    # Test valid request with individual messages
    request = BulkSMSRequest(
        phones=["+12025550108", "+12025550109"],  # Example E.164 formatted numbers
        individual_messages={
            "+12025550108": "Message 1",
            "+12025550109": "Message 2"
        },
        key="test_key"
    )
    assert len(request.phones) == 2
    assert request.individual_messages["+12025550108"] == "Message 1"

    # Test invalid phone number format
    with pytest.raises(ValueError):
        BulkSMSRequest(
            phones=["12025550108"],  # Missing +
            message="Test message",
            key="test_key"
        )

    # Test empty phones list
    with pytest.raises(ValueError):
        BulkSMSRequest(
            phones=[],
            message="Test message",
            key="test_key"
        )

    # Test missing messages for some phones
    with pytest.raises(ValueError):
        BulkSMSRequest(
            phones=["+12025550108", "+12025550109"],
            individual_messages={"+12025550108": "Message 1"},
            key="test_key"
        )

    # Test invalid batch size
    with pytest.raises(ValueError):
        BulkSMSRequest(
            phones=["+12025550108"],
            message="Test message",
            key="test_key",
            batch_size=0
        )

    # Test invalid delay
    with pytest.raises(ValueError):
        BulkSMSRequest(
            phones=["+12025550108"],
            message="Test message",
            key="test_key",
            delay_between_messages=0.01
        )

@pytest.mark.asyncio
async def test_bulk_send_success(client, base_request, respx_mock):
    # Mock successful responses for both messages
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

    response = await client.send_bulk_sms(base_request)

    assert response.total_messages == 2
    assert response.successful_messages == 2
    assert response.failed_messages == 0
    assert response.success is True
    assert response.partial_success is False

@pytest.mark.asyncio
async def test_bulk_send_partial_failure(client, base_request, respx_mock):
    # Mock different responses based on phone number
    def mock_response(request):
        # Parse form data
        form_data = {}
        for item in request.content.decode().split("&"):
            if "=" in item:
                key, value = item.split("=", 1)
                form_data[key] = value.replace("%2B", "+")  # Handle URL encoding

        phone = form_data.get("phone")

        if phone == "+12025550108":
            return httpx.Response(
                200,
                json={
                    "success": True,
                    "quotaRemaining": 100,
                    "textId": "12345"
                }
            )
        return httpx.Response(
            200,
            json={
                "success": False,
                "error": "Invalid number",
                "quotaRemaining": 99
            }
        )

    respx_mock.post("https://textbelt.com/text").mock(side_effect=mock_response)

    response = await client.send_bulk_sms(base_request)

    assert response.total_messages == 2
    assert response.successful_messages == 1
    assert response.failed_messages == 1
    assert not response.success
    assert response.partial_success
    assert len(response.errors) == 1
    assert "Invalid number" in response.errors["+12025550109"]

@pytest.mark.asyncio
async def test_bulk_send_quota_exceeded(client, base_request, respx_mock):
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

    with pytest.raises(QuotaExceededError) as exc_info:
        await client.send_bulk_sms(base_request)
    assert "quota exceeded" in str(exc_info.value)

@pytest.mark.asyncio
async def test_bulk_send_rate_limit(client, base_request, respx_mock):
    respx_mock.post("https://textbelt.com/text").mock(
        return_value=httpx.Response(
            429,
            json={
                "success": False,
                "error": "Rate limit exceeded",
                "retryAfter": 60
            }
        )
    )

    with pytest.raises(RateLimitError) as exc_info:
        await client.send_bulk_sms(base_request)
    assert exc_info.value.retry_after == 60

@pytest.mark.asyncio
async def test_bulk_send_concurrent_batching(client, respx_mock):
    # Test that messages are sent in correct batch sizes
    phones = [f"+1{i:010d}" for i in range(150)]  # 150 phone numbers
    request = BulkSMSRequest(
        phones=phones,
        message="Test message",
        key="test_key",
        batch_size=50  # Should create 3 batches
    )

    # Track the number of concurrent requests
    concurrent_requests = 0
    max_concurrent = 0

    async def mock_response(request):
        nonlocal concurrent_requests, max_concurrent
        concurrent_requests += 1
        max_concurrent = max(max_concurrent, concurrent_requests)
        
        # Simulate some processing time
        await asyncio.sleep(0.1)
        
        concurrent_requests -= 1
        return httpx.Response(
            200,
            json={
                "success": True,
                "quotaRemaining": 100,
                "textId": "12345"
            }
        )

    respx_mock.post("https://textbelt.com/text").mock(side_effect=mock_response)

    response = await client.send_bulk_sms(request)

    assert response.total_messages == 150
    assert response.successful_messages == 150
    assert max_concurrent <= 50  # Ensure we don't exceed batch size 