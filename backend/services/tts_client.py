import logging
import httpx
from backend.config import settings

logger = logging.getLogger(__name__)

PRESET_VOICES = [
    {"id": "bingtang", "name": "冰糖", "lang": "zh", "gender": "female", "desc": "通用场景，发音清晰自然"},
    {"id": "moli", "name": "茉莉", "lang": "zh", "gender": "female", "desc": "温柔亲切，适合有声书、睡前故事"},
    {"id": "suda", "name": "苏打", "lang": "zh", "gender": "male", "desc": "年轻活力，适合短视频、游戏解说"},
    {"id": "baihua", "name": "白桦", "lang": "zh", "gender": "male", "desc": "沉稳大气，适合新闻播报、纪录片"},
    {"id": "Mia", "name": "Mia", "lang": "en", "gender": "female", "desc": "美式英语，通用场景"},
    {"id": "Chloe", "name": "Chloe", "lang": "en", "gender": "female", "desc": "美式英语，温柔知性"},
    {"id": "Milo", "name": "Milo", "lang": "en", "gender": "male", "desc": "美式英语，年轻阳光"},
    {"id": "Dean", "name": "Dean", "lang": "en", "gender": "male", "desc": "美式英语，成熟稳重"},
]


def _build_messages(text: str, style_tags: list[str], custom_style: str, singing: bool):
    messages = []
    user_content = custom_style if custom_style else ""
    assistant_text = text
    if singing:
        assistant_text = "（唱歌）" + assistant_text
    if style_tags:
        tag_str = "，".join(style_tags)
        assistant_text = f"（{tag_str}）{assistant_text}"
    if user_content:
        messages.append({"role": "user", "content": user_content})
    messages.append({"role": "assistant", "content": assistant_text})
    return messages


def _get_headers(api_key: str) -> dict:
    return {"api-key": api_key, "Content-Type": "application/json"}


def _extract_audio_b64(data: dict) -> str:
    """从 API 响应中提取 Base64 音频字符串，兼容多种响应格式。"""
    audio = data["choices"][0]["message"]["audio"]

    # 如果已经是字符串，直接返回
    if isinstance(audio, str):
        return audio

    # 如果是 dict，尝试常见的字段名
    if isinstance(audio, dict):
        for key in ("data", "audio", "content", "base64", "b64", "audio_data"):
            if key in audio and isinstance(audio[key], str):
                return audio[key]
        # 记录实际结构以便调试
        logger.error(f"audio 字段是 dict，但找不到 Base64 数据。keys={list(audio.keys())}")
        logger.error(f"audio 内容: {str(audio)[:500]}")
        raise ValueError(f"无法从 audio 响应中提取 Base64 数据，字段: {list(audio.keys())}")

    # 如果是 list（可能是 chunks）
    if isinstance(audio, list):
        # 拼接所有 chunk
        chunks = []
        for item in audio:
            if isinstance(item, str):
                chunks.append(item)
            elif isinstance(item, dict):
                for key in ("data", "audio", "content", "base64"):
                    if key in item and isinstance(item[key], str):
                        chunks.append(item[key])
                        break
        if chunks:
            return "".join(chunks)

    logger.error(f"audio 字段类型未知: {type(audio)}, 值: {str(audio)[:500]}")
    raise ValueError(f"无法解析 audio 响应，类型: {type(audio)}")


async def _call_tts(api_key: str, payload: dict) -> dict:
    """调用 MiMo TTS API 并返回标准格式的响应。"""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{settings.api_base_url}/chat/completions",
            headers=_get_headers(api_key),
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

        audio_b64 = _extract_audio_b64(data)
        logger.debug(f"API 响应 audio 数据长度: {len(audio_b64) if isinstance(audio_b64, str) else 'N/A'}")
        return {"audio_base64": audio_b64}


async def synthesize_preset(text: str, voice: str, style_tags: list[str], custom_style: str, singing: bool, audio_format: str = "wav", api_key: str = "") -> dict:
    key = api_key or settings.api_key
    messages = _build_messages(text, style_tags, custom_style, singing)
    payload = {
        "model": "mimo-v2.5-tts",
        "messages": messages,
        "voice": voice,
        "audio_format": audio_format,
        "stream": False,
    }
    result = await _call_tts(key, payload)
    result["format"] = audio_format
    return result


async def synthesize_voice_design(voice_description: str, text: str, audio_format: str = "wav", api_key: str = "") -> dict:
    key = api_key or settings.api_key
    messages = [
        {"role": "user", "content": voice_description},
        {"role": "assistant", "content": text},
    ]
    payload = {
        "model": "mimo-v2.5-tts-voicedesign",
        "messages": messages,
        "audio_format": audio_format,
        "stream": False,
    }
    result = await _call_tts(key, payload)
    result["format"] = audio_format
    return result


async def synthesize_voice_clone(audio_base64: str, text: str, style_tags: list[str], custom_style: str, audio_format: str = "wav", api_key: str = "") -> dict:
    key = api_key or settings.api_key
    assistant_text = text
    if style_tags:
        tag_str = "，".join(style_tags)
        assistant_text = f"（{tag_str}）{assistant_text}"
    messages = [
        {"role": "user", "content": custom_style or "请用这个声音说话"},
        {"role": "audio", "audio": audio_base64},
        {"role": "assistant", "content": assistant_text},
    ]
    payload = {
        "model": "mimo-v2.5-tts-voiceclone",
        "messages": messages,
        "audio_format": audio_format,
        "stream": False,
    }
    result = await _call_tts(key, payload)
    result["format"] = audio_format
    return result


async def validate_api_key(api_key: str) -> bool:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{settings.api_base_url}/chat/completions",
            headers=_get_headers(api_key),
            json={
                "model": "mimo-v2.5-tts",
                "messages": [{"role": "assistant", "content": "测试"}],
                "voice": "bingtang",
                "audio_format": "wav",
                "stream": False,
            },
        )
        return resp.status_code == 200
