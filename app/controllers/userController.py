# agenda-risetec-backend/app/controllers/userController.py

from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, selectinload

from app.controllers.base import CRUDBase
from app.models.userModel import User
from app.models.userProfileModel import UserProfile
from app.schemas.userSchema import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from app.utils import apply_filters_dynamic

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    
    # ALTERADO: O método create agora associa os perfis.
    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        hashed_password = get_password_hash(obj_in.password)
        
        create_data = obj_in.model_dump(exclude_unset=True, exclude_none=True)
        
        create_data.pop("password", None)
        
        db_obj = self.model(**create_data, password=hashed_password)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # ALTERADO: O método update agora pode atualizar a associação de perfis.
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: User,
        obj_in: UserUpdate
    ) -> User:
        update_data = obj_in.model_dump(exclude_unset=True, exclude_none=True)

        # Se uma nova senha for fornecida, faz o hash
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            db_obj.password = hashed_password

        # Atualiza os outros campos
        return await super().update(db=db, db_obj=db_obj, obj_in=update_data)


    async def authenticate(
        self, db: AsyncSession, *, email: str, password: str
    ) -> Optional[User]:
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(User.profile).selectinload(UserProfile.permissions), 
                selectinload(User.events)
            )
            .where(self.model.email == email)
        )
        user = result.scalars().unique().first()
        if not user:
            return None
        if not verify_password(password, user.password):
            return None
        return user
       
    async def get_users_with_details(self, db: AsyncSession, skip: int = 0, limit: int = 10, filters: Optional[str] = None, model: str = ""):
        query = select(self.model)

        if filters and model:
            query = apply_filters_dynamic(query, filters, model)
            
        result = await db.execute(
            query
            .options(
                selectinload(User.profile).selectinload(UserProfile.permissions), 
                selectinload(User.events)
            )
            .offset(skip)
            .limit(limit if limit > 0 else None)
        )
        return result.scalars().unique().all()

    async def get_user_with_details(self, db: AsyncSession, user_id: int):
        result = await db.execute(
            select(self.model)
            .options(
                selectinload(User.profile).selectinload(UserProfile.permissions), 
                selectinload(User.events)
            )
            .where(self.model.id == user_id)
        )
        user = result.scalars().unique().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

user_controller = CRUDUser(User)