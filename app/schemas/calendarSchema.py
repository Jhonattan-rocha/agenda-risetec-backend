# agenda-risetec-backend/app/schemas/calendarSchema.py

from pydantic import BaseModel
from typing import Optional, List
# Importa o schema de Evento corrigido
from .eventsSchema import Event

class CalendarBase(BaseModel):
    name: str
    color: str
    visible: bool

class CalendarCreate(CalendarBase):
    # ID não é necessário na criação, o banco de dados o gera.
    # Se precisar passar no PUT, crie um schema CalendarUpdate
    pass

class Calendar(CalendarBase):
    id: int
    events: List[Optional[Event]] = [] # Este agora é seguro para usar

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True