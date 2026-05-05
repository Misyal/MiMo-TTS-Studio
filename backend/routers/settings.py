from fastapi import APIRouter
from backend.models import SettingsUpdate
from backend.database import get_setting, set_setting
from backend.config import settings

router = APIRouter(prefix="/api", tags=["settings"])


@router.get("/settings")
async def get_settings():
    return {
        "api_key": await get_setting("api_key", settings.api_key),
        "default_voice": await get_setting("default_voice", settings.default_voice),
        "default_format": await get_setting("default_format", settings.default_format),
        "default_save_dir": await get_setting("default_save_dir", settings.default_save_dir),
        "theme": await get_setting("theme", settings.theme),
        "language": await get_setting("language", settings.language),
    }


@router.put("/settings")
async def update_settings(req: SettingsUpdate):
    updates = req.model_dump(exclude_none=True)
    for key, value in updates.items():
        await set_setting(key, str(value))
    return {"message": "设置已更新"}
