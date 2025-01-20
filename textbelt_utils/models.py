from dataclasses import dataclass
from typing import Optional, Literal

@dataclass
class SMSRequest:
    phone: str
    message: str
    key: str
    sender: Optional[str] = None
    reply_webhook_url: Optional[str] = None
    webhook_data: Optional[str] = None

@dataclass
class SMSResponse:
    success: bool
    quota_remaining: int
    text_id: Optional[str] = None
    error: Optional[str] = None

@dataclass
class WebhookResponse:
    text_id: str
    from_number: str
    text: str
    data: Optional[str] = None

StatusType = Literal["DELIVERED", "SENT", "SENDING", "FAILED", "UNKNOWN"]

@dataclass
class StatusResponse:
    status: StatusType

@dataclass
class QuotaResponse:
    success: bool
    quota_remaining: int
