from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers import fileController as file_controller
from app.database import database
from app.controllers.tokenController import verify_token
from app.schemas import fileSchema
import shutil, os, time

router = APIRouter(prefix="/crud")

# Upload de Arquivos
@router.post("/files/", response_model=fileSchema.FileCreate)
async def create_file(
    file: UploadFile = File(...), db: AsyncSession = Depends(database.get_db), validation: int = Depends(verify_token)
):  
    name, ext = os.path.splitext(file.filename)
    filename = str(time.time_ns()) + "_" + name + ext
    file_location = f"./files/{filename}"  # Define o caminho para salvar o arquivo

    if not os.path.exists("./files"):
        os.mkdir("./files")
        
    # Salvar arquivo no sistema de arquivos
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Criar um registro no banco de dados
    db_file = await file_controller.create_file(
        db=db,
        file=fileSchema.FileBase(
            filename=filename,
            originalname=file.filename,
            content_type=file.content_type,
            file_path=os.path.abspath(file_location)
        ),
    )
    return db_file

@router.get("/files/download/{file_id}", response_class=FileResponse)
async def download_file(file_id: int, db: AsyncSession = Depends(database.get_db)):
    db_file = await file_controller.get_file(db, file_id=file_id)
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")

    # Verificar se o arquivo existe no caminho especificado
    if not os.path.exists(db_file.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    # Retornar o arquivo para download
    return FileResponse(path=db_file.file_path, filename=db_file.filename, media_type=db_file.content_type)


@router.get("/files/", response_model=list[fileSchema.FileResponse])
async def read_files(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(database.get_db), filters: Optional[List[str]] = None, validation: int = Depends(verify_token)):
    files = await file_controller.get_files(db=db, skip=skip, limit=limit, filters=filters, model="File")
    return files

@router.get("/files/{file_id}", response_model=fileSchema.FileResponse)
async def read_file(file_id: int, db: AsyncSession = Depends(database.get_db), validation: int = Depends(verify_token)):
    db_file = await file_controller.get_file(db, file_id=file_id)
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return db_file

@router.delete("/files/{file_id}", response_model=bool)
async def delete_file(file_id: int, db: AsyncSession = Depends(database.get_db), validation: int = Depends(verify_token)):
    result = await file_controller.delete_file(db=db, file_id=file_id)
    if not result:
        raise HTTPException(status_code=404, detail="File not found")
    return True
