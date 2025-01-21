import os
from textbelt_utils.client import TextbeltClient
from textbelt_utils.models import SMSRequest
from textbelt_utils.exceptions import QuotaExceededError, InvalidRequestError

def get_env_var(var_name: str) -> str:
    """Get environment variable or raise error with helpful message."""
    value = os.getenv(var_name)
    if not value:
        raise ValueError(
            f"Please set {var_name} environment variable\n"
            f"Example: export {var_name}=your_{var_name.lower()}_here"
        )
    return value

def main():
    # Get configuration from environment variables
    api_key = get_env_var('TEXTBELT_API_KEY')
    phone_number = get_env_var('TEXTBELT_TEST_PHONE')

    # Initialize client
    client = TextbeltClient(api_key=api_key)

    # Create request
    request = SMSRequest(
        phone=phone_number,
        message="Test message from textbelt-utils!",
        key=api_key
    )

    try:
        # Send test message (doesn't use quota)
        print("Sending test message...")
        response = client.send_test(request)
        print(f"Success: {response.success}")
        print(f"Message ID: {response.text_id}")
        print(f"Remaining quota: {response.quota_remaining}")

        # Check quota
        print("\nChecking quota...")
        quota = client.check_quota()
        print(f"Current quota: {quota.quota_remaining}")

    except QuotaExceededError:
        print("Error: Out of quota")
    except InvalidRequestError as e:
        print(f"Error: Invalid request - {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()