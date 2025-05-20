from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class EventUser(Base):
    __tablename__ = "event_user"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    