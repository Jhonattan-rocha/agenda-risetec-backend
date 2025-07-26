# app/routers/eventsRouter.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.controllers import eventsController
from app.controllers.tokenController import verify_token
from app.database import database
from app.schemas.eventsSchema import Event, EventBase
from app.schemas.eventsSchema import EventUpdate

router = APIRouter(prefix="/crud", dependencies=[Depends(verify_token)], tags=["Events"])

@router.post("/event/", response_model=Event)
async def create_event(event: EventBase, db: AsyncSession = Depends(database.get_db)):
    return await eventsController.event_controller.create(db=db, obj_in=event)

@router.get("/event/", response_model=list[Event])
async def read_events(
    filters: str = None, 
    skip: int = 0, 
    limit: int = 10,
    db: AsyncSession = Depends(database.get_db),
):
    return await eventsController.event_controller.get_multi_filtered(
        db=db, 
        skip=skip, 
        limit=limit, 
        filters=filters,
        load_options=[selectinload(eventsController.event_controller.model.users)],
        model="Events"
    )

@router.get("/event/{event_id}", response_model=Event)
async def read_event(event_id: int, db: AsyncSession = Depends(database.get_db)):
    return await eventsController.event_controller.get_event_with_users(db=db, id=event_id)

@router.put("/event/{event_id}", response_model=Event)
async def update_event(
    event_id: int, 
    updated_event: EventUpdate,
    db: AsyncSession = Depends(database.get_db), 
):
    # CORREÇÃO: Usar o método que já carrega o relacionamento 'users'
    db_event = await eventsController.event_controller.get_event_with_users(db=db, id=event_id)
    return await eventsController.event_controller.update(db=db, db_obj=db_event, obj_in=updated_event)

@router.delete("/event/{event_id}", response_model=Event)
async def delete_event(event_id: int, db: AsyncSession = Depends(database.get_db)):
    deleted_event = await eventsController.event_controller.remove(db=db, id=event_id)
    if not deleted_event:
        raise HTTPException(status_code=404, detail="Event not found")
    return deleted_event