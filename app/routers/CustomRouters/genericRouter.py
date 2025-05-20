from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers.CustomControllers import GenericController, models_mapping
from app.database import database, Base
from app.schemas.CustomSchemas import genericSchema
from app.controllers import verify_token

router = APIRouter(prefix="/crud")


@router.post("/generic", response_model=genericSchema.GenericCreate)
async def generic_create(generic: genericSchema.GenericCreate,
                         db: AsyncSession = Depends(database.get_db), model: str = "", validation: str = Depends(verify_token)):


    generic_controller = GenericController(model=model)
    result = await generic_controller.create(obj_in=generic, db=db)
    aux = {}
    for key in generic_controller.fields:
        aux[key] = getattr(result, key)
    return genericSchema.GenericCreate(**{
        'values': aux,
        'model': model
    })


@router.get("/generic", response_model=list[genericSchema.GenericCreate])
async def generic_reads(skip: int = 0, limit: int = 10, model: str = "",
                        db: AsyncSession = Depends(database.get_db), filters: str = None, validation: str = Depends(verify_token)):


    generic_controller = GenericController(model=model)
    result = await generic_controller.catch(skip=skip, limit=limit, db=db, model=model, filters=filters)
    if len(result) < 1:
        return []
    keys = [key for key in result[0].__dict__.keys() if not key.startswith('_')]
    getValueFromObj = lambda item: {key: getattr(item, key) if not isinstance(getattr(item, key), Base) else generic_controller.serialize_item(getattr(item, key)) for key in keys}
    return [genericSchema.GenericCreate(**{'values': {**getValueFromObj(item)}, 'model': model}) for item in result]


@router.get("/generic/{generic_id}",
            response_model=genericSchema.GenericCreate)
async def generic_read(generic_id: int, model: str = "", db: AsyncSession = Depends(database.get_db), validation: str = Depends(verify_token)):


    generic_controller = GenericController(model=model)
    result = await generic_controller.get(id=generic_id, db=db)
    if result is None:
        raise HTTPException(status_code=404, detail="Item not found")

    keys = [key for key in result.__dict__.keys() if not key.startswith('_')]
    return genericSchema.GenericCreate(**{'values': {key: getattr(result, key) if not isinstance(getattr(result, key), Base) else generic_controller.serialize_item(getattr(result, key)) for key in keys}, 'model': model})


@router.put("/generic/{generic_id}",
            response_model=genericSchema.GenericCreate)
async def generic_update(generic_id: int,
                         model: str,
                         updated_generic: genericSchema.GenericCreate,
                         db: AsyncSession = Depends(database.get_db), validation: str = Depends(verify_token)):


    generic_controller = GenericController(model=model)
    db_obj = await generic_controller.get(id=generic_id, db=db)
    result = await generic_controller.update(db_obj=db_obj, obj_in=updated_generic, db=db)
    keys = [key for key in result.__dict__.keys() if not key.startswith('_')]
    return genericSchema.GenericCreate(**{'values': {key: getattr(result, key) if not isinstance(getattr(result, key), Base) else generic_controller.serialize_item(getattr(result, key)) for key in keys}, 'model': model})


@router.delete("/generic/{generic_id}", response_model=genericSchema.GenericCreate)
async def generic_delete(generic_id: int, model: str, db: AsyncSession = Depends(database.get_db), validation: str = Depends(verify_token)):


    generic_controller = GenericController(model=model)
    result = await generic_controller.delete(id=generic_id, db=db)
    if result is None:
        raise HTTPException(status_code=404, detail="Item not found")
    keys = [key for key in result.__dict__.keys() if not key.startswith('_')]
    return genericSchema.GenericCreate(**{'values': {key: getattr(result, key) if not isinstance(getattr(result, key), Base) else generic_controller.serialize_item(getattr(result, key)) for key in keys}, 'model': model})
