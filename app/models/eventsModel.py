# agenda-risetec-backend/app/models/eventsModel.py

from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Table
from app.database.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship

# NOVO: Tabela de associação para a relação N-N entre usuários e eventos.
# Esta tabela não é uma classe, é uma definição direta de tabela do SQLAlchemy.
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
    
    # CORREÇÃO: A coluna de data deve ser do tipo DateTime, não String.
    date = Column(DateTime(timezone=True), default=datetime.now)
    
    isAllDay = Column(Boolean, default=False)
    startTime = Column(String, nullable=False)
    endTime = Column(String, nullable=False)
    color = Column(String)
    
    calendar_id = Column(Integer, ForeignKey("calendars.id"), nullable=False)

    users = relationship(
        "User",
        secondary=user_events_association,
        lazy="selectin"
    )