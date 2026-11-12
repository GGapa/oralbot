"""抓课程列表页，判断每项是「查看」(已完成) 还是「开始」。"""
import json
import time

from playwright.sync_api import sync_playwright

from paths import BASE

cfg = json.loads((BASE / "config.json").read_text(encoding="utf-8"))
entry = cfg["entry_url"]
origin = cfg["origin"] + "/"
ck = json.loads((BASE / "cookies.json").read_text(encoding="utf-8"))

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=False)
    ctx = b.new_context()
    # __Host- 前缀 cookie 必须 host-only，用 url= 不能用 domain=
    ctx.add_cookies([{"name": k, "value": v, "url": origin,
                      "secure": True} for k, v in ck.items()])
    pg = ctx.new_page()
    pg.goto(entry, wait_until="networkidle", timeout=60000)
    time.sleep(5)
    txt = pg.inner_text("body")
    (BASE / "course_list.txt").write_text(txt, encoding="utf-8")
    print(txt[:200])
    b.close()