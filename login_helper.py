"""打开浏览器让人工登录一次，成功后导出 cookie。

用法：login_helper.py [账号标签]
  每个账号用独立的浏览器 profile（.pw_profile_<标签>），否则持久化 profile 里
  残留的上一个账号会话会让登录判定瞬间通过，导出的是旧账号的 cookie。
  `login_helper.py --reset <标签>` 会先删掉该 profile 再登录。
"""
import json
import shutil
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from paths import BASE, browser_channel

_args = [a for a in sys.argv[1:] if a]
RESET = "--reset" in _args
TAG = "".join(a for a in _args if not a.startswith("--")).strip()
PROFILE = BASE / (".pw_profile_%s" % TAG if TAG else ".pw_profile")
if RESET and PROFILE.exists():
    shutil.rmtree(PROFILE, ignore_errors=True)
    print("已清空 profile：%s" % PROFILE.name, flush=True)
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
    ctx = p.chromium.launch_persistent_context(str(PROFILE), channel=browser_channel(), headless=False,
                                               args=["--use-fake-ui-for-media-stream"])
    pg = ctx.pages[0] if ctx.pages else ctx.new_page()
    pg.goto(entry, wait_until="domcontentloaded", timeout=60000)
    print("已打开登录页，请在窗口里登录（最多等 15 分钟）", flush=True)
    ok = False
    body = ""
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
            pg.goto(entry, wait_until="domcontentloaded", timeout=60000)
            time.sleep(6)
            body = pg.inner_text("body")
        except Exception:
            continue
        if "课程内容" in body:
            ok = True
            break
    if ok:
        _domain = urlparse(entry).netloc
        ck = {c["name"]: c["value"] for c in ctx.cookies() if _domain in c.get("domain", "")}
        (BASE / "cookies.json").write_text(json.dumps(ck), encoding="utf-8")
        # 从页面头部「返回 / 课程管理 / 姓名 / 课程名」里取当前登录人，作为换账号的验收凭据
        lines = [l.strip() for l in body.splitlines() if l.strip()]
        name = lines[lines.index("课程管理") + 1] if "课程管理" in lines else "?"
        (BASE / "account.txt").write_text(name, encoding="utf-8")
        STOP.write_text("ok", encoding="utf-8")
        print("LOGIN OK，当前账号：%s，cookie 已保存，登录窗口将自动关闭" % name, flush=True)
    else:
        STOP.write_text("fail", encoding="utf-8")
        print("登录超时", flush=True)
    ctx.close()
