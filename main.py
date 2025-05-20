import json
import app.services.notificate
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
from app.routers.DefaultRouters.tasksRouter import router as tasksRouter
from app.services.notificate import job_executed_listener, check_and_notify, EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, AsyncIOScheduler
import os
from uvicorn.config import LOGGING_CONFIG
import globals


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
    app.include_router(tasksRouter)
    generate_doc()
    async with database.engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)
    
    # Inicialização do scheduler
    app.state.scheduler = AsyncIOScheduler()
    app.state.scheduler.add_listener(lambda event: job_executed_listener(event, app.state.scheduler), EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    app.state.scheduler.add_job(lambda: check_and_notify(database.SessionLocal()), 'interval', hours=24)
    app.state.scheduler.start()

    yield


def generate_doc():
    with open("openapi.json", "w") as f:
        json.dump(app.openapi(), f, indent=4)


app = FastAPI(lifespan=lifespan_startup,
              title="Agenda-IMKTEC",
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
app.add_middleware(LoggingMiddleware)

# Configuração do formato do log
LOGGING_CONFIG["formatters"]["access"] = {
    "()": "uvicorn.logging.AccessFormatter",
    "fmt": "%(asctime)s - %(levelname)s - %(client_addr)s - %(request_line)s - %(status_code)s",
}

# Configuração do handler para salvar os logs em arquivo
LOGGING_CONFIG["handlers"]["file"] = {
    "class": "logging.FileHandler",
    "filename": os.path.join(".", "logs", "access.log"),  # Nome do arquivo de log
    "formatter": "access",
}

# Adiciona o novo handler no logger de acesso
LOGGING_CONFIG["loggers"]["uvicorn.access"] = {
    "level": "INFO",
    "handlers": ["file"],  # Define que o log de acesso será salvo no arquivo
    "propagate": False,
}

if __name__ == "__main__":
    import uvicorn
    import sys
    
    if not os.path.exists(os.path.join(".", "logs")):    
        os.mkdir(os.path.join(".", "logs"))
    uvicorn.run("main:app", ssl_certfile=os.path.join(".", "cert", "cert.pem"), ssl_keyfile=os.path.join(".", "cert", "key.pem"), host=sys.argv[1] if len(sys.argv) > 1 else "localhost", port=8081, reload=True, log_config=LOGGING_CONFIG, proxy_headers=True)
