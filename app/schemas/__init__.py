from .eventsSchema import Event
from .userSchema import User

User.model_rebuild()
Event.model_rebuild()