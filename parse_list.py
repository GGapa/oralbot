"""解析 course_list.txt，统计完成情况。"""
import re

from paths import BASE

lines = [l.strip() for l in (BASE / "course_list.txt").read_text(encoding="utf-8").splitlines()
         if l.strip()]
rows = []
i = 0
while i < len(lines):
    m = re.match(r"^(\d+\.\d+\.\d+)\s+(.+)$", lines[i])
    if m:
        num, title = m.group(1), m.group(2)
        kind = lines[i + 1] if i + 1 < len(lines) else ""
        btn = ""
        for j in range(i + 2, min(i + 6, len(lines))):
            if lines[j] in ("查看", "开始", "继续", "重做"):
                btn = lines[j]
                break
        rows.append((num, title, kind, btn))
        i += 1
    else:
        i += 1
for r in rows:
    print(r[0], r[3].ljust(3), r[2].ljust(8), r[1][:40])
print("\n完成(查看):", sum(1 for r in rows if r[3] == "查看"), "/", len(rows))
