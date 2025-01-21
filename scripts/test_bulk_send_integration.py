import os
import asyncio
from typing import List
import argparse

from textbelt_utils import TextbeltClient, AsyncTextbeltClient, BulkSMSRequest
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

def test_sync_bulk_send():
    """Test synchronous bulk SMS sending."""
    print("\n🔄 Testing synchronous bulk SMS...")
    
    # Get configuration
    api_key = get_env_var('TEXTBELT_API_KEY')
    phones = [get_env_var('TEXTBELT_TEST_PHONE')] * 3  # Send 3 messages to same number
    
    # Initialize client
    client = TextbeltClient(api_key=api_key)
    
    # Create request with individual messages
    request = BulkSMSRequest(
        phones=phones,
        individual_messages={
            phone: f"Test message {i+1} from textbelt-utils bulk send!"
            for i, phone in enumerate(phones)
        },
        key=api_key,
        batch_size=2,  # Small batch size for testing
        delay_between_messages=1.0  # 1 second delay between messages
    )
    
    try:
        # Send messages
        print("Sending messages...")
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

async def test_async_bulk_send():
    """Test asynchronous bulk SMS sending."""
    print("\n⚡ Testing asynchronous bulk SMS...")
    
    # Get configuration
    api_key = get_env_var('TEXTBELT_API_KEY')
    phones = [get_env_var('TEXTBELT_TEST_PHONE')] * 3  # Send 3 messages to same number
    
    try:
        async with AsyncTextbeltClient(api_key=api_key) as client:
            # Create request with shared message
            request = BulkSMSRequest(
                phones=phones,
                message="Test message from textbelt-utils async bulk send!",
                key=api_key,
                batch_size=2,  # Small batch size for testing
                delay_between_messages=1.0  # 1 second delay between messages
            )
            
            # Send messages
            print("Sending messages...")
            response = await client.send_bulk_sms(request)
            
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
            status_tasks = []
            for phone, result in response.results.items():
                if result.text_id:
                    status_tasks.append(client.check_status(result.text_id))
            
            if status_tasks:
                statuses = await asyncio.gather(*status_tasks)
                for phone, status in zip(response.results.keys(), statuses):
                    print(f"  {phone}: {status.status}")
            
            # Check remaining quota
            quota = await client.check_quota()
            print(f"\nRemaining quota: {quota.quota_remaining}")
            
    except QuotaExceededError:
        print("Error: Out of quota")
    except InvalidRequestError as e:
        print(f"Error: Invalid request - {e}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description='Test bulk SMS functionality')
    parser.add_argument('--async-test', action='store_true', help='Run async test instead of sync')
    args = parser.parse_args()
    
    if args.async_test:
        asyncio.run(test_async_bulk_send())
    else:
        test_sync_bulk_send()

if __name__ == '__main__':
    main() 