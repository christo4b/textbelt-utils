import os
import asyncio
from textbelt_utils.async_client import AsyncTextbeltClient
from textbelt_utils.models import SMSRequest
from textbelt_utils.exceptions import QuotaExceededError, InvalidRequestError

async def main():
    # Get configuration from environment variables
    api_key = os.getenv('TEXTBELT_API_KEY')
    phone_number = os.getenv('TEXTBELT_TEST_PHONE')

    if not api_key or not phone_number:
        raise ValueError("Please set TEXTBELT_API_KEY and TEXTBELT_TEST_PHONE environment variables")

    # Create request
    request = SMSRequest(
        phone=phone_number,
        message="Async test message from textbelt-utils!",
        key=api_key
    )

    try:
        async with AsyncTextbeltClient(api_key=api_key) as client:
            # Send test message
            print("Sending test message...")
            response = await client.send_test(request)
            print(f"Success: {response.success}")
            print(f"Message ID: {response.text_id}")
            print(f"Remaining quota: {response.quota_remaining}")

            # Check quota
            print("\nChecking quota...")
            quota = await client.check_quota()
            print(f"Current quota: {quota.quota_remaining}")

    except QuotaExceededError:
        print("Error: Out of quota")
    except InvalidRequestError as e:
        print(f"Error: Invalid request - {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    asyncio.run(main())
