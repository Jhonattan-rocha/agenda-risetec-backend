from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Tasks(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), default="")
    desc = Column(String, default="")
    date = Column(String, default=str(datetime.now()))
    ready = Column(Boolean, default=False)
    pendding_notifi = Column(Boolean, default=False)
    loop = Column(Boolean, default=False)
    time_to_dispatch = Column(Float)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)

    task_users = relationship("TaskUser", cascade="all, delete")
