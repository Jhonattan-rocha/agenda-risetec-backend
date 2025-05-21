import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import database
from app.middleware.loggerMiddleware import LoggingMiddleware
from app.middleware.securityHeaders import SecurityHeadersMiddleware
from app.routers.DefaultRouters.userRouter import router as userRouter
from app.routers.DefaultRouters.userProfileRouter import router as userProfileRouter
from app.routers.DefaultRouters.permissionsRouter import router as permissionsRouter
from app.routers.DefaultRouters.tokenRouter import router as tokenRouter
from app.routers.DefaultRouters.fileRouter import router as fileRouter
from app.routers.DefaultRouters.logRouter import router as logRouter
from app.routers.CustomRouters.genericRouter import router as genericRouter
from app.routers.DefaultRouters.eventsRouter import router as eventsRouter
from app.routers.DefaultRouters.calendarRouter import router as calendarRouter
import os

@asynccontextmanager
async def lifespan_startup(app: FastAPI):
    app.include_router(genericRouter)
    app.include_router(userRouter)
    app.include_router(userProfileRouter)
    app.include_router(permissionsRouter)
    app.include_router(tokenRouter)
    app.include_router(fileRouter)
    app.include_router(logRouter)
    app.include_router(eventsRouter)
    app.include_router(calendarRouter)
    generate_doc()
    async with database.engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)
    
    yield


def generate_doc():
    with open("openapi.json", "w") as f:
        json.dump(app.openapi(), f, indent=4)


app = FastAPI(lifespan=lifespan_startup,
              title="Agenda Risetec",
              description="API under development",
              summary="Routes of app",
              version="0.0.1",
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

origins = [
    "https://localhost:3000",
    "https://localhost:5173",
    "*",
]

static_path = os.path.join(".", "files")

app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=origins,  # Permite essas origens
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos os cabeçalhos
)
app.add_middleware(SecurityHeadersMiddleware)
# app.add_middleware(LoggingMiddleware)
