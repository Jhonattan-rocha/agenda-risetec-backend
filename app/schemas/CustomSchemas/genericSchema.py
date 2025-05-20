from pydantic import BaseModel


class GenericBase(BaseModel):
    values: dict[str, object] = {}


class GenericCreate(GenericBase):
    model: str = ""


class Generic(GenericBase):
    id: int
    model: str = ""

    class Config:
        orm_mode: True
        from_attributes: True
        arbitrary_types_allowed: True
