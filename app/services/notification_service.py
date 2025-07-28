# app/services/notification_service.py

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.eventsModel import Events
from app.models.notificationLogModel import NotificationLog
from app.services.email_services import email_service
from app.services.whatsapp_client_service import whatsapp_client_service
from app.database.database import SessionLocal
from datetime import datetime, timedelta
import asyncio

class NotificationService:
    # O intervalo fixo entre as repetições
    REPEAT_INTERVAL_MINUTES = 5

    async def send_reminders(self):
        """Verifica e envia lembretes de eventos."""
        print(f"[{datetime.now()}] Verificando lembretes de eventos...")
        async with SessionLocal() as db:
            try:
                now = datetime.now(datetime.now().astimezone().tzinfo)
                
                # O select agora funciona com o relacionamento carregado via 'lazy="selectin"'
                result = await db.execute(
                    select(Events).options(selectinload(Events.users), selectinload(Events.calendar)).filter(Events.date > now)
                )
                upcoming_events = result.scalars().unique().all()

                tasks = [asyncio.create_task(self.process_event_reminder(event, now)) for event in upcoming_events]
                await asyncio.gather(*tasks)

            except Exception as e:
                print(f"Erro ao processar lembretes: {e}")

    async def process_event_reminder(self, event: Events, now: datetime):
        """
        Processa um único evento para determinar se um lembrete deve ser enviado,
        considerando as repetições e usando o schema correto.
        """
        async with SessionLocal() as db:
            # --- Lógica de herança correta ---
            # `event.calendar` agora funciona graças ao relacionamento que adicionamos.
            notify_type = event.notification_type or event.calendar.notification_type
            
            # Usa o campo `notification_time_before` (minutos) do evento ou do calendário
            time_before_minutes = event.notification_time_before if event.notification_time_before is not None else event.calendar.notification_time_before

            repeats = event.notification_repeats if event.notification_repeats is not None else event.calendar.notification_repeats
            message_template = event.notification_message or event.calendar.notification_message

            if notify_type == 'none' or time_before_minutes is None or repeats < 1:
                return

            # --- Lógica de cálculo de tempo simplificada ---
            initial_reminder_timedelta = timedelta(minutes=time_before_minutes)
            repeat_interval_delta = timedelta(minutes=self.REPEAT_INTERVAL_MINUTES)
                
            initial_reminder_time = event.date - initial_reminder_timedelta
            # Loop para verificar cada repetição agendada
            for i in range(repeats):
                current_reminder_time = initial_reminder_time + (i * repeat_interval_delta)
                # Verifica se a hora atual corresponde à janela de envio desta repetição
                if now >= current_reminder_time:
                    print(f"Enviando lembrete (Repetição {i+1}/{repeats}) para o evento: '{event.title}'")

                    # Formata a mensagem
                    event_time_str = event.startTime or event.date.strftime('%H:%M')
                    message = message_template.format(event_title=event.title, event_time=event_time_str)
                    
                    # Dispara as notificações e sai do loop
                    await self.send_notification_to_users(db, event, notify_type, message)
                    break

    async def send_notification_to_users(self, db: AsyncSession, event: Events, notify_type: str, message: str):
        """Função auxiliar para enviar notificações."""

        # Esta função não precisa de alterações
        for user in event.users:
            if user.email and notify_type in ['email', 'both']:
                log_entry_email = NotificationLog(
                    user_id=user.id, event_id=event.id, channel='email', content=message
                )
                try:
                    await email_service.send_email(
                        subject=f"Lembrete: {event.title}",
                        recipients=[user.email],
                        template_name="reminder.html",
                        template_body={"event_title": event.title, "event_date": (event.startTime or event.date.strftime('%H:%M')), "user_name": user.name}
                    )
                    log_entry_email.status = 'sent'
                    print(f" - E-mail de lembrete enviado para {user.email}")
                except Exception as e:
                    log_entry_email.status = 'failed'
                    print(f" - Falha ao enviar e-mail para {user.email}: {e}")
                db.add(log_entry_email)

            if user.phone_number and notify_type in ['whatsapp', 'both']:
                log_entry_number = NotificationLog(
                    user_id=user.id, event_id=event.id, channel='whatsapp', content=message
                )
                try:
                    await whatsapp_client_service.send_message(
                        phone_number=user.phone_number,
                        message=message
                    )
                    log_entry_number.status = 'sent'
                    print(f" - WhatsApp de lembrete enviado para {user.phone_number}")
                except Exception as e:
                    log_entry_number.status = 'failed'
                    print(f" - Falha ao enviar WhatsApp para {user.phone_number}: {e}")
                db.add(log_entry_number)
            await db.commit()
            await db.refresh(log_entry_email)
            await db.refresh(log_entry_number)


# Instância global do serviço
notification_service = NotificationService()