from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.controllers import userController
from app.controllers.genericController import GenericController
from app.database import database
from app.schemas.tokenSchema import Token
from app.core.security import create_access_token
from app.core.config import settings

router = APIRouter(prefix="/crud", tags=["Login"])

@router.post("/token/", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(database.get_db),
):
    # ALTERAÇÃO: Lógica de autenticação foi movida para o controller
    user = await userController.user_controller.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"id": user.id, "email": user.email}, expires_delta=access_token_expires
    )

    # A serialização do genericController é útil aqui para o retorno do perfil
    generic_controller = GenericController("User")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "profile": generic_controller.serialize_item(user.profiles) if user.profiles else None,
        }
    }
    