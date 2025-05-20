from typing import Optional, List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.DefaultModels.eventsModel import Events
from app.schemas import EventBase, EventCreate
from app.utils import apply_filters_dynamic


async def create_event(db: AsyncSession, event: EventBase):
    db_event = Events(**event.model_dump(exclude_none=True))
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)
    return db_event


async def get_events(db: AsyncSession, skip: int = 0, limit: int = 10, filters: Optional[List[str]] = None,
                    model: str = ""):
    query = select(Events)

    if filters and model:
        query = apply_filters_dynamic(query, filters, model)
    result = await db.execute(
        query
        .offset(skip)
        .limit(limit if limit > 0 else None)
    )
    return result.scalars().unique().all()


async def get_event(db: AsyncSession, event_id: int):
    result = await db.execute(
        select(Events)
        .where(Events.id == event_id)
    )
    event = result.scalars().unique().first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid id, not found",
        )
    return event


async def update_event(db: AsyncSession, event_id: int, updated_event: EventCreate):
    result = await db.execute(select(Events).where(Events.id == event_id))
    event = result.scalars().first()
    if event is None:
        return None

    for key, value in updated_event.model_dump(exclude_none=True).items():
        if str(value):
            setattr(event, key, value)

    await db.commit()
    await db.refresh(event)
    return event


async def delete_event(db: AsyncSession, event_id: int):
    result = await db.execute(select(Events).where(Events.id == event_id))
    event = result.scalars().first()
    if event is None:
        return None
    await db.delete(event)
    await db.commit()
    return event
