# agenda-risetec-backend/app/controllers/eventsController.py

from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.controllers.base import CRUDBase
from app.models.eventsModel import Events
# NOVO: Importe o modelo User para poder buscar os usuários
from app.models.userModel import User 
from app.schemas.eventsSchema import EventCreate, EventBase
from app.utils import apply_filters_dynamic

# NOVO: Classe CRUD específica para Events.
class CRUDEvent(CRUDBase[Events, EventCreate, EventCreate]):
    
    # NOVO: Sobrescreva o método create para lidar com o relacionamento N-N
    async def create(self, db: AsyncSession, *, obj_in: EventBase) -> Events:
        # 1. Extraia os dados do schema Pydantic
        obj_in_data = obj_in.model_dump()
        
        # 2. Remova 'user_ids' dos dados, pois não é uma coluna em Events
        user_ids = obj_in_data.pop('user_ids', [])

        # 3. Crie o objeto Events com os dados restantes
        db_obj = self.model(**obj_in_data)
        
        # 4. Busque os usuários correspondentes aos IDs
        if user_ids:
            result = await db.execute(
                select(User).where(User.id.in_(user_ids))
            )
            users = result.scalars().all()
            if len(users) != len(user_ids):
                raise HTTPException(status_code=404, detail="Um ou mais usuários não foram encontrados.")
            # 5. Associe os usuários ao evento
            db_obj.users = users

        # 6. Adicione, salve e atualize o objeto no banco de dados
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # NOVO: Método para buscar um evento específico.
    async def get_event(self, db: AsyncSession, *, id: int) -> Optional[Events]:
        event = await super().get(db, id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )
        return event

    # NOVO: Método customizado que mantém a lógica de filtros dinâmicos.
    async def get_multi_filtered(
        self, db: AsyncSession, *, skip: int, limit: int, filters: str, model: str
    ) -> List[Events]:
        query = select(self.model)

        if filters and model:
            query = apply_filters_dynamic(query, filters, model)

        result = await db.execute(
            query.offset(skip).options(joinedload(Events.users)).limit(limit if limit > 0 else None)
        )
        return result.scalars().unique().all()

# NOVO: Instância do controller para ser usada nas rotas.
event_controller = CRUDEvent(Events)