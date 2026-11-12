"""把题目里的句型模板变成可直接朗读的英文句子。"""
import re

FILL = [
    ("has been affecting my life", "my anxiety about my studies has been affecting my life"),
    ("decided to seek help because", "I realized I could not handle it alone"),
    ("I've been feeling or experiencing", "I have been feeling very stressed and tired"),
    ("It started about", "It started about two months"),
    ("Since then, I've been experiencing", "Since then, I have been experiencing constant worry and poor sleep"),
    ("It has been affecting my", "It has been affecting my study and my sleep"),
    ("The most difficult part has been", "The most difficult part has been waking up with a heavy heart"),
    ("The important people in my life are", "The important people in my life are my parents and two close friends"),
    ("They support me by", "They support me by listening without judging me"),
    ("A typical day for me usually looks like", "A typical day for me usually looks like classes, homework and part time work"),
    ("but recently", "but recently I have felt tired all the time"),
    ("Things that bring me joy are", "Things that bring me joy are playing badminton with friends"),
    ("things that drain me are", "things that drain me are endless deadlines and group projects"),
    ("When changes happen, I usually", "When changes happen, I usually make a small plan and take one step at a time"),
    ("When things are difficult, I usually turn to", "When things are difficult, I usually turn to my roommate and my mother"),
    ("I've tried coping by", "I have tried coping by keeping a journal and running in the evening"),
    ("and it has helped or not helped because", "and it has helped because it clears my head and helps me sleep"),
    ("My strengths are", "My strengths are patience and curiosity"),
    ("people close to me would describe me as", "people close to me would describe me as a reliable and warm person"),
    ("I feel safe and supported when", "I feel safe and supported when my friends listen to me without judging"),
    ("I hope therapy or counselling can help me with", "I hope therapy or counselling can help me with my anxiety and better study habits"),
    ("I'm a bit confused about", "I am a bit confused about how to start reading research papers"),
    ("I have some experience with", "I have some experience with Python and data analysis"),
    ("I'd love to help with", "I would love to help with data labeling and preprocessing"),
    ("I'm from", "I am from Hangzhou, a lively city in the east of China"),
    ("best known for", "it is best known for its beautiful West Lake and rich history"),
    ("I'm closest to", "I am closest to my older sister"),
    ("The main reason is that", "the main reason is that she always listens to me patiently"),
    ("my biggest ambition right now is to", "my biggest ambition right now is to become a data engineer"),
    ("a ton of free time as a", "a ton of free time as a computer science major"),
    ("I usually grab a cup of coffee", "I usually grab a cup of coffee before my morning class"),
    ("I usually just drag myself", "I usually just drag myself out of bed and rush to class"),
]

CN = re.compile(r"[\u4e00-\u9fff，。；：、（）\s]+")


def clean_sample(s):
    s = str(s or "").replace("\n", " ").strip()
    # 方括号里常是中文提示，保留其中的英文示例
    def br(m):
        inner = m.group(1)
        eng = re.sub(r"[\u4e00-\u9fff，。；：、（）]+", " ", inner).strip(" ,")
        return eng if eng else ""
    s = re.sub(r"\[([^\]]*)\]", br, s)
    s = CN.sub(" ", s)
    # 去掉斜杠选项：保留第一项
    s = re.sub(r"\s*/\s*[^/]{1,60}/\s*", " ", s)
    s = re.sub(r"\s*/\s*", " ", s)
    s = re.sub(r"\+[^.]*", " ", s)
    s = re.sub(r"\(\s*\)", " ", s)
    s = re.sub(r"\s{2,}", " ", s).strip(" ,.;:")
    return s


def fill(s):
    out = []
    for chunk in re.split(r"(?<=[.!?])\s+", s):
        c = chunk.strip()
        if not c:
            continue
        if c.endswith("?"):
            out.append(c)
            continue
        hit = None
        for key, rep in FILL:
            if key.lower() in c.lower():
                hit = rep
                break
        if hit:
            out.append(hit)
        elif "..." in c or "…" in c:
            continue
        else:
            out.append(c)
    s = " ".join(out[:3])
    s = s.replace("...", " ").replace("…", " ")
    s = re.sub(r"\b(\w+)( \1\b)+", r"\1", s)      # 去相邻重复词
    s = re.sub(r"\s+([,.;:])", r"\1", s)
    s = re.sub(r"\s{2,}", " ", s)
    s = re.sub(r",\s*,", ",", s)
    return s.strip(" ,.;:")


def answer_for(sample, qtext=""):
    s = clean_sample(sample)
    if not s:
        s = clean_sample(qtext)
    s = fill(s)
    if len(s) < 8:
        s = "Well, I would say that it matters a lot to me and I try to handle it step by step"
    if not s.endswith((".", "?", "!")):
        s += "."
    return s


def round2(text):
    """第二轮：加衔接词，句子稍作变化。"""
    body = text.rstrip(".")
    return "Sure. " + body + ", and that is the main point I want to share."


def shot_answer(tip, subtitles=""):
    """情景口语：优先读参考句式，其次按字幕做通用应答。"""
    t = clean_sample(tip)
    m = re.search(r"(?:参考句式|reference)[:：]\s*(.+)", str(tip or ""))
    if m:
        t = clean_sample(m.group(1))
    if t:
        t = fill(t)
    if len(t) < 8:
        t = "That makes sense. I feel a little nervous, but I really want to talk about it and get some support."
    if not t.endswith((".", "?", "!")):
        t += "."
    return t
