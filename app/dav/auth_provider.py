# app/dav/auth_provider.py

import asyncio
from app.database.database import SessionLocal
from app.controllers import userController

class RiseTecDomainController:
    """
    Controlador de domínio customizado para autenticar usuários
    contra o banco de dados da aplicação, compatível com WsgiDAV v3+.
    """
    # --- CORREÇÃO AQUI ---
    # O construtor agora aceita `wsgidav_app` e `config` como esperado pela biblioteca.
    def __init__(self, wsgidav_app, config):
        self._wsgidav_app = wsgidav_app
        self._config = config

    def is_share_anonymous(self, share):
        """
        Informa ao WsgiDAV que nenhuma das nossas pastas permite acesso anônimo.
        'share' aqui é a chave do `provider_mapping` (no nosso caso, "/").
        """
        return False
    
    def require_authentication(self, realm, environ):
        """
        Informa ao WsgiDAV que este realm (qualquer parte do nosso servidor)
        sempre requer autenticação.
        """
        return True

    def get_domain_realm(self, path_info, environ):
        """Retorna o nome do 'realm' para o diálogo de autenticação."""
        return "RiseTec Agenda"

    def basic_auth_user(self, realm, user_name, password, environ):
        """
        Autentica um usuário usando o método Basic Auth.
        Este método é síncrono, então precisamos de uma maneira de chamar nosso
        código assíncrono de forma segura.
        """
        try:
            # Usamos asyncio.run para executar nossa coroutine de autenticação
            # em um novo loop de eventos.
            user = asyncio.run(self._authenticate_async(user_name, password))

            if user:
                # Se a autenticação for bem-sucedida, informamos ao wsgidav.
                environ["wsgidav.auth.user_name"] = user.name
                environ["wsgidav.auth.display_name"] = user.name
                if user.profile:
                    environ["wsgidav.auth.roles"] = {user.profile.name}
                return True

        except Exception as e:
            # Registra qualquer erro que ocorra durante a autenticação
            print(f"Erro na autenticação DAV: {e}")

        # Se a autenticação falhar por qualquer motivo, retorna False.
        return False

    async def _authenticate_async(self, email, password):
        """Função auxiliar assíncrona para interagir com o banco de dados."""
        async with SessionLocal() as db:
            return await userController.user_controller.authenticate(
                db=db, email=email, password=password
            )

    def supports_http_digest_auth(self):
        # Informamos que não suportamos o método Digest, apenas Basic.
        return False