import httpx
from ..core.config import settings

class WhatsAppClientService:
    def __init__(self):
        self.base_url = f"{settings.WHATSAPP_SERVICE_URL}/" # Aponta para a raiz do serviço
    
    async def get_status(self):
        """Busca o status completo do serviço de WhatsApp."""
        status_url = f"{self.base_url}status"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(status_url, timeout=10.0)
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                return {"status": "UNREACHABLE", "message": f"Não foi possível conectar ao serviço de WhatsApp: {e}"}
            except httpx.HTTPStatusError as e:
                return {"status": "ERROR", "message": f"O serviço de WhatsApp retornou um erro: {e.response.status_code}"}

    async def reconnect(self):
        """Envia um comando para o serviço de WhatsApp se reconectar."""
        reconnect_url = f"{self.base_url}reconnect"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(reconnect_url, timeout=10.0)
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                return {"success": False, "message": f"Não foi possível conectar ao serviço de WhatsApp: {e}"}
            except httpx.HTTPStatusError as e:
                return {"success": False, "message": f"O serviço de WhatsApp retornou um erro: {e.response.status_code}"}

    async def send_message(self, phone_number: str, message: str):
        send_url = "http://10.10.124.244:8080/api/messages/send"
        payload = {"number": phone_number, "body": message}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(send_url, json=payload, timeout=30.0, headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer lahskjdsadsiu",
                            "X_TOKEN": "lahskjdsadsiu"
                        })
                response.raise_for_status()
                return {"success": True, "details": response.json()}
            except httpx.RequestError as e:
                return {"success": False, "details": f"Não foi possível conectar ao serviço de WhatsApp em {e.request.url}"}
            except httpx.HTTPStatusError as e:
                return {"success": False, "details": f"O serviço de WhatsApp retornou um erro: {e.response.status_code}, {e.response.text}"}

    async def send_messagev2(self, phone_number: str, message: str):
        """Envia uma mensagem de texto."""
        send_url = f"{self.base_url}send-message"
        payload = {"phone_number": phone_number, "message": message}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(send_url, json=payload, timeout=30.0)
                response.raise_for_status()
                return {"success": True, "details": response.json()}
            except httpx.RequestError as e:
                return {"success": False, "details": f"Não foi possível conectar ao serviço de WhatsApp em {e.request.url}"}
            except httpx.HTTPStatusError as e:
                return {"success": False, "details": f"O serviço de WhatsApp retornou um erro: {e.response.status_code}, {e.response.text}"}

    async def logout(self):
        """Envia um comando para o serviço de WhatsApp fazer logout."""
        logout_url = f"{self.base_url}logout"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(logout_url, timeout=10.0)
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                return {"success": False, "message": f"Não foi possível conectar ao serviço de WhatsApp: {e}"}
            except httpx.HTTPStatusError as e:
                return {"success": False, "message": f"O serviço de WhatsApp retornou um erro: {e.response.status_code}"}


whatsapp_client_service = WhatsAppClientService()