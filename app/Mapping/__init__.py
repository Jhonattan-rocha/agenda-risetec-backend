from app.models.DefaultModels.userModel import User
from app.models.DefaultModels.userProfileModel import UserProfile
from app.models.DefaultModels.permissionsModel import Permissions
from app.models.DefaultModels.fileModel import File
from app.models.DefaultModels.logModel import Logger
from app.models.DefaultModels.eventsModel import Events

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
    "User": ("name", "email", "lang", "profile_id"),
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
