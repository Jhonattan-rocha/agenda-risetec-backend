from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.controllers.base import CRUDBase
from app.models.calendarModel import Calendar
from app.models.eventsModel import Events
from app.schemas.calendarSchema import CalendarCreate, CalendarBase
from app.utils import apply_filters_dynamic

# NOVO: Classe CRUD específica para Calendar, herdando de CRUDBase.
class CRUDCalendar(CRUDBase[Calendar, CalendarCreate, CalendarCreate]):
    
    # NOVO: Método customizado para buscar um calendário com seus eventos.
    async def get_with_events(self, db: AsyncSession, *, id: int) -> Optional[Calendar]:
        result = await db.execute(
            select(self.model)
            .options(selectinload(self.model.events))
            .filter(self.model.id == id)
        )
        calendar = result.scalars().unique().first()
        if not calendar:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Calendar not found",
            )
        return calendar

    # NOVO: Método customizado para buscar múltiplos calendários com seus eventos e filtros.
    async def get_multi_with_events(
        self, db: AsyncSession, *, skip: int, limit: int, filters: str, model: str
    ) -> List[Calendar]:
        query = select(self.model).options(selectinload(self.model.events))

        if filters and model:
            query = apply_filters_dynamic(query, filters, model)

        result = await db.execute(
            query.offset(skip).limit(limit if limit > 0 else None)
        )
        return result.scalars().unique().all()

# NOVO: Instância do controller para ser usada nas rotas.
calendar_controller = CRUDCalendar(Calendar)