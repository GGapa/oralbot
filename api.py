"""会话：cookie 注入 + token 自动续期。"""
import json

from urllib.parse import urlparse

import requests

from paths import BASE

CFG_FILE = BASE / "config.json"
COOKIE_FILE = BASE / "cookies.json"

if not CFG_FILE.exists():
    raise SystemExit("缺少 config.json：先复制 config.example.json 并填写 entry_url，再运行 bootstrap.py")

cfg = json.loads(CFG_FILE.read_text(encoding="utf-8"))
if not COOKIE_FILE.exists():
    raise SystemExit("缺少 cookies.json：先运行 login_helper.py 登录一次")

ck = json.loads(COOKIE_FILE.read_text(encoding="utf-8"))
s = requests.Session()
_domain = urlparse(cfg["origin"]).netloc
for k, v in ck.items():
    s.cookies.set(k, v, domain=_domain, path="/")

H = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
base = cfg["origin"] + "/api/"


def save_cookies():
    jar = {c.name: c.value for c in s.cookies if _domain in (c.domain or "")}
    if jar:
        COOKIE_FILE.write_text(json.dumps(jar), encoding="utf-8")


def refresh():
    r = s.post(base + "portal-login/auth/refresh", headers=H, timeout=60)
    if r.status_code == 200:
        save_cookies()
        return True
    return False


def get(p):
    r = s.get(base + p, headers=H, timeout=30)
    if r.status_code == 401 and refresh():
        r = s.get(base + p, headers=H, timeout=30)
    return r.status_code, r.text


if __name__ == "__main__":
    import sys
    if sys.argv[1:2] == ["refresh"]:
        print("refresh", refresh())
    else:
        for p in sys.argv[1:]:
            code, txt = get(p)
            print("==", code, p)
            print(txt[:800])