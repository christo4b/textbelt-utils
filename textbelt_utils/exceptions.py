from typing import Optional

class TextbeltError(Exception):
    """Base exception for textbelt-utils"""
    pass

class QuotaExceededError(TextbeltError):
    """Raised when the API quota is exceeded"""
    pass

class InvalidRequestError(TextbeltError):
    """Raised when the request is invalid"""
    pass

class WebhookVerificationError(TextbeltError):
    """Raised when webhook verification fails"""
    pass

class APIError(TextbeltError):
    """Raised when the API returns an error"""
    pass

class BulkSendError(Exception):
    """Raised when there is a batch-level error during bulk sending."""
    def __init__(self, message: str, failed_phones: dict[str, str]):
        super().__init__(message)
        self.failed_phones = failed_phones

class RateLimitError(Exception):
    """Raised when API rate limits are exceeded."""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after
