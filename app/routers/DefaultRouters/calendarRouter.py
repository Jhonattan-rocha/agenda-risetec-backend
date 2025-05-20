from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers.DefaultControllers import calendarController as calendar_controller
from app.controllers.DefaultControllers.tokenController import verify_token
from app.database import database
from app.schemas.DefaultSchemas import calendarSchema

router = APIRouter(prefix="/crud")


@router.post("/calendar/", response_model=calendarSchema.CalendarCreate)
async def create_calendar(calendar: calendarSchema.CalendarBase, db: AsyncSession = Depends(database.get_db)):
    return await calendar_controller.create_calendar(calendar=calendar, db=db)


@router.get("/calendar/", response_model=list[calendarSchema.Calendar])
async def read_calendars(filters: str = None, skip: int = 0, limit: int = 10,
                         db: AsyncSession = Depends(database.get_db),
                         validation: str = Depends(verify_token)):
    return await calendar_controller.get_calendars(skip=skip, limit=limit, db=db, filters=filters, model="Calendar")


@router.get("/calendar/{calendar_id}", response_model=calendarSchema.Calendar)
async def read_calendar(calendar_id: int, db: AsyncSession = Depends(database.get_db),
                        validation: str = Depends(verify_token)):
    return await calendar_controller.get_calendar(calendar_id=calendar_id, db=db)


@router.put("/calendar/{calendar_id}", response_model=calendarSchema.CalendarCreate)
async def update_calendar(calendar_id: int, updated_calendar: calendarSchema.CalendarCreate,
                          db: AsyncSession = Depends(database.get_db), validation: str = Depends(verify_token)):
    return await calendar_controller.update_calendar(calendar_id=calendar_id, updated_calendar=updated_calendar, db=db)


@router.delete("/calendar/{calendar_id}")
async def delete_calendar(calendar_id: int, db: AsyncSession = Depends(database.get_db),
                          validation: str = Depends(verify_token)):
    return await calendar_controller.delete_calendar(calendar_id=calendar_id, db=db)
