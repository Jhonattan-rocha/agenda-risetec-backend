from pydantic import BaseModel
from typing import Optional, List
from .eventsSchema import Event

class CalendarBase(BaseModel):
    name: str
    color: str

class CalendarCreate(CalendarBase):
    id: int


class Calendar(CalendarBase):
    id: int
    events: List[Optional[Event]]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
