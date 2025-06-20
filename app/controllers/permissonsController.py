# agenda-risetec-backend/app/controllers/permissonsController.py

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.controllers.base import CRUDBase
from app.models.permissionsModel import Permissions
from app.schemas.permissionsSchema import PermissionsCreate, PermissionsBase

# NOVO: Classe CRUD para Permissions.
class CRUDPermission(CRUDBase[Permissions, PermissionsCreate, PermissionsCreate]):
    
    # NOVO: Método para buscar permissão com o perfil.
    async def get_with_profile(self, db: AsyncSession, *, id: int) -> Optional[Permissions]:
        result = await db.execute(
            select(self.model)
            .options(joinedload(self.model.profile))
            .filter(self.model.id == id)
        )
        return result.scalars().unique().first()

    # NOVO: Método para buscar múltiplas permissões com perfil.
    async def get_multi_with_profile(
        self, db: AsyncSession, *, skip: int, limit: int
    ) -> List[Permissions]:
        result = await db.execute(
            select(self.model)
            .options(joinedload(self.model.profile))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().unique().all()

# NOVO: Instância do controller.
permission_controller = CRUDPermission(Permissions)