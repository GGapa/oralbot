"""打开浏览器让人工登录一次，成功后导出 cookie。"""
import json
import time
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from paths import BASE

PROFILE = BASE / ".pw_profile"
cfg_file = BASE / "config.json"
example = json.loads((BASE / "config.example.json").read_text(encoding="utf-8"))
cfg = json.loads(cfg_file.read_text(encoding="utf-8")) if cfg_file.exists() else example
entry = cfg.get("entry_url", "")
if "?" not in entry:
    raise SystemExit("请先运行 bootstrap.py 生成 config.json")

STOP = BASE / "login_ok.txt"
if STOP.exists():
    STOP.unlink()

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(str(PROFILE), channel="chrome", headless=False,
                                               args=["--use-fake-ui-for-media-stream"])
    pg = ctx.pages[0] if ctx.pages else ctx.new_page()
    pg.goto(entry, wait_until="domcontentloaded", timeout=60000)
    print("已打开登录页，请在窗口里登录（最多等 15 分钟）", flush=True)
    ok = False
    deadline = time.time() + 900
    while time.time() < deadline:
        time.sleep(3)
        try:
            names = {c["name"] for c in ctx.cookies()}
        except Exception:
            break
        if "tera_session" not in names:
            continue
        try:
            pg.goto(entry, wait_until="networkidle", timeout=60000)
            time.sleep(2)
            body = pg.inner_text("body")[:400]
        except Exception:
            continue
        if "课程内容" in body:
            ok = True
            break
    if ok:
        _domain = urlparse(entry).netloc
        ck = {c["name"]: c["value"] for c in ctx.cookies() if _domain in c.get("domain", "")}
        (BASE / "cookies.json").write_text(json.dumps(ck), encoding="utf-8")
        STOP.write_text("ok", encoding="utf-8")
        print("LOGIN OK，cookie 已保存", flush=True)
    else:
        STOP.write_text("fail", encoding="utf-8")
        print("登录超时", flush=True)
    ctx.close()