# agenda-risetec-backend/app/controllers/userProfileController.py

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.controllers.base import CRUDBase
from app.models.userProfileModel import UserProfile
from app.schemas.userProfileSchema import UserProfileCreate, UserProfileBase
from app.utils import apply_filters_dynamic

# NOVO: Classe CRUD para UserProfile.
class CRUDUserProfile(CRUDBase[UserProfile, UserProfileCreate, UserProfileCreate]):

    # NOVO: Método para buscar perfil com permissões.
    async def get_with_permissions(self, db: AsyncSession, *, id: int) -> Optional[UserProfile]:
        result = await db.execute(
            select(self.model)
            .options(joinedload(self.model.permissions))
            .filter(self.model.id == id)
        )
        return result.scalars().unique().first()

    # NOVO: Método para buscar múltiplos perfis com permissões e filtros.
    async def get_multi_with_permissions(
        self, db: AsyncSession, *, skip: int, limit: int, filters: str, model: str
    ) -> List[UserProfile]:
        query = select(self.model).options(joinedload(self.model.permissions))
        if filters and model:
            query = apply_filters_dynamic(query, filters, model)
        result = await db.execute(
            query.offset(skip).limit(limit if limit > 0 else None)
        )
        return result.scalars().unique().all()

# NOVO: Instância do controller.
user_profile_controller = CRUDUserProfile(UserProfile)