"""公共路径与外部工具探测。"""
import os
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent


def ffmpeg() -> str:
    env = os.environ.get("FFMPEG")
    if env and Path(env).exists():
        return env
    found = shutil.which("ffmpeg")
    if found:
        return found
    for p in [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe"),
    ]:
        if Path(p).exists():
            return p
    raise RuntimeError("找不到 ffmpeg，请安装并加入 PATH，或设置环境变量 FFMPEG")
