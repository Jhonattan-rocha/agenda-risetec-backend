from typing import Optional, List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.DefaultModels.calendarModel import Calendar
from app.schemas import CalendarBase, CalendarCreate
from app.utils import apply_filters_dynamic
from sqlalchemy.orm import joinedload


async def create_calendar(db: AsyncSession, calendar: CalendarBase):
    db_calendar = Calendar(**calendar.model_dump(exclude_none=True))
    db.add(db_calendar)
    await db.commit()
    await db.refresh(db_calendar)
    return db_calendar


async def get_calendars(db: AsyncSession, skip: int = 0, limit: int = 10, filters: Optional[List[str]] = None,
                        model: str = ""):
    query = select(Calendar)

    if filters and model:
        query = apply_filters_dynamic(query, filters, model)

    result = await db.execute(
        query
        .offset(skip)
        .options(joinedload(Calendar.events))
        .limit(limit if limit > 0 else None)
    )
    return result.scalars().unique().all()


async def get_calendar(db: AsyncSession, calendar_id: int):
    result = await db.execute(
        select(Calendar)
        .options(joinedload(Calendar.events))
        .where(Calendar.id == calendar_id)
    )
    calendar = result.scalars().unique().first()
    if not calendar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid id, not found",
        )
    return calendar


async def update_calendar(db: AsyncSession, calendar_id: int, updated_calendar: CalendarCreate):
    result = await db.execute(select(Calendar).where(Calendar.id == calendar_id))
    calendar = result.scalars().first()
    if calendar is None:
        return None

    for key, value in updated_calendar.model_dump(exclude_none=True).items():
        if str(value):
            setattr(calendar, key, value)

    await db.commit()
    await db.refresh(calendar)
    return calendar


async def delete_calendar(db: AsyncSession, calendar_id: int):
    result = await db.execute(select(Calendar).where(Calendar.id == calendar_id))
    calendar = result.scalars().first()
    if calendar is None:
        return None
    await db.delete(calendar)
    await db.commit()
    return calendar
