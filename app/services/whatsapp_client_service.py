import httpx
from ..core.config import settings

class WhatsAppClientService:
    """
    Este serviço atua como um cliente para o nosso microserviço de WhatsApp.
    Ele é responsável por fazer as chamadas HTTP para o outro serviço.
    """
    def __init__(self):
        # A URL base do serviço de WhatsApp é pega das configurações.
        self.base_url = f"{settings.WHATSAPP_SERVICE_URL}/whatsapp"

    async def send_message(self, phone_number: str, message: str):
        """
        Envia uma requisição POST para o serviço de WhatsApp para enviar uma mensagem.
        """
        # Endpoint específico para envio de mensagens.
        send_url = f"{self.base_url}/send"
        payload = {"phone_number": phone_number, "message": message}

        async with httpx.AsyncClient() as client:
            try:
                print(f"Tentando enviar notificação via WhatsApp para: {phone_number}")
                response = await client.post(send_url, json=payload, timeout=30.0)

                # Lança uma exceção se a resposta for um erro HTTP (4xx ou 5xx).
                response.raise_for_status()

                print(f"Resposta do serviço de WhatsApp: {response.json()}")
                return {"success": True, "details": response.json()}

            except httpx.RequestError as e:
                # Ocorre se houver um problema de conexão com o serviço.
                print(f"Erro de conexão ao tentar contatar o serviço de WhatsApp: {e}")
                return {"success": False, "details": f"Não foi possível conectar ao serviço de WhatsApp em {e.request.url}"}

            except httpx.HTTPStatusError as e:
                # Ocorre se o serviço de WhatsApp retornar um erro (ex: 500).
                print(f"Serviço de WhatsApp retornou um erro: {e.response.status_code} - {e.response.text}")
                return {"success": False, "details": f"O serviço de WhatsApp retornou um erro: {e.response.status_code}"}

# Instância que pode ser importada em outros lugares
whatsapp_client_service = WhatsAppClientService()