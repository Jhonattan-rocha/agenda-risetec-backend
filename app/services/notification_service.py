# app/services/notification_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.eventsModel import Events
from app.models.calendarModel import Calendar
from app.services.email_services import email_service
from app.services.whatsapp_client_service import whatsapp_client_service
from app.database.database import SessionLocal
from datetime import datetime, timedelta
import asyncio

class NotificationService:
    async def send_reminders(self):
        """
        Verifica todos os eventos que precisam de um lembrete e os envia.
        Esta função é projetada para ser executada periodicamente por um agendador.
        """
        print(f"[{datetime.now()}] Verificando lembretes de eventos...")
        
        # Usamos SessionLocal para criar uma nova sessão de banco de dados para esta tarefa
        async with SessionLocal() as db:
            try:
                # O SQLAlchemy lida com o timezone, mas vamos garantir que estamos comparando de forma consistente
                now = datetime.now(datetime.utcnow().astimezone().tzinfo)
                
                # Seleciona eventos que ainda não aconteceram
                result = await db.execute(
                    select(Events)
                    .options(
                        selectinload(Events.users),
                        selectinload(Events.calendar) # Carrega o calendário relacionado
                    )
                    .filter(Events.date > now)
                )
                upcoming_events = result.scalars().unique().all()

                tasks = []
                for event in upcoming_events:
                    # Adiciona a tarefa de processar cada evento à lista de tarefas concorrentes
                    tasks.append(self.process_event_reminder(event, now))
                
                # Executa todas as tarefas de verificação de lembrete em paralelo
                await asyncio.gather(*tasks)

            except Exception as e:
                print(f"Erro ao processar lembretes: {e}")

    async def process_event_reminder(self, event: Events, now: datetime):
        """
        Processa um único evento para determinar se um lembrete deve ser enviado.
        """
        # Determina as configurações de notificação (prioriza o evento, senão usa o do calendário)
        notify_type = event.notification_type or event.calendar.notification_type
        time_before = event.notification_time_before if event.notification_time_before is not None else event.calendar.notification_time_before
        message_template = event.notification_message or event.calendar.notification_message

        if notify_type == 'none':
            return # Não faz nada se as notificações estiverem desativadas

        reminder_time = event.date - timedelta(minutes=time_before)

        # Verifica se a hora atual está na janela de envio do lembrete (ex: 1 minuto)
        if now >= reminder_time and now < reminder_time + timedelta(minutes=1):
            print(f"Enviando lembrete para o evento: '{event.title}' (ID: {event.id})")

            # Formata a mensagem
            event_time_str = event.startTime or event.date.strftime('%H:%M')
            message = message_template.format(event_title=event.title, event_time=event_time_str)

            for user in event.users:
                # Enviar e-mail
                if user.email and notify_type in ['email', 'both']:
                    try:
                        await email_service.send_email(
                            subject=f"Lembrete: {event.title}",
                            recipients=[user.email],
                            template_name="reminder.html", # Supondo que você tenha este template
                            template_body={"event_title": event.title, "event_date": event_time_str, "user_name": user.name}
                        )
                        print(f" - E-mail de lembrete enviado para {user.email}")
                    except Exception as e:
                        print(f" - Falha ao enviar e-mail para {user.email}: {e}")

                # Enviar WhatsApp
                if user.phone_number and notify_type in ['whatsapp', 'both']:
                    try:
                        await whatsapp_client_service.send_message(
                            phone_number=user.phone_number,
                            message=message
                        )
                        print(f" - WhatsApp de lembrete enviado para {user.phone_number}")
                    except Exception as e:
                        print(f" - Falha ao enviar WhatsApp para {user.phone_number}: {e}")

# Instância global do serviço
notification_service = NotificationService()