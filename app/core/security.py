# agenda-risetec-backend/app/core/security.py

from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
import jwt
from app.core.config import settings

# NOVO: Configuração do contexto de hashing com bcrypt.
# Isso substitui completamente o hashing manual com salt + sha256.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Função para verificar se a senha fornecida corresponde ao hash armazenado.
def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Compatibiliza GLPI ($2y$) com passlib/bcrypt ($2b$)
    if hashed_password.startswith("$2y$"):
        hashed_password = "$2b$" + hashed_password[4:]
    return pwd_context.verify(plain_password, hashed_password)

# Função para gerar o hash de uma senha.
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Função para criar um token de acesso JWT.
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Padrão de 30 dias se não for especificado
        expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt