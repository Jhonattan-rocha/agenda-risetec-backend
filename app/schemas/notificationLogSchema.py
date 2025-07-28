# app/schemas/notificationLogSchema.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class NotificationLogBase(BaseModel):
    id: int
    user_id: int
    event_id: Optional[int] = None
    channel: str
    status: str
    content: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationLog(NotificationLogBase):
    pass