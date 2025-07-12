# app/dav/caldav_provider.py

import asyncio
from wsgidav.dav_provider import DAVCollection, DAVNonCollection
from wsgidav.dav_error import DAVError, HTTP_NOT_FOUND, HTTP_FORBIDDEN
from icalendar import Calendar as ICal, Event as ICalEvent
from datetime import datetime
import pytz # Necessário para timezones

# Importe seus controllers e o SessionLocal
from app.database.database import SessionLocal
from app.controllers import userController, calendarController, eventsController
from app.models.userModel import User
from app.models.calendarModel import Calendar
from app.models.eventsModel import Events

# --- Funções Utilitárias ---

async def get_user_by_email(email: str) -> User | None:
    """Busca um usuário pelo email."""
    async with SessionLocal() as db:
        # Assumindo que seu user_controller tem um método para buscar por email
        # Se não, você precisará criá-lo.
        # Por enquanto, vamos usar o get_multi_filtered
        users = await userController.user_controller.get_multi_filtered(db, filters=f"email+eq+{email}")
        return users[0] if users else None

async def get_calendar_by_owner_and_id(user_id: int, calendar_id: int) -> Calendar | None:
    """Busca um calendário específico de um usuário."""
    async with SessionLocal() as db:
        # Usando o get_with_events para já carregar os eventos
        calendar = await calendarController.calendar_controller.get_with_events(db, id=calendar_id)
        if calendar and calendar.owner_id == user_id:
            return calendar
        return None

async def get_event_by_id(event_id: int) -> Events | None:
    """Busca um evento específico."""
    async with SessionLocal() as db:
        return await eventsController.event_controller.get(db, id=event_id)


# --- Classes de Recurso DAV ---

class EventResource(DAVNonCollection):
    """Representa um único evento (.ics)."""
    def __init__(self, path, environ, event_id):
        super().__init__(path, environ)
        self.event_id = event_id
        self.event = None # Carregado sob demanda

    async def get_content(self):
        self.event = await get_event_by_id(self.event_id)
        if not self.event:
            raise DAVError(HTTP_NOT_FOUND)

        # Crie o objeto iCalendar
        cal = ICal()
        cal.add('prodid', '-//RiseTec Agenda//')
        cal.add('version', '2.0')

        ievent = ICalEvent()
        # Garanta que o datetime tem timezone. Assumindo UTC se não tiver.
        dt_start = self.event.date
        if dt_start.tzinfo is None:
            dt_start = pytz.utc.localize(dt_start)

        ievent.add('summary', self.event.title)
        ievent.add('description', self.event.description)
        ievent.add('dtstart', dt_start)
        # TODO: Adicionar dtend, location, etc.
        ievent['uid'] = f"{self.event.id}@risetec.agenda"
        ievent['dtstamp'] = pytz.utc.localize(datetime.utcnow())

        cal.add_component(ievent)

        # Retorna um stream de bytes
        return asyncio.get_event_loop().run_in_executor(None, cal.to_ical)

    def get_content_type(self):
        return "text/calendar"

    def get_display_name(self):
        return f"{self.event_id}.ics"


class CalendarCollection(DAVCollection):
    """Representa uma coleção de calendário."""
    def __init__(self, path, environ, user_id, calendar_id):
        super().__init__(path, environ)
        self.user_id = user_id
        self.calendar_id = calendar_id
        self.calendar = None # Carregado sob demanda

    async def get_member_names(self):
        """Lista os eventos (.ics) dentro deste calendário."""
        self.calendar = await get_calendar_by_owner_and_id(self.user_id, self.calendar_id)
        if not self.calendar:
            return []
        # O `get_with_events` já carregou os eventos
        return [f"{event.id}.ics" for event in self.calendar.events]

    async def get_member(self, name):
        """Retorna a instância do recurso para um evento específico."""
        try:
            event_id = int(name.replace(".ics", ""))
            return EventResource(f"{self.path}/{name}", self.environ, event_id)
        except (ValueError, IndexError):
            return None

    def get_display_name(self):
        # Em uma implementação real, o nome viria do self.calendar.name
        return str(self.calendar_id)

    # --- Implementação do PROPFIND ---
    async def get_property(self, name, raise_error=True):
        """Retorna o valor de uma propriedade (para PROPFIND)."""
        # Propriedades essenciais para que um cliente reconheça isto como um calendário
        if name == "{DAV:}resourcetype":
            return """<resourcetype><collection/><C:calendar xmlns:C="urn:ietf:params:xml:ns:caldav"/></resourcetype>"""
        elif name == "{urn:ietf:params:xml:ns:caldav}supported-calendar-component-set":
            return """<C:supported-calendar-component-set xmlns:C="urn:ietf:params:xml:ns:caldav"><C:comp name="VEVENT"/></C:supported-calendar-component-set>"""
        return await super().get_property(name, raise_error)


class UserCalendarsCollection(DAVCollection):
    """Representa a coleção de todos os calendários de um usuário."""
    def __init__(self, path, environ, user_email):
        super().__init__(path, environ)
        self.user_email = user_email
        self.user = None

    async def get_member_names(self):
        """Lista os calendários disponíveis para este usuário."""
        self.user = await get_user_by_email(self.user_email)
        if not self.user:
            return []
        # Precisamos de um método para buscar calendários por owner_id
        # Vamos simular por enquanto.
        # TODO: Adicionar em calendarController -> get_by_owner(owner_id)
        return ["default"] # Simulação, deveria ser lista de IDs/nomes de calendários

    async def get_member(self, name):
        if not self.user:
            self.user = await get_user_by_email(self.user_email)
        if not self.user:
            return None
        # O nome aqui seria o ID/nome do calendário
        # Simulando com um ID fixo = 1
        calendar_id = 1
        return CalendarCollection(f"{self.path}/{name}", self.environ, self.user.id, calendar_id)

    def get_display_name(self):
        return self.user_email


# --- Classe Principal do Provedor ---

from wsgidav.dav_provider import DAVProvider

class CaldavProvider(DAVProvider):
    """
    Provedor DAV que mapeia URLs para os recursos de calendário no banco de dados.
    Estrutura de URL: /<user_email>/<calendar_name>/<event_id>.ics
    """
    def __init__(self):
        super().__init__()

    async def get_resource_inst(self, path, environ):
        """
        Ponto de entrada: resolve um caminho de URL para um recurso específico.
        Este é o "roteador" do nosso servidor CalDAV.
        """
        # Ex: path = "/user@example.com/default/123.ics"
        parts = [p for p in path.strip("/").split("/") if p]

        # Raiz
        if not parts:
            return RootCollection(path, environ)

        user_email = parts[0]
        # /user@example.com
        if len(parts) == 1:
            return UserCalendarsCollection(path, environ, user_email)

        calendar_name = parts[1]
        # Carregar o usuário para obter o ID
        user = await get_user_by_email(user_email)
        if not user:
            return None # Ou DAVError(HTTP_NOT_FOUND)

        # Carregar o calendário para obter o ID
        # TODO: Implementar busca de calendário por nome e owner_id
        calendar_id = 1 # Simulação

        # /user@example.com/default
        if len(parts) == 2:
            return CalendarCollection(path, environ, user.id, calendar_id)

        event_name = parts[2]
        # /user@example.com/default/123.ics
        if len(parts) == 3:
            try:
                event_id = int(event_name.replace(".ics", ""))
                return EventResource(path, environ, event_id)
            except (ValueError, IndexError):
                return None

        return None

class RootCollection(DAVCollection):
    """Representa a coleção raiz '/'."""
    def __init__(self, path, environ):
        super().__init__(path, environ)

    async def get_member_names(self):
        """Lista todos os usuários que têm calendários."""
        # Em uma implementação real, você listaria os usuários do banco.
        # Por enquanto, vamos manter simples.
        async with SessionLocal() as db:
            users = await userController.user_controller.get_multi(db, limit=100)
            return [user.email for user in users]

    async def get_member(self, name):
        """Retorna a coleção de calendários de um usuário."""
        return UserCalendarsCollection(f"/{name}", self.environ, name)