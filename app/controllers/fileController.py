# crud.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.fileModel import File
from app.schemas.fileSchema import FileBase
from app.utils import apply_filters_dynamic
import os

async def get_file(db: AsyncSession, file_id: int):
    result = await db.execute(
        select(File)
        .where(File.id == file_id)
    )
    return result.scalars().unique().first()

async def get_files(db: AsyncSession, skip: int = 0, limit: int = 10, filters: Optional[List[str]] = None,
                    model: str = ""):
    query = select(File)
    if filters and model:
        query = apply_filters_dynamic(query, filters, model)
    result = await db.execute(
        query
        .offset(skip)
        .limit(limit if limit > 0 else None)
    )
    return result.scalars().unique().first()

async def create_file(db: AsyncSession, file: FileBase):
    db_file = File(**file.model_dump(exclude_none=True))
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)
    return db_file

async def delete_file(db: AsyncSession, file_id: int):
    result = await db.execute(select(File).where(File.id == file_id))
    file = result.scalars().first()
    if file is None:
        return None
    
    if os.path.exists(file.file_path):
        os.unlink(file.file_path)
        
    await db.delete(file)
    await db.commit()
    return file
