# agenda-risetec-backend/app/schemas/userSchema.py

from __future__ import annotations 
from pydantic import BaseModel, Field
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .eventsSchema import Event
    from .userProfileSchema import UserProfile

class UserBase(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    profile_id: int | None = None
    # NOVO CAMPO
    phone_number: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    phone_number: Optional[str] = None

class User(UserBase):
    id: int
    password: Optional[str] = Field(exclude=True)
    profile: Optional["ProfileInUser"]
    events: List[Optional["EventInUser"]]
    # NOVO CAMPO
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class EventInUser(BaseModel):
    id: int
    title: str
    date: datetime
    calendar_id: int

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class ProfileInUser(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

User.model_rebuild()