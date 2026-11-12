"""从入口 URL 生成 config.json（课程标识 + 活动清单）。"""
import json
import re
from urllib.parse import parse_qs, urlparse

from paths import BASE

cfg_file = BASE / "config.json"
example = json.loads((BASE / "config.example.json").read_text(encoding="utf-8"))
cfg = json.loads(cfg_file.read_text(encoding="utf-8")) if cfg_file.exists() else dict(example)

url = cfg.get("entry_url") or example["entry_url"]
if "entry_url" not in cfg or "?" not in url:
    raise SystemExit("请先在 config.json 里填写 entry_url（浏览器地址栏里 delivery-course-play 那一串）")

q = {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}
parsed = urlparse(url)
cfg.update({
    "origin": "%s://%s" % (parsed.scheme, parsed.netloc),
    "schoolId": q.get("schoolId", ""),
    "courseOfferingId": q.get("courseOfferingId", ""),
    "courseId": q.get("courseId", ""),
    "sectionId": q.get("sectionId", ""),
    "entry_url": url,
})
cfg_file.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
print("已写入 config.json：", {k: v for k, v in cfg.items() if k != "entry_url"})

import api  # noqa: E402  需 config.json 就绪后才能导入

code, txt = api.get("learning-practice/contents-preview/table-of-contents/%s" % cfg["courseId"])
if code != 200:
    raise SystemExit("拉取课程目录失败 %s：%s" % (code, txt[:200]))

tree = json.loads(txt)
rows = []


def walk(ch, root=""):
    for a in ch.get("activities", []):
        rows.append({
            "title": a["title"],
            "id": a["activityId"],
            "type": a["type"],
            "dur": a.get("recommendedDuration"),
            "chapter": root,
        })
    for c in ch.get("childChapters", []):
        walk(c, root + "/" + c["title"])


for ch in tree:
    walk(ch, ch["title"])

cfg["activities"] = rows
cfg_file.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")
print("活动 %d 个：" % len(rows))
for r in rows:
    print("  %-22s %s" % (r["type"], r["title"][:44]))
