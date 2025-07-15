# radicale_config/auth.py

import requests
from radicale.auth import BaseAuth

FASTAPI_AUTH_URL = "http://127.0.0.1:9000/radicale_auth/authenticate"

class Auth(BaseAuth):
    def __init__(self, configuration, *args, **kwargs):
        self.configuration = configuration

    def login(self, login, password):
        if not login or not password:
            print("[Radicale Auth] Login ou senha vazios.")
            return None

        try:
            response = requests.post(
                FASTAPI_AUTH_URL,
                json={"username": login, "password": password},
                timeout=5
            )

            print(f"[Radicale Auth] Resposta da API: {response.status_code} - {response.text}")

            if response.status_code == 200:
                return login, password

        except requests.exceptions.RequestException as e:
            print(f"[Radicale Auth] Erro na autenticação via API: {e}")

        return None

    def get_external_login(self, environ):
        return environ.get("REMOTE_USER", "")
