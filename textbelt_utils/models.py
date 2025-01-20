from dataclasses import dataclass
import re
from typing import Optional, Literal, ClassVar

@dataclass
class SMSRequest:
    """Request model for sending SMS messages via Textbelt API.
    
    Attributes:
        phone: Phone number in E.164 format (e.g., +1234567890)
        message: The message to send (max 2000 characters)
        key: Your Textbelt API key
        sender: Optional sender name for compliance purposes
        reply_webhook_url: Optional URL to receive reply webhooks
        webhook_data: Optional custom data to include in webhooks
    """
    phone: str
    message: str
    key: str
    sender: Optional[str] = None
    reply_webhook_url: Optional[str] = None
    webhook_data: Optional[str] = None

    # Constants for validation
    MAX_MESSAGE_LENGTH: ClassVar[int] = 2000
    PHONE_REGEX: ClassVar[re.Pattern] = re.compile(r'^\+[1-9]\d{1,14}$')

    def __post_init__(self):
        """Validate the request data after initialization."""
        if not self.PHONE_REGEX.match(self.phone):
            raise ValueError(
                "Phone number must be in E.164 format (e.g., +1234567890)"
            )
        
        if len(self.message) > self.MAX_MESSAGE_LENGTH:
            raise ValueError(
                f"Message length exceeds maximum of {self.MAX_MESSAGE_LENGTH} characters"
            )
        
        if len(self.message) == 0:
            raise ValueError("Message cannot be empty")

@dataclass
class SMSResponse:
    """Response model for SMS sending operations.
    
    Attributes:
        success: Whether the operation was successful
        quota_remaining: Number of messages remaining in your quota
        text_id: Unique identifier for the sent message
        error: Error message if the operation failed
    """
    success: bool
    quota_remaining: int
    text_id: Optional[str] = None
    error: Optional[str] = None

@dataclass
class WebhookResponse:
    """Response model for webhook data from Textbelt.
    
    Attributes:
        text_id: The ID of the message this webhook is for
        from_number: The phone number that sent the reply
        text: The content of the reply message
        data: Custom data that was included in the original message
    """
    text_id: str
    from_number: str
    text: str
    data: Optional[str] = None

# Status types with detailed documentation
StatusType = Literal[
    "DELIVERED",  # Carrier has confirmed sending
    "SENT",      # Sent to carrier but confirmation receipt not available
    "SENDING",   # Queued or dispatched to carrier
    "FAILED",    # Not received
    "UNKNOWN"    # Could not determine status
]

@dataclass
class StatusResponse:
    """Response model for message status checks.
    
    Attributes:
        status: Current status of the message. Can be one of:
            - DELIVERED: Carrier has confirmed sending
            - SENT: Sent to carrier but confirmation receipt not available
            - SENDING: Queued or dispatched to carrier
            - FAILED: Not received
            - UNKNOWN: Could not determine status
            
    Note: Delivery statuses are not standardized between mobile carriers.
    Some carriers will report SMS as "delivered" when they attempt transmission
    to the handset while other carriers actually report delivery receipts from
    the handsets. Some carriers do not have a way of tracking delivery, so all
    their messages will be marked "SENT".
    """
    status: StatusType

@dataclass
class QuotaResponse:
    """Response model for quota checks.
    
    Attributes:
        success: Whether the quota check was successful
        quota_remaining: Number of messages remaining in your quota
    """
    success: bool
    quota_remaining: int
