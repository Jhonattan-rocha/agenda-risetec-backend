# agenda-risetec-backend/app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import EmailStr

class Settings(BaseSettings):
    # Configurações do Banco de Dados
    DATABASE_URL: str

    # Configurações de Autenticação
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Configurações de Email
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    class Config:
        env_file = ".env"

settings = Settings()