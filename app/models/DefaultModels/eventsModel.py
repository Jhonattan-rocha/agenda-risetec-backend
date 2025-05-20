from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from app.database import Base
from datetime import datetime
from sqlalchemy.orm import relationship

class Events(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), default="")
    description = Column(String(255), default="", nullable=True)
    date = Column(DateTime, default=str(datetime.now()))
    isAllDay = Column(Boolean, default=False)
    startTime = Column(String, nullable=False)
    endTime = Column(String, nullable=False)

    calendar_id = Column(Integer, ForeignKey("calendars.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
