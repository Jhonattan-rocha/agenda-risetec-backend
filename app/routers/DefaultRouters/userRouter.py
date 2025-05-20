from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers.DefaultControllers import userController as user_controller
from app.controllers.DefaultControllers.tokenController import verify_token
from app.database import database
from app.schemas.DefaultSchemas import userSchema

router = APIRouter(prefix="/crud")


@router.post("/user/", response_model=userSchema.UserCreate)
async def create_user(user: userSchema.UserBase, db: AsyncSession = Depends(database.get_db),):
    return await user_controller.create_user(user=user, db=db)


@router.get("/user/", response_model=list[userSchema.User])
async def read_users(filters: str = None, skip: int = 0, limit: int = 10,
                     db: AsyncSession = Depends(database.get_db),
                     validation: str = Depends(verify_token)):
    result = await user_controller.get_users(skip=skip, limit=limit, db=db, filters=filters, model="User")
    return result


@router.get("/user/{user_id}", response_model=userSchema.User)
async def read_user(user_id: int, db: AsyncSession = Depends(database.get_db), validation: str = Depends(verify_token)):
    return await user_controller.get_user(user_id=user_id, db=db)


@router.put("/user/{user_id}", response_model=userSchema.UserCreate)
async def update_user(user_id: int, updated_user: userSchema.UserCreate,
                      db: AsyncSession = Depends(database.get_db), validation: str = Depends(verify_token)):
    return await user_controller.update_user(user_id=user_id, updated_user=updated_user, db=db)


@router.delete("/user/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(database.get_db),
                      validation: str = Depends(verify_token)):
    return await user_controller.delete_user(user_id=user_id, db=db)
