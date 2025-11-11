import uuid
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict

class NotificationRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    notification_type: str = Field(..., pattern="^email$")  # v2 uses `pattern` instead of `regex`
    user_id: Optional[str] = None
    email: EmailStr
    template_code: str
    variables: Dict
    priority: int = 1
    metadata: Optional[Dict] = None


class TestEmailRequest(BaseModel):
    email: EmailStr
    template_code: str
    variables: Dict
    priority: int = 1
    metadata: Optional[Dict] = None
