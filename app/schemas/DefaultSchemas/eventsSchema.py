from pydantic import BaseModel, field_validator
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

    @field_validator("date")
    def remove_timezone(cls, v):
        if v and v.tzinfo:
            return v.replace(tzinfo=None)
        return v


class EventCreate(EventBase):
    id: int


class Event(EventBase):
    id: int

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
