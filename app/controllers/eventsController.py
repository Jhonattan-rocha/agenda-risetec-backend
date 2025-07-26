# app/controllers/eventsController.py

from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import delete, and_
from datetime import datetime, timedelta
from dateutil.rrule import rrulestr, rrule, rruleset

from app.controllers.base import CRUDBase
from app.models.eventsModel import Events, user_events_association
from app.models.userModel import User
from app.schemas.eventsSchema import EventCreate, EventBase, EventUpdate
from app.utils import apply_filters_dynamic

class CRUDEvent(CRUDBase[Events, EventCreate, EventUpdate]):

    async def create(self, db: AsyncSession, *, obj_in: EventBase) -> Events:
        obj_in_data = obj_in.model_dump(exclude_unset=True, exclude_none=True)
        user_ids = obj_in_data.pop('user_ids', [])
        db_obj = self.model(**obj_in_data)
        
        if user_ids:
            result = await db.execute(select(User).where(User.id.in_(user_ids)))
            users = result.scalars().unique().all()
            if len(users) != len(user_ids):
                raise HTTPException(status_code=404, detail="Um ou mais usuários não foram encontrados.")
            db_obj.users = users

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Events,
        obj_in: EventUpdate
    ) -> Events:
        update_data = obj_in.model_dump(exclude_unset=True)
        edit_mode = update_data.pop("edit_mode", "all")
        occurrence_date = update_data.pop("occurrence_date", None)

        if edit_mode == "all" or not db_obj.recurring_rule:
            return await self.update_associations(db=db, db_obj=db_obj, obj_in=update_data)

        if not occurrence_date:
            raise HTTPException(status_code=400, detail="A data da ocorrência é necessária para editar um evento recorrente.")

        original_rule_str = f"DTSTART:{db_obj.date.strftime('%Y%m%dT%H%M%S%z')}\n{db_obj.recurring_rule}"
        rule_set = rrulestr(original_rule_str, forceset=True)
        original_rule = rule_set._rrule[0]

        if edit_mode == "future":
            new_until_date = occurrence_date - timedelta(days=1)
            original_rule._until = new_until_date
            db_obj.recurring_rule = rrule.from_options(**original_rule._unpack_options()).to_string()
            db.add(db_obj)

            new_event_data = {**self.model_to_dict(db_obj), **update_data}
            user_ids_for_new = new_event_data.pop('user_ids', None)
            new_event_data.pop('id', None)
            new_event_data.pop('uid', None)
            new_event_data['date'] = occurrence_date
            
            new_event = self.model(**new_event_data)
            if user_ids_for_new:
                result = await db.execute(select(User).where(User.id.in_(user_ids_for_new)))
                new_event.users = result.scalars().unique().all()

            db.add(new_event)
            await db.commit()
            await db.refresh(new_event)
            return new_event

        if edit_mode == "this":
            # CORREÇÃO: Anexa a nova data de exceção à string da regra existente.
            # Isso é mais seguro do que reconstruir a regra inteira.
            new_exdate_line = f"EXDATE:{occurrence_date.strftime('%Y%m%dT%H%M%S')}"
            
            if db_obj.recurring_rule:
                db_obj.recurring_rule = f"{db_obj.recurring_rule}\n{new_exdate_line}".strip()
            else:
                db_obj.recurring_rule = new_exdate_line # Caso de segurança
            
            db.add(db_obj)

            # Cria um novo evento único com as alterações
            new_event_data = {**self.model_to_dict(db_obj), **update_data}
            user_ids_for_new = new_event_data.pop('user_ids', None)
            new_event_data.pop('id', None)
            new_event_data.pop('uid', None)
            new_event_data['recurring_rule'] = None
            new_event_data['date'] = occurrence_date
            
            new_event = self.model(**new_event_data)
            if user_ids_for_new:
                result = await db.execute(select(User).where(User.id.in_(user_ids_for_new)))
                new_event.users = result.scalars().unique().all()

            db.add(new_event)
            await db.commit()
            await db.refresh(new_event)
            return new_event

        return db_obj

    def model_to_dict(self, model_instance):
        d = {c.key: getattr(model_instance, c.key) for c in model_instance.__table__.columns}
        d['user_ids'] = [user.id for user in model_instance.users]
        return d
        
    async def update_associations(self, db: AsyncSession, db_obj: Events, obj_in: dict) -> Events:
        if 'user_ids' in obj_in:
            user_ids = obj_in.pop('user_ids')
            if user_ids is not None:
                await db.execute(delete(user_events_association).where(user_events_association.c.event_id == db_obj.id))
                if user_ids:
                    result = await db.execute(select(User).where(User.id.in_(user_ids)))
                    new_users = result.scalars().unique().all()
                    db_obj.users = new_users
                else:
                    db_obj.users = []
        return await super().update(db=db, db_obj=db_obj, obj_in=obj_in)

    async def get_event(self, db: AsyncSession, *, id: int) -> Optional[Events]:
        event = await super().get(db, id)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        return event

    async def get_multi_filtered(
        self, db: AsyncSession, *, skip: int, limit: int, filters: Optional[str] = None, model: Optional[str] = "", load_options: Optional[List] = None
    ) -> List[Events]:
        query = select(self.model)
        if load_options:
            query = query.options(*load_options)
        
        if filters and model:
            query = apply_filters_dynamic(query, filters, model)

        result = await db.execute(query.offset(skip).limit(limit if limit > 0 else None))
        return result.scalars().unique().all()
    
    async def get_event_with_users(self, db: AsyncSession, *, id: int) -> Optional[Events]:
        result = await db.execute(
            select(self.model)
            .options(selectinload(Events.users))
            .filter(self.model.id == id)
        )
        event = result.scalars().unique().first()
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        return event

    async def get_events_in_range(
        self, db: AsyncSession, *, calendar_id: int, start_date: datetime, end_date: datetime
    ) -> List[Events]:
        result = await db.execute(
            select(self.model)
            .where(
                (self.model.calendar_id == calendar_id) &
                (self.model.date >= start_date) &
                (self.model.date < end_date)
            )
        )
        return result.scalars().unique().all()

event_controller = CRUDEvent(Events)