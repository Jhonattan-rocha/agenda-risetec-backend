from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Permissions(Base):
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True)
    entity_name = Column(String(255), nullable=False)
    can_view = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_update = Column(Boolean, default=False)
    can_create = Column(Boolean, default=False)
    profile_id = Column(Integer, ForeignKey('user_profile.id'), nullable=False)

    profile = relationship("UserProfile", back_populates="permissions")
