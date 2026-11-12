import json
import api
import tasks
from util import get

acts = api.cfg["activities"]
pm = tasks.progress_map()
for a in acts:
    if a["type"] != "OralQuestionAnswer":
        continue
    att = pm.get(a["id"], {}).get("attemptId")
    if not att:
        print(a["title"][:30], "no attempt")
        continue
    code, rv = get("orchestration-context/my/contexts/%s/properties/reviewResult" % att)
    try:
        d = json.loads(rv["reviewResult"])
        fr = d.get("finalResult") or {}
        print(a["title"][:30], "score", round(fr.get("score") or 0, 1),
              [(x["title"], round(x["score"], 1)) for x in (fr.get("dimensions") or [])])
    except Exception as e:
        print(a["title"][:30], "n/a", str(rv)[:80])
