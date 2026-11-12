import json, time
import api
from util import post, get, upload
from tts import speak
from answers import shot_answer

OFF = api.cfg["courseOfferingId"]
SEC = api.cfg.get("sectionId", "")


def do_situational(act, mode="practice", max_shots=40):
    code, sc = post("learning-practice/contents/situational/%s/scene" % act["id"],
                    {"offeringId": OFF, "sectionId": SEC})
    if not isinstance(sc, dict) or not sc.get("sceneId"):
        return "scene-failed %s" % str(sc)[:120]
    ace = sc["activityExecutionId"]
    code, st = post("learning-practice/attempts/%s/%s/%s/situational" % (OFF, act["id"], mode),
                    {"sectionId": SEC})
    if not isinstance(st, dict) or not st.get("attemptId"):
        return "create-failed %s" % str(st)[:120]
    att = st["attemptId"]

    seen = {}
    shots = 0
    answers = 0
    for step in range(max_shots):
        code, ns = get("learning-practice/attempts/situational/%s/next-shot" % ace)
        if not isinstance(ns, dict):
            return "next-shot-failed %s %s" % (code, str(ns)[:120])
        if ns.get("isEnding"):
            break
        sid = ns.get("shotId")
        seen[sid] = seen.get(sid, 0) + 1
        if seen[sid] > 3:
            break
        shots += 1
        rid = ns.get("recordId")
        limit = int(ns.get("timeLimit") or 0)
        if rid and limit > 0:
            text = shot_answer(ns.get("tip", ""), ns.get("subtitles", ""))
            path = "%s_s%d.m4a" % (act["id"][:12], step)
            speak(text, path)
            with open(path, "rb") as f:
                acc = upload(f.read(), "record.m4a")
            code, res = post("learning-practice/reviews/situational/%s/%s" % (ace, rid),
                             {"contextId": att, "record": acc})
            exe = res.get("executionId") if isinstance(res, dict) else None
            for _ in range(40):
                if not exe:
                    break
                c2, p = get("orchestration-pipeline/pipeline-executions/%s/progress" % exe)
                if isinstance(p, dict) and p.get("status") in ("Completed", "Succeeded", "Failed"):
                    break
                time.sleep(2)
            answers += 1
            print("   sit shot %d answered" % (step + 1), flush=True)
        else:
            time.sleep(1)

    code, _ = post("learning-practice/attempts/%s/%s/situational/complete" % (ace, att),
                   {"trainingType": "Practice"})
    return "sit shots=%d answers=%d complete=%s" % (shots, answers, code)
