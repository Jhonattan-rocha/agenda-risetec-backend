# agenda-risetec-backend/app/schemas/calendarSchema.py

from pydantic import BaseModel
from typing import Optional, List
from .eventsSchema import Event

class CalendarBase(BaseModel):
    name: str
    color: str
    visible: bool
    # NOVOS CAMPOS
    description: Optional[str] = None
    is_private: Optional[bool] = False
    owner_id: Optional[int] = None


class CalendarCreate(CalendarBase):
    pass

class Calendar(CalendarBase):
    id: int
    events: List[Optional[Event]] = []

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True