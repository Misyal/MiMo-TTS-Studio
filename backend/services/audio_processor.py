import base64
import struct
import io

SAMPLE_RATE = 24000
CHANNELS = 1
BITS_PER_SAMPLE = 16


def pcm16_to_wav(pcm_data: bytes) -> bytes:
    """给裸 PCM16 数据加上 WAV 文件头。"""
    data_size = len(pcm_data)
    byte_rate = SAMPLE_RATE * CHANNELS * BITS_PER_SAMPLE // 8
    block_align = CHANNELS * BITS_PER_SAMPLE // 8

    buf = io.BytesIO()
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + data_size))
    buf.write(b"WAVE")
    buf.write(b"fmt ")
    buf.write(struct.pack("<I", 16))
    buf.write(struct.pack("<HHIIHH", 1, CHANNELS, SAMPLE_RATE, byte_rate, block_align, BITS_PER_SAMPLE))
    buf.write(b"data")
    buf.write(struct.pack("<I", data_size))
    buf.write(pcm_data)
    return buf.getvalue()


def decode_audio(audio_base64: str, audio_format: str) -> bytes:
    """解码 Base64 音频数据。

    MiMo API 在 audio_format=wav 时返回的已经是完整 WAV 文件，
    此时只需 Base64 解码，不能再加 WAV 头。
    """
    raw = base64.b64decode(audio_base64)

    # 检查是否已经是 WAV 格式（以 RIFF 头开头）
    if raw[:4] == b"RIFF":
        return raw

    # 裸 PCM16 数据，需要添加 WAV 头
    if audio_format == "wav":
        return pcm16_to_wav(raw)

    return raw
