from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers.DefaultControllers import permissonsController as permissons_controller
from app.database import database
from app.schemas.DefaultSchemas import permissionsSchema
from app.controllers import verify_token

router = APIRouter(prefix="/crud")


@router.post("/permissions/", response_model=permissionsSchema.PermissionsCreate)
async def create_permission(permissions: permissionsSchema.PermissionsBase, db: AsyncSession = Depends(database.get_db), validation: str = Depends(verify_token)):
    return await permissons_controller.create_permissions(permissions=permissions, db=db)


@router.get("/permissions/", response_model=list[permissionsSchema.Permissions])
async def read_permissions(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(database.get_db), validation: str = Depends(verify_token)):
    return await permissons_controller.get_permissions(skip=skip, limit=limit, db=db)


@router.get("/permissions/{permission_id}", response_model=permissionsSchema.Permissions)
async def read_permission(permission_id: int, db: AsyncSession = Depends(database.get_db), validation: str = Depends(verify_token)):
    return await permissons_controller.get_permission(permissions_id=permission_id, db=db)


@router.put("/permissions/{permission_id}", response_model=permissionsSchema.PermissionsCreate)
async def update_permission(permission_id: int, updated_permissions: permissionsSchema.PermissionsCreate,
                          db: AsyncSession = Depends(database.get_db), validation: str = Depends(verify_token)):
    return await permissons_controller.update_permissions(permissions_id=permission_id,
                                                          updated_permissions=updated_permissions, db=db)


@router.delete("/permissions/{permission_id}")
async def delete_permission(permission_id: int, db: AsyncSession = Depends(database.get_db), validation: str = Depends(verify_token)):
    return await permissons_controller.delete_permissions(permissions_id=permission_id, db=db)
