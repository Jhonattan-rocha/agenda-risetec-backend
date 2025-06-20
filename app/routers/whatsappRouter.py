from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import database
from ..controllers.tokenController import verify_token
from ..controllers import userController
from ..services.whatsapp_client_service import whatsapp_client_service

router = APIRouter(
    prefix="/crud/whatsapp",
    tags=["Admin - WhatsApp"]
)

async def get_admin_user(
    current_user_id: int = Depends(verify_token),
    db: AsyncSession = Depends(database.get_db)
):
    """
    Dependência de segurança que verifica se o usuário logado é um admin.
    Adapte o `profile.name` para o nome do perfil de admin no seu sistema.
    """
    user = await userController.user_controller.get_user_with_details(db, user_id=current_user_id)
    # IMPORTANTE: Altere "Admin" para o nome exato do seu perfil de administrador
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Recurso disponível apenas para administradores."
        )
    return user

@router.get("/status")
async def get_whatsapp_status(admin_user: dict = Depends(get_admin_user)):
    """
    Obtém o status atual do serviço de WhatsApp.
    Se o status for 'SCAN_QR', o campo 'qrCode' conterá os dados para gerar a imagem.
    """
    return await whatsapp_client_service.get_status()

@router.post("/reconnect")
async def reconnect_whatsapp_service(admin_user: dict = Depends(get_admin_user)):
    """
    Envia um comando para o serviço de WhatsApp tentar se reconectar.
    Útil se o serviço estiver no estado 'DISCONNECTED'.
    """
    return await whatsapp_client_service.reconnect()

@router.post("/logout")
async def logout_whatsapp_service(admin_user: dict = Depends(get_admin_user)):
    """
    Desconecta a sessão atual do WhatsApp.
    O serviço entrará no estado 'DISCONNECTED' e será necessário reconectar e escanear um novo QR Code.
    """
    return await whatsapp_client_service.logout()