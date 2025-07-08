# agenda-risetec-backend/app/models/calendarModel.py

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
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
    # --- FIM NOVOS CAMPOS ---

    # Relacionamento com eventos
    events = relationship("Events", lazy="selectin", cascade="all, delete-orphan")
    
    # NOVO: Relacionamento com o proprietário do calendário
    owner = relationship("User", foreign_keys=[owner_id])