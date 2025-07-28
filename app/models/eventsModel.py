# app/models/eventsModel.py

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Table, Text
from app.database.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship
import uuid

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
    uid = Column(String(255), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    date = Column(DateTime(timezone=True), default=datetime.now)
    endDate = Column(DateTime(timezone=True), nullable=True) # NOVO CAMPO
    
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

    # --- CAMPOS DE NOTIFICAÇÃO (PARA OVERRIDE) ---
    notification_type = Column(String(20), nullable=True)
    notification_time_before = Column(Integer, nullable=True)
    notification_repeats = Column(Integer, nullable=True)
    notification_message = Column(Text, nullable=True)
    
    # --- FIM NOVOS CAMPOS ---
    calendar = relationship("Calendar", back_populates="events", lazy="selectin")

    # Relacionamento com usuários (participantes)
    users = relationship(
        "User",
        secondary=user_events_association,
        back_populates="events", # Adicionado back_populates
        lazy="noload" # Alterado para 'selectin' para consistência
    )