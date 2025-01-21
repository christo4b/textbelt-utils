from textbelt_utils import (
    TextbeltClient,
    BulkSMSRequest,
    load_config,
    get_env_var,
)
from textbelt_utils.exceptions import (
    QuotaExceededError,
    InvalidRequestError,
)

def main():
    # Load environment variables from .env file
    load_config()
    
    # Get configuration from environment variables
    api_key = get_env_var('TEXTBELT_API_KEY')
    test_phone1 = get_env_var('TEXTBELT_TEST_PHONE')
    test_phone2 = get_env_var('TEXTBELT_TEST_PHONE2')
    
    # Initialize client
    client = TextbeltClient(api_key=api_key)
    
    # Create request with individual messages
    request = BulkSMSRequest(
        phones=[test_phone1, test_phone2],
        individual_messages={
            test_phone1: "Hello! This is test message #1 from textbelt-utils bulk send!",
            test_phone2: "Hello! This is test message #2 from textbelt-utils bulk send!"
        },
        batch_size=2,
        delay_between_messages=1.0
    )
    
    try:
        # Check quota before sending
        quota = client.check_quota()
        print(f"\nCurrent quota: {quota.quota_remaining}")
        
        # Send messages
        print("\nSending messages...")
        response = client.send_bulk_sms(request)
        
        # Print results
        print(f"\nResults:")
        print(f"Total messages: {response.total_messages}")
        print(f"Successful: {response.successful_messages}")
        print(f"Failed: {response.failed_messages}")
        
        if response.errors:
            print("\nErrors:")
            for phone, error in response.errors.items():
                print(f"  {phone}: {error}")
        
        # Check message statuses
        print("\nMessage statuses:")
        for phone, result in response.results.items():
            if result.text_id:
                status = client.check_status(result.text_id)
                print(f"  {phone}: {status.status}")
        
        # Check remaining quota
        quota = client.check_quota()
        print(f"\nRemaining quota: {quota.quota_remaining}")
        
    except QuotaExceededError:
        print("Error: Out of quota")
    except InvalidRequestError as e:
        print(f"Error: Invalid request - {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main() 