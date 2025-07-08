# agenda-risetec-backend/app/controllers/eventsController.py

from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.controllers.base import CRUDBase
from app.models.eventsModel import Events
from app.models.userModel import User 
from app.schemas.eventsSchema import EventCreate, EventBase
from app.utils import apply_filters_dynamic

class CRUDEvent(CRUDBase[Events, EventCreate, EventCreate]):
    
    async def create(self, db: AsyncSession, *, obj_in: EventBase) -> Events:
        obj_in_data = obj_in.model_dump(exclude_unset=True, exclude_none=True)
        user_ids = obj_in_data.pop('user_ids', [])
        db_obj = self.model(**obj_in_data)
        
        if user_ids:
            result = await db.execute(
                select(User).where(User.id.in_(user_ids))
            )
            users = result.scalars().unique().all()
            if len(users) != len(user_ids):
                raise HTTPException(status_code=404, detail="Um ou mais usuários não foram encontrados.")
            db_obj.users = users

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_event(self, db: AsyncSession, *, id: int) -> Optional[Events]:
        event = await super().get(db, id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )
        return event

    # ATUALIZADO: para lidar com o filtro de usuário
    async def get_multi_filtered(
        self, db: AsyncSession, *, skip: int, limit: int, filters: Optional[str] = None, model: Optional[str] = ""
    ) -> List[Events]:
        query = select(self.model).options(selectinload(Events.users))

        # Adiciona a lógica de filtro dinâmico
        if filters and model:
            # NOVO: Verifica se o filtro é para usuário e aplica um join
            import json
            filter_data = json.loads(filters)
            if 'user_id' in filter_data and model == 'Events':
                user_id = filter_data['user_id']
                query = query.join(Events.users).where(User.id == user_id)
            else:
                # Mantém o filtro dinâmico para outros campos
                query = apply_filters_dynamic(query, filters, model)

        result = await db.execute(
            query.offset(skip).limit(limit if limit > 0 else None)
        )
        return result.scalars().unique().all()


event_controller = CRUDEvent(Events)