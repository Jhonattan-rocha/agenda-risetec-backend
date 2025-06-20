from typing import Optional, List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.models.DefaultModels.logModel import Logger
from app.models.DefaultModels.userModel import User
from app.models.DefaultModels.userProfileModel import UserProfile
from app.schemas import LoggerBase, LoggerCreate
from app.utils import apply_filters_dynamic

async def create_log(db: AsyncSession, log: LoggerBase):
    db_log = Logger(**log.model_dump(exclude_none=True))
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log


async def get_logs(db: AsyncSession, skip: int = 0, limit: int = 10, filters: Optional[List[str]] = None,
                   model: str = ""):
    query = select(Logger)

    if filters and model:
        query = apply_filters_dynamic(query, filters, model)
    result = await db.execute(
        query
        .options(joinedload(Logger.user).joinedload(User.profile).joinedload(UserProfile.permissions))
        .offset(skip)
        .limit(limit if limit > 0 else None)
    )
    return result.scalars().unique().all()
