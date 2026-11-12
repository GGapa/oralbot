"""第 1/3 章为"回答型"，第 2/4 章为"提问型"，各章答案不同。"""

ORAL_ANSWERS = {
    0: [  # 1.1.5 心理初诊（扮演小杭）
        "I came here today because I have been feeling very anxious about my studies, and it is affecting my sleep and my mood. I feel like I need some support.",
        "I have been feeling stressed and tired for weeks, and last night I could not sleep at all. I realized that I cannot handle this alone anymore.",
        "It started about two months ago, when the midterm exams began. Since then I have been worrying all the time and I find it hard to concentrate.",
        "It has been affecting my study and my sleep. I wake up at three in the morning, I cannot focus in class, and I have started to avoid my friends.",
        "The important people in my life are my parents and two close friends from my dormitory. They support me by listening to me without judging.",
        "A typical day for me is classes in the morning, homework in the afternoon, and part time work in the evening. But recently I have felt tired all the time.",
        "Things that bring me joy are playing badminton with my friends and listening to music. Things that drain me are endless deadlines and group projects.",
        "When changes happen, I usually make a small plan and take one step at a time. I try to keep my daily routine and I talk to my friends.",
        "When things are difficult, I usually turn to my roommate and my mother. They are patient and they always make me feel calmer.",
        "I have tried coping by keeping a journal and running in the evening. It has helped because it clears my head and helps me sleep.",
        "My strengths are patience and curiosity. People close to me would describe me as a reliable and warm person who never gives up.",
        "I feel safe and supported when my friends listen to me without judging, and when my parents tell me that they are proud of me.",
        "I hope therapy or counselling can help me understand my anxiety and build better study habits, so that I can enjoy my university life again.",
    ],
    1: [  # 2.1.5 Office Hour（向教授提问/表达）
        "I really enjoy your class, and I have become quite interested in research, especially in artificial intelligence and how models explain their decisions.",
        "I am a bit confused about how you evaluate model interpretability. Could you walk me through the way your lab usually does it?",
        "I have some experience with Python, and I have been learning data analysis on my own. I am also comfortable with statistics and basic machine learning.",
        "I would love to help with data labeling and preprocessing. I am open to working for course credit, and I am willing to learn anything the project needs.",
        "I completely understand, Professor. Thank you for being upfront. Could you recommend another professor or a PhD student I could talk to?",
    ],
    2: [  # 3.1.5 雅思口语日常题
        "Sure. I am from Hangzhou, a lively city in the east of China. It is famous for the West Lake, and it is only about an hour from Shanghai by train.",
        "Well, it is best known for the West Lake and its long history. Tourists also come for the tea and the old temples around the lake.",
        "Well, to be honest, I do not have a ton of free time as a computer science major, but when I do, I enjoy playing badminton and reading novels.",
        "I have to admit that I am not a morning person. I usually drag myself out of bed, grab a quick coffee, and rush to my first class.",
        "Without a doubt, I am closest to my older sister. The main reason is that she always listens to me patiently and gives me honest advice.",
        "Yeah, definitely. I would say we get along really well. The main reason is that we often study together and help each other before exams.",
        "Oh, definitely. I am a bit of a coffee person. I usually grab a cup of coffee before my morning class, but I try not to drink it late at night.",
        "Well, my biggest ambition right now is to become a data engineer and work on projects that actually help people learn better.",
    ],
    3: [  # 4.1.5 职业规划（向导师提问）
        "What is the best advice you can give to help me plan a career rather than simply worry about finding a job?",
        "What do you consider most when you plan for your career?",
        "What would you do if you were me, at my stage of study?",
        "How would you describe your personal working style?",
        "What mistakes have you made in your career, and what did you learn from them?",
        "What values are you committed to in the workplace?",
        "Do you have any books or other resources that you would suggest I read?",
        "What do you suggest that I do now as my next step?",
    ],
}


def for_oral(block_index, q_index, sample="", qtext=""):
    lst = ORAL_ANSWERS.get(block_index)
    if lst and q_index < len(lst):
        return lst[q_index]
    from answers import answer_for
    return answer_for(sample, qtext)
