from pydantic import BaseModel, field_validator
from datetime import datetime

from typing import Optional, List, TYPE_CHECKING
if TYPE_CHECKING:
    from .userSchema import User

class EventBase(BaseModel):
    title: str
    description: str = ""
    date: datetime
    isAllDay: bool
    startTime: str
    endTime: str
    color: str
    user_ids: List[int] = []
    
    calendar_id: int

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            try:
                # O formato toISOString() do JavaScript inclui um "Z" no final para UTC.
                # Substituir por "+00:00" torna-o compatível com fromisoformat() do Python.
                if v.endswith("Z"):
                    v = v[:-1] + "+00:00"
                return datetime.fromisoformat(v)
            except ValueError:
                raise ValueError(f"Formato de data inválido: '{v}'. Use o formato ISO 8601.")
        # Se não for uma string (ex: já é um datetime), apenas retorna o valor.
        return v


class EventCreate(EventBase):
    id: int


class Event(EventBase):
    id: int
    users: List[Optional["User"]] = []

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
