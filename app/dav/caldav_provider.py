# app/dav/caldav_provider.py

from wsgidav.dav_provider import DAVCollection, DAVNonCollection
from wsgidav.dav_error import DAVError, HTTP_NOT_FOUND, HTTP_FORBIDDEN, HTTP_NO_CONTENT, HTTP_CREATED
from icalendar import Calendar as ICal, Event as ICalEvent
from datetime import datetime
import pytz
from io import BytesIO

# Importe seus controllers e o SessionLocal SÍNCRONOS
from app.database.database import SessionLocalSync
from app.controllers import syncUserController, syncCalendarController, syncEventsController
from app.schemas.calendarSchema import CalendarBase

# --- Classes de Recurso DAV Síncronas ---

class EventResource(DAVNonCollection):
    """Representa um único evento (.ics)."""
    def __init__(self, path, environ, event_id):
        super().__init__(path, environ)
        self.event_id = event_id

    def get_content(self):
        db = SessionLocalSync()
        try:
            event = syncEventsController.get_sync(db, self.event_id)
            if not event:
                raise DAVError(HTTP_NOT_FOUND)

            cal = ICal()
            cal.add('prodid', '-//RiseTec Agenda//')
            cal.add('version', '2.0')

            ievent = ICalEvent()
            dt_start = event.date
            if dt_start.tzinfo is None:
                dt_start = pytz.utc.localize(dt_start)

            ievent.add('summary', event.title)
            ievent.add('description', event.description)
            ievent.add('dtstart', dt_start)
            ievent['uid'] = f"{event.id}@risetec.agenda"
            ievent['dtstamp'] = pytz.utc.localize(datetime.utcnow())
            cal.add_component(ievent)
            
            return BytesIO(cal.to_ical())
        finally:
            db.close()

    def delete(self):
        db = SessionLocalSync()
        try:
            deleted_event = syncEventsController.remove_sync(db=db, id=self.event_id)
            if not deleted_event:
                raise DAVError(HTTP_NOT_FOUND)
            raise DAVError(HTTP_NO_CONTENT)
        finally:
            db.close()
    
    def begin_write(self, content_type):
        if not content_type.lower().startswith("text/calendar"):
            raise DAVError(HTTP_FORBIDDEN, "Unsupported content type.")
        self._put_stream = BytesIO()
        return self._put_stream

    def end_write(self, with_error):
        """
        Invocado após o conteúdo do PUT ter sido completamente escrito.
        Agora lida com VEVENT (Eventos) e VTODO (Tarefas).
        """
        if with_error:
            return

        ics_data = self._put_stream.getvalue()
        db = SessionLocalSync()
        try:
            cal = ICal.from_ical(ics_data)

            # --- LÓGICA ATUALIZADA PARA ENCONTRAR O COMPONENTE CERTO ---
            component = None
            is_task = False
            try:
                # Primeiro, tenta encontrar um evento
                component = next(cal.walk('VEVENT'))
            except StopIteration:
                try:
                    # Se não for um evento, tenta encontrar uma tarefa
                    component = next(cal.walk('VTODO'))
                    is_task = True
                except StopIteration:
                    # Se não for nenhum dos dois, o arquivo é inválido
                    raise DAVError(400, "O objeto iCalendar deve conter um VEVENT ou VTODO.")
            # --- FIM DA LÓGICA ATUALIZADA ---

            # Extrai o ID do calendário e do usuário do path
            parts = [p for p in self.path.strip("/").split("/") if p]
            user_email = parts[0]
            calendar_name = parts[1]
            
            user = syncUserController.get_user_by_email_sync(db, email=user_email)
            if not user: raise DAVError(HTTP_FORBIDDEN)
            
            calendar = syncCalendarController.get_by_owner_and_name_sync(db, owner_id=user.id, name=calendar_name)
            if not calendar: raise DAVError(HTTP_NOT_FOUND)

            # --- LÓGICA ATUALIZADA PARA EXTRAIR DADOS ---
            item_data = {
                "title": str(component.get('summary', '')),
                "description": str(component.get('description', '')),
                "created_by": user.id,
                "user_ids": [user.id]  # Define o criador como participante padrão
            }

            if is_task:
                # É uma TAREFA (VTODO)
                due_date = component.get('due')
                # A data de vencimento de uma tarefa vai para o campo 'date' do nosso modelo
                item_data['date'] = due_date.dt if due_date else datetime.now(pytz.utc)
                # Mapeia o status da tarefa (ex: 'needs-action', 'completed')
                item_data['status'] = str(component.get('status', 'needs-action')).lower()
                item_data['isAllDay'] = True  # Tarefas são geralmente tratadas como "dia inteiro"
            else:
                # É um EVENTO (VEVENT)
                item_data['date'] = component.get('dtstart').dt
                item_data['status'] = 'confirmed' # Status padrão para eventos
                item_data['isAllDay'] = not isinstance(component.get('dtstart').dt, datetime)
            # --- FIM DA LÓGICA ATUALIZADA ---

            # Usa o ID da URL para criar ou atualizar o item no banco
            syncEventsController.create_or_update_sync(db, event_data=item_data, event_id=self.event_id, calendar_id=calendar.id)
            
        except Exception as e:
            print(f"Erro ao processar PUT (CalDAV): {e}")
            raise DAVError(500, "Falha ao processar dados do calendário.")
        finally:
            db.close()


    def get_content_type(self):
        return "text/calendar"

    def get_display_name(self):
        return f"{self.event_id}.ics"
        
    def get_etag(self):
        db = SessionLocalSync()
        try:
            event = syncEventsController.get_sync(db, self.event_id)
            if not event:
                return None
            return f'"{event.id}-{int(event.date.timestamp())}"'
        finally:
            db.close()

class CalendarCollection(DAVCollection):
    """Representa uma coleção de calendário."""
    def __init__(self, path, environ, user_id, calendar_id, calendar_name):
        super().__init__(path, environ)
        self.user_id = user_id
        self.calendar_id = calendar_id
        self.calendar_name = calendar_name

    def get_member_names(self):
        db = SessionLocalSync()
        try:
            calendar = syncCalendarController.get_with_events_sync(db, id=self.calendar_id)
            if not calendar or calendar.owner_id != self.user_id:
                return []
            return [f"{event.id}.ics" for event in calendar.events]
        finally:
            db.close()

    def get_member(self, name):
        try:
            event_id = int(name.replace(".ics", ""))
            return EventResource(f"{self.path}/{name}", self.environ, event_id)
        except (ValueError, IndexError):
            return None

    def get_display_name(self):
        return self.calendar_name

    def get_property(self, name, raise_error=True):
        """Retorna o valor de uma propriedade (para PROPFIND)."""
        if name == "{DAV:}resourcetype":
            return """<resourcetype><collection/><C:calendar xmlns:C="urn:ietf:params:xml:ns:caldav"/></resourcetype>"""
        elif name == "{urn:ietf:params:xml:ns:caldav}supported-calendar-component-set":
            return """<C:supported-calendar-component-set xmlns:C="urn:ietf:params:xml:ns:caldav">
                          <C:comp name="VEVENT"/>
                          <C:comp name="VTODO"/>
                      </C:supported-calendar-component-set>"""
        return super().get_property(name, raise_error)

class UserCalendarsCollection(DAVCollection):
    """Representa a coleção de todos os calendários de um usuário."""
    def __init__(self, path, environ, user_email: str):
        super().__init__(path, environ)
        self.user_email = user_email

    def get_member_names(self):
        db = SessionLocalSync()
        try:
            user = syncUserController.get_user_by_email_sync(db, email=self.user_email)
            if not user:
                return []
            calendars = syncCalendarController.get_all_by_owner_sync(db, owner_id=user.id)
            return [cal.name for cal in calendars]
        finally:
            db.close()

    def get_member(self, name):
        db = SessionLocalSync()
        try:
            user = syncUserController.get_user_by_email_sync(db, email=self.user_email)
            if not user:
                return None
            calendar = syncCalendarController.get_by_owner_and_name_sync(db, owner_id=user.id, name=name)
            if not calendar:
                return None
            return CalendarCollection(f"{self.path}/{name}", self.environ, user.id, calendar.id, calendar.name)
        finally:
            db.close()

    def get_display_name(self):
        return self.user_email

    def create_collection(self, name):
        # Implementação do MKCALENDAR (criar novo calendário)
        db = SessionLocalSync()
        try:
            user = syncUserController.get_user_by_email_sync(db, email=self.user_email)
            if not user:
                raise DAVError(HTTP_FORBIDDEN)

            new_calendar_schema = CalendarBase(
                name=name,
                description=f"Calendário {name}",
                color="#0000FF",
                visible=True,
                is_private=True,
                owner_id=user.id
            )
            syncCalendarController.create_sync(db, obj_in=new_calendar_schema)
            raise DAVError(HTTP_CREATED)
        except Exception as e:
            print(f"Erro ao criar calendário (CalDAV): {e}")
            raise DAVError(500)
        finally:
            db.close()
    
    # --- MÉTODO CORRIGIDO ---
    def get_property(self, name, raise_error=True):
        """Manipula as propriedades para a coleção principal do usuário."""
        # O caminho para a coleção principal do usuário.
        # Ex: '/dav/seu-email@dominio.com/'
        # wsgidav.mount_path é o prefixo onde o app DAV está montado (se houver)
        mount_path = self.environ.get("wsgidav.mount_path", "")
        principal_path = f"{mount_path}/{self.user_email}/"

        # Constrói o valor da propriedade como uma string XML
        href_value = f"<D:href xmlns:D='DAV:'>{principal_path}</D:href>"

        if name == "{DAV:}current-user-principal":
            return href_value

        if name == "{urn:ietf:params:xml:ns:caldav}calendar-home-set":
            return href_value

        if name == "{urn:ietf:params:xml:ns:carddav}addressbook-home-set":
            # Responde também para CardDAV para evitar erros de descoberta
            return href_value
            
        return super().get_property(name, raise_error)

class RootCollection(DAVCollection):
    """Representa a coleção raiz '/'."""
    def __init__(self, path, environ):
        super().__init__(path, environ)

    def get_member_names(self):
        # Em uma implementação real, você pode querer listar todos os usuários aqui
        # Por questões de segurança, é melhor não expor todos os e-mails na raiz.
        return []

    def get_member(self, name):
        # 'name' aqui seria o e-mail do usuário
        return UserCalendarsCollection(f"/{name}", self.environ, name)

    # --- MÉTODO CORRIGIDO ---
    def get_property(self, name, raise_error=True):
        """
        Responde à descoberta do 'usuário principal' e dos 'home-sets' na raiz.
        Esta implementação foi corrigida para responder adequadamente ao cliente CalDAV
        retornando o valor como uma string XML.
        """
        # Tenta obter o nome de usuário do ambiente, que é preenchido pelo auth_provider
        user_email = self.environ.get("wsgidav.auth.user_name")
        if not user_email:
            # Se o usuário não estiver autenticado, não podemos fornecer os caminhos
            # e delegamos para a implementação da classe pai.
            return super().get_property(name, raise_error)

        # O caminho para a coleção principal do usuário.
        # Ex: '/dav/seu-email@dominio.com/'
        # wsgidav.mount_path é o prefixo onde o app DAV está montado (se houver)
        mount_path = self.environ.get("wsgidav.mount_path", "")
        principal_path = f"{mount_path}/{user_email}/"

        # Constrói o valor da propriedade como uma string XML
        href_value = f"<D:href xmlns:D='DAV:'>{principal_path}</D:href>"

        if name in (
            "{DAV:}current-user-principal",
            "{urn:ietf:params:xml:ns:caldav}calendar-home-set",
            "{urn:ietf:params:xml:ns:carddav}addressbook-home-set",
        ):
            return href_value

        # Se a propriedade não for uma das acima, delega para a classe pai.
        return super().get_property(name, raise_error)

from wsgidav.dav_provider import DAVProvider

class CaldavProvider(DAVProvider):
    """Provedor DAV que mapeia URLs para os recursos de calendário."""
    def __init__(self):
        super().__init__()

    def get_resource_inst(self, path, environ):
        parts = [p for p in path.strip("/").split("/") if p]
        
        if not parts:
            return RootCollection(path, environ)

        user_email = parts[0]
        root_collection = RootCollection(path, environ)
        user_collection = root_collection.get_member(user_email)
        
        if len(parts) == 1:
            return user_collection
        
        calendar_name = parts[1]
        calendar_collection = user_collection.get_member(calendar_name)
        
        if len(parts) == 2:
            return calendar_collection
        
        event_name = parts[2]
        if len(parts) == 3 and calendar_collection:
            return calendar_collection.get_member(event_name)

        return None