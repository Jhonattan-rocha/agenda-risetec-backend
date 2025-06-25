from pydantic import BaseModel, Field
from typing import Optional, List
from .userProfileSchema import UserProfile
from .eventsSchema import Event

class UserBase(BaseModel):
    name: str
    email: str

class UserCreate(UserBase):
    password: str

# NOVO: Schema para atualização, onde a senha é opcional.
class UserUpdate(UserBase):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

class User(UserBase):
    id: int
    # ALTERAÇÃO: Campo 'salt' removido
    password: Optional[str] = Field(exclude=True)
    profiles: List[Optional[UserProfile]]
    events: List[Optional[Event]]
    
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True