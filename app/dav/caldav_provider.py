# app/dav/caldav_provider.py

from wsgidav.dav_provider import DAVCollection, DAVNonCollection, DAVProvider
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
        # Armazena o objeto do evento em cache para evitar buscas repetidas no DB
        self._event_data = None 

    def _get_event_data(self):
        """Busca o evento no banco de dados (com cache simples)."""
        if self._event_data:
            return self._event_data
        db = SessionLocalSync()
        try:
            # Usando .first() diretamente na query para performance
            event = db.query(syncEventsController.Events).filter(syncEventsController.Events.id == self.event_id).first()
            self._event_data = event
            return event
        finally:
            db.close()

    def get_content(self):
        db = SessionLocalSync()
        try:
            event = self._get_event_data()
            if not event:
                raise DAVError(HTTP_NOT_FOUND)

            cal = ICal()
            cal.add('prodid', '-//RiseTec Agenda//')
            cal.add('version', '2.0')

            ievent = ICalEvent()
            dt_start = event.date
            
            # Garante que a data tenha timezone (essencial para CalDAV)
            if not isinstance(dt_start, datetime): # Se for um objeto date
                 dt_start = datetime.combine(dt_start, datetime.min.time(), tzinfo=pytz.utc)
            elif dt_start.tzinfo is None:
                dt_start = pytz.utc.localize(dt_start)

            ievent.add('summary', event.title)
            ievent.add('description', event.description or '') # Garante que não seja None
            ievent.add('dtstart', dt_start)
            # UID é obrigatório e deve ser único
            ievent['uid'] = f"{event.id}@risetec.agenda" 
            ievent['dtstamp'] = datetime.now(pytz.utc)
            
            cal.add_component(ievent)
            
            return BytesIO(cal.to_ical())
        finally:
            db.close()

    def delete(self):
        db = SessionLocalSync()
        try:
            # O controller já lida com a busca e deleção
            deleted_event = syncEventsController.remove_sync(db=db, id=self.event_id)
            if not deleted_event:
                raise DAVError(HTTP_NOT_FOUND)
            # HTTP 204 No Content é a resposta correta para um DELETE bem-sucedido
            raise DAVError(HTTP_NO_CONTENT)
        finally:
            db.close()
    
    def begin_write(self, content_type):
        if not content_type or not content_type.lower().startswith("text/calendar"):
            raise DAVError(HTTP_FORBIDDEN, "Unsupported content type.")
        self._put_stream = BytesIO()
        return self._put_stream

    def end_write(self, with_error):
        """Invocado após o conteúdo do PUT ter sido completamente escrito."""
        if with_error:
            return

        ics_data = self._put_stream.getvalue()
        db = SessionLocalSync()
        try:
            cal = ICal.from_ical(ics_data)

            component = next(cal.walk(('VEVENT', 'VTODO')), None)
            if not component:
                raise DAVError(400, "O objeto iCalendar deve conter um VEVENT ou VTODO.")
            
            is_task = component.name == 'VTODO'

            parts = [p for p in self.path.strip("/").split("/") if p]
            user_email, calendar_name = parts[0], parts[1]
            
            user = syncUserController.get_user_by_email_sync(db, email=user_email)
            if not user: raise DAVError(HTTP_FORBIDDEN)
            
            calendar = syncCalendarController.get_by_owner_and_name_sync(db, owner_id=user.id, name=calendar_name)
            if not calendar: raise DAVError(HTTP_NOT_FOUND)

            item_data = {
                "title": str(component.get('summary', 'Sem Título')),
                "description": str(component.get('description', '')),
                "created_by": user.id,
                "user_ids": [user.id] 
            }

            if is_task:
                due_date = component.get('due')
                item_data['date'] = due_date.dt if due_date else datetime.now(pytz.utc)
                item_data['status'] = str(component.get('status', 'needs-action')).lower()
                item_data['isAllDay'] = True
            else: # É um evento (VEVENT)
                dtstart = component.get('dtstart').dt
                item_data['date'] = dtstart
                item_data['status'] = 'confirmed'
                # Um evento é "all-day" se dtstart for um objeto date, não datetime
                item_data['isAllDay'] = not isinstance(dtstart, datetime)

            # Usa o controller para criar ou atualizar o item no banco
            syncEventsController.create_or_update_sync(db, event_data=item_data, event_id=self.event_id, calendar_id=calendar.id)
            
        except Exception as e:
            # Em produção, seria bom logar o erro `e`
            raise DAVError(500, "Falha ao processar dados do calendário.")
        finally:
            db.close()

    def get_content_type(self):
        return "text/calendar; charset=utf-8"

    def get_display_name(self):
        return f"{self.event_id}.ics"
        
    def get_etag(self):
        event = self._get_event_data()
        if not event or not hasattr(event, 'date') or not event.date:
            return None
        # ETag deve ser uma string entre aspas
        return f'"{event.id}-{int(event.date.timestamp())}"'

class CalendarCollection(DAVCollection):
    """Representa uma coleção de calendário (um único calendário)."""
    def __init__(self, path, environ, user_id, calendar_id, calendar_name):
        super().__init__(path, environ)
        self.user_id = user_id
        self.calendar_id = calendar_id
        self.calendar_name = calendar_name

    def get_member_names(self):
        db = SessionLocalSync()
        try:
            # Apenas busca os IDs para otimizar
            event_ids = db.query(syncEventsController.Events.id).filter(syncEventsController.Events.calendar_id == self.calendar_id).all()
            return [f"{id_[0]}.ics" for id_ in event_ids]
        finally:
            db.close()

    def get_member(self, name):
        try:
            # Extrai o ID do nome do arquivo .ics
            event_id = int(name.split(".")[0])
            return EventResource(f"{self.path.rstrip('/')}/{name}", self.environ, event_id)
        except (ValueError, IndexError):
            return None

    def get_display_name(self):
        return self.calendar_name

    def get_property(self, name, raise_error=True):
        """Retorna o valor de uma propriedade (para PROPFIND)."""
        if name == "{DAV:}resourcetype":
            # Anuncia que este recurso é uma coleção E um calendário CalDAV
            return '<D:resourcetype><D:collection/><C:calendar xmlns:C="urn:ietf:params:xml:ns:caldav"/></D:resourcetype>'
        if name == "{urn:ietf:params:xml:ns:caldav}supported-calendar-component-set":
            # Anuncia que o calendário suporta Eventos (VEVENT) e Tarefas (VTODO)
            return '<C:supported-calendar-component-set xmlns:C="urn:ietf:params:xml:ns:caldav"><C:comp name="VEVENT"/><C:comp name="VTODO"/></C:supported-calendar-component-set>'
        
        return super().get_property(name, raise_error)

    # --- NOVO: Implementação dos relatórios CalDAV ---
    def report_urn_ietf_params_xml_ns_caldav_calendar_query(self, request, response, depth):
        """Executa o relatório calendar-query."""
        response.write('<?xml version="1.0" encoding="utf-8" ?>\n')
        response.write('<D:multistatus xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">\n')

        db = SessionLocalSync()
        try:
            # Em uma implementação real, você analisaria o XML de `request` para aplicar filtros.
            # Esta versão simplificada retorna todos os eventos do calendário.
            calendar = syncCalendarController.get_with_events_sync(db, id=self.calendar_id)
            if not calendar or calendar.owner_id != self.user_id:
                raise DAVError(HTTP_FORBIDDEN)
            
            for event in calendar.events:
                event_path = f"{self.path.rstrip('/')}/{event.id}.ics"
                event_resource = EventResource(event_path, self.environ, event.id)
                etag = event_resource.get_etag()

                response.write(f'<D:response>\n')
                response.write(f'  <D:href>{event_path}</D:href>\n')
                response.write(f'  <D:propstat>\n')
                response.write(f'    <D:prop>\n')
                if etag:
                    response.write(f'      <D:getetag>{etag}</D:getetag>\n')
                response.write('      <C:calendar-data>')
                # Escapa caracteres especiais de XML se necessário, mas icalendar deve lidar com isso
                response.write(event_resource.get_content().read().decode('utf-8'))
                response.write('</C:calendar-data>\n')
                response.write(f'    </D:prop>\n')
                response.write(f'    <D:status>HTTP/1.1 200 OK</D:status>\n')
                response.write(f'  </D:propstat>\n')
                response.write(f'</D:response>\n')
        finally:
            db.close()

        response.write('</D:multistatus>\n')

    def report_urn_ietf_params_xml_ns_caldav_calendar_multiget(self, request, response, depth):
        """Executa o relatório calendar-multiget."""
        # A implementação real extrairia os hrefs do request. Esta é uma simplificação.
        # Reutilizamos a lógica do query report para esta implementação básica.
        self.report_urn_ietf_params_xml_ns_caldav_calendar_query(request, response, depth)

class UserCalendarsCollection(DAVCollection):
    """Representa a coleção de todos os calendários de um usuário (`/dav/user@email.com/`)."""
    def __init__(self, path, environ, user_email: str):
        super().__init__(path, environ)
        self.user_email = user_email
        self._user = None # Cache para o objeto do usuário

    def _get_user(self, db):
        if self._user:
            return self._user
        self._user = syncUserController.get_user_by_email_sync(db, email=self.user_email)
        return self._user

    def get_member_names(self):
        db = SessionLocalSync()
        try:
            user = self._get_user(db)
            if not user: return []
            calendars = syncCalendarController.get_all_by_owner_sync(db, owner_id=user.id)
            return [cal.name for cal in calendars]
        finally:
            db.close()

    def get_member(self, name):
        db = SessionLocalSync()
        try:
            user = self._get_user(db)
            if not user: return None
            calendar = syncCalendarController.get_by_owner_and_name_sync(db, owner_id=user.id, name=name)
            if not calendar: return None
            return CalendarCollection(f"{self.path.rstrip('/')}/{name}", self.environ, user.id, calendar.id, calendar.name)
        finally:
            db.close()

    def get_display_name(self):
        return self.user_email

    def create_collection(self, name):
        """Implementação do MKCALENDAR (criar novo calendário)."""
        db = SessionLocalSync()
        try:
            user = self._get_user(db)
            if not user:
                raise DAVError(HTTP_FORBIDDEN)

            new_calendar_schema = CalendarBase(
                name=name, color="#0000FF", visible=True, is_private=True, owner_id=user.id
            )
            syncCalendarController.create_sync(db, obj_in=new_calendar_schema)
            raise DAVError(HTTP_CREATED)
        except Exception as e:
            raise DAVError(500, f"Erro ao criar calendário: {e}")
        finally:
            db.close()
    
    def get_property(self, name, raise_error=True):
        """Manipula as propriedades para a coleção principal do usuário."""
        # O caminho para esta coleção é o próprio principal e o "home-set"
        href_value = f"<D:href xmlns:D='DAV:'>{self.path.rstrip('/')}/</D:href>"

        if name in ("{DAV:}current-user-principal", 
                    "{urn:ietf:params:xml:ns:caldav}calendar-home-set", 
                    "{urn:ietf:params:xml:ns:carddav}addressbook-home-set", # Para compatibilidade
                    "{DAV:}owner"):
            return href_value
            
        return super().get_property(name, raise_error)

class RootCollection(DAVCollection):
    """Representa a coleção raiz (`/dav/` ou `/`)."""
    def __init__(self, path, environ):
        super().__init__(path, environ)

    def get_member_names(self):
        # Por segurança, não listamos todos os usuários na raiz.
        return []

    def get_member(self, name):
        # `name` aqui seria o e-mail do usuário, que forma o próximo nível do path
        return UserCalendarsCollection(f"/{name}", self.environ, name)

    # --- CORREÇÃO PRINCIPAL ---
    def get_property(self, name, raise_error=True):
        """Responde à descoberta do 'usuário principal' (current-user-principal)."""
        if name == "{DAV:}current-user-principal":
            user_email = self.environ.get("wsgidav.auth.user_name")
            if user_email:
                mount_path = self.environ.get("wsgidav.mount_path", "")
                principal_path = f"{mount_path.rstrip('/')}/{user_email}/"
                return f"<D:href xmlns:D='DAV:'>{principal_path}</D:href>"
        
        # Para outras propriedades, usa a implementação padrão.
        # Isso retornará 404 para `calendar-home-set` na raiz, o que é correto.
        # O cliente deve seguir o `current-user-principal` para encontrar o `home-set`.
        return super().get_property(name, raise_error)

class CaldavProvider(DAVProvider):
    """Provedor DAV que mapeia URLs para os recursos de calendário."""
    def __init__(self):
        super().__init__()

    def get_resource_inst(self, path, environ):
        # `path` é o caminho relativo ao mount point do DAV
        parts = [p for p in path.strip("/").split("/") if p]
        
        if not parts:
            # Caminho é `/` (a raiz do DAV) -> RootCollection
            return RootCollection(path, environ)

        # Caminho é `/{user_email}` -> UserCalendarsCollection
        user_email = parts[0]
        user_collection = UserCalendarsCollection(f"/{user_email}", environ, user_email)
        if len(parts) == 1:
            return user_collection
        
        # Caminho é `/{user_email}/{calendar_name}` -> CalendarCollection
        calendar_name = parts[1]
        calendar_collection = user_collection.get_member(calendar_name)
        if len(parts) == 2:
            return calendar_collection
        
        # Caminho é `/{user_email}/{calendar_name}/{event.ics}` -> EventResource
        event_name = parts[2]
        if len(parts) == 3 and calendar_collection:
            return calendar_collection.get_member(event_name)

        # Se não encontrar um recurso correspondente
        return None