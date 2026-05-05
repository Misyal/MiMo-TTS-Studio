import uuid
import logging
from datetime import datetime
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException

from backend.models import SynthesizeRequest, VoiceDesignRequest, VoiceCloneRequest, ValidateKeyRequest
from backend.services.tts_client import synthesize_preset, synthesize_voice_design, synthesize_voice_clone, validate_api_key
from backend.services.audio_processor import decode_audio
from backend.database import get_db, get_setting
from backend.config import AUDIO_DIR, settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["synthesize"])


async def _get_api_key() -> str:
    """获取 API Key，未配置时抛出 401 异常。"""
    api_key = await get_setting("api_key", settings.api_key)
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="未配置 API Key，请先在设置页面配置 API Key。"
        )
    return api_key


async def _save_audio(audio_base64: str, audio_format: str) -> tuple[str, float]:
    audio_bytes = decode_audio(audio_base64, audio_format)
    now = datetime.now()
    rel_dir = f"{now.year}/{now.month:02d}"
    save_dir = AUDIO_DIR / rel_dir
    save_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex[:12]}.{audio_format}"
    filepath = save_dir / filename
    filepath.write_bytes(audio_bytes)
    # 估算时长: pcm16 24000Hz mono = 2 bytes/sample
    duration = len(audio_bytes) / (24000 * 2)
    return f"{rel_dir}/{filename}", round(duration, 2)


async def _record_history(model_type: str, voice_info: str, style_tags: str, text: str, audio_path: str, audio_format: str, duration: float):
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO history (model_type, voice_info, style_tags, text_content, audio_path, audio_format, duration) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (model_type, voice_info, style_tags, text, audio_path, audio_format, duration),
        )
        await db.commit()
    finally:
        await db.close()


@router.post("/synthesize")
async def synthesize(req: SynthesizeRequest):
    api_key = await _get_api_key()
    try:
        result = await synthesize_preset(
            req.text, req.voice, req.style_tags, req.custom_style,
            req.singing, req.audio_format, api_key=api_key
        )
        audio_path, duration = await _save_audio(result["audio_base64"], req.audio_format)
        style_str = ",".join(req.style_tags)
        await _record_history("preset", req.voice, style_str, req.text, audio_path, req.audio_format, duration)
        return {"audio_base64": result["audio_base64"], "format": req.audio_format, "duration": duration, "audio_path": audio_path}
    except HTTPException:
        raise
    except httpx.TimeoutException:
        logger.error("合成请求超时")
        raise HTTPException(status_code=504, detail="请求超时，请稍后重试")
    except httpx.HTTPStatusError as e:
        logger.error(f"MiMo API 返回错误: {e.response.status_code} - {e.response.text}")
        detail = f"API 返回错误 ({e.response.status_code})"
        try:
            err_data = e.response.json()
            if "error" in err_data:
                detail = err_data["error"].get("message", detail)
        except Exception:
            pass
        raise HTTPException(status_code=502, detail=detail)
    except Exception as e:
        logger.error(f"合成失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"合成失败: {str(e)}")


@router.post("/voice-design")
async def voice_design(req: VoiceDesignRequest):
    api_key = await _get_api_key()
    try:
        result = await synthesize_voice_design(
            req.voice_description, req.text, req.audio_format, api_key=api_key
        )
        audio_path, duration = await _save_audio(result["audio_base64"], req.audio_format)
        await _record_history("voice_design", req.voice_description, "", req.text, audio_path, req.audio_format, duration)
        return {"audio_base64": result["audio_base64"], "format": req.audio_format, "duration": duration, "audio_path": audio_path}
    except HTTPException:
        raise
    except httpx.TimeoutException:
        logger.error("音色设计请求超时")
        raise HTTPException(status_code=504, detail="请求超时，请稍后重试")
    except httpx.HTTPStatusError as e:
        logger.error(f"MiMo API 返回错误: {e.response.status_code} - {e.response.text}")
        detail = f"API 返回错误 ({e.response.status_code})"
        try:
            err_data = e.response.json()
            if "error" in err_data:
                detail = err_data["error"].get("message", detail)
        except Exception:
            pass
        raise HTTPException(status_code=502, detail=detail)
    except Exception as e:
        logger.error(f"音色设计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"音色设计失败: {str(e)}")


@router.post("/voice-clone")
async def voice_clone(req: VoiceCloneRequest):
    api_key = await _get_api_key()
    try:
        result = await synthesize_voice_clone(
            req.audio_base64, req.text, req.style_tags, req.custom_style,
            req.audio_format, api_key=api_key
        )
        audio_path, duration = await _save_audio(result["audio_base64"], req.audio_format)
        style_str = ",".join(req.style_tags)
        await _record_history("voice_clone", req.filename, style_str, req.text, audio_path, req.audio_format, duration)
        return {"audio_base64": result["audio_base64"], "format": req.audio_format, "duration": duration, "audio_path": audio_path}
    except HTTPException:
        raise
    except httpx.TimeoutException:
        logger.error("音色克隆请求超时")
        raise HTTPException(status_code=504, detail="请求超时，请稍后重试")
    except httpx.HTTPStatusError as e:
        logger.error(f"MiMo API 返回错误: {e.response.status_code} - {e.response.text}")
        detail = f"API 返回错误 ({e.response.status_code})"
        try:
            err_data = e.response.json()
            if "error" in err_data:
                detail = err_data["error"].get("message", detail)
        except Exception:
            pass
        raise HTTPException(status_code=502, detail=detail)
    except Exception as e:
        logger.error(f"音色克隆失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"音色克隆失败: {str(e)}")


@router.post("/validate-key")
async def validate_key(req: ValidateKeyRequest):
    try:
        ok = await validate_api_key(req.api_key)
        return {"valid": ok}
    except httpx.TimeoutException:
        return {"valid": False, "error": "验证超时，请检查网络连接"}
    except Exception as e:
        logger.error(f"API Key 验证失败: {e}")
        return {"valid": False, "error": "验证失败，请检查网络连接"}
