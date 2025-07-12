# agenda-risetec-backend/app/controllers/eventsController.py

from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.controllers.base import CRUDBase
from app.models.eventsModel import Events
from app.models.userModel import User 
from app.schemas.eventsSchema import EventCreate, EventBase, EventUpdate
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
    
    # NOVO E CORRIGIDO: Método 'update' específico para eventos
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Events,
        obj_in: EventUpdate
    ) -> Events:
        # Converte o schema de entrada para um dicionário
        update_data = obj_in.model_dump(exclude_unset=True)

        # Lógica específica para atualizar a lista de participantes
        if 'user_ids' in update_data:
            user_ids = update_data.pop('user_ids')
            if user_ids is not None: # Permite enviar uma lista vazia para remover todos
                result = await db.execute(
                    select(User).where(User.id.in_(user_ids))
                )
                new_users = result.scalars().unique().all()
                if len(new_users) != len(user_ids):
                    raise HTTPException(status_code=404, detail="Um ou mais IDs de usuário para atualização não foram encontrados.")
                # Substitui a lista de usuários antiga pela nova
                db_obj.users = new_users
            else: # Se user_ids for None, não faz nada
                pass
        
        # Chama o método de update da classe base para atualizar os outros campos
        # Passa o dicionário 'update_data' que agora não contém mais 'user_ids'
        return await super().update(db, db_obj=db_obj, obj_in=update_data)


    # ATUALIZADO: para lidar com o filtro de usuário
    async def get_multi_filtered(
        self, db: AsyncSession, *, skip: int, limit: int, filters: Optional[str] = None, model: Optional[str] = "", load_options: Optional[List] = None 
    ) -> List[Events]:
        query = select(self.model)
        if load_options:
            query = query.options(*load_options)
            
        print(filters)
        # Adiciona a lógica de filtro dinâmico
        if filters and model:
            query = apply_filters_dynamic(query, filters, model)

        result = await db.execute(
            query.offset(skip).limit(limit if limit > 0 else None)
        )
        return result.scalars().unique().all()
    
    # O get_event pode ser simplificado ou usar o get da base com selectinload
    async def get_event_with_users(self, db: AsyncSession, *, id: int) -> Optional[Events]:
        result = await db.execute(
            select(self.model)
            .options(selectinload(Events.users))
            .filter(self.model.id == id)
        )
        event = result.scalars().unique().first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )
        return event


event_controller = CRUDEvent(Events)