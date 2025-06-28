# agenda-risetec-backend/app/schemas/userSchema.py

from __future__ import annotations # Essencial para referências futuras
from pydantic import BaseModel, Field
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

# Usamos TYPE_CHECKING para importar os outros schemas apenas para type hinting
if TYPE_CHECKING:
    from .eventsSchema import Event
    from .userProfileSchema import UserProfile

# --- Schemas de Usuário ---
class UserBase(BaseModel):
    id: Optional[int] = None
    name: str
    email: str

class UserCreate(UserBase):
    password: str
    profile_id: int | None = None

class UserUpdate(UserBase):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    profile_id: int | None = None

# Schema principal de resposta do Usuário
class User(UserBase):
    id: int
    password: Optional[str] = Field(exclude=True)
    # Usa referências futuras como strings para evitar importação direta
    profile: Optional["ProfileInUser"]
    events: List[Optional["EventInUser"]]
    
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

# --- Schemas de outros modelos (para evitar o ciclo) ---

# Schema "slim" de Evento para usar dentro do Usuário.
# Ele não tem a lista de 'users', quebrando o ciclo.
class EventInUser(BaseModel):
    id: int
    title: str
    date: datetime
    calendar_id: int

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

# Schema "slim" de Perfil para usar dentro do Usuário.
class ProfileInUser(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

# Atualiza as referências futuras no schema de User.
User.model_rebuild()