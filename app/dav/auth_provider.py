# app/dav/auth_provider.py

from wsgidav.domain_controller import WsgiDavDir, WsgiDavDomainController
from app.database.database import SessionLocal
from app.controllers import userController

class RiseTecDomainController(WsgiDavDomainController):
    def __init__(self):
        super().__init__()
        self.user_mapping = {}

    def get_domain_realm(self, input_url, environ):
        return "RiseTec Agenda"

    async def require_authentication(self, realm, environ):
        # Sempre requer autenticação
        return True

    async def basic_auth_user(self, realm, user_name, password, environ):
        """Autentica um usuário usando o controller existente."""
        async with SessionLocal() as db:
            try:
                # Usa a função de autenticação que já existe no seu projeto
                user = await userController.user_controller.authenticate(
                    db, email=user_name, password=password
                )
                if user:
                    # Se o usuário for válido, retorna True
                    return True
            except Exception as e:
                print(f"Erro na autenticação DAV: {e}")
                return False
        return False