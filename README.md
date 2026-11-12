# lindge-oral-bot

凌极云（lindgecloud）课程自动化：图文导学、微课、词汇训练、微测验、口语问答、
情景口语（练习 / 实战）全部一键完成。

针对的是 `*.lindgecloud.com/views/course-hub/learning/learning-activities/learning-frame.html`
这套 Vue3 播放器。逆向出的接口、完成判定、上传协议都写在下面，换学校/换课程同样适用。

## 特点

- **不用真挂机**：图文/微课的完成判定只看服务端 KV（`readingDuration` /
  `finishReading` / `isReachDurationTarget` / `finished`），写全即判完成，不必等 5–10 分钟。
- **微测验拿满分**：先随便提交一次，服务端在 `reviewResult.reference` 里回传正确答案，
  重做后按答案提交 → 100 分。
- **语音全自动**：离线 TTS（Windows SAPI，约 1 秒/条）生成 AAC/m4a，按平台上传协议提交，
  走真实语音评测（发音分通常 95+）。
- **断点可续**：按课程目录逐项处理，已完成项自动跳过。

## 环境要求

- Windows（语音用系统 SAPI；其他系统需自行替换 `tts.py`）
- Python 3.10+
- Chrome
- ffmpeg（在 PATH 里，或用环境变量 `FFMPEG` 指定）

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## 使用

1. 复制配置模板，填入入口 URL（浏览器打开课程学习页，地址栏整串复制）：

```bash
copy config.example.json config.json
```

2. 登录一次（会弹出 Chrome，在里面用学校账号登录，成功后自动保存 cookie）：

```bash
.venv\Scripts\python.exe login_helper.py
```

3. 拉取课程目录、生成活动清单：

```bash
.venv\Scripts\python.exe bootstrap.py
```

4. 开跑：

```bash
.venv\Scripts\python.exe run.py                # 补齐所有未完成项
.venv\Scripts\python.exe run.py Quiz           # 只跑微测验
.venv\Scripts\python.exe run.py Oral 3.1       # 只跑 3.1 章口语
.venv\Scripts\python.exe run.py Article 2.1 force   # 强制重跑（会新建 attempt）
```

5. 验收（抓课程列表的「查看 / 开始」）：

```bash
.venv\Scripts\python.exe pw_list.py
.venv\Scripts\python.exe parse_list.py
```

6. 看口语分数：

```bash
.venv\Scripts\python.exe scores.py
```

> 会话约 1 小时过期。掉线就重跑 `login_helper.py`。
> **不要同时开多个脚本**：每个进程都会用 `tera_refresh` 换新 token，
> 并发刷新会让彼此的 refresh token 互相作废。

## 接口速查

前缀 `/api/`。

### 阅读类（图文 / 微课）

```
POST learning-practice/attempts/{off}/{act}/reading             {sectionId, finished:false} -> attemptId
POST learning-practice/attempts/{off}/{act}/{att}/reading/ensure {sectionId}
POST orchestration-context/my/contexts/{att}/timing/heartbeat   {featureCodes:["reading"], expiresIn:3600}
POST orchestration-context/my/contexts/{att}/process-data       {dataType:"KeyValue", kvEntries:{...}}
POST learning-practice/attempts/{att}/reading/complete
```

必须写全 KV：`readingDuration`（字符串秒，≥60）、`finishReading:"true"`、
`isReachDurationTarget:"true"`、`finished:"1"`。

### 词汇训练

```
GET  learning-practice/contents-preview/vocabulary/{act}   -> vocabularies[].{replyId,term}
POST /api/media-evaluation/quick/vocabulary                multipart: language, refText, audio
GET  /api/media-evaluation/quick/vocabulary/{taskId}       -> status Succeeded/Failed
```

### 微测验

```
GET  learning-practice/contents/quiz/{act}/answer          题目（不含答案）
POST learning-practice/attempts/{att}/quiz/complete        {questions:[{itemId,replyId,answer}]}
GET  orchestration-context/my/contexts/{att}/properties/reviewResult
```

`reference` 多选形如 `"A,B,C"`，填空形如 `"ans1|ans2"`（取第一个）。

### 口语问答

```
POST learning-practice/attempts/{off}/{act}/practice/oral   -> attemptId
POST learning-practice/contents/oral/{act}/full              -> activityExecutionId + 题目
POST learning-practice/reviews/oral/{ace}/{recordId}         {record: accessId, contextId}
GET  orchestration-pipeline/pipeline-executions/{exe}/progress
POST learning-practice/attempts/{ace}/{att}/oral/complete    {trainingType:"Practice"}
```

### 情景口语

```
POST learning-practice/contents/situational/{act}/scene      -> activityExecutionId, sceneId
POST learning-practice/attempts/{off}/{act}/practice/situational
GET  learning-practice/attempts/situational/{ace}/next-shot  -> shotId/type/recordId/timeLimit/tip
POST learning-practice/reviews/situational/{ace}/{recordId}  {contextId, record}
POST learning-practice/attempts/{ace}/{att}/situational/complete
```

`next-shot` 幂等：不提交录音就不推进。`Narrative`（`timeLimit=0`）镜再取一次即跳过，
`PureResponse` / `VisualResponse` 需要交录音。偶发 405 是暂时性的，重试即可。

### 音频上传

```
POST /api/repository-blobstore/files/upload
Content-Type: audio/mp4
X-Blob-Original-File-Name: <urlencoded 文件名>
X-Blob-File-Size: <字节数>
body = 原始字节   ->  {accessId}
```

## 文件

| 文件 | 作用 |
|---|---|
| `paths.py` | 项目根目录、ffmpeg 探测 |
| `api.py` | 会话（cookie 注入 + token 自动续期） |
| `util.py` | 请求封装（网络抖动重试、401 自动刷新、blob 上传） |
| `tasks.py` | 微测验 / 阅读类 / 词汇训练 |
| `oral_task.py` | 口语问答；`oral_answers.py` 答案语料 |
| `sit_task.py` | 情景口语 |
| `run.py` | 主入口 |
| `bootstrap.py` | 从入口 URL 生成 `config.json` |
| `login_helper.py` | 人工登录一次，导出 cookie |
| `pw_list.py` / `parse_list.py` | 抓列表页验收 |
| `scores.py` | 读口语评分 |

## 注意

- 仅用于减少重复操作的时间开销，成绩与学习效果仍是自己的事。
- `config.json`、`cookies.json`、`.pw_profile/` 含个人会话与课程信息，已在
  `.gitignore` 中排除，不要提交。
- 平台若改版（接口或完成判定变化），按上面的接口表重新对齐即可。
