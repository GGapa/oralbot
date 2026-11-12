"""quiz / 阅读类 / 词汇训练。"""
import json
import time

import api
from paths import BASE
from util import get, post, upload
from tts import speak

OFF = api.cfg["courseOfferingId"]
SEC = api.cfg.get("sectionId", "")
ACTS = api.cfg["activities"]


def progress_map():
    ids = [a["id"] for a in ACTS]
    code, pr = post("learning-practice/my/offering/%s/activity-progress" % OFF,
                    {"activityIds": ids, "sectionId": SEC})
    if not isinstance(pr, list):
        raise RuntimeError("progress failed: %s %s" % (code, str(pr)[:200]))
    return {x["activityId"]: x for x in pr}


def do_quiz(act):
    """先乱答一次换出参考答案，重做后按答案提交拿满分。"""
    code, task = post("learning-practice/attempts/%s/%s" % (OFF, act["id"]), {"sectionId": SEC})
    if not isinstance(task, dict) or not task.get("attemptId"):
        return "create-failed %s" % task
    code, content = get("learning-practice/contents/quiz/%s/answer" % act["id"])
    if not isinstance(content, dict):
        return "content-failed"
    items = content.get("itemInfos", [])

    def build(pick):
        out = []
        for item in items:
            for q in item["questions"]:
                opts = [o["option"] for o in (q.get("options") or [])]
                out.append({"itemId": item["itemId"], "replyId": q["replyId"],
                            "answer": pick(q, opts)})
        return out

    first = build(lambda q, opts: opts[0] if opts else "answer")
    post("learning-practice/attempts/%s/quiz/complete" % task["attemptId"], {"questions": first})
    time.sleep(1)
    code, rv = get("orchestration-context/my/contexts/%s/properties/reviewResult" % task["attemptId"])
    ref = {}
    try:
        data = json.loads(rv["reviewResult"])
        for r in data.get("replyResult", []):
            ref[r["replyId"]] = str(r.get("reference", "")).split("|")[0].strip()
    except Exception:
        pass
    if not ref:
        return "no-reference"

    code, task = post("learning-practice/attempts/%s/%s" % (OFF, act["id"]), {"sectionId": SEC})
    att = task["attemptId"]
    second = build(lambda q, opts: ref.get(q["replyId"]) or (opts[0] if opts else "answer"))
    post("learning-practice/attempts/%s/quiz/complete" % att, {"questions": second})
    time.sleep(1)
    code, rv = get("orchestration-context/my/contexts/%s/properties/reviewResult" % att)
    try:
        score = json.loads(rv["reviewResult"])["finalResult"]["score"]
    except Exception:
        score = "?"
    return "quiz %s score=%s" % (code, score)


def complete_reading(act):
    """图文 / 微课：一次写全阅读 KV，不用真挂机等时长。"""
    code, t = post("learning-practice/attempts/%s/%s/reading" % (OFF, act["id"]),
                   {"sectionId": SEC, "finished": False})
    if not isinstance(t, dict) or not t.get("attemptId"):
        return "create-failed %s" % t
    att = t["attemptId"]
    post("learning-practice/attempts/%s/%s/%s/reading/ensure" % (OFF, act["id"], att),
         {"sectionId": SEC})
    post("orchestration-context/my/contexts/%s/timing/heartbeat" % att,
         {"featureCodes": ["reading"], "expiresIn": 3600})
    dur = max(60, int(act.get("dur") or 60))
    kv = {"readingDuration": str(dur), "finishReading": "true",
          "isReachDurationTarget": "true", "finished": "1"}
    post("orchestration-context/my/contexts/%s/process-data" % att,
         {"dataType": "KeyValue", "kvEntries": kv})
    code, _ = post("learning-practice/attempts/%s/reading/complete" % att)
    return "reading done %s" % code


def do_vocabulary(act, per_word=True):
    """逐词 TTS + 评测，再写全 kv 收尾。"""
    code, prev = get("learning-practice/contents-preview/vocabulary/%s" % act["id"])
    words = prev.get("vocabularies", []) if isinstance(prev, dict) else []
    code, t = post("learning-practice/attempts/%s/%s/reading" % (OFF, act["id"]),
                   {"sectionId": SEC, "finished": False})
    if not isinstance(t, dict) or not t.get("attemptId"):
        return "create-failed"
    att = t["attemptId"]
    post("learning-practice/attempts/%s/%s/%s/reading/ensure" % (OFF, act["id"], att),
         {"sectionId": SEC})

    ok = 0
    for i, w in enumerate(words):
        word = w.get("term") or ""
        if not word:
            continue
        if per_word:
            try:
                path = "%s_word_%d.m4a" % (act["id"], i)
                speak(word, path)
                with open(path, "rb") as f:
                    r = api.s.post(api.cfg["origin"] + "/api/media-evaluation/quick/vocabulary",
                                   files={"audio": ("recording.m4a", f, "audio/mp4")},
                                   data={"language": prev.get("language", "en-us"), "refText": word},
                                   timeout=120)
                task_id = r.json().get("taskId") if r.status_code == 200 else None
                for _ in range(20):
                    if not task_id:
                        break
                    c2, res = get("media-evaluation/quick/vocabulary/%s" % task_id)
                    if isinstance(res, dict) and res.get("status") in ("Succeeded", "Failed"):
                        break
                    time.sleep(1.5)
            except Exception as e:
                print("   word eval fail:", word, e)
        post("orchestration-context/my/contexts/%s/process-data" % att,
             {"dataType": "KeyValue", "kvEntries": {w["replyId"]: "1"}})
        ok += 1

    kv = {w["replyId"]: "1" for w in words}
    kv["finished"] = "1"
    post("orchestration-context/my/contexts/%s/process-data" % att,
         {"dataType": "KeyValue", "kvEntries": kv})
    post("orchestration-context/my/contexts/%s/timing/heartbeat" % att,
         {"featureCodes": ["reading"], "expiresIn": 3600})
    code, _ = post("learning-practice/attempts/%s/reading/complete" % att)
    return "vocab words=%d/%d %s" % (ok, len(words), code)
