from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers.DefaultControllers import eventsController as event_controller
from app.controllers.DefaultControllers.tokenController import verify_token
from app.database import database
from app.schemas.DefaultSchemas import eventsSchema

router = APIRouter(prefix="/crud")


@router.post("/event/", response_model=eventsSchema.EventCreate)
async def create_event(event: eventsSchema.EventBase, db: AsyncSession = Depends(database.get_db), validation: str = Depends(verify_token)):
    return await event_controller.create_event(event=event, db=db)


@router.get("/event/", response_model=list[eventsSchema.Event])
async def read_events(filters: str = None, skip: int = 0, limit: int = 10,
                     db: AsyncSession = Depends(database.get_db),
                     validation: str = Depends(verify_token)):
    result = await event_controller.get_events(skip=skip, limit=limit, db=db, filters=filters, model="Events")
    return result


@router.get("/event/{event_id}", response_model=eventsSchema.Event)
async def read_event(event_id: int, db: AsyncSession = Depends(database.get_db), validation: str = Depends(verify_token)):
    return await event_controller.get_event(event_id=event_id, db=db)


@router.put("/event/{event_id}", response_model=eventsSchema.EventCreate)
async def update_event(event_id: int, updated_event: eventsSchema.EventCreate,
                      db: AsyncSession = Depends(database.get_db), validation: str = Depends(verify_token)):
    return await event_controller.update_event(event_id=event_id, updated_event=updated_event, db=db)


@router.delete("/event/{event_id}")
async def delete_event(event_id: int, db: AsyncSession = Depends(database.get_db),
                      validation: str = Depends(verify_token)):
    return await event_controller.delete_event(event_id=event_id, db=db)
