from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.database.database import Base
from sqlalchemy.orm import relationship


class Logger(Base):
    __tablename__ = "logger"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    action = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    entity = Column(String, nullable=False)
    data = Column(String, nullable=False)
    
    user = relationship("User", foreign_keys="Logger.user_id", lazy="selectin")