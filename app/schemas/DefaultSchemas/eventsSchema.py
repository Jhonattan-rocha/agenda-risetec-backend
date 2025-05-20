from pydantic import BaseModel
from typing import Optional, List
from app.schemas.DefaultSchemas.tasksSchema import Task

class EventBase(BaseModel):
    name: str
    desc: str
    date: str
    user_id: int
    private: Optional[bool] = False

class EventCreate(EventBase):
    id: int


class Event(EventBase):
    id: int
    tasks: Optional[List[Task]]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
