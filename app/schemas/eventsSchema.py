# agenda-risetec-backend/app/schemas/eventsSchema.py

from __future__ import annotations 
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .userSchema import User

class EventBase(BaseModel):
    title: str
    description: Optional[str] = ""
    date: datetime
    isAllDay: bool
    startTime: Optional[str] = ""
    endTime: Optional[str] = ""
    color: Optional[str] = ""
    user_ids: List[int] = []
    calendar_id: int
    # NOVOS CAMPOS
    location: Optional[str] = None
    status: Optional[str] = "confirmed" # e.g., 'confirmed', 'tentative', 'cancelled'
    recurring_rule: Optional[str] = None # e.g., "FREQ=WEEKLY;BYDAY=MO"
    created_by: Optional[int] = None

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            try:
                if v.endswith("Z"):
                    v = v[:-1] + "+00:00"
                return datetime.fromisoformat(v)
            except ValueError:
                raise ValueError(f"Formato de data inválido: '{v}'. Use o formato ISO 8601.")
        return v

class EventCreate(EventBase):
    id: int

class Event(EventBase):
    id: int
    users: List[Optional["UserInEvent"]] = []

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class UserInEvent(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

Event.model_rebuild()