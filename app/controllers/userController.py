# agenda-risetec-backend/app/controllers/userController.py

from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.controllers.base import CRUDBase
from app.models.userModel import User
from app.models.userProfileModel import UserProfile
from app.schemas.userSchema import UserCreate, UserBase, UserUpdate
from app.core.security import get_password_hash, verify_password
from app.utils import apply_filters_dynamic

# NOVO: Herda de CRUDBase
class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def create(self, db: AsyncSession, *, obj_in: UserBase) -> User:
        # ALTERAÇÃO: Usa o novo sistema de hashing
        hashed_password = get_password_hash(obj_in.password)
        
        create_data = obj_in.model_dump()
        create_data.pop("password", None) # Remove a senha em texto plano
        
        db_obj = self.model(**create_data, password=hashed_password)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def authenticate(
        self, db: AsyncSession, *, email: str, password: str
    ) -> Optional[User]:
        # NOVO: Lógica de autenticação centralizada aqui
        result = await db.execute(
            select(self.model)
            .options(joinedload(User.profile).joinedload(UserProfile.permissions))
            .where(self.model.email == email)
        )
        user = result.scalars().first()
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user
    
    # Mantém métodos com lógica customizada (filtros, joins)
    async def get_users_with_details(self, db: AsyncSession, skip: int = 0, limit: int = 10, filters: Optional[str] = None, model: str = ""):
        query = select(self.model)

        if filters and model:
            query = apply_filters_dynamic(query, filters, model)
            
        result = await db.execute(
            query
            .options(joinedload(User.profile).joinedload(UserProfile.permissions), joinedload(User.events))
            .offset(skip)
            .limit(limit if limit > 0 else None)
        )
        return result.scalars().unique().all()

    async def get_user_with_details(self, db: AsyncSession, user_id: int):
        result = await db.execute(
            select(self.model)
            .options(joinedload(User.profile).joinedload(UserProfile.permissions), joinedload(User.events))
            .where(self.model.id == user_id)
        )
        user = result.scalars().unique().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

# Instância do controller para ser usada nas rotas
user_controller = CRUDUser(User)