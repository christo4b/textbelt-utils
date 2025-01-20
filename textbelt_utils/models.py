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

@dataclass
class OTPGenerateRequest:
    """Request model for generating and sending OTP via Textbelt API.
    
    Attributes:
        phone: Phone number in E.164 format (e.g., +1234567890)
        userid: Unique identifier for the user
        key: Your Textbelt API key
        message: Optional custom message template. Use $OTP to include the code
        lifetime: Optional validity duration in seconds (default: 180)
        length: Optional number of digits in OTP (default: 6)
    """
    phone: str
    userid: str
    key: str
    message: Optional[str] = None
    lifetime: Optional[int] = None
    length: Optional[int] = None

    # Constants for validation
    PHONE_REGEX: ClassVar[re.Pattern] = re.compile(r'^\+[1-9]\d{1,14}$')
    MIN_LIFETIME: ClassVar[int] = 30  # minimum 30 seconds
    MAX_LIFETIME: ClassVar[int] = 3600  # maximum 1 hour
    MIN_LENGTH: ClassVar[int] = 4
    MAX_LENGTH: ClassVar[int] = 10

    def __post_init__(self):
        """Validate the request data after initialization."""
        if not self.PHONE_REGEX.match(self.phone):
            raise ValueError(
                "Phone number must be in E.164 format (e.g., +1234567890)"
            )
        
        if not self.userid:
            raise ValueError("userid cannot be empty")

        if self.lifetime is not None:
            if not isinstance(self.lifetime, int):
                raise ValueError("lifetime must be an integer")
            if self.lifetime < self.MIN_LIFETIME or self.lifetime > self.MAX_LIFETIME:
                raise ValueError(
                    f"lifetime must be between {self.MIN_LIFETIME} and {self.MAX_LIFETIME} seconds"
                )

        if self.length is not None:
            if not isinstance(self.length, int):
                raise ValueError("length must be an integer")
            if self.length < self.MIN_LENGTH or self.length > self.MAX_LENGTH:
                raise ValueError(
                    f"length must be between {self.MIN_LENGTH} and {self.MAX_LENGTH} digits"
                )

@dataclass
class OTPGenerateResponse:
    """Response model for OTP generation.
    
    Attributes:
        success: Whether the OTP was successfully sent
        quota_remaining: Number of messages remaining in your quota
        text_id: The ID of the text message sent
        otp: The generated one-time code (only returned in test mode)
        error: Error message if the operation failed
    """
    success: bool
    quota_remaining: int
    text_id: Optional[str] = None
    otp: Optional[str] = None
    error: Optional[str] = None

@dataclass
class OTPVerifyRequest:
    """Request model for verifying OTP codes.
    
    Attributes:
        otp: The code entered by the user
        userid: The ID of the user (must match the ID used in generate)
        key: Your Textbelt API key
    """
    otp: str
    userid: str
    key: str

    def __post_init__(self):
        """Validate the request data after initialization."""
        if not self.otp:
            raise ValueError("otp cannot be empty")
        if not self.otp.isdigit():
            raise ValueError("otp must contain only digits")
        if not self.userid:
            raise ValueError("userid cannot be empty")

@dataclass
class OTPVerifyResponse:
    """Response model for OTP verification.
    
    Attributes:
        success: Whether the request was successfully processed
        is_valid_otp: Whether the OTP is correct for the given userid
        error: Error message if the operation failed
    """
    success: bool
    is_valid_otp: bool
    error: Optional[str] = None

@dataclass
class BulkSMSRequest:
    """Request model for sending bulk SMS messages via Textbelt API.
    
    Attributes:
        phones: List of phone numbers in E.164 format (e.g., ['+1234567890', '+1987654321'])
        message: Single message to send to all recipients, or None if using individual_messages
        individual_messages: Dict mapping phone numbers to their specific messages, or None if using message
        key: Your Textbelt API key
        sender: Optional sender name for compliance purposes
        reply_webhook_url: Optional URL to receive reply webhooks
        webhook_data: Optional custom data to include in webhooks
        batch_size: Maximum number of messages to send concurrently (default: 100)
        delay_between_messages: Optional delay in seconds between messages (default: 0.1)
    """
    phones: list[str]
    message: Optional[str] = None
    individual_messages: Optional[dict[str, str]] = None
    key: str = ""
    sender: Optional[str] = None
    reply_webhook_url: Optional[str] = None
    webhook_data: Optional[str] = None
    batch_size: int = 100
    delay_between_messages: float = 0.1

    # Constants for validation
    MAX_BATCH_SIZE: ClassVar[int] = 1000
    MIN_DELAY: ClassVar[float] = 0.1

    def __post_init__(self):
        """Validate the request data after initialization."""
        # Validate phone numbers
        if not self.phones:
            raise ValueError("At least one phone number must be provided")
        
        for phone in self.phones:
            if not SMSRequest.PHONE_REGEX.match(phone):
                raise ValueError(
                    f"Phone number {phone} must be in E.164 format (e.g., +1234567890)"
                )
        
        # Validate message configuration
        if self.message is None and self.individual_messages is None:
            raise ValueError("Either message or individual_messages must be provided")
        if self.message is not None and self.individual_messages is not None:
            raise ValueError("Cannot provide both message and individual_messages")
        
        # If using individual messages, validate all phones have messages
        if self.individual_messages is not None:
            missing_phones = set(self.phones) - set(self.individual_messages.keys())
            if missing_phones:
                raise ValueError(f"Missing messages for phones: {missing_phones}")
            
            # Validate message lengths
            for phone, msg in self.individual_messages.items():
                if len(msg) > SMSRequest.MAX_MESSAGE_LENGTH:
                    raise ValueError(
                        f"Message for {phone} exceeds maximum length of {SMSRequest.MAX_MESSAGE_LENGTH}"
                    )
                if len(msg) == 0:
                    raise ValueError(f"Message for {phone} cannot be empty")
        
        # If using shared message, validate its length
        if self.message is not None:
            if len(self.message) > SMSRequest.MAX_MESSAGE_LENGTH:
                raise ValueError(
                    f"Message exceeds maximum length of {SMSRequest.MAX_MESSAGE_LENGTH}"
                )
            if len(self.message) == 0:
                raise ValueError("Message cannot be empty")
        
        # Validate batch size
        if self.batch_size < 1:
            raise ValueError("Batch size must be at least 1")
        if self.batch_size > self.MAX_BATCH_SIZE:
            raise ValueError(f"Batch size cannot exceed {self.MAX_BATCH_SIZE}")
        
        # Validate delay
        if self.delay_between_messages < self.MIN_DELAY:
            raise ValueError(f"Delay between messages must be at least {self.MIN_DELAY} seconds")

@dataclass
class BulkSMSResponse:
    """Response model for bulk SMS sending operations.
    
    Attributes:
        total_messages: Total number of messages in the batch
        successful_messages: Number of successfully sent messages
        failed_messages: Number of failed messages
        results: Dictionary mapping phone numbers to their individual SMSResponse objects
        errors: Dictionary mapping phone numbers to their error messages (if any)
    """
    total_messages: int
    successful_messages: int
    failed_messages: int
    results: dict[str, SMSResponse]
    errors: dict[str, str]

    @property
    def success(self) -> bool:
        """Return True if all messages were sent successfully."""
        return self.failed_messages == 0

    @property
    def partial_success(self) -> bool:
        """Return True if some messages were sent successfully."""
        return self.successful_messages > 0 and self.failed_messages > 0
