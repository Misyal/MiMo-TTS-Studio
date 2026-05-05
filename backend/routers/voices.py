import logging

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.config import settings, PREVIEW_DIR
from backend.database import get_setting
from backend.services.tts_client import PRESET_VOICES, synthesize_preset
from backend.services.audio_processor import decode_audio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["voices"])

PREVIEW_TEXT = "欢迎使用MiMo语音合成"


@router.get("/voices")
async def list_voices():
    return {"voices": PRESET_VOICES}


@router.get("/voice-preview/{voice_id}")
async def voice_preview(voice_id: str):
    """返回指定音色的试听音频。优先使用缓存，否则调用 API 生成。"""
    # 校验音色 ID
    valid_ids = [v["id"] for v in PRESET_VOICES]
    if voice_id not in valid_ids:
        raise HTTPException(status_code=404, detail=f"音色不存在: {voice_id}")

    # 检查缓存文件
    cache_file = PREVIEW_DIR / f"{voice_id}.wav"
    if cache_file.exists():
        return FileResponse(str(cache_file), media_type="audio/wav")

    # 无缓存，尝试调用 API 生成
    api_key = await get_setting("api_key", settings.api_key)
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="未配置 API Key，无法生成试听音频。请先在设置页面配置 API Key。"
        )

    try:
        result = await synthesize_preset(
            text=PREVIEW_TEXT,
            voice=voice_id,
            style_tags=[],
            custom_style="",
            singing=False,
            audio_format="wav",
            api_key=api_key,
        )

        # 保存到缓存
        audio_bytes = decode_audio(result["audio_base64"], "wav")
        cache_file.write_bytes(audio_bytes)
        logger.info(f"已生成音色试听缓存: {voice_id}")

        return FileResponse(str(cache_file), media_type="audio/wav")
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="生成试听音频超时，请稍后重试")
    except Exception as e:
        logger.error(f"生成试听音频失败 ({voice_id}): {e}")
        raise HTTPException(status_code=500, detail=f"生成试听音频失败: {str(e)}")
