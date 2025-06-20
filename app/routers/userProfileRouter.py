# agenda-risetec-backend/app/routers/userProfileRouter.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

# ALTERAÇÃO: Importa a instância do controller.
from app.controllers import userProfileController
from app.controllers.tokenController import verify_token
from app.database import database
from app.schemas.userProfileSchema import UserProfile, UserProfileBase, UserProfileCreate

router = APIRouter(prefix="/crud", dependencies=[Depends(verify_token)])

@router.post("/user_profile/", response_model=UserProfile)
async def create_user_profile(
    user_profile: UserProfileBase, 
    db: AsyncSession = Depends(database.get_db),
    current_user_id: int = Depends(verify_token)
):
    return await userProfileController.user_profile_controller.create(db=db, obj_in=user_profile)

@router.get("/user_profile/", response_model=list[UserProfile])
async def read_user_profiles(
    filters: str = None, 
    skip: int = 0, 
    limit: int = 10, 
    db: AsyncSession = Depends(database.get_db),
    current_user_id: int = Depends(verify_token)
):
    return await userProfileController.user_profile_controller.get_multi_with_permissions(
        db=db, skip=skip, limit=limit, filters=filters, model="UserProfile"
    )

@router.get("/user_profile/{user_profile_id}", response_model=UserProfile)
async def read_user_profile(
    user_profile_id: int, 
    db: AsyncSession = Depends(database.get_db),
    current_user_id: int = Depends(verify_token)
):
    user_profile = await userProfileController.user_profile_controller.get_with_permissions(db=db, id=user_profile_id)
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return user_profile

@router.put("/user_profile/{user_profile_id}", response_model=UserProfile)
async def update_user_profile(
    user_profile_id: int, 
    updated_user_profile: UserProfileCreate,
    db: AsyncSession = Depends(database.get_db), 
    current_user_id: int = Depends(verify_token)
):
    db_user_profile = await userProfileController.user_profile_controller.get(db=db, id=user_profile_id)
    if not db_user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    return await userProfileController.user_profile_controller.update(db=db, db_obj=db_user_profile, obj_in=updated_user_profile)

@router.delete("/user_profile/{user_profile_id}", response_model=UserProfile)
async def delete_user_profile(
    user_profile_id: int, 
    db: AsyncSession = Depends(database.get_db),
    current_user_id: int = Depends(verify_token)
):
    try:
        deleted_profile = await userProfileController.user_profile_controller.remove(db=db, id=user_profile_id)
        if not deleted_profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        return deleted_profile
    except Exception: # Idealmente, capturar a exceção específica de integridade do DB
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="There are still users linked to this profile",
        )