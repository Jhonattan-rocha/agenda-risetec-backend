from typing import Optional, List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.DefaultModels.notifiModel import Notification
from app.schemas import NotificationBase, NotificationCreate
from app.utils import apply_filters_dynamic

async def create_notification(db: AsyncSession, notification: NotificationBase):
    db_notification = Notification(**notification.model_dump(exclude_none=True))
    db.add(db_notification)
    await db.commit()
    await db.refresh(db_notification)
    return db_notification


async def get_notifications(db: AsyncSession, skip: int = 0, limit: int = 10, filters: Optional[List[str]] = None,
                    model: str = ""):
    query = select(Notification)

    if filters and model:
        query = apply_filters_dynamic(query, filters, model)
    result = await db.execute(
        query
        .offset(skip)
        .limit(limit if limit > 0 else None)
    )
    return result.scalars().unique().all()


async def get_notification(db: AsyncSession, notification_id: int):
    result = await db.execute(
        select(Notification)
        .where(Notification.id == notification_id)
    )
    notification = result.scalars().unique().first()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid id, not found",
        )
    return notification


async def update_notification(db: AsyncSession, notification_id: int, updated_notification: NotificationCreate):
    result = await db.execute(select(Notification).where(Notification.id == notification_id))
    notification = result.scalars().first()
    if notification is None:
        return None

    for key, value in updated_notification.model_dump(exclude_none=True).items():
        if str(value):
            setattr(notification, key, value)

    await db.commit()
    await db.refresh(notification)
    return notification


async def delete_notification(db: AsyncSession, notification_id: int):
    result = await db.execute(select(Notification).where(Notification.id == notification_id))
    notification = result.scalars().first()
    if notification is None:
        return None
    await db.delete(notification)
    await db.commit()
    return notification
