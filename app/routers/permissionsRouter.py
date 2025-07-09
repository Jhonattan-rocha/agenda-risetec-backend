# agenda-risetec-backend/app/routers/permissionsRouter.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers import permissonsController
from app.database import database
from app.schemas.permissionsSchema import Permissions, PermissionsBase, PermissionsCreate
from app.controllers.tokenController import verify_token

router = APIRouter(prefix="/crud", tags=["Permission"], dependencies=[Depends(verify_token)])

@router.post("/permissions/", response_model=Permissions)
async def create_permission(
    permissions: PermissionsBase, 
    db: AsyncSession = Depends(database.get_db), 
):
    return await permissonsController.permission_controller.create(db=db, obj_in=permissions)

@router.get("/permissions/", response_model=list[Permissions])
async def read_permissions(
    skip: int = 0, 
    limit: int = 10, 
    db: AsyncSession = Depends(database.get_db), 
):
    return await permissonsController.permission_controller.get_multi_with_profile(db=db, skip=skip, limit=limit)

@router.get("/permissions/{permission_id}", response_model=Permissions)
async def read_permission(
    permission_id: int, 
    db: AsyncSession = Depends(database.get_db), 
):
    permission = await permissonsController.permission_controller.get_with_profile(db=db, id=permission_id)
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    return permission

@router.put("/permissions/{permission_id}", response_model=Permissions)
async def update_permission(
    permission_id: int, 
    updated_permissions: PermissionsCreate,
    db: AsyncSession = Depends(database.get_db), 
):
    db_permission = await permissonsController.permission_controller.get(db=db, id=permission_id)
    if not db_permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    return await permissonsController.permission_controller.update(db=db, db_obj=db_permission, obj_in=updated_permissions)

@router.delete("/permissions/{permission_id}", response_model=Permissions)
async def delete_permission(
    permission_id: int, 
    db: AsyncSession = Depends(database.get_db), 
):
    deleted_permission = await permissonsController.permission_controller.remove(db=db, id=permission_id)
    if not deleted_permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    return deleted_permission