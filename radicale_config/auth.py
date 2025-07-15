# radicale_storage/auth.py

import requests

# URL para o endpoint de autenticação que vamos criar na sua API FastAPI
# ATENÇÃO: Se sua API rodar em outra porta, ajuste aqui.
FASTAPI_AUTH_URL = "http://127.0.0.1:9000/radicale_auth/authenticate"

def my_auth(user, password):
    """
    Função que o Radicale chamará para autenticar um usuário.
    """
    if not user or not password:
        return None

    try:
        # Faz uma requisição POST para a sua API FastAPI
        response = requests.post(
            FASTAPI_AUTH_URL,
            json={"username": user, "password": password},
            timeout=5  # Timeout de 5 segundos
        )

        # Se a resposta for 200 OK, a autenticação foi bem-sucedida
        if response.status_code == 200:
            # Retorna o nome de usuário (login)
            # O Radicale usará isso para identificar o usuário
            return user

    except requests.exceptions.RequestException as e:
        # Em caso de falha na comunicação com a API, loga o erro
        # (O Radicale mostrará isso no seu log se o level for DEBUG)
        print(f"Erro ao autenticar com a API FastAPI: {e}")

    # Se qualquer outra coisa acontecer, a autenticação falha
    return None