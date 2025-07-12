# app/controllers/syncUserController.py

from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from typing import Optional

from app.models.userModel import User
from app.models.userProfileModel import UserProfile
from app.core.security import verify_password
from app.models.userProfileModel import UserProfile # Adicione esta importação
from sqlalchemy import select # Adicione esta importação

def get_user_by_email_sync(db: Session, *, email: str) -> Optional[User]:
    """
    Função SÍNCRONA para buscar um usuário pelo email.
    """
    try:
        # Usando a sintaxe 2.0 que também funciona com sessões síncronas
        stmt = select(User).options(
            selectinload(User.profile).selectinload(UserProfile.permissions)
        ).where(User.email == email)
        return db.scalars(stmt).unique().first()
    except Exception as e:
        print(f"Erro no banco de dados durante a busca síncrona de usuário: {e}")
        db.rollback()
        return None
    
def authenticate_sync(db: Session, *, email: str, password: str) -> Optional[User]:
    """
    Função de autenticação SÍNCRONA. Busca um usuário pelo email
    e verifica sua senha.
    """
    try:
        # A consulta é síncrona
        result = db.execute(
            select(User)
            .options(
                selectinload(User.profile).selectinload(UserProfile.permissions)
            )
            .where(User.email == email)
        )
        user = result.scalars().unique().first()

        if not user:
            print(f"Usuário síncrono não encontrado: {email}")
            return None
        
        # A verificação de senha já é síncrona
        if not verify_password(password, user.password):
            print(f"Senha síncrona inválida para o usuário: {email}")
            return None
            
        print(f"Usuário síncrono autenticado com sucesso: {email}")
        return user
    except Exception as e:
        print(f"Erro no banco de dados durante a autenticação síncrona: {e}")
        db.rollback()
        return None