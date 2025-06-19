from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from pydantic import EmailStr
from typing import List
from app.core.config import settings
from pathlib import Path

class EmailService:
    def __init__(self):
        self.conf = ConnectionConfig(
            MAIL_USERNAME=settings.MAIL_USERNAME,
            MAIL_PASSWORD=settings.MAIL_PASSWORD,
            MAIL_FROM=settings.MAIL_FROM,
            MAIL_PORT=settings.MAIL_PORT,
            MAIL_SERVER=settings.MAIL_SERVER,
            MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
            MAIL_STARTTLS=settings.MAIL_STARTTLS,
            MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
            TEMPLATE_FOLDER=Path(__file__).parent.parent / 'templates'
        )

    async def send_email(self, subject: str, recipients: List[EmailStr], template_name: str, template_body: dict):
        """
        Envia um e-mail usando um template.

        Args:
            subject: O assunto do e-mail.
            recipients: Uma lista de e-mails dos destinatários.
            template_name: O nome do arquivo de template (ex: 'welcome.html').
            template_body: Um dicionário com as variáveis para o template.
        """
        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            template_body=template_body,
            subtype="html"
        )

        fm = FastMail(self.conf)
        await fm.send_message(message, template_name=template_name)

# Instância global para ser usada com injeção de dependência
email_service = EmailService()