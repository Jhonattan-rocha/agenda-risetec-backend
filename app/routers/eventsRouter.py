# agenda-risetec-backend/app/routers/eventsRouter.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
# ALTERAÇÃO: Importa a instância do controller.
from app.controllers import eventsController
from app.controllers.tokenController import verify_token
from app.database import database
from app.schemas.eventsSchema import Event, EventBase, EventCreate

router = APIRouter(prefix="/crud", dependencies=[Depends(verify_token)], tags=["Events"])

@router.post("/event/", response_model=Event)
async def create_event(
    event: EventBase, 
    db: AsyncSession = Depends(database.get_db), 
):
    return await eventsController.event_controller.create(db=db, obj_in=event)

@router.get("/event/", response_model=list[Event])
async def read_events(
    filters: str = None, 
    skip: int = 0, 
    limit: int = 10,
    db: AsyncSession = Depends(database.get_db),
):
    return await eventsController.event_controller.get_multi_filtered(
        db=db, skip=skip, limit=limit, filters=filters, model="Events"
    )

@router.get("/event/{event_id}", response_model=Event)
async def read_event(
    event_id: int, 
    db: AsyncSession = Depends(database.get_db), 
):
    return await eventsController.event_controller.get_event(db=db, id=event_id)

@router.put("/event/{event_id}", response_model=Event)
async def update_event(
    event_id: int, 
    updated_event: EventCreate,
    db: AsyncSession = Depends(database.get_db), 
):
    db_event = await eventsController.event_controller.get(db=db, id=event_id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    return await eventsController.event_controller.update(db=db, db_obj=db_event, obj_in=updated_event)

@router.delete("/event/{event_id}", response_model=Event)
async def delete_event(
    event_id: int, 
    db: AsyncSession = Depends(database.get_db),
):
    deleted_event = await eventsController.event_controller.remove(db=db, id=event_id)
    if not deleted_event:
        raise HTTPException(status_code=404, detail="Event not found")
    return deleted_event