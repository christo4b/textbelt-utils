import hmac
import hashlib
import time

from .exceptions import WebhookVerificationError

def verify_webhook(
    api_key: str,
    timestamp: str,
    signature: str,
    payload: str,
    max_age: int = 900
) -> bool:
    """
    Verify a webhook request from Textbelt
    
    Args:
        api_key: Your Textbelt API key
        timestamp: X-textbelt-timestamp header value
        signature: X-textbelt-signature header value
        payload: Raw request body
        max_age: Maximum age of timestamp in seconds (default 15 minutes)
    
    Returns:
        bool: True if verification succeeds
        
    Raises:
        WebhookVerificationError: If verification fails
    """
    try:
        ts = int(timestamp)
        current_time = int(time.time())
        
        if current_time - ts > max_age:
            raise WebhookVerificationError("Webhook timestamp too old")

        expected = hmac.new(
            api_key.encode('utf-8'),
            (timestamp + payload).encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected)
        
    except (ValueError, TypeError) as e:
        raise WebhookVerificationError(f"Invalid webhook data: {str(e)}")

def is_valid_e164(phone: str) -> bool:
    """
    Basic validation for E.164 format phone numbers
    Returns True if the number appears to be in E.164 format
    """
    if not phone:
        return False
    
    # Remove any whitespace
    phone = phone.strip()
    
    # Check basic E.164 format (+ followed by 10-15 digits)
    if not phone.startswith('+'):
        return False
        
    digits = phone[1:]
    if not digits.isdigit():
        return False
        
    return 10 <= len(digits) <= 15
