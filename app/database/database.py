# agenda-risetec-backend/app/database/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
import os

# --- Configuração Assíncrona (para o resto do seu app FastAPI) ---
engine = create_async_engine(settings.DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

# --- Configuração Síncrona (para o CalDAV) ---
# Substitui o driver assíncrono (+asyncpg) pelo driver síncrono (padrão psycopg2)
sync_database_url = settings.DATABASE_URL.replace("+asyncpg", "") 
sync_engine = create_engine(sync_database_url, echo=True)
SessionLocalSync = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

Base = declarative_base()

# --- Sessão Assíncrona para Injeção de Dependência ---
async def get_db():
    async with SessionLocal() as session:
        yield session