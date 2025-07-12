# app/controllers/syncCalendarController.py

from sqlalchemy.orm import Session, selectinload
from typing import Optional, List
from app.models.calendarModel import Calendar
from app.models.userModel import User # Importar User para o relacionamento
from app.schemas.calendarSchema import CalendarBase

def get_with_events_sync(db: Session, *, id: int) -> Optional[Calendar]:
    """Busca um calendário com seus eventos pré-carregados."""
    return db.query(Calendar).options(selectinload(Calendar.events)).filter(Calendar.id == id).first()

def get_by_owner_and_name_sync(db: Session, *, owner_id: int, name: str) -> Optional[Calendar]:
    """Busca um calendário pelo nome e ID do proprietário."""
    return db.query(Calendar).filter_by(owner_id=owner_id, name=name).first()

def get_all_by_owner_sync(db: Session, *, owner_id: int) -> List[Calendar]:
    """Busca todos os calendários de um proprietário."""
    return db.query(Calendar).filter_by(owner_id=owner_id).all()

def create_sync(db: Session, *, obj_in: CalendarBase) -> Calendar:
    """Cria um novo calendário no banco de dados."""
    db_obj = Calendar(**obj_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj