# app/dav/caldav_provider.py

import asyncio
from wsgidav.dav_provider import DAVCollection, DAVNonCollection
from wsgidav.dav_error import DAVError, HTTP_NOT_FOUND, HTTP_FORBIDDEN, HTTP_NO_CONTENT, HTTP_CREATED
from icalendar import Calendar as ICal, Event as ICalEvent
from datetime import datetime
import pytz # Necessário para timezones
from defusedxml import ElementTree as ET

# Importe seus controllers e o SessionLocal
from app.database.database import SessionLocal
from app.controllers import userController, calendarController, eventsController
from app.models.userModel import User
from app.models.calendarModel import Calendar
from app.models.eventsModel import Events
from app.schemas.eventsSchema import EventBase, EventUpdate
from app.schemas.calendarSchema import CalendarBase # Novo import

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

    # --- Método GET (Leitura) - Sem alterações ---
    async def get_content(self):
        self.event = await get_event_by_id(self.event_id)
        if not self.event:
            raise DAVError(HTTP_NOT_FOUND)

        cal = ICal()
        cal.add('prodid', '-//RiseTec Agenda//')
        cal.add('version', '2.0')

        ievent = ICalEvent()
        dt_start = self.event.date
        if dt_start.tzinfo is None:
            dt_start = pytz.utc.localize(dt_start)

        ievent.add('summary', self.event.title)
        ievent.add('description', self.event.description)
        ievent.add('dtstart', dt_start)
        ievent['uid'] = f"{self.event.id}@risetec.agenda"
        ievent['dtstamp'] = pytz.utc.localize(datetime.utcnow())

        cal.add_component(ievent)
        return asyncio.get_event_loop().run_in_executor(None, cal.to_ical)

    # --- NOVO: Método DELETE ---
    async def delete(self):
        """
        Invocado quando uma requisição DELETE é recebida.
        Exclui o evento do banco de dados.
        """
        try:
            async with SessionLocal() as db:
                # Usa o controller de eventos para remover o evento pelo ID
                deleted_event = await eventsController.event_controller.remove(db=db, id=self.event_id)
                if not deleted_event:
                    # Se o evento não foi encontrado, retorna 404
                    raise DAVError(HTTP_NOT_FOUND)
            
            # Se a exclusão for bem-sucedida, wsgidav espera que um erro HTTP_NO_CONTENT seja levantado
            # para enviar a resposta correta (204) ao cliente.
            raise DAVError(HTTP_NO_CONTENT)
            
        except Exception as e:
            # Se for um DAVError, repassa. Senão, encapsula como erro interno.
            if isinstance(e, DAVError):
                raise
            print(f"Erro ao deletar evento {self.event_id}: {e}")
            raise DAVError(500, "Failed to delete event.")

    # --- NOVO: Método PUT (Escrita) ---
    async def begin_write(self, content_type):
        """Invocado quando uma requisição PUT é iniciada."""
        if content_type.lower() != "text/calendar; charset=utf-8" and content_type.lower() != "text/calendar":
             # Recusa qualquer coisa que não seja um iCalendar
            raise DAVError(HTTP_FORBIDDEN, "Unsupported content type.")
        # Retorna um stream para onde o wsgidav escreverá o conteúdo do PUT
        from io import BytesIO
        self._put_stream = BytesIO()
        return self._put_stream

    async def end_write(self, with_error):
        """
        Invocado após o conteúdo do PUT ter sido completamente escrito.
        Aqui é onde a mágica acontece.
        """
        if with_error:
            # Se algo deu errado durante a escrita do stream, não fazemos nada.
            return

        # 1. Obter o conteúdo .ics do stream
        ics_data = self._put_stream.getvalue()

        try:
            # 2. Fazer o parse do conteúdo iCalendar
            cal = ICal.from_ical(ics_data)
            # Pegamos o primeiro componente VEVENT do calendário
            ievent = next(cal.walk('VEVENT'))

            # 3. Extrair os dados do evento
            # O UID é crucial para identificar o evento de forma única
            uid = str(ievent.get('uid'))
            summary = str(ievent.get('summary'))
            description = str(ievent.get('description', ''))
            dtstart = ievent.get('dtstart').dt # .dt converte para objeto datetime

            # Precisamos do calendar_id e do created_by
            # Extraímos do path: /<user_email>/<calendar_name>/...
            parts = [p for p in self.path.strip("/").split("/") if p]
            user_email = parts[0]
            calendar_name = parts[1] # Simulação, deveria buscar o ID

            async with SessionLocal() as db:
                user = await get_user_by_email(user_email)
                if not user:
                    raise DAVError(HTTP_FORBIDDEN, "User not found")

                # TODO: Implementar busca de calendário por nome para obter o ID correto
                calendar_id_db = 1 # Simulação

                # 4. Preparar os dados para o nosso schema
                event_data = {
                    "title": summary,
                    "description": description,
                    "date": dtstart,
                    "isAllDay": False, # TODO: Detectar se é um evento de dia inteiro
                    "calendar_id": calendar_id_db,
                    "created_by": user.id,
                    "user_ids": [user.id] # Adiciona o criador como participante
                }

                # 5. Verificar se o evento já existe (pelo nosso event_id/self.event_id)
                db_event = await eventsController.event_controller.get(db=db, id=self.event_id)

                if db_event:
                    # Se existe, ATUALIZA
                    update_schema = EventUpdate(**event_data)
                    await eventsController.event_controller.update(db=db, db_obj=db_event, obj_in=update_schema)
                else:
                    # Se não existe, CRIA
                    create_schema = EventBase(**event_data)
                    await eventsController.event_controller.create(db=db, obj_in=create_schema)

        except Exception as e:
            # Em caso de erro no parse ou no banco, retorna um erro para o cliente
            print(f"Erro ao processar PUT: {e}")
            raise DAVError(500, "Failed to process calendar data.")

    # --- Outros métodos ---

    def get_content_type(self):
        return "text/calendar"

    def get_display_name(self):
        return f"{self.event_id}.ics"

    # --- NOVO: ETag para versionamento ---
    async def get_etag(self):
        """
        Retorna um identificador único para a versão atual do recurso.
        Crucial para que os clientes saibam se precisam baixar o evento novamente.
        """
        if not self.event:
            self.event = await get_event_by_id(self.event_id)

        if not self.event:
            return None

        # Uma forma simples de ETag é usar um timestamp da última modificação
        # Em um modelo real, você teria um campo `updated_at`. Vamos simular.
        # return f'"{int(self.event.date.timestamp())}"'
        # Por enquanto, vamos usar o ID como um etag simples.
        return f'"{self.event.id}-{int(self.event.date.timestamp())}"'


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

    # --- NOVO: Método REPORT ---
    async def report_calendar_query(self, xml_report_info, depth):
        """
        Lida com a requisição REPORT do tipo 'calendar-query'.
        Este é o principal mecanismo de busca do CalDAV.
        """
        # 1. Parsear o XML da requisição para encontrar o time-range
        try:
            # Encontra o elemento 'time-range' dentro do filtro do 'calendar-query'
            # Namespace 'C' para CalDAV, 'D' para DAV
            ns = {'D': 'DAV:', 'C': 'urn:ietf:params:xml:ns:caldav'}
            time_range = xml_report_info.find('C:filter/C:comp-filter/C:time-range', ns)

            if time_range is None:
                raise DAVError(400, "REPORT sem time-range não é suportado.")

            # Extrai as datas de início e fim
            start_str = time_range.get("start")
            end_str = time_range.get("end")

            # Converte as strings para objetos datetime (formato: 20240713T000000Z)
            # O 'Z' no final indica UTC (Zulu time)
            start_date = datetime.strptime(start_str, "%Y%m%dT%H%M%SZ").replace(tzinfo=pytz.utc)
            end_date = datetime.strptime(end_str, "%Y%m%dT%H%M%SZ").replace(tzinfo=pytz.utc)

        except Exception as e:
            print(f"Erro ao parsear o REPORT: {e}")
            raise DAVError(400, "XML do REPORT mal formatado.")

        # 2. Buscar os eventos no banco de dados usando nosso novo método do controller
        async with SessionLocal() as db:
            events = await eventsController.event_controller.get_events_in_range(
                db,
                calendar_id=self.calendar_id,
                start_date=start_date,
                end_date=end_date
            )

        # 3. Construir a resposta XML 'multistatus'
        from wsgidav.xml_tools import make_response, make_prop_stat_response

        responses = []
        for event in events:
            # Para cada evento, criamos um recurso temporário para obter seus dados
            event_resource = EventResource(f"{self.path}/{event.id}.ics", self.environ, event.id)
            event_resource.event = event # Pré-carrega o evento para evitar outra busca no DB

            # Obtém o ETag e os dados iCalendar (.ics) do evento
            etag = await event_resource.get_etag()
            ics_data = await event_resource.get_content()

            # Monta a parte da resposta para este evento específico
            responses.append(
                make_prop_stat_response(
                    f"{self.path}{event.id}.ics", # URL completa do recurso
                    {
                        "{DAV:}getetag": etag,
                        "{urn:ietf:params:xml:ns:caldav}calendar-data": ics_data.decode('utf-8')
                    }
                )
            )

        # Retorna a resposta completa no formato XML multistatus
        return "".join(make_response(r) for r in responses)


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

    # --- NOVO MÉTODO: MKCALENDAR ---
    async def create_collection(self, name):
        """
        Lida com a requisição MKCALENDAR para criar um novo calendário.
        O 'name' é o último segmento da URL (ex: 'Trabalho').
        """
        # 1. Obter o corpo XML da requisição
        try:
            # wsgidav disponibiliza o corpo da requisição no environ
            content_length = int(self.environ.get("CONTENT_LENGTH", 0))
            xml_data = self.environ["wsgi.input"].read(content_length)
        except Exception as e:
            print(f"Erro ao ler o corpo da requisição MKCALENDAR: {e}")
            raise DAVError(500)

        # 2. Parsear o XML para extrair propriedades
        display_name = name # Usa o nome da URL como padrão
        description = None
        # Adicione outras propriedades que você queira suportar, como cor

        if xml_data:
            try:
                ns = {'D': 'DAV:', 'C': 'urn:ietf:params:xml:ns:caldav'}
                root = ET.fromstring(xml_data)
                # Encontra a propriedade displayname
                dn_node = root.find("D:set/D:prop/D:displayname", ns)
                if dn_node is not None and dn_node.text:
                    display_name = dn_node.text

                # Encontra a descrição do calendário
                desc_node = root.find("D:set/D:prop/{urn:ietf:params:xml:ns:caldav}calendar-description", ns)
                if desc_node is not None and desc_node.text:
                    description = desc_node.text

            except Exception as e:
                print(f"Erro ao parsear o XML do MKCALENDAR: {e}")
                # Não é um erro fatal, podemos prosseguir com os padrões
                pass

        # 3. Chamar o controller para criar o calendário no banco de dados
        try:
            async with SessionLocal() as db:
                # Garante que o usuário existe
                if not self.user:
                    self.user = await get_user_by_email(self.user_email)
                if not self.user:
                    raise DAVError(HTTP_FORBIDDEN, "User not found to create calendar for.")

                # Prepara o schema Pydantic para a criação
                new_calendar_schema = CalendarBase(
                    name=display_name,
                    description=description,
                    color="#0000FF", # Cor padrão
                    visible=True,
                    is_private=True,
                    owner_id=self.user.id
                )

                # Cria o calendário
                await calendarController.calendar_controller.create(db, obj_in=new_calendar_schema)

        except Exception as e:
            print(f"Erro de banco de dados ao criar calendário: {e}")
            raise DAVError(500, "Could not create calendar in database.")

        # 4. Retorna a resposta de sucesso
        # wsgidav lida com o envio do status 201 Created quando levantamos este erro
        raise DAVError(HTTP_CREATED)



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