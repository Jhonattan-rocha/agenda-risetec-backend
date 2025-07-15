# radicale_config/auth.py

import requests

FASTAPI_AUTH_URL = "http://127.0.0.1:9000/radicale_auth/authenticate"

class Auth:
    def __init__(self, configuration, *args, **kwargs):
        self.configuration = configuration

    def login(self, login, password):
        if not login or not password:
            return None

        try:
            response = requests.post(
                FASTAPI_AUTH_URL,
                json={"username": login, "password": password},
                timeout=5
            )

            if response.status_code == 200:
                return login

        except requests.exceptions.RequestException as e:
            print(f"[Radicale Auth] Erro na autenticação via API: {e}")

        return None
