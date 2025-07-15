# radicale_storage/storage.py

import uuid
from datetime import datetime
from icalendar import Calendar as ICal, Event as ICalEvent
import pytz

# Importações da sua aplicação
from app.database.database import SessionLocalSync
from app.models.userModel import User
from app.models.calendarModel import Calendar as CalendarModel
from app.models.eventsModel import Events as EventModel

# Classe base do Radicale para armazenamento
from radicale.storage import BaseStorage

class Storage(BaseStorage):
    """
    Backend de armazenamento customizado que se conecta ao banco de dados da sua aplicação.
    """

    def _get_user_calendars(self, user_login):
        """Busca os calendários de um usuário no banco de dados."""
        db = SessionLocalSync()
        try:
            user = db.query(User).filter(User.email == user_login).first()
            if not user:
                return []
            # Retorna todos os calendários pertencentes a este usuário
            return db.query(CalendarModel).filter(CalendarModel.owner_id == user.id).all()
        finally:
            db.close()

    def get_collection(self, collection_id, user):
        """
        Retorna uma instância de um calendário específico (Coleção).
        O Radicale chama isso quando acessa um calendário, ex: /user.email@example.com/calendar_name/
        """
        if collection_id is None:
            return
        
        # O collection_id para nós será o nome do calendário
        db = SessionLocalSync()
        try:
            # Encontra o usuário para pegar o owner_id
            db_user = db.query(User).filter(User.email == user).first()
            if not db_user:
                return None
            
            # Busca o calendário pelo nome e pelo dono
            calendar = db.query(CalendarModel).filter(
                CalendarModel.owner_id == db_user.id,
                CalendarModel.name == collection_id
            ).first()

            if calendar:
                return Collection(calendar, user)
        finally:
            db.close()
        return None

    def get_collections(self, user):
        """
        Retorna uma lista de todos os calendários (Coleções) para um usuário.
        O Radicale chama isso para listar os calendários na raiz do usuário.
        """
        calendars = self._get_user_calendars(user)
        return [Collection(c, user) for c in calendars]

    def create_collection(self, collection_id, user):
        """Cria um novo calendário."""
        db = SessionLocalSync()
        try:
            db_user = db.query(User).filter(User.email == user).first()
            if not db_user:
                # Não deveria acontecer se a autenticação funcionou
                return

            # Cria a nova instância do modelo do calendário
            new_calendar = CalendarModel(
                name=collection_id,
                color="#0000FF", # Cor padrão
                visible=True,
                is_private=True,
                owner_id=db_user.id
            )
            db.add(new_calendar)
            db.commit()
        finally:
            db.close()


class Collection:
    """Representa um único calendário (uma coleção de eventos)."""

    def __init__(self, calendar_model: CalendarModel, user: str):
        self.calendar_model = calendar_model
        self.user = user

    @property
    def id(self):
        """O Radicale usa o ID para identificar a coleção. Usaremos o nome do calendário."""
        return self.calendar_model.name

    @property
    def owner(self):
        """
        PROPRIEDADE ADICIONADA: Informa ao Radicale quem é o dono da coleção.
        O dono é o login do usuário, que já armazenamos em self.user.
        """
        return self.user

    def get_meta(self):
        """Retorna metadados sobre o calendário."""
        return {
            "{DAV:}displayname": self.calendar_model.name,
            "{http://apple.com/ns/ical/}calendar-color": self.calendar_model.color
        }

    def list(self):
        """Retorna a lista de todos os itens (eventos) no calendário."""
        db = SessionLocalSync()
        try:
            events = db.query(EventModel).filter(EventModel.calendar_id == self.calendar_model.id).all()
            # O Radicale espera o ID do item (href) e o etag (para cache)
            return [(f"{event.id}.ics", str(event.date.timestamp())) for event in events]
        finally:
            db.close()

    def get_item(self, href):
        """Retorna um único item (evento) do calendário."""
        try:
            event_id = int(href.replace(".ics", ""))
        except (ValueError, TypeError):
            return None

        db = SessionLocalSync()
        try:
            event = db.query(EventModel).filter(EventModel.id == event_id).first()
            if event:
                return Item(event)
        finally:
            db.close()
        return None

    def upload(self, href, item):
        """Salva um novo evento ou atualiza um existente."""
        # 'item.text' contém os dados do iCalendar (ICS)
        cal = ICal.from_ical(item.text)
        ievent = cal.walk('VEVENT')[0] # Pega o primeiro evento do arquivo

        db = SessionLocalSync()
        try:
            # Tenta extrair o ID do evento do nome do arquivo
            try:
                event_id = int(href.replace(".ics", ""))
            except (ValueError, TypeError):
                event_id = None
            
            db_user = db.query(User).filter(User.email == self.user).first()
            if not db_user:
                return

            # Prepara os dados do evento para salvar no banco
            event_data = {
                "title": str(ievent.get('summary', 'Sem Título')),
                "description": str(ievent.get('description', '')),
                "date": ievent.get('dtstart').dt,
                "isAllDay": not isinstance(ievent.get('dtstart').dt, datetime),
                "created_by": db_user.id,
                "calendar_id": self.calendar_model.id
            }

            # Verifica se é uma criação ou atualização
            if event_id:
                # Atualização
                db_event = db.query(EventModel).filter(EventModel.id == event_id).first()
                if db_event:
                    for key, value in event_data.items():
                        setattr(db_event, key, value)
                else: # O evento foi deletado, cria um novo
                    db_event = EventModel(**event_data)
                    db.add(db_event)
            else:
                # Criação
                db_event = EventModel(**event_data)
                db.add(db_event)
            
            db.commit()
            db.refresh(db_event)
            # Retorna o etag do novo item
            return str(db_event.date.timestamp())
        finally:
            db.close()
    
    def delete(self, href):
        """Deleta um evento."""
        try:
            event_id = int(href.replace(".ics", ""))
        except (ValueError, TypeError):
            return

        db = SessionLocalSync()
        try:
            event = db.query(EventModel).filter(EventModel.id == event_id).first()
            if event:
                db.delete(event)
                db.commit()
        finally:
            db.close()


class Item:
    """Representa um único evento (um arquivo .ics)."""
    def __init__(self, event_model: EventModel):
        self.event_model = event_model
        super().__init__(self.to_ical())

    def to_ical(self):
        """Converte os dados do nosso banco para o formato iCalendar."""
        cal = ICal()
        cal.add('prodid', '-//RiseTec Agenda//')
        cal.add('version', '2.0')

        ievent = ICalEvent()
        
        # Garante que a data tenha timezone, essencial para CalDAV
        dt_start = self.event_model.date
        if not isinstance(dt_start, datetime):
            dt_start = datetime.combine(dt_start, datetime.min.time(), tzinfo=pytz.utc)
        elif dt_start.tzinfo is None:
            dt_start = pytz.utc.localize(dt_start)
        
        ievent.add('summary', self.event_model.title)
        ievent.add('description', self.event_model.description or '')
        ievent.add('dtstart', dt_start)
        
        # UID é obrigatório e deve ser único
        ievent['uid'] = f"{self.event_model.id}-{uuid.uuid4()}@risetec.agenda"
        ievent['dtstamp'] = datetime.now(pytz.utc)

        cal.add_component(ievent)
        return cal.to_ical()