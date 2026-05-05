from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SynthesizeRequest(BaseModel):
    text: str
    voice: str = "bingtang"
    style_tags: list[str] = []
    custom_style: str = ""
    singing: bool = False
    audio_format: str = "wav"


class VoiceDesignRequest(BaseModel):
    voice_description: str
    text: str
    audio_format: str = "wav"


class VoiceCloneRequest(BaseModel):
    audio_base64: str
    filename: str
    text: str
    style_tags: list[str] = []
    custom_style: str = ""
    audio_format: str = "wav"


class HistoryRecord(BaseModel):
    id: int
    created_at: str
    model_type: str
    voice_info: Optional[str] = None
    style_tags: Optional[str] = None
    text_content: str
    audio_path: str
    audio_format: str = "wav"
    duration: Optional[float] = None
    is_favorite: bool = False


class SettingsUpdate(BaseModel):
    api_key: Optional[str] = None
    default_voice: Optional[str] = None
    default_format: Optional[str] = None
    default_save_dir: Optional[str] = None
    theme: Optional[str] = None
    language: Optional[str] = None


class ValidateKeyRequest(BaseModel):
    api_key: str
