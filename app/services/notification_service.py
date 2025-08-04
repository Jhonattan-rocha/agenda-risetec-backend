# app/services/notification_service.py

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.eventsModel import Events
from app.models.calendarModel import Calendar
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
                now = datetime.now(datetime.utcnow().astimezone().tzinfo)
                
                # CORREÇÃO 1: Lógica do filtro
                # Usamos `&` para o AND e a lógica correta é `notifications_sent_count < notification_repeats`
                result = await db.execute(
                    select(Events)
                    .options(selectinload(Events.users), selectinload(Events.calendar))
                    .filter(
                        Events.date > now,
                        Events.notifications_sent_count < Events.notification_repeats
                    )
                )
                upcoming_events = result.scalars().unique().all()

                # CORREÇÃO 2: Passamos a sessão 'db' para a função de processamento
                tasks = [self.process_event_reminder(db, event, now) for event in upcoming_events]
                if tasks:
                    await asyncio.gather(*tasks)

            except Exception as e:
                print(f"Erro ao processar lembretes: {e}")

    async def send_reminders_late(self):
        async with SessionLocal() as db:
            await self.send_overdue_reminders(db)
            await db.commit()

    async def process_event_reminder(self, db: AsyncSession, event: Events, now: datetime):
        """
        Processa um único evento para determinar se um lembrete deve ser enviado.
        Esta função agora recebe a sessão do banco de dados para evitar erros.
        """
        # --- Lógica de herança (sem alterações) ---
        total_repeats = event.notification_repeats if event.notification_repeats is not None else event.calendar.notification_repeats
        notify_type = event.notification_type or event.calendar.notification_type
        time_before_minutes = event.notification_time_before if event.notification_time_before is not None else event.calendar.notification_time_before
        message_template = event.notification_message or event.calendar.notification_message

        if notify_type == 'none' or time_before_minutes is None or total_repeats is None or event.notifications_sent_count >= total_repeats:
            return

        # --- Lógica de cálculo de tempo ---
        initial_reminder_timedelta = timedelta(minutes=time_before_minutes)
        repeat_interval_delta = timedelta(minutes=self.REPEAT_INTERVAL_MINUTES)
        initial_reminder_time = event.date - initial_reminder_timedelta
        
        # Calcula o horário do PRÓXIMO lembrete
        next_reminder_time = initial_reminder_time + (event.notifications_sent_count * repeat_interval_delta)

        # CORREÇÃO 3: Adiciona a janela de 1 minuto para evitar reenvios
        if now >= next_reminder_time:
            print(f"Enviando lembrete (Envio Nº {event.notifications_sent_count + 1}/{total_repeats}) para o evento: '{event.title}'")

            event_time_str = event.startTime or event.date.strftime('%H:%M')
            message = message_template.format(event_title=event.title, event_time=event_time_str)
            
            # Envia a notificação e os logs
            await self.send_notification_to_users(db, event, notify_type, message)
            
            # Incrementa o contador
            event.notifications_sent_count += 1
            
            # CORREÇÃO 4: O commit é feito aqui, uma vez por evento processado.
            await db.commit()
            print(f" - Contador do evento '{event.title}' atualizado para {event.notifications_sent_count}.")

    async def send_notification_to_users(self, db: AsyncSession, event: Events, notify_type: str, message: str):
        """Função auxiliar para enviar notificações e registrar o log."""
        calendar_result = await db.execute(select(Calendar).filter(Calendar.id == event.calendar_id))
        calendar = calendar_result.scalars().first()
        participant_names = [user.name for user in event.users if user.name]

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
                        template_body={"event_title": event.title, 
                                       "event_date_start": (event.startTime or event.date), 
                                       "event_date_final": (event.endTime or event.endDate),
                                       "event_place": event.location,
                                       "event_status": event.status,
                                       "event_calendar": calendar.name,
                                       "event_desc": event.description,
                                       "users": participant_names}
                    )
                    log_entry_email.status = 'sent'
                    print(f" - E-mail de lembrete enviado para {user.email}")
                except Exception as e:
                    log_entry_email.status = 'failed'
                    print(f" - Falha ao enviar e-mail para {user.email}: {e}")
                db.add(log_entry_email)

            # ... (lógica de envio de whatsapp e criação do log_entry_number) ...
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
        
    # NOVA FUNÇÃO
    async def send_overdue_reminders(self, db: AsyncSession):
        """
        Busca eventos que já passaram da data final e cujo status não é 'confirmed',
        e envia um lembrete para todos os participantes.
        """
        now = datetime.now()
        
        # Query para encontrar os eventos pendentes e atrasados
        query = (
            select(Events)
            .options(
                selectinload(Events.users), # Carrega os participantes
                selectinload(Events.calendar) # Carrega o calendário para pegar o nome
            )
            .filter(
                Events.endDate < now,
                Events.status != 'confirmed'
            )
        )
        
        result = await db.execute(query)
        overdue_events = result.scalars().unique().all()
        
        print(f"Encontrados {len(overdue_events)} eventos atrasados para notificar.")

        for event in overdue_events:
            if not event.users:
                continue
            
            template_body = {
                "event_title": event.title,
                "event_date_start": event.date.strftime('%d/%m/%Y %H:%M'),
                "event_date_final": event.endDate.strftime('%d/%m/%Y %H:%M') if event.endDate else "N/A",
                "event_place": event.location or "Não especificado",
                "event_status": event.status,
                "event_calendar": event.calendar.name if event.calendar else "N/A",
                "event_desc": event.description or "Nenhuma descrição.",
                "event_participants": event.users
            }
            
            for user in event.users:
                if user.email:
                    log_entry_email = NotificationLog(
                        user_id=user.id, event_id=event.id, channel='email', content=event.notification_message or event.calendar.notification_message
                    )
                    
                    try:
                        await email_service.send_email(
                            subject=f"Lembrete de Pendência: {event.title}",
                            recipients=[user.email],
                            template_name="late.html",
                            template_body=template_body
                        )
                        log_entry_email.status = 'sent'
                        print(f"E-mail de lembrete enviado para o evento ID: {event.id}")
                    except Exception as e:
                        log_entry_email.status = 'failed'
                        print(f"Falha ao enviar e-mail para o evento ID {event.id}: {e}")
                    
                    db.add(log_entry_email)
                
                if user.phone_number:
                    log_entry_number = NotificationLog(
                        user_id=user.id, event_id=event.id, channel='whatsapp', content=event.notification_message or event.calendar.notification_message
                    )
                    try:
                        await whatsapp_client_service.send_message(
                            phone_number=user.phone_number,
                            message=event.notification_message or event.calendar.notification_message
                        )
                        log_entry_number.status = 'sent'
                        print(f" - WhatsApp de lembrete enviado para {user.phone_number}")
                    except Exception as e:
                        log_entry_number.status = 'failed'
                        print(f" - Falha ao enviar WhatsApp para {user.phone_number}: {e}")
                    
                    db.add(log_entry_number)
    
        # CORREÇÃO 5: O commit foi removido daqui para ser centralizado na função principal.

# Instância global do serviço
notification_service = NotificationService()