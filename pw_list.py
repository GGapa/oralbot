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
    b = p.chromium.launch(channel="chrome", headless=True)
    ctx = b.new_context()
    # __Host- 前缀 cookie 必须 host-only，用 url= 不能用 domain=
    ctx.add_cookies([{"name": k, "value": v, "url": origin,
                      "secure": True} for k, v in ck.items()])
    pg = ctx.new_page()
    pg.goto(entry, wait_until="domcontentloaded", timeout=60000)
    time.sleep(8)
    txt = pg.inner_text("body")
    (BASE / "course_list.txt").write_text(txt, encoding="utf-8")
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    name = lines[lines.index("课程管理") + 1] if "课程管理" in lines else "?"
    course = lines[lines.index("课程管理") + 2] if "课程管理" in lines else "?"
    print("当前账号：%s ｜ 课程：%s ｜ 列表项：%d 行" % (name, course, len(lines)))
    b.close()