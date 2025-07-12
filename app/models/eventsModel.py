# agenda-risetec-backend/app/models/eventsModel.py

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Table
from app.database.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship

# Tabela de associação para a relação N-N entre usuários e eventos.
user_events_association = Table(
    'user_events', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
    Column('event_id', Integer, ForeignKey('events.id', ondelete="CASCADE"), primary_key=True)
)


class Events(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), default="")
    description = Column(String(255), default="", nullable=True)
    
    # CORRIGIDO E ATUALIZADO: Garante que o tipo da coluna seja DateTime com fuso horário.
    date = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    isAllDay = Column(Boolean, default=False)
    startTime = Column(String, nullable=True) # Pode ser nulo se for dia todo
    endTime = Column(String, nullable=True)   # Pode ser nulo se for dia todo
    color = Column(String)
    
    calendar_id = Column(Integer, ForeignKey("calendars.id"), nullable=False)

    # --- NOVOS CAMPOS ---
    location = Column(String(255), nullable=True)
    status = Column(String(50), default='confirmed', nullable=False) # e.g., 'confirmed', 'tentative', 'cancelled'
    recurring_rule = Column(String(255), nullable=True) # Ex: "FREQ=WEEKLY;BYDAY=MO"
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    # --- FIM NOVOS CAMPOS ---

    # Relacionamento com usuários (participantes)
    users = relationship(
        "User",
        secondary=user_events_association,
        back_populates="events", # Adicionado back_populates
        lazy="noload" # Alterado para 'selectin' para consistência
    )