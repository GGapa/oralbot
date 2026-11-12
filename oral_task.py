import json, time
import api
from util import post, get, upload
from tts import speak
from oral_answers import for_oral
from answers import round2

OFF = api.cfg["courseOfferingId"]
SEC = api.cfg.get("sectionId", "")


def do_oral(act, block_index, rounds=2, tmpdir="."):
    code, t = post("learning-practice/attempts/%s/%s/%s/oral" % (OFF, act["id"], "practice"),
                   {"sectionId": SEC})
    if not isinstance(t, dict) or not t.get("attemptId"):
        return "create-failed %s" % t
    att = t["attemptId"]
    code, full = post("learning-practice/contents/oral/%s/full" % act["id"],
                      {"offeringId": OFF, "sectionId": SEC})
    if not isinstance(full, dict):
        return "full-failed"
    ace = full["activityExecutionId"]
    qs = []
    for it in full["itemInfos"]:
        for q in it["questions"]:
            qs.append(q)

    done = 0
    for rnd in range(rounds):
        for i, q in enumerate(qs):
            text = for_oral(block_index, i, (q.get("guideSamples") or [{}])[0].get("sentencePattern", ""), q.get("text", ""))
            if rnd > 0:
                text = round2(text)
            path = "%s_o%d_%d.m4a" % (act["id"][:12], rnd, i)
            speak(text, path)
            with open(path, "rb") as f:
                acc = upload(f.read(), "record.m4a")
            code, res = post("learning-practice/reviews/oral/%s/%s" % (ace, q["recordId"]),
                             {"record": acc, "contextId": att})
            exe = res.get("executionId") if isinstance(res, dict) else None
            t0 = time.time()
            for _ in range(25):
                if not exe:
                    break
                c2, p = get("orchestration-pipeline/pipeline-executions/%s/progress" % exe)
                if isinstance(p, dict) and p.get("status") in ("Completed", "Succeeded", "Failed"):
                    break
                time.sleep(1.5)
            done += 1
            print("   oral %d/%d r%d %.1fs" % (i + 1, len(qs), rnd + 1, time.time() - t0), flush=True)

    code, _ = post("learning-practice/attempts/%s/%s/oral/complete" % (ace, att), {"trainingType": "Practice"})
    return "oral q=%d rounds=%d done=%d" % (len(qs), rounds, done)
