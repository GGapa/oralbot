import json, time
import api
from util import post, get, upload
from tts import speak
from answers import shot_answer

OFF = api.cfg["courseOfferingId"]
SEC = api.cfg.get("sectionId", "")


def _ids(att, ace):
    """失败时把作答 / 场景执行 id 带出去。这些分支不递交完成，
    服务端那次作答会停留在未关闭状态，人工清理时得有 id 可查。"""
    return "attempt=%s scene=%s" % (att or "-", ace or "-")


def do_situational(act, mode=None, max_shots=40):
    code, preview = get("learning-practice/contents-preview/situational-speaking/%s" % act["id"])
    if code != 200 or not isinstance(preview, dict):
        return "preview-failed %s" % code
    mode = mode if mode is not None else preview.get("trainingMode")
    training_type = {"practice": "Practice", "exam": "Exam"}.get(str(mode).lower())
    if training_type is None:
        return "invalid-training-mode %s" % mode
    mode = training_type.lower()
    code, st = post("learning-practice/attempts/%s/%s/%s/situational" % (OFF, act["id"], mode),
                    {"sectionId": SEC})
    if not 200 <= code < 300 or not isinstance(st, dict) or not st.get("attemptId"):
        return "create-failed %s" % str(st)[:120]
    att = st["attemptId"]
    # The webpage creates the attempt before requesting its scene execution.
    code, sc = post("learning-practice/contents/situational/%s/scene" % act["id"],
                    {"offeringId": OFF, "sectionId": SEC})
    if not 200 <= code < 300 or not isinstance(sc, dict) or not sc.get("sceneId") or not sc.get("activityExecutionId"):
        return "scene-failed %s %s" % (_ids(att, None), str(sc)[:120])
    ace = sc["activityExecutionId"]

    seen = {}
    shots = 0
    answers = 0
    ended = False
    for step in range(max_shots):
        code, ns = get("learning-practice/attempts/situational/%s/next-shot" % ace)
        tries = 0
        while code >= 500 and tries < 6:
            time.sleep(3)
            tries += 1
            code, ns = get("learning-practice/attempts/situational/%s/next-shot" % ace)
        if code != 200 or not isinstance(ns, dict):
            return "next-shot-failed %s %s %s" % (code, _ids(att, ace), str(ns)[:120])
        if ns.get("isEnding"):
            ended = True
            break
        sid = ns.get("shotId")
        if not sid:
            return "next-shot-missing-id %s" % _ids(att, ace)
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
            if not 200 <= code < 300 or not exe:
                return "review-start-failed %s %s" % (code, _ids(att, ace))
            for _ in range(40):
                c2, p = get("orchestration-pipeline/pipeline-executions/%s/progress" % exe)
                if c2 == 200 and isinstance(p, dict):
                    if p.get("status") == "Failed":
                        return "review-failed %s" % _ids(att, ace)
                    if p.get("status") in ("Completed", "Succeeded"):
                        break
                time.sleep(2)
            else:
                return "review-timeout %s" % _ids(att, ace)
            answers += 1
            print("   sit shot %d answered" % (step + 1), flush=True)
        else:
            time.sleep(1)

    if not ended:
        return "scene-not-ended shots=%d answers=%d %s" % (shots, answers, _ids(att, ace))
    code, _ = post("learning-practice/attempts/%s/%s/situational/complete" % (ace, att),
                   {"trainingType": training_type})
    if not 200 <= code < 300:
        return "complete-failed %s %s" % (code, _ids(att, ace))
    return "sit shots=%d answers=%d complete=%s" % (shots, answers, code)
