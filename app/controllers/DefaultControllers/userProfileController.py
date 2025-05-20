from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.models.DefaultModels.userProfileModel import UserProfile
from app.schemas import UserProfileCreate, UserProfileBase
from app.utils import apply_filters_dynamic


async def create_user_profile(db: AsyncSession, user_profile: UserProfileBase):
    db_user_profile = UserProfile(**user_profile.model_dump(exclude_none=True))
    db.add(db_user_profile)
    await db.commit()
    await db.refresh(db_user_profile)
    return db_user_profile


async def get_user_profiles(db: AsyncSession, skip: int = 0, limit: int = 10, filters: str = None, model: str = None):
    query = select(UserProfile)

    if filters and model:
        query = apply_filters_dynamic(query, filters, model)

    result = await db.execute(
        query
        .options(joinedload(UserProfile.permissions))
        .offset(skip).limit(limit if limit > 0 else None)
    )
    return result.scalars().unique().all()


async def get_user_profile(db: AsyncSession, user_profile_id: int):
    result = await db.execute(
        select(UserProfile)
        .options(joinedload(UserProfile.permissions))
        .where(UserProfile.id == user_profile_id)
    )
    return result.scalars().unique().first()


async def update_user_profile(db: AsyncSession, user_profile_id: int, updated_user_profile: UserProfileCreate):
    result = await db.execute(select(UserProfile).where(UserProfile.id == user_profile_id))
    user_profile = result.scalars().first()
    if user_profile is None:
        return None

    for key, value in updated_user_profile.model_dump(exclude_none=True).items():
        if str(value):
            setattr(user_profile, key, value)

    await db.commit()
    await db.refresh(user_profile)
    return user_profile


async def delete_user_profile(db: AsyncSession, user_profile_id: int):
    result = await db.execute(select(UserProfile).where(UserProfile.id == user_profile_id))
    user_profile = result.scalars().first()
    if user_profile is None:
        return None
    await db.delete(user_profile)
    await db.commit()
    return user_profile
