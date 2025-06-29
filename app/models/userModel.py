# agenda-risetec-backend/app/models/userModel.py

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base

# NOVO: Importamos a tabela de associação definida no outro arquivo.
from .eventsModel import user_events_association


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), default="")
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    profile_id = Column(Integer, ForeignKey("user_profile.id"), nullable=True)
    profile = relationship("UserProfile", lazy="selectin")
    
    # ALTERADO: O relacionamento agora usa o argumento `secondary` para
    # apontar para a nossa tabela de associação.
    events = relationship(
        "Events",
        secondary=user_events_association,
        cascade="all, delete",
        lazy="selectin"
    )