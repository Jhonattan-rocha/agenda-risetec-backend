# app/schemas/eventsSchema.py

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
    endDate: Optional[datetime] = None
    isAllDay: bool
    startTime: Optional[str] = ""
    endTime: Optional[str] = ""
    color: Optional[str] = ""
    user_ids: List[int] = []
    calendar_id: int
    location: Optional[str] = None
    status: Optional[str] = "confirmed"
    recurring_rule: Optional[str] = None
    created_by: Optional[int] = None

    @field_validator("date", "endDate", mode="before")
    @classmethod
    def parse_date(cls, v):
        if v is None:
            return v
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

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    endDate: Optional[datetime] = None
    isAllDay: Optional[bool] = None
    startTime: Optional[str] = None
    endTime: Optional[str] = None
    color: Optional[str] = None
    user_ids: Optional[List[int]] = None
    calendar_id: Optional[int] = None
    location: Optional[str] = None
    status: Optional[str] = None
    recurring_rule: Optional[str] = None
    created_by: Optional[int] = None

    # NOVO: Campos para controlar a edição de eventos recorrentes
    edit_mode: Optional[str] = "all"  # 'this', 'future', 'all'
    occurrence_date: Optional[datetime] = None # Data da ocorrência que foi clicada

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