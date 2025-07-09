from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.database import Base
from app.utils import apply_filters_dynamic

# Define tipos genéricos para o modelo e os esquemas
ModelType = TypeVar("ModelType", bound=Base) # type: ignore
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        Controller base com operações CRUD.

        **Parâmetros**

        * `model`: Uma classe de modelo SQLAlchemy
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        result = await db.execute(select(self.model).filter(self.model.id == id))
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        result = await db.execute(
            select(self.model)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    # NOVO: Método centralizado para obter múltiplos registros com filtros e ordenação
    async def get_multi_filtered(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100, 
        filters: Optional[str] = None,
        # Permite passar opções de carregamento (selectinload)
        load_options: Optional[List] = None 
    ) -> List[ModelType]:
        query = select(self.model)

        # Aplica o carregamento eager de relacionamentos se fornecido
        if load_options:
            query = query.options(*load_options)

        # Aplica os filtros dinâmicos se existirem
        if filters:
            # Passa o nome do modelo para a função de filtro
            query = apply_filters_dynamic(query, filters, self.model.__name__)

        query = query.offset(skip).limit(limit if limit > 0 else None)
        
        result = await db.execute(query)
        # Usa .unique() para evitar duplicatas ao usar joins
        return result.scalars().unique().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in.model_dump(exclude_unset=True, exclude_none=True))
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    # --- MÉTODO CORRIGIDO ---
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        # Determina a fonte dos dados de atualização
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # Se for um schema Pydantic, converte para dict, excluindo valores não definidos
            update_data = obj_in.model_dump(exclude_unset=True)

        # Itera diretamente sobre os dados recebidos para atualizar o objeto
        for field, value in update_data.items():
            setattr(db_obj, field, value)
                
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    # --- FIM DA CORREÇÃO ---

    async def remove(self, db: AsyncSession, *, id: int) -> Optional[ModelType]:
        result = await db.execute(select(self.model).filter(self.model.id == id))
        obj = result.scalars().first()
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj