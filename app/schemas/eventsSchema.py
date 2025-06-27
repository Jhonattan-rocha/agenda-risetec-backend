# agenda-risetec-backend/app/schemas/eventsSchema.py

from __future__ import annotations # Essencial para referências futuras
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

# Usamos TYPE_CHECKING para importar o schema de usuário apenas para type hinting
if TYPE_CHECKING:
    from .userSchema import User

# --- Schemas de Evento ---
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

# Schema principal de resposta do Evento, que será usado em outros locais
class Event(EventBase):
    id: int
    # A lista de usuários usará uma referência futura para o schema 'UserInEvent'
    # que será definido no arquivo de usuário.
    users: List[Optional["UserInEvent"]] = []

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

# --- Schemas de Usuário (para evitar o ciclo) ---

# Schema "slim" de Usuário para usar dentro do Evento.
# Ele não tem a lista de 'events', quebrando o ciclo.
class UserInEvent(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

# Atualiza a referência futura no schema de Evento.
# Isso garante que Pydantic saiba qual modelo usar para 'UserInEvent'.
Event.model_rebuild()