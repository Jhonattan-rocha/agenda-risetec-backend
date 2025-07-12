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
        db = SessionLocalSync()
        try:
            user = authenticate_sync(db=db, email=user_name, password=password)
            
            if user:
                # --- CORREÇÃO AQUI ---
                # Armazena o e-mail do usuário (user_name) no ambiente, pois é usado nos caminhos de URL.
                environ["wsgidav.auth.user_name"] = user_name
                environ["wsgidav.auth.display_name"] = user.name
                if user.profile:
                    environ["wsgidav.auth.roles"] = {user.profile.name}
                return True

        except Exception as e:
            print(f"Erro na autenticação DAV: {e}")
            db.rollback()
        finally:
            db.close()

        return False

    def supports_http_digest_auth(self):
        return False