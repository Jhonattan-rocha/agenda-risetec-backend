from pydantic import BaseModel
from typing import Optional
from app.schemas.DefaultSchemas.tasksSchema import Task
from app.schemas.DefaultSchemas.userSchema import User
from app.schemas.DefaultSchemas.eventsSchema import Event

class NotificationBase(BaseModel):
    send: bool
    user_id: int
    event_id: int
    message: str
    view: bool = False
    task_id: int | None = None

class NotificationCreate(NotificationBase):
    id: int


class Notification(NotificationBase):
    id: int
    
    user: Optional[User]
    event: Optional[Event]
    task: Optional[Task]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
