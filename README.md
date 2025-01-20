# textbelt-utils

A lightweight Python package for interacting with the Textbelt SMS API. Send SMS messages, check delivery status, and handle webhook responses with a clean, type-hinted interface.

## Features

- 🚀 Simple, intuitive API
- 📝 Type hints and dataclasses for better IDE support
- ✅ Webhook verification
- 🧪 Test mode support
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

response = client.send_sms(request)
```

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

## Development

### Running Tests

```bash
python -m unittest discover tests
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.