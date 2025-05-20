from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.schemas.CustomSchemas import GenericCreate
from app.Mapping import models_mapping, models_fields_mapping
from app.utils.filter import apply_filters_dynamic
from app.database import Base
from sqlalchemy.orm.collections import InstrumentedList


class GenericController:
    def __init__(self, model: str):
        self.model = models_mapping[model] if model in models_mapping.keys() else models_mapping["*"]
        self.fields = models_fields_mapping[model] if model in models_fields_mapping.keys() else models_fields_mapping["*"]

    async def create(self, db: AsyncSession, obj_in: GenericCreate):
        db_obj = self.model(**obj_in.values)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(self, db: AsyncSession, id: int):
        result = await db.execute(select(self.model).filter(self.model.id == id))
        db_obj = result.scalars().first()
        if not db_obj:
            return None
        return db_obj

    async def catch(self, db: AsyncSession, skip: int = 0, limit: int = 10, filters: Optional[List[str]] = None,
                    model: str = ""):
        query = select(self.model)

        if filters and model:
            query = apply_filters_dynamic(query, filters, model)
        result = await db.execute(
            query
            .offset(skip)
            .limit(limit if limit > 0 else None)
        )
        return result.scalars().unique().all()

    async def update(self, db: AsyncSession, db_obj, obj_in: GenericCreate):
        aux = {}
        for key in self.fields:
            aux[key] = obj_in.values[key]

        for key, value in aux.items():
            setattr(db_obj, key, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, id: int):
        result = await db.execute(select(self.model).filter(self.model.id == id))
        db_obj = result.scalars().first()
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
            return db_obj
        return None
    
    def serialize_item(self, item):
        result = {}
        for key in item.__dict__.keys():
            if not key.startswith('_'):
                value = getattr(item, key)
                
                if isinstance(value, Base):  # Se o valor for outro objeto SQLAlchemy
                    result[key] = self.serialize_item(value)
                elif isinstance(value, InstrumentedList):  # Se o valor for uma lista de objetos SQLAlchemy
                    result[key] = [self.serialize_item(i) for i in value]
                else:
                    result[key] = value
        return result