# app/dav/auth_provider.py

from app.database.database import SessionLocalSync
from app.controllers.syncUserController import authenticate_sync

class RiseTecDomainController:
    """
    Controlador de domínio customizado para autenticar usuários
    contra o banco de dados da aplicação, compatível com WsgiDAV v3+.
    """
    def __init__(self, wsgidav_app, config):
        self._wsgidav_app = wsgidav_app
        self._config = config

    def is_share_anonymous(self, share):
        return False
    
    def require_authentication(self, realm, environ):
        return True

    def get_domain_realm(self, path_info, environ):
        return "RiseTec Agenda"

    def basic_auth_user(self, realm, user_name, password, environ):
        """
        Autentica um usuário usando o método Basic Auth de forma SÍNCRONA.
        """
        # Cria uma nova sessão síncrona
        db = SessionLocalSync()
        try:
            # Autentica usando a sessão síncrona
            user = authenticate_sync(db=db, email=user_name, password=password)
            
            if user:
                environ["wsgidav.auth.user_name"] = user.name
                environ["wsgidav.auth.display_name"] = user.name
                if user.profile:
                    environ["wsgidav.auth.roles"] = {user.profile.name}
                return True

        except Exception as e:
            print(f"Erro na autenticação DAV: {e}")
            # Desfaz qualquer transação pendente em caso de erro
            db.rollback()
        finally:
            # Garante que a sessão do banco de dados seja sempre fechada
            db.close()

        # Falha na autenticação se o usuário não for encontrado ou a senha estiver incorreta
        return False

    def supports_http_digest_auth(self):
        return False