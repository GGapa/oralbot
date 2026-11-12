import json
import sys
import time

import api
import tasks
import oral_task
import sit_task

ACTS = api.cfg["activities"]
ORAL_IDX = {}
n = 0
for a in ACTS:
    if a["type"] == "OralQuestionAnswer":
        ORAL_IDX[a["id"]] = n
        n += 1


def status_of(a, pm):
    x = pm.get(a["id"], {})
    return x.get("status", "NOT_DONE")


def handle(a, pm):
    st = status_of(a, pm)
    t = a["type"]
    print("[%s] %s (%s)" % (st, a["title"][:38], t), flush=True)
    if t == "Quiz":
        return tasks.do_quiz(a)
    if t == "Article" or t == "MicrolectureVideo":
        return tasks.complete_reading(a)
    if t == "VocabularyTraining":
        return tasks.do_vocabulary(a)
    if t == "OralQuestionAnswer":
        return oral_task.do_oral(a, ORAL_IDX.get(a["id"], 0))
    if t == "SituationalSpeaking":
        return sit_task.do_situational(a)
    return "skip"


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    chapter = sys.argv[2] if len(sys.argv) > 2 else ""
    force = len(sys.argv) > 3 and sys.argv[3] == "force"
    pm = tasks.progress_map()
    todo = [a for a in ACTS if force or status_of(a, pm) != "COMPLETED"]
    if only:
        todo = [a for a in todo if only.lower() in a["type"].lower()]
    if chapter:
        todo = [a for a in todo if a["title"].startswith(chapter)]
    print("待处理 %d 个活动\n" % len(todo), flush=True)
    for i, a in enumerate(todo, 1):
        print("=== %d/%d" % (i, len(todo)), flush=True)
        try:
            r = handle(a, pm)
        except Exception as e:
            r = "ERROR %s" % e
        print("   ->", r, flush=True)
        time.sleep(1)
    print("\n等待状态结算...", flush=True)
    time.sleep(45)
    pm = tasks.progress_map()
    left = [a for a in ACTS if status_of(a, pm) != "COMPLETED"]
    print("剩余未完成 %d 个:" % len(left), flush=True)
    for a in left:
        print("  -", status_of(a, pm), a["title"][:44], flush=True)


if __name__ == "__main__":
    main()
