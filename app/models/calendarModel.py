# agenda-risetec-backend/app/models/calendarModel.py

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from app.database.database import Base
from sqlalchemy.orm import relationship

class Calendar(Base):
    __tablename__ = "calendars"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), default="")
    color = Column(String(255), default="")
    visible = Column(Boolean, default=True)

    # --- NOVOS CAMPOS ---
    description = Column(String(500), nullable=True)
    is_private = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # --- CAMPOS DE NOTIFICAÇÃO ---
    notification_type = Column(String(20), default='email') # pode ser 'email', 'whatsapp', 'both', 'none'
    notification_time_before = Column(Integer, default=30) # em minutos
    notification_repeats = Column(Integer, default=1) # quantidade de vezes
    notification_message = Column(Text, default='Lembrete: {event_title} às {event_time}.') # template da mensagem

    # --- FIM NOVOS CAMPOS ---

    # Relacionamento com eventos
    events = relationship("Events", lazy="selectin", cascade="all, delete-orphan")
    
    # NOVO: Relacionamento com o proprietário do calendário
    owner = relationship("User", foreign_keys=[owner_id])