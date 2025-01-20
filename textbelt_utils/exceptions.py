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
