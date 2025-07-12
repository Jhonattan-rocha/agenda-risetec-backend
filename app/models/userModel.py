# agenda-risetec-backend/app/models/userModel.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database.database import Base
from datetime import datetime

# Importamos a tabela de associação para o Python reconhecer a variável
from .eventsModel import user_events_association


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), default="")
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    
    # --- NOVOS CAMPOS ---
    phone_number = Column(String(50), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    # --- FIM NOVOS CAMPOS ---
    
    profile_id = Column(Integer, ForeignKey("user_profile.id"), nullable=True)
    profile = relationship("UserProfile", lazy="selectin")
    
    # ATUALIZADO: O relacionamento agora usa `back_populates` para uma relação bidirecional explícita.
    events = relationship(
        "Events",
        secondary=user_events_association,
        back_populates="users", # Garante que o lado Events.users também se atualize
        lazy="noload"
    )