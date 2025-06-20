# agenda-risetec-backend/app/routers/userRouter.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers import userController
from app.database import database
from app.schemas.userSchema import User, UserCreate, UserUpdate
from app.controllers.tokenController import verify_token

router = APIRouter(prefix="/crud", tags=["User"])


@router.post("/user/", response_model=User)
async def create_user(user: UserCreate, db: AsyncSession = Depends(database.get_db)):
    return await userController.user_controller.create(db=db, obj_in=user)


@router.get("/user/", response_model=list[User])
async def read_users(
    filters: str = None, 
    skip: int = 0, 
    limit: int = 10,
    db: AsyncSession = Depends(database.get_db),
    current_user_id: int = Depends(verify_token)
):
    # ALTERAÇÃO: usa o método customizado do controller para carregar detalhes
    return await userController.user_controller.get_users_with_details(
        db=db, skip=skip, limit=limit, filters=filters, model="User"
    )


@router.get("/user/{user_id}", response_model=User)
async def read_user(
    user_id: int, 
    db: AsyncSession = Depends(database.get_db), 
    current_user_id: int = Depends(verify_token)
):
    # ALTERAÇÃO: usa o método customizado do controller para carregar detalhes
    return await userController.user_controller.get_user_with_details(db=db, user_id=user_id)


@router.put("/user/{user_id}", response_model=User)
async def update_user(
    user_id: int, 
    updated_user: UserUpdate,
    db: AsyncSession = Depends(database.get_db), 
    current_user_id: int = Depends(verify_token)
):
    db_user = await userController.user_controller.get(db=db, id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return await userController.user_controller.update(db=db, db_obj=db_user, obj_in=updated_user)


@router.delete("/user/{user_id}", response_model=User)
async def delete_user(
    user_id: int, 
    db: AsyncSession = Depends(database.get_db),
    current_user_id: int = Depends(verify_token)
):
    deleted_user = await userController.user_controller.remove(db=db, id=user_id)
    if not deleted_user:
        raise HTTPException(status_code=404, detail="User not found")
    return deleted_user