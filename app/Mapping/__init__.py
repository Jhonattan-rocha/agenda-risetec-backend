from app.models.userModel import User
from app.models.userProfileModel import UserProfile
from app.models.permissionsModel import Permissions
from app.models.fileModel import File
from app.models.logModel import Logger
from app.models.eventsModel import Events

from typing import Any

models_mapping: dict[str, Any] = {
    "User": User,
    "UserProfile": UserProfile,
    "Permissions": Permissions,
    "File": File,
    "Logger": Logger,
    "Events": Events,
    "*": None
}

models_fields_mapping: dict[str, tuple] = {
    "User": ("name", "email", "lang"),
    "UserProfile": ("name",),
    "Events": ("name", "date", "desc", "user_id"),
    "Permissions": (
        "entity_name",
        "can_view",
        "can_delete",
        "can_update",
        "can_create",
        "profile_id",
    ),
    "File": ("filename", "originalname", "content_type", "file_path"),
    "Logger": ("action", "user_id", "entity", "data"),
    "*": ("", "")
}
