import json
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException, status
import jwt
from app.database import SessionLocal
from app.controllers.DefaultControllers import get_user, create_log
from app.controllers.DefaultControllers import SECRET_KEY, ALGORITHM
from app.schemas.DefaultSchemas import LoggerBase
import datetime
import os

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Inicializa o banco de dados
        async with SessionLocal() as db:
            # Captura os dados da requisição
            request_body = await request.body()
            action = (
                "Criar" if request.method.lower() == "post"
                else "Editar" if request.method.lower() in ["put", "patch"]
                else "Deletar" if request.method.lower() == "delete"
                else "Consultar"
            )
            
            user_id = await self.extract_user_id(request)
            user_info = None
            # Busca informações do usuário
            if user_id:
                try:
                    user = await get_user(db, user_id)
                    user_info = {
                        "email": user.email,
                        "id": user.id, 
                        "profile": user.profile_id,
                        "name": user.name
                    }
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid user id or token",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                    
                aux = "FILE"
                try:
                    aux = request_body.decode('utf-8') if request_body else None
                except Exception as e:
                    print(e)
                    
                request_data = {
                    "method": request.method,
                    "url": str(request.url),
                    "headers": dict(request.headers),
                    "body": aux,
                    "action": action,
                    "user": user_info, 
                    "type": "request",
                    "date": f"{datetime.datetime.now()}"
                }

                log = LoggerBase(**{
                    "action": action,
                    "user_id": int(user_id) if user_id else int(user_info["id"]),
                    "entity": request.url.path,
                    "data": json.dumps(request_data)
                })
                
                await create_log(db, log)
                
                # Processa a requisição
                response = await call_next(request)

                # Captura os dados da resposta
                response_data = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "action": action,
                    "user": user_info,  # Inclui as informações do usuário na resposta
                    "type": "response",
                    "date": f"{datetime.datetime.now()}"
                }

                log = LoggerBase(**{
                    "action": action,
                    "user_id": int(user_id) if user_id else int(user_info["id"]),
                    "entity": request.url.path,
                    "data": json.dumps(response_data)
                })
                
                await create_log(db, log)

                return response
            else:
                return await call_next(request)

    async def extract_user_id(self, request: Request) -> int:
        """
        Extrai o ID do usuário do JWT presente no cabeçalho Authorization.
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload.get("id")
        except Exception:
            return None
