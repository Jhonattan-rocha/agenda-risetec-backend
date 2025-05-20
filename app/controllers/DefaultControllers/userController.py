from typing import Optional, List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.models.DefaultModels.userModel import User
from app.models.DefaultModels.eventsModel import Events
from app.models.DefaultModels.userProfileModel import UserProfile
from app.schemas import UserBase, UserCreate
from app.utils import gen_random_string, apply_filters_dynamic
import hashlib


async def create_user(db: AsyncSession, user: UserBase):
    user.salt = gen_random_string(15)
    hash_password = hashlib.sha256(user.salt.encode()).hexdigest() + hashlib.sha256(user.password.encode()).hexdigest()
    user.password = hashlib.sha256(hash_password.encode()).hexdigest()
    db_user = User(**user.model_dump(exclude_none=True))
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_users(db: AsyncSession, skip: int = 0, limit: int = 10, filters: Optional[List[str]] = None,
                    model: str = ""):
    query = select(User)

    if filters and model:
        query = apply_filters_dynamic(query, filters, model)
    result = await db.execute(
        query
        .options(joinedload(User.profile).joinedload(UserProfile.permissions), joinedload(User.events).joinedload(Events.tasks))
        .offset(skip)
        .limit(limit if limit > 0 else None)
    )
    return result.scalars().unique().all()


async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(User)
        .options(joinedload(User.profile).joinedload(UserProfile.permissions))
        .where(User.id == user_id)
    )
    user = result.scalars().unique().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid id, not found",
        )
    return user


async def update_user(db: AsyncSession, user_id: int, updated_user: UserCreate):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        return None

    for key, value in updated_user.model_dump(exclude_none=True).items():
        if str(value):
            setattr(user, key, value)

    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        return None
    await db.delete(user)
    await db.commit()
    return user
