from pydantic import BaseModel


class PermissionsBase(BaseModel):
    entity_name: str
    can_view: bool
    can_delete: bool
    can_update: bool
    can_create: bool
    profile_id: int


class PermissionsCreate(PermissionsBase):
    id: int


class Permissions(PermissionsBase):
    id: int

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
