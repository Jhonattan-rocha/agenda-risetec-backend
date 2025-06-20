from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.models.DefaultModels.permissionsModel import Permissions
from app.schemas import PermissionsBase, PermissionsCreate


async def create_permissions(db: AsyncSession, permissions: PermissionsBase):
    db_permissions = Permissions(**permissions.model_dump(exclude_none=True))
    db.add(db_permissions)
    await db.commit()
    await db.refresh(db_permissions)
    return db_permissions


async def get_permissions(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(
        select(Permissions)
        .options(joinedload(Permissions.profile))
        .offset(skip).limit(limit)
    )
    return result.scalars().unique().all()


async def get_permission(db: AsyncSession, permissions_id: int):
    result = await db.execute(
        select(Permissions)
        .options(joinedload(Permissions.profile))
        .where(Permissions.id == permissions_id)
    )
    return result.scalars().unique().first()


async def update_permissions(db: AsyncSession, permissions_id: int, updated_permissions: PermissionsCreate):
    result = await db.execute(select(Permissions).where(Permissions.id == permissions_id))
    permissions = result.scalars().first()
    if permissions is None:
        return None

    for key, value in updated_permissions.model_dump(exclude_none=True).items():
        if str(value):
            setattr(permissions, key, value)

    await db.commit()
    await db.refresh(permissions)
    return permissions


async def delete_permissions(db: AsyncSession, permissions_id: int):
    result = await db.execute(select(Permissions).where(Permissions.id == permissions_id))
    permissions = result.scalars().first()
    if permissions is None:
        return None
    await db.delete(permissions)
    await db.commit()
    return permissions
