import sqlalchemy.exc
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.controllers.DefaultControllers import userProfileController as user_profile_controller
from app.controllers.DefaultControllers.tokenController import verify_token
from app.database import database
from app.schemas.DefaultSchemas import userProfileSchema

router = APIRouter(prefix="/crud")


@router.post("/user_profile/", response_model=userProfileSchema.UserProfileCreate)
async def create_user(user_profile: userProfileSchema.UserProfileBase, db: AsyncSession = Depends(database.get_db),
                      validation: str = Depends(verify_token)):
    return await user_profile_controller.create_user_profile(user_profile=user_profile, db=db)


@router.get("/user_profile/", response_model=list[userProfileSchema.UserProfile])
async def read_users(filters: str = None, skip: int = 0, limit: int = 10, db: AsyncSession = Depends(database.get_db),
                     validation: str = Depends(verify_token)):
    return await user_profile_controller.get_user_profiles(skip=skip, limit=limit, db=db, filters=filters, model="UserProfile")


@router.get("/user_profile/{user_profile_id}", response_model=userProfileSchema.UserProfile)
async def read_user(user_profile_id: int, db: AsyncSession = Depends(database.get_db),
                    validation: str = Depends(verify_token)):
    return await user_profile_controller.get_user_profile(user_profile_id=user_profile_id, db=db)


@router.put("/user_profile/{user_profile_id}", response_model=userProfileSchema.UserProfileCreate)
async def update_user(user_profile_id: int, updated_user_profile: userProfileSchema.UserProfileCreate,
                          db: AsyncSession = Depends(database.get_db), validation: str = Depends(verify_token)):
    return await user_profile_controller.update_user_profile(user_profile_id=user_profile_id,
                                                             updated_user_profile=updated_user_profile, db=db)


@router.delete("/user_profile/{user_profile_id}")
async def delete_user(user_profile_id: int, db: AsyncSession = Depends(database.get_db),
                      validation: str = Depends(verify_token)):
    try:
        return await user_profile_controller.delete_user_profile(user_profile_id=user_profile_id, db=db)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="There are still users linked to this profile",
        )
