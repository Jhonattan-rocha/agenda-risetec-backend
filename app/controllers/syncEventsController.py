# app/controllers/syncEventsController.py

from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, delete, and_
from typing import Optional, List
from datetime import datetime

from app.models.eventsModel import Events, user_events_association
from app.models.userModel import User
from app.schemas.eventsSchema import EventUpdate

def get_sync(db: Session, id: int) -> Optional[Events]:
    """Busca um evento pelo ID."""
    return db.query(Events).filter(Events.id == id).first()

def remove_sync(db: Session, *, id: int) -> Optional[Events]:
    """Remove um evento do banco de dados."""
    obj = db.query(Events).get(id)
    if obj:
        db.delete(obj)
        db.commit()
    return obj

def create_or_update_sync(db: Session, *, event_data: dict, event_id: int = None, calendar_id: int = None) -> Events:
    """Cria ou atualiza um evento."""
    user_ids = event_data.pop('user_ids', [])
    
    # Se event_id for fornecido, tenta atualizar
    db_event = None
    if event_id:
        db_event = get_sync(db, event_id)

    if db_event: # Atualiza
        for field, value in event_data.items():
            setattr(db_event, field, value)
    else: # Cria
        event_data['calendar_id'] = calendar_id
        db_event = Events(**event_data)
        db.add(db_event)

    # Atualiza usuários
    if user_ids:
        users = db.query(User).filter(User.id.in_(user_ids)).all()
        db_event.users = users
    else:
        db_event.users = []

    db.commit()
    db.refresh(db_event)
    return db_event