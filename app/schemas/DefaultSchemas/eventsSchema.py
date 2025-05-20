from pydantic import BaseModel
from datetime import datetime

class EventBase(BaseModel):
    title: str
    description: str = ""
    date: datetime
    isAllDay: bool
    startTime: str
    endTime: str

    calendar_id: int
    user_id: int | None = None


class EventCreate(EventBase):
    id: int


class Event(EventBase):
    id: int

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
