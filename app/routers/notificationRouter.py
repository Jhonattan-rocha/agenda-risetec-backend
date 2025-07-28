# app/routers/notificationRouter.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from typing import List
from app.database.database import get_db
from app.models.notificationLogModel import NotificationLog
from app.schemas.notificationLogSchema import NotificationLog as NotificationLogSchema
from app.controllers.tokenController import verify_token

router = APIRouter(prefix="/crud/notifications", tags=["Notifications"])

@router.get("/", response_model=List[NotificationLogSchema])
async def get_user_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(verify_token),
    limit: int = 20,
    unread_only: bool = False
):
    """Busca o histórico de notificações para o usuário logado."""
    query = select(NotificationLog).filter(NotificationLog.user_id == int(current_user))
    if unread_only:
        query = query.filter(NotificationLog.is_read == False)
    
    query = query.order_by(NotificationLog.created_at.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/read")
async def mark_notifications_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(verify_token)
):
    """Marca todas as notificações do usuário como lidas."""
    stmt = update(NotificationLog).where(
        NotificationLog.user_id == int(current_user),
        NotificationLog.is_read == False
    ).values(is_read=True)
    
    await db.execute(stmt)
    await db.commit()
    return {"message": "Notifications marked as read"}