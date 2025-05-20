from typing import Optional, List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.DefaultModels.taskModel import Tasks
from app.schemas import TaskBase, TaskCreate
from app.utils import apply_filters_dynamic


async def create_task(db: AsyncSession, task: TaskBase):
    db_task = Tasks(**task.model_dump(exclude_none=True))
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task


async def get_tasks(db: AsyncSession, skip: int = 0, limit: int = 10, filters: Optional[List[str]] = None,
                    model: str = ""):
    query = select(Tasks)

    if filters and model:
        query = apply_filters_dynamic(query, filters, model)
    result = await db.execute(
        query
        .offset(skip)
        .limit(limit if limit > 0 else None)
    )
    return result.scalars().unique().all()


async def get_task(db: AsyncSession, task_id: int):
    result = await db.execute(
        select(Tasks)
        .where(Tasks.id == task_id)
    )
    task = result.scalars().unique().first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid id, not found",
        )
    return task


async def update_task(db: AsyncSession, task_id: int, updated_task: TaskCreate):
    result = await db.execute(select(Tasks).where(Tasks.id == task_id))
    task = result.scalars().first()
    if task is None:
        return None

    for key, value in updated_task.model_dump(exclude_none=True).items():
        if str(value):
            setattr(task, key, value)

    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task_id: int):
    result = await db.execute(select(Tasks).where(Tasks.id == task_id))
    task = result.scalars().first()
    if task is None:
        return None
    await db.delete(task)
    await db.commit()
    return task
