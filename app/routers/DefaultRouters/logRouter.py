from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers.DefaultControllers import logController as log_controller
from app.controllers.DefaultControllers.tokenController import verify_token
from app.database import database
from app.schemas.DefaultSchemas import logSchema

router = APIRouter(prefix="/crud")


@router.post("/log/", response_model=logSchema.LoggerCreate)
async def create_log(log: logSchema.LoggerBase, db: AsyncSession = Depends(database.get_db), validation: str = Depends(verify_token)):
    return await log_controller.create_log(log=log, db=db)

@router.get("/logs/", response_model=list[logSchema.Logger])
async def read_logs(filters: str = None, skip: int = 0, limit: int = 10,
                     db: AsyncSession = Depends(database.get_db),
                     validation: str = Depends(verify_token)):
    result = await log_controller.get_logs(skip=skip, limit=limit, db=db, filters=filters, model="Logger")
    return result
