from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base


class UserProfile(Base):
    __tablename__ = "user_profile"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    permissions = relationship("Permissions", back_populates="profile", lazy="selectin", cascade="all, delete-orphan")
    user = relationship("User", back_populates="profiles", lazy="selectin")
