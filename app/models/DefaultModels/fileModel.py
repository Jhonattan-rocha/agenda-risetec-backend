from sqlalchemy import Column, Integer, String
from app.database import Base

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    originalname = Column(String, index=True)
    content_type = Column(String)
    file_path = Column(String)
