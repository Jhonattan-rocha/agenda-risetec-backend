# app/models/notificationLogModel.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.database.database import Base

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    event_id = Column(Integer, ForeignKey('events.id', ondelete="CASCADE"), nullable=True)
    
    channel = Column(String(50), nullable=False)  # 'email' ou 'whatsapp'
    status = Column(String(50), default='sent') # 'sent' ou 'failed'
    content = Column(Text, nullable=False)
    
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())