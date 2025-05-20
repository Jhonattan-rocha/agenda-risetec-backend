from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers.DefaultControllers import tasksController as task_controller
from app.controllers.DefaultControllers.tokenController import verify_token
from app.database import database
from app.schemas.DefaultSchemas import tasksSchema

router = APIRouter(prefix="/crud")


@router.post("/task/", response_model=tasksSchema.TaskCreate)
async def create_task(task: tasksSchema.TaskBase, db: AsyncSession = Depends(database.get_db), validation: str = Depends(verify_token)):
    return await task_controller.create_task(task=task, db=db)


@router.get("/task/", response_model=list[tasksSchema.Task])
async def read_tasks(filters: str = None, skip: int = 0, limit: int = 10,
                     db: AsyncSession = Depends(database.get_db),
                     validation: str = Depends(verify_token)):
    result = await task_controller.get_tasks(skip=skip, limit=limit, db=db, filters=filters, model="Tasks")
    return result


@router.get("/task/{task_id}", response_model=tasksSchema.Task)
async def read_task(task_id: int, db: AsyncSession = Depends(database.get_db), validation: str = Depends(verify_token)):
    return await task_controller.get_task(task_id=task_id, db=db)


@router.put("/task/{task_id}", response_model=tasksSchema.TaskCreate)
async def update_task(task_id: int, updated_task: tasksSchema.TaskCreate,
                      db: AsyncSession = Depends(database.get_db), validation: str = Depends(verify_token)):
    return await task_controller.update_task(task_id=task_id, updated_task=updated_task, db=db)


@router.delete("/task/{task_id}")
async def delete_task(task_id: int, db: AsyncSession = Depends(database.get_db),
                      validation: str = Depends(verify_token)):
    return await task_controller.delete_task(task_id=task_id, db=db)
