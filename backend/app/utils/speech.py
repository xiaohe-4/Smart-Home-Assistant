import re


def for_voice(text: str) -> str:
    """把功率单位改成中文，避免语音把 W 读成英文字母。"""
    if not text:
        return text
    spoken = re.sub(r"kWh", "千瓦时", text, flags=re.I)
    spoken = re.sub(r"kW", "千瓦", spoken, flags=re.I)
    spoken = re.sub(r"(\d+(?:\.\d+)?)\s*[Ww]\b", r"\1 瓦", spoken)
    return spoken
