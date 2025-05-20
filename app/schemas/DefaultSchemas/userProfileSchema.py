from pydantic import BaseModel
from typing import List, Optional
from app.schemas.DefaultSchemas.permissionsSchema import Permissions


class UserProfileBase(BaseModel):
    name: str


class UserProfileCreate(UserProfileBase):
    id: int


class UserProfile(UserProfileBase):
    id: int
    permissions: List[Optional["Permissions"]] = []

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
