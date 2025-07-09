# agenda-risetec-backend/app/routers/calendarRouter.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.controllers import calendarController
from app.controllers.tokenController import verify_token
from app.database import database
from app.schemas.calendarSchema import Calendar, CalendarBase, CalendarCreate

router = APIRouter(prefix="/crud", tags=["Calendars"], dependencies=[Depends(verify_token)])

@router.post("/calendar/", response_model=Calendar)
async def create_calendar(
    calendar: CalendarBase, 
    db: AsyncSession = Depends(database.get_db), 
):
    return await calendarController.calendar_controller.create(db=db, obj_in=calendar)

@router.get("/calendar/", response_model=list[Calendar])
async def read_calendars(
    filters: str = None, 
    skip: int = 0, 
    limit: int = 100, # Aumentei o limite padrão
    db: AsyncSession = Depends(database.get_db),
    current_user: int = Depends(verify_token)
):
    # ATUALIZADO: Chama o método genérico e passa a opção de carregar eventos.
    return await calendarController.calendar_controller.get_multi_filtered(
        db=db, 
        skip=skip, 
        limit=limit, 
        filters=filters,
        load_options=[selectinload(calendarController.calendar_controller.model.events)]
    )

@router.get("/calendar/{calendar_id}", response_model=Calendar)
async def read_calendar(
    calendar_id: int, 
    db: AsyncSession = Depends(database.get_db),
):
    # ALTERAÇÃO: Usa o método customizado 'get_with_events'.
    return await calendarController.calendar_controller.get_with_events(db=db, id=calendar_id)

@router.put("/calendar/{calendar_id}", response_model=Calendar)
async def update_calendar(
    calendar_id: int, 
    updated_calendar: CalendarCreate,
    db: AsyncSession = Depends(database.get_db), 
):
    # ALTERAÇÃO: Busca o objeto antes de atualizar.
    db_calendar = await calendarController.calendar_controller.get(db=db, id=calendar_id)
    if not db_calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")
    return await calendarController.calendar_controller.update(db=db, db_obj=db_calendar, obj_in=updated_calendar)

@router.delete("/calendar/{calendar_id}", response_model=Calendar)
async def delete_calendar(
    calendar_id: int, 
    db: AsyncSession = Depends(database.get_db),
):
    # ALTERAÇÃO: Usa o método 'remove' da classe base.
    deleted_calendar = await calendarController.calendar_controller.remove(db=db, id=calendar_id)
    if not deleted_calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")
    return deleted_calendar