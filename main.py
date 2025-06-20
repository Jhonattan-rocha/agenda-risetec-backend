# agenda-risetec-backend/main.py

import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import database
from app.middleware.loggerMiddleware import LoggingMiddleware
from app.middleware.securityHeaders import SecurityHeadersMiddleware
import os

# NOVO: Lista centralizada de roteadores para inclusão automática
from app.routers import (
    userRouter, userProfileRouter, permissionsRouter, tokenRouter,
    fileRouter, logRouter, genericRouter, eventsRouter, calendarRouter
)

# NOVO: Agrupa todos os roteadores em uma lista para facilitar o registro
all_routers = [
    genericRouter.router,
    userRouter.router,
    userProfileRouter.router,
    permissionsRouter.router,
    tokenRouter.router,
    fileRouter.router,
    logRouter.router,
    eventsRouter.router,
    calendarRouter.router
]

@asynccontextmanager
async def lifespan_startup(app: FastAPI):
    # NOVO: Itera sobre a lista de roteadores e os inclui na aplicação
    for router in all_routers:
        app.include_router(router)
    
    generate_doc()
    async with database.engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)
    
    yield


def generate_doc():
    # Esta função pode ser movida para um script de build/deploy em um ambiente de produção
    with open("openapi.json", "w") as f:
        json.dump(app.openapi(), f, indent=4)


app = FastAPI(lifespan=lifespan_startup,
              title="Agenda Risetec",
              description="API under development",
              summary="Routes of app",
              version="0.0.2", # Versão atualizada
              terms_of_service="http://example.com/terms/",
              contact={
                  "name": "Jhonattan Rocha da Silva",
                  "url": "http://www.example.com/contact/",
                  "email": "jhonattab246rocha@gmail.com",
              },
              license_info={
                  "name": "Apache 2.0",
                  "identifier": "MIT",
              })

# ATENÇÃO: Em produção, evite usar "*" e especifique as origens permitidas.
origins = [
    "https://localhost:3000",
    "https://localhost:5173",
    "*",
]

static_path = os.path.join(".", "files")

app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
# O LoggingMiddleware está comentado, mantendo o comportamento original.
# app.add_middleware(LoggingMiddleware)