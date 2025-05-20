from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers.DefaultControllers import get_events, get_users, create_notification, get_task
from app.schemas.DefaultSchemas.notificationSchema import NotificationBase
from app.database import database
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
import logging, os

# Configuração do logging
logging.basicConfig(filename=os.path.join(".", "logs", "app_notification.log"), level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def job_executed_listener(event, scheduler: AsyncIOScheduler):
    if event.exception:
        logger.error(f"O job com ID {event.job_id} falhou ao enviar notificação para o email: {event.retval.split('para ')[1].split(':')[0]}: {event.exception}")

        # Tentativas de re-agendamento (máximo 3 tentativas)
        retries = event.job.kwargs.get('retries', 0)
        if retries < 3:
            new_run_time = datetime.now() + timedelta(minutes=(retries + 1) * 2)  # Aumenta o tempo a cada tentativa
            logger.info(f"Reagendando job {event.job_id} para {new_run_time} (tentativa {retries + 1})")

            event.job.kwargs['retries'] = retries + 1  # Atualiza o contador de tentativas

            scheduler.reschedule_job(event.job_id, trigger=DateTrigger(run_date=new_run_time), kwargs=event.job.kwargs)  # Reagendar o job

        else:
            logger.error(f"Job {event.job_id} excedeu o número máximo de tentativas.")
    else:
        if "Email enviado com sucesso" in event.retval:
            logger.info(f"O job com ID {event.job_id} foi executado com sucesso: {event.retval}")

            # Buscar a tarefa no banco de dados (substitua com sua lógica de acesso ao banco)
            if event.job_id.startswith('notification_after_'):
                _, event_id, task_id, user_id = event.job_id.split('_')[2:]
                async with database.SessionLocal() as db:
                    # Substitua 'get_task_by_id' pela sua função que busca a tarefa no banco
                    task = await get_task(db, task_id)

                    # Verificar se a tarefa ainda está pendente
                    if task and not task.ready:
                        scheduler.remove_job(event.job_id)
                    else:
                        logger.info(f"Job {event.job_id} não removido, pois a tarefa já foi concluída ou não foi encontrada.")
        else:
            logger.error(f"O job com ID {event.job_id} retornou um erro: {event.retval}")


async def convert_to_datetime(date_string):
    formats = ["%d %B, %H:%M", "%Y-%m-%dT%H:%M"]
    for date_format in formats:
        try:
            datetime_object = datetime.strptime(date_string, date_format)
            if "%Y" not in date_format:
                datetime_object = datetime_object.replace(year=datetime.now().year)
            return datetime_object
        except ValueError:
            continue

async def send_notification(body: str, to_email: str, db: AsyncSession, event_id: int, user_id: int, task_id: int, subject: str = "Lembrete"):
    # Configurações do servidor SMTP do Gmail
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = "agenda@imtkec.com.br"  # Substitua pelo seu email
    smtp_password = "Dez@101611"  # Substitua pela sua senha ou app password

    # Cria a mensagem MIME
    message = MIMEMultipart()
    message["From"] = smtp_username
    message["To"] = to_email
    message["Subject"] = subject

    # Adiciona o corpo do email
    message.attach(MIMEText(body, "plain"))

    # Inicia a conexão com o servidor SMTP
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(smtp_username, to_email, message.as_string())

        await create_notification(db, NotificationBase(message=f"Email enviado com sucesso para {to_email}", send=True, user_id=user_id, event_id=event_id, task_id=task_id, view=False))
        return f"Email enviado com sucesso para {to_email}"

    except Exception as e:
        await create_notification(db, NotificationBase(message=f"Erro ao enviar email para {to_email}: {e}", send=False, user_id=user_id, event_id=event_id, task_id=task_id, view=False))
        return f"Erro ao enviar email para {to_email}: {e}"

async def schedule_notifications(db: AsyncSession, scheduler: AsyncIOScheduler):
    result = await get_events(db, 0, 0, "", "Events")
    for event in result:
        for task in event.tasks:
            if task.pendding_notifi:
                event_datetime = await convert_to_datetime(event.date)
                notification_time = event_datetime - timedelta(hours=task.time_to_dispatch)

                users_id = [event.user_id]
                for event_user_rel in event.event_users:
                    users_id.append(event_user_rel.user_id)
                users = await get_users(db, 0, 0, f"id+in+{','.join(map(str, users_id))}", "User")

                for user in users:
                    # Agendar notificação antes do evento
                    scheduler.add_job(
                        send_notification,
                        DateTrigger(run_date=notification_time),
                        args=[f"O Evento {event.name} tem a tarefa pendente: {task.name}, faltam {task.time_to_dispatch} horas!", user.email, db, event.id, user.id, task.id, "Lembrete de Vencimento!!!!"],
                        id=f'notification_before_{event.id}_{task.id}_{user.id}',
                        replace_existing=True,
                        kwargs={'retries': 0}
                    )

                    # Agendar notificação de atraso se aplicável
                    if task.loop and not task.ready:
                        if event_datetime < datetime.now():
                            scheduler.add_job(
                                send_notification,
                                DateTrigger(run_date=datetime.now() + timedelta(seconds=5)),
                                args=[f"O Evento {event.name} tem a tarefa pendente: {task.name}, está atrasada!!!!", user.email, db, event.id, user.id, task.id, "Lembrete de Atraso!!!!"],
                                id=f'notification_after_{event.id}_{task.id}_{user.id}',
                                replace_existing=True,
                                kwargs={'retries': 0}
                            )
                        else:
                            scheduler.add_job(
                                send_notification,
                                DateTrigger(run_date=event_datetime + timedelta(days=1, hours=task.time_to_dispatch)),
                                args=[f"O Evento {event.name} tem a tarefa pendente: {task.name}, está atrasada!!!!", user.email, db, event.id, user.id, task.id, "Lembrete de Atraso!!!!"],
                                id=f'notification_after_{event.id}_{task.id}_{user.id}',
                                replace_existing=True,
                                kwargs={'retries': 0}
                            )

async def check_and_notify(db: AsyncSession, scheduler: AsyncIOScheduler):
    await schedule_notifications(db, scheduler)
