# agenda-risetec-backend/app/controllers/eventsController.py

from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.controllers.base import CRUDBase
from app.models.eventsModel import Events
from app.schemas.eventsSchema import EventCreate, EventBase
from app.utils import apply_filters_dynamic

# NOVO: Classe CRUD específica para Events.
class CRUDEvent(CRUDBase[Events, EventCreate, EventCreate]):
    
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
            query.offset(skip).limit(limit if limit > 0 else None)
        )
        return result.scalars().unique().all()

# NOVO: Instância do controller para ser usada nas rotas.
event_controller = CRUDEvent(Events)