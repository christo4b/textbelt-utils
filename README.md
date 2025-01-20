# textbelt-utils

A lightweight Python package for interacting with the Textbelt SMS API. Send SMS messages, check delivery status, and handle webhook responses with a clean, type-hinted interface.

## Features

- 🚀 Simple, intuitive API
- 📝 Type hints and dataclasses for better IDE support
- ✅ Webhook verification
- 🧪 Test mode support
- 🔐 One-Time Password (OTP) support
- 🏢 Custom sender name support
- 📨 Bulk SMS support with rate limiting
- ⚡ Async/sync clients for flexibility
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

### Bulk SMS

Send multiple SMS messages efficiently with rate limiting and batching:

```python
from textbelt_utils import TextbeltClient, BulkSMSRequest

client = TextbeltClient(api_key="your_api_key")

# Send same message to multiple recipients
request = BulkSMSRequest(
    phones=["+1234567890", "+1987654321"],
    message="Broadcast message to all recipients!",
    batch_size=100,  # Process in batches of 100
    delay_between_messages=0.1  # 100ms delay between messages
)

# Or send individual messages to each recipient
request = BulkSMSRequest(
    phones=["+1234567890", "+1987654321"],
    individual_messages={
        "+1234567890": "Custom message for recipient 1",
        "+1987654321": "Different message for recipient 2"
    },
    batch_size=100,
    delay_between_messages=0.1
)

response = client.send_bulk_sms(request)
print(f"Total messages: {response.total_messages}")
print(f"Successful: {response.successful_messages}")
print(f"Failed: {response.failed_messages}")

# Check individual results
for phone, result in response.results.items():
    if result.text_id:
        status = client.check_status(result.text_id)
        print(f"{phone}: {status.status}")
```

### Async Bulk SMS

Send messages concurrently with proper rate limiting:

```python
from textbelt_utils import AsyncTextbeltClient, BulkSMSRequest
import asyncio

async def send_bulk():
    async with AsyncTextbeltClient(api_key="your_api_key") as client:
        request = BulkSMSRequest(
            phones=["+1234567890", "+1987654321"],
            message="Async bulk message!",
            batch_size=100,  # Process 100 messages concurrently
            delay_between_messages=0.1
        )
        
        response = await client.send_bulk_sms(request)
        print(f"Sent: {response.successful_messages}")
        print(f"Failed: {response.failed_messages}")

asyncio.run(send_bulk())
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

### One-Time Password (OTP)

The package provides built-in support for generating and verifying one-time passwords:

```python
from textbelt_utils import AsyncTextbeltClient, OTPGenerateRequest, OTPVerifyRequest

async def handle_otp():
    async with AsyncTextbeltClient(api_key="your_api_key") as client:
        # Generate and send OTP
        generate_request = OTPGenerateRequest(
            phone="+1234567890",
            userid="user@example.com",  # Unique identifier for your user
            key="your_api_key",
            message="Your verification code is $OTP",  # Optional custom message
            lifetime=180,  # Optional validity duration in seconds (default: 180)
            length=6      # Optional code length (default: 6)
        )
        
        response = await client.generate_otp(generate_request)
        print(f"OTP sent! Message ID: {response.text_id}")
        
        # Later, verify the OTP entered by the user
        verify_request = OTPVerifyRequest(
            otp="123456",    # Code entered by user
            userid="user@example.com",  # Same userid used in generate
            key="your_api_key"
        )
        
        verify_response = await client.verify_otp(verify_request)
        if verify_response.is_valid_otp:
            print("OTP verified successfully!")
        else:
            print("Invalid OTP")
```

#### OTP Features

- **Custom Messages**: Use the `$OTP` placeholder in your message to control where the code appears
- **Configurable Lifetime**: Set how long the code remains valid (30-3600 seconds)
- **Configurable Length**: Choose the number of digits in the code (4-10 digits)
- **No Extra Cost**: OTP functionality is included in your regular SMS quota
- **Automatic Cleanup**: Invalid/expired codes are automatically cleaned up
- **Input Validation**: Built-in validation for phone numbers, message length, and code format

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

### Environment Setup

1. Copy the environment template:
```bash
cp .env.template .env
```

2. Edit `.env` with your configuration:
```bash
# Textbelt API Configuration
TEXTBELT_API_KEY=your_api_key_here

# Test Phone Numbers (E.164 format)
TEXTBELT_TEST_PHONE=your_test_phone_here
TEXTBELT_TEST_PHONE2=your_second_test_phone_here
```

The package automatically loads environment variables from your `.env` file on import. You can also explicitly load or reload configuration:

```python
from textbelt_utils import load_config, get_env_var

# Load default .env file
load_config()

# Load specific env file
load_config(".env.test")

# Get environment variables with helpful error messages
api_key = get_env_var('TEXTBELT_API_KEY')
test_phone = get_env_var('TEXTBELT_TEST_PHONE')

# Get with default value
debug_mode = get_env_var('DEBUG', 'false')
```

For testing, you can use `.env.test` which contains safe test values:

```bash
# Use test environment
cp .env.test .env

# Or specify a different env file in code
load_config(".env.test")
```

### Running Tests

```bash
poetry run python -m unittest discover tests
```

## Testing Your Integration

### Testing SMS

The package includes test scripts in the `scripts` directory to help you verify your Textbelt integration. To use them:

1. Set up your environment variables:
```bash
export TEXTBELT_API_KEY=your_api_key_here
export TEXTBELT_TEST_PHONE=your_phone_number_here  # E.164 format, e.g., +1234567890
```

2. Run the test scripts:
```bash
# Test basic SMS
poetry run python scripts/test_send.py

# Test async SMS
poetry run python scripts/test_send_async.py

# Test bulk SMS
poetry run python scripts/test_bulk_send.py
```

The scripts will:
- Send test messages (using test mode, won't use your quota)
- Display message IDs and delivery status
- Show your remaining quota

### Testing OTP

The package also includes an OTP test script:

```bash
# Using environment variables
poetry run python scripts/test_otp.py

# Or provide values directly
poetry run python scripts/test_otp.py --phone +1234567890 --key your_api_key
```

### Security Note
- Never commit test scripts with actual phone numbers or API keys
- Always use environment variables for sensitive data
- Add test scripts to your `.gitignore` if you modify them with any sensitive data

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
- [ ] Add retry mechanism for failed API calls

### Medium Priority
- [ ] Add rate limiting configuration options
- [ ] Add logging configuration options
- [ ] Add support for scheduling messages
- [ ] Add support for message templates
- [ ] Add support for contact lists/groups

### Low Priority
- [ ] Add message history tracking
- [ ] Add support for delivery reports
- [ ] Add support for analytics and reporting
- [ ] Add CLI tool for common operations



