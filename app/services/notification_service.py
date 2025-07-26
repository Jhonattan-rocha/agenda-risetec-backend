# app/services/notification_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.eventsModel import Events
from app.services.email_services import email_service
from app.services.whatsapp_client_service import whatsapp_client_service
from datetime import datetime, timedelta

class NotificationService:
    async def send_reminders(self, db: AsyncSession):
        """
        Verifica os eventos que ocorrerão em breve e envia lembretes.
        """
        now = datetime.now()
        reminder_time = now + timedelta(minutes=30) # Lembretes para eventos nos próximos 30 minutos

        result = await db.execute(
            select(Events)
            .where(Events.date >= now)
            .where(Events.date <= reminder_time)
        )
        events_to_remind = result.scalars().all()

        for event in events_to_remind:
            for user in event.users:
                # Enviar e-mail
                await email_service.send_email(
                    subject=f"Lembrete: {event.title}",
                    recipients=[user.email],
                    template_name="reminder.html",
                    template_body={"event_title": event.title, "event_date": event.date}
                )

                # Enviar WhatsApp (se o usuário tiver número de telefone)
                if user.phone_number:
                    await whatsapp_client_service.send_message(
                        phone_number=user.phone_number,
                        message=f"Lembrete do seu evento: {event.title} às {event.date.strftime('%H:%M')}."
                    )

notification_service = NotificationService()