from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.CustomControllers import GenericController
from app.database import database
from datetime import timedelta

from app.schemas.DefaultSchemas import Token
from app.controllers.DefaultControllers import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.DefaultModels.userModel import User
from app.models.DefaultModels.userProfileModel import UserProfile
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
import hashlib
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes 
import globals
import base64

router = APIRouter(prefix="/crud")

# Rota para gerar o token
@router.post("/token/", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(database.get_db),
):
    result = await db.execute(
        select(User)
        .options(joinedload(User.profile).joinedload(UserProfile.permissions))
        .where(User.email == form_data.username)
    )
    user = result.scalars().first()

    if user:
        hash_password = (
            hashlib.sha256(user.salt.encode()).hexdigest() +
            hashlib.sha256(form_data.password.encode()).hexdigest()
        )
        user_password = hashlib.sha256(hash_password.encode()).hexdigest()

        if not user or user.password != user_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"id": user.id, "email": user.email}, expires_delta=access_token_expires
        )

        generic_controller = GenericController("User")
        aux = {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "profile": generic_controller.serialize_item(user.profile) if user.profile else user.profile,
            }
        }
        return aux

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Incorrect username or password, user not found",
        headers={"WWW-Authenticate": "Bearer"},
    )
