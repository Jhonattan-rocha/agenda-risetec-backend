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
        if with_error:
            return

        ics_data = self._put_stream.getvalue()
        db = SessionLocalSync()
        try:
            cal = ICal.from_ical(ics_data)
            ievent = next(cal.walk('VEVENT'))
            
            # Extrai o ID do calendário e do usuário do path
            parts = [p for p in self.path.strip("/").split("/") if p]
            user_email = parts[0]
            calendar_name = parts[1]
            
            user = syncUserController.get_user_by_email_sync(db, email=user_email)
            if not user: raise DAVError(HTTP_FORBIDDEN)
            
            calendar = syncCalendarController.get_by_owner_and_name_sync(db, owner_id=user.id, name=calendar_name)
            if not calendar: raise DAVError(HTTP_NOT_FOUND)

            event_data = {
                "title": str(ievent.get('summary', '')),
                "description": str(ievent.get('description', '')),
                "date": ievent.get('dtstart').dt,
                "isAllDay": False,
                "created_by": user.id,
                "user_ids": [user.id]
            }
            
            # Usa o ID do evento da URL para criar ou atualizar
            syncEventsController.create_or_update_sync(db, event_data=event_data, event_id=self.event_id, calendar_id=calendar.id)
        except Exception as e:
            print(f"Erro ao processar PUT (CalDAV): {e}")
            raise DAVError(500, "Failed to process calendar data.")
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
    def __init__(self, path, environ, user_email):
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