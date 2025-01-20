# textbelt-utils

A lightweight Python package for interacting with the Textbelt SMS API. Send SMS messages, check delivery status, and handle webhook responses with a clean, type-hinted interface.

## Features

- 🚀 Simple, intuitive API
- 📝 Type hints and dataclasses for better IDE support
- ✅ Webhook verification
- 🧪 Test mode support
- 🏢 Custom sender name support
- 0️⃣ Zero external dependencies beyond requests

## Installation

```bash
pip install textbelt-utils
```

## Quick Start

```python
from textbelt_utils import TextbeltClient, SMSRequest

# Initialize client
client = TextbeltClient(api_key="your_api_key")

# Send an SMS
request = SMSRequest(
    phone="+1234567890",
    message="Hello from textbelt-utils!",
    key="your_api_key"
)

response = client.send_sms(request)
print(f"Message sent! ID: {response.text_id}")
```

## Features

### Send SMS

```python
from textbelt_utils import TextbeltClient, SMSRequest

client = TextbeltClient(api_key="your_api_key")

# Basic SMS
request = SMSRequest(
    phone="+1234567890",
    message="Hello!",
    key="your_api_key"
)

# SMS with webhook for replies
request_with_webhook = SMSRequest(
    phone="+1234567890",
    message="Reply to this message!",
    key="your_api_key",
    reply_webhook_url="https://your-site.com/webhook",
    webhook_data="custom_data"
)

# SMS with custom sender name
request_with_sender = SMSRequest(
    phone="+1234567890",
    message="Message from your company!",
    key="your_api_key",
    sender="MyCompany"  # Set a custom sender name for this message
)

response = client.send_sms(request)
```

### Sender Name

You can set a sender name for your SMS messages in two ways:

1. Account-wide: Set a default sender name in your Textbelt account settings at https://textbelt.com/account
2. Per-message: Set the `sender` parameter in your `SMSRequest`

The sender name is used for compliance purposes and helps recipients identify who sent the message. If you don't specify a sender name, Textbelt will automatically append your default sender name to the message (unless it already appears in the message content).

```python
# Example with custom sender name
request = SMSRequest(
    phone="+1234567890",
    message="Important update!",
    key="your_api_key",
    sender="MyCompany"  # This overrides your account's default sender name
)
```

Note: The sender name is used strictly for compliance purposes and does not override the "From" number for the SMS sender.

### Check Message Status

```python
status = client.check_status("text_id")
print(f"Message status: {status.status}")  # DELIVERED, SENT, SENDING, etc.
```

### Check Quota

```python
quota = client.check_quota()
print(f"Remaining messages: {quota.quota_remaining}")
```

### Test Mode

```python
# Send a test message (doesn't use quota)
response = client.send_test(request)
```

### Webhook Verification

```python
from textbelt_utils.utils import verify_webhook

is_valid = verify_webhook(
    api_key="your_api_key",
    timestamp="webhook_timestamp",
    signature="webhook_signature",
    payload="webhook_payload"
)
```

## Error Handling

The package provides specific exceptions for different error cases:

```python
from textbelt_utils.exceptions import (
    QuotaExceededError,
    InvalidRequestError,
    WebhookVerificationError,
    APIError
)

try:
    response = client.send_sms(request)
except QuotaExceededError:
    print("Out of quota!")
except InvalidRequestError as e:
    print(f"Invalid request: {e}")
except WebhookVerificationError:
    print("Webhook verification failed")
except APIError as e:
    print(f"API error: {e}")
```

## Asynchronous Usage

```python
from textbelt_utils import AsyncTextbeltClient, SMSRequest
import asyncio

async def main():
    async with AsyncTextbeltClient(api_key="your_api_key") as client:
        # Send SMS
        request = SMSRequest(
            phone="+1234567890",
            message="Async hello!",
            key="your_api_key"
        )
        response = await client.send_sms(request)
        
        # Check status
        status = await client.check_status(response.text_id)
        
        # Check quota
        quota = await client.check_quota()

if __name__ == "__main__":
    asyncio.run(main())
```

### Mixed Sync/Async Usage

```python
from textbelt_utils import TextbeltClient, AsyncTextbeltClient, SMSRequest

# Synchronous
sync_client = TextbeltClient(api_key="your_api_key")
sync_response = sync_client.send_sms(request)

# Asynchronous
async def send_async():
    async with AsyncTextbeltClient(api_key="your_api_key") as client:
        async_response = await client.send_sms(request)
```


## Development

### Running Tests

```bash
poetry run python -m unittest discover tests
```

## Testing Your Integration

### Using the Test Script

The package includes a `test_send.py` script to help you verify your Textbelt integration. To use it:

1. Set up your environment variables:
```bash
export TEXTBELT_API_KEY=your_api_key_here
export TEXTBELT_TEST_PHONE=your_phone_number_here  # E.164 format, e.g., +1234567890
```

2. Run the test script:
```bash
poetry run python test_send.py
```

The script will:
- Send a test message (using test mode, won't use your quota)
- Display the message ID and delivery status
- Show your remaining quota

### Security Note
- Never commit `test_send.py` with actual phone numbers or API keys
- Always use environment variables for sensitive data
- Add `test_send.py` to your `.gitignore` if you modify it with any sensitive data

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## TODO

### High Priority
- [ ] Add comprehensive webhook support
  - [ ] Add webhook handler/router functionality
  - [ ] Add webhook signature verification middleware
  - [ ] Add example webhook handlers for common use cases
  - [ ] Document webhook payload structure and events
  - [ ] Add webhook testing utilities

### Medium Priority
- [ ] Add retry mechanism for failed API calls
- [ ] Add rate limiting support
- [ ] Add logging configuration options
- [ ] Add support for bulk SMS sending
- [ ] Add support for scheduling messages

### Low Priority
- [ ] Add support for message templates
- [ ] Add support for contact lists/groups
- [ ] Add message history tracking
- [ ] Add support for delivery reports



