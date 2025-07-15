# app/routers/radicaleAuthRouter.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Import síncrono, pois o Radicale precisa de respostas rápidas
from app.database.database import SessionLocalSync
from app.core.security import verify_password
from app.models.userModel import User

router = APIRouter(prefix="/radicale_auth", tags=["Radicale Auth"])

class AuthRequest(BaseModel):
    username: str
    password: str

# Função para obter uma sessão de banco de dados síncrona
def get_db_sync():
    db = SessionLocalSync()
    try:
        yield db
    finally:
        db.close()

@router.post("/authenticate")
def authenticate_for_radicale(
    auth_request: AuthRequest,
    db: Session = Depends(get_db_sync)
):
    """
    Endpoint privado para o Radicale verificar as credenciais do usuário.
    """
    user = db.query(User).filter(User.email == auth_request.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    if not verify_password(auth_request.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # Se chegou até aqui, o usuário é válido. Retorna 200 OK.
    return {"status": "ok", "user": user.email}