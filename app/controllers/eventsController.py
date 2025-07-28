# app/controllers/eventsController.py

from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from dateutil.rrule import rrulestr, rrule, rruleset

from app.controllers.base import CRUDBase
from app.models.eventsModel import Events
from app.models.userModel import User
from app.schemas.eventsSchema import EventCreate, EventBase, EventUpdate
from app.utils import apply_filters_dynamic
from app.models.calendarModel import Calendar  # IMPORTANTE

def serialize_rruleset(rs: rruleset, dtstart: datetime) -> str:
    """
    Serializa manualmente um rruleset para o formato iCalendar (RFC 5545).
    Inclui RRULE, RDATE, EXDATE, EXRULE.
    """
    lines = [f"DTSTART:{dtstart.strftime('%Y%m%dT%H%M%S')}"]

    for rule in rs._rrule:
        lines.append(f"RRULE:{str(rule).splitlines()[1].replace('RRULE:', '')}")

    for exrule in rs._exrule:
        lines.append(f"EXRULE:{str(exrule).splitlines()[1].replace('RRULE:', '')}")

    for rdate in rs._rdate:
        for d in rdate:
            lines.append(f"RDATE:{d.strftime('%Y%m%dT%H%M%S')}")

    for exdate in rs._exdate:
        lines.append(f"EXDATE:{exdate.strftime('%Y%m%dT%H%M%S')}")

    return '\n'.join(lines)

class CRUDEvent(CRUDBase[Events, EventCreate, EventUpdate]):

    async def _associate_users(self, db: AsyncSession, db_obj: Events, user_ids: List[int]) -> Events:
        """
        Função auxiliar para associar usuários a um evento, limpando as associações antigas.
        """
        # Carrega a relação 'users' se ainda não estiver carregada, para evitar erros.
        if 'users' not in db_obj.__dict__:
            result = await db.execute(select(Events).options(selectinload(Events.users)).filter(Events.id == db_obj.id))
            db_obj = result.scalars().first()

        if user_ids:
            result = await db.execute(select(User).where(User.id.in_(user_ids)))
            users = result.scalars().unique().all()
            if len(users) != len(user_ids):
                raise HTTPException(status_code=404, detail="Um ou mais usuários não foram encontrados.")
            db_obj.users = users

        return db_obj

    async def create(self, db: AsyncSession, *, obj_in: EventBase) -> Events:
        # Busca o calendário para herdar as configurações
        calendar_result = await db.execute(select(Calendar).filter(Calendar.id == obj_in.calendar_id))
        calendar = calendar_result.scalars().first()
        if not calendar:
            raise HTTPException(status_code=404, detail="Calendário não encontrado.")

        obj_in_data = obj_in.model_dump(exclude_unset=True, exclude_none=True)
        user_ids = obj_in_data.pop('user_ids', [])
        
        # --- ALTERAÇÃO PRINCIPAL AQUI ---
        # Define a cor do evento como a cor do calendário, se nenhuma cor for especificada.
        obj_in_data.setdefault('color', calendar.color)
        
        # Preenche as configurações de notificação do evento com as do calendário, se não forem fornecidas
        obj_in_data.setdefault('notification_type', calendar.notification_type)
        obj_in_data.setdefault('notification_time_before', calendar.notification_time_before)
        obj_in_data.setdefault('notification_repeats', calendar.notification_repeats)
        obj_in_data.setdefault('notification_message', calendar.notification_message)
        
        db_obj = self.model(**obj_in_data)
        
        if user_ids:
            result = await db.execute(select(User).where(User.id.in_(user_ids)))
            db_obj.users = result.scalars().unique().all()

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
        user_ids_payload = update_data.pop('user_ids', None)

        # Edição de um evento não-recorrente ou de toda a série
        if edit_mode == "all" or not db_obj.recurring_rule:
            updated_obj = await super().update(db=db, db_obj=db_obj, obj_in=update_data)
            if user_ids_payload is not None:
                updated_obj = await self._associate_users(db, updated_obj, user_ids_payload)
            await db.commit()
            await db.refresh(updated_obj)
            return updated_obj

        # Validação para edição de instâncias
        if not occurrence_date:
            raise HTTPException(status_code=400, detail="A data da ocorrência é necessária para editar um evento recorrente.")

        await db.refresh(db_obj, attribute_names=['users'])

        # Prepara os dados para o novo evento ANTES de modificar o original
        new_event_data = self.model_to_dict(db_obj)
        new_event_data.update(update_data)
        new_event_data.pop('id', None)
        new_event_data.pop('uid', None)
        new_event_data['date'] = occurrence_date
        new_event_data['recurring_rule'] = None 

        original_rule_str = f"DTSTART:{db_obj.date.strftime('%Y%m%dT%H%M%S')}\n{db_obj.recurring_rule}"
        rule_set = rrulestr(original_rule_str, forceset=True)
        
        if edit_mode == "future":
            original_rule: rrule = rule_set._rrule[0]
            db_obj.recurring_rule = original_rule.__str__()
            new_event_data['recurring_rule'] = db_obj.recurring_rule.replace(f"UNTIL={original_rule._until.strftime('%Y%m%dT%H%M%S')}Z", "")

        elif edit_mode == "this":
            rule_set.exdate(occurrence_date)
            db_obj.recurring_rule = serialize_rruleset(rule_set, db_obj.date)


        db.add(db_obj) # Adiciona o objeto original modificado à sessão

        new_event = self.model(**new_event_data)
        db.add(new_event) # Adiciona o novo evento à sessão
        
        await db.commit() # Salva ambas as alterações
        await db.refresh(new_event)

        # Associa os participantes ao novo evento criado
        final_user_ids = user_ids_payload if user_ids_payload is not None else [user.id for user in db_obj.users]
        new_event_with_users = await self._associate_users(db, new_event, final_user_ids)
        
        await db.commit() # Salva as associações de usuários
        await db.refresh(new_event_with_users)

        return new_event_with_users

    def model_to_dict(self, model_instance):
        return {c.key: getattr(model_instance, c.key) for c in model_instance.__table__.columns}
        
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