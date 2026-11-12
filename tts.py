"""离线 TTS（Windows SAPI）→ AAC/m4a，供平台语音评测。"""
import os
import subprocess

from paths import ffmpeg

PS = ("Add-Type -AssemblyName System.Speech;"
      "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
      "$s.SelectVoice('Microsoft Zira Desktop');"
      "$s.Rate={rate};"
      "$s.SetOutputToWaveFile('{wav}');"
      "$s.Speak([IO.File]::ReadAllText('{txt}'));"
      "$s.Dispose()")


def speak(text, out_m4a, rate=170):
    """每条起独立 PowerShell 进程，避免 pyttsx3 复用挂起。"""
    txt = out_m4a + ".txt"
    wav = out_m4a + ".wav"
    with open(txt, "w", encoding="utf-8") as f:
        f.write(text)
    cmd = PS.format(rate=0 if rate >= 170 else -1, wav=wav, txt=txt)
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                   capture_output=True, timeout=120)
    if not (os.path.exists(wav) and os.path.getsize(wav) > 500):
        raise RuntimeError("tts failed: %s" % text[:60])
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-i", wav,
                    "-c:a", "aac", "-b:a", "96k", "-ar", "44100", out_m4a], check=True)
    for p in (wav, txt):
        try:
            os.remove(p)
        except OSError:
            pass
    return out_m4a
