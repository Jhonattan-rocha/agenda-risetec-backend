# agenda-risetec-backend/app/schemas/userProfileSchema.py

from pydantic import BaseModel
from typing import List, Optional
from app.schemas.permissionsSchema import Permissions

class UserProfileBase(BaseModel):
    name: str

class UserProfileCreate(UserProfileBase):
    # Opcional: pode ser usado se o ID for enviado no corpo do PUT
    id: Optional[int] = None

class UserProfile(UserProfileBase):
    id: int
    permissions: List[Optional[Permissions]] = []

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True