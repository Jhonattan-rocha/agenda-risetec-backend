# radicale_config/storage.py

from datetime import datetime
from icalendar import Calendar as ICal, Event as ICalEvent
import pytz
import uuid

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
        db = SessionLocalSync()
        try:
            user = db.query(User).filter(User.email == user_login).first()
            if not user:
                return []
            return db.query(CalendarModel).filter(CalendarModel.owner_id == user.id).all()
        finally:
            db.close()

    def get_collection(self, collection_id, user):
        if collection_id is None:
            return None
        
        db = SessionLocalSync()
        try:
            db_user = db.query(User).filter(User.email == user).first()
            if not db_user:
                return None
            
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
        calendars = self._get_user_calendars(user)
        return [Collection(c, user) for c in calendars]

    def create_collection(self, collection_id, user):
        db = SessionLocalSync()
        try:
            db_user = db.query(User).filter(User.email == user).first()
            if not db_user:
                return

            new_calendar = CalendarModel(
                name=collection_id,
                color="#0000FF",
                visible=True,
                is_private=True,
                owner_id=db_user.id
            )
            db.add(new_calendar)
            db.commit()
            return Collection(new_calendar, user)
        finally:
            db.close()


class Collection:
    def __init__(self, calendar_model: CalendarModel, user: str):
        self.calendar_model = calendar_model
        self.user = user

    @property
    def id(self):
        return self.calendar_model.name

    @property
    def owner(self):
        return self.user

    def get_meta(self):
        return {
            "{DAV:}displayname": self.calendar_model.name,
            "{http://apple.com/ns/ical/}calendar-color": self.calendar_model.color
        }

    def list(self):
        """
        Lista todos os itens (eventos) e corrige dinamicamente os que não têm UID.
        """
        db = SessionLocalSync()
        try:
            events = db.query(EventModel).filter(EventModel.calendar_id == self.calendar_model.id).all()
            
            events_to_return = []
            made_changes = False
            for event in events:
                # Se um evento não tiver UID, cria um, salva no banco e o usa.
                if not event.uid:
                    event.uid = str(uuid.uuid4())
                    db.add(event)
                    made_changes = True
                events_to_return.append((f"{event.uid}.ics", str(event.date.timestamp())))

            # Se fizemos alguma alteração, comita para persistir os novos UIDs.
            if made_changes:
                db.commit()
            
            return events_to_return
        finally:
            db.close()

    def get_item(self, href):
        """Retorna um único item (evento) pelo UID."""
        event_uid = href.replace(".ics", "")

        db = SessionLocalSync()
        try:
            event = db.query(EventModel).filter(EventModel.uid == event_uid).first()
            if event:
                return Item(event)
        finally:
            db.close()
        return None

    def upload(self, href, item):
        """Salva um novo evento ou atualiza um existente usando o UID."""
        cal = ICal.from_ical(item.text)
        ievent = cal.walk('VEVENT')[0]
        
        # Lógica robusta para obter ou criar o UID
        event_uid_prop = ievent.get('UID')
        event_uid = str(event_uid_prop) if event_uid_prop else None
        if not event_uid:
            event_uid = str(uuid.uuid4())

        db = SessionLocalSync()
        try:
            db_user = db.query(User).filter(User.email == self.user).first()
            if not db_user:
                return

            db_event = db.query(EventModel).filter(EventModel.uid == event_uid).first()
            
            event_data = {
                "title": str(ievent.get('summary', 'Sem Título')),
                "description": str(ievent.get('description', '')),
                "date": ievent.get('dtstart').dt,
                "isAllDay": not isinstance(ievent.get('dtstart').dt, datetime),
                "created_by": db_user.id,
                "calendar_id": self.calendar_model.id,
                "uid": event_uid
            }

            if db_event:
                for key, value in event_data.items():
                    setattr(db_event, key, value)
            else:
                db_event = EventModel(**event_data)
                db.add(db_event)
            
            db.commit()
            db.refresh(db_event)
            return str(db_event.date.timestamp())
        finally:
            db.close()
    
    def delete(self, href):
        """Deleta um evento pelo UID."""
        event_uid = href.replace(".ics", "")

        db = SessionLocalSync()
        try:
            event = db.query(EventModel).filter(EventModel.uid == event_uid).first()
            if event:
                db.delete(event)
                db.commit()
        finally:
            db.close()


class Item:
    def __init__(self, event_model: EventModel):
        self.event_model = event_model
        self._text = None

    @property
    def text(self):
        """Converte os dados do banco para o formato iCalendar."""
        if self._text is None:
            cal = ICal()
            cal.add('prodid', '-//RiseTec Agenda//')
            cal.add('version', '2.0')

            ievent = ICalEvent()
            
            ievent['uid'] = self.event_model.uid
            ievent['dtstamp'] = datetime.now(pytz.utc)
            ievent.add('summary', self.event_model.title)
            ievent.add('description', self.event_model.description or '')

            dt_start = self.event_model.date
            
            if self.event_model.isAllDay:
                ievent.add('dtstart', dt_start.date())
            else:
                if dt_start.tzinfo is None:
                    dt_start = pytz.utc.localize(dt_start)
                ievent.add('dtstart', dt_start)

            cal.add_component(ievent)
            self._text = cal.to_ical()
        return self._text