import os
from pathlib import Path
from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
AUDIO_DIR = DATA_DIR / "audio"
PREVIEW_DIR = DATA_DIR / "preview"
LOG_DIR = DATA_DIR / "logs"

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    # MiMo API
    api_base_url: str = "https://api.xiaomimimo.com/v1"
    api_key: str = ""

    # 服务配置
    host: str = "127.0.0.1"
    port: int = 18700

    # 数据库
    db_path: str = str(DATA_DIR / "tts.db")

    # 默认参数
    default_voice: str = "bingtang"
    default_format: str = "wav"
    default_save_dir: str = str(DATA_DIR / "audio")

    # 界面偏好
    theme: str = "light"
    language: str = "zh"

    class Config:
        env_file = ".env"
        env_prefix = "MIMO_"


settings = Settings()
