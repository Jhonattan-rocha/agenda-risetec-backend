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
    # CAMPOS DE NOTIFICAÇÃO
    notification_type: Optional[str] = 'email'
    notification_time_before: Optional[int] = 30
    notification_repeats: Optional[int] = 1
    notification_message: Optional[str] = 'Lembrete: {event_title} às {event_time}.'


class CalendarCreate(CalendarBase):
    pass

class Calendar(CalendarBase):
    id: int
    events: List[Optional[Event]] = []

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True