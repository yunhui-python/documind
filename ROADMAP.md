# 四周作战计划（Week 1–4）

> 目标：四周后你有一个**能跑、能测、能演示、能讲清楚**的项目挂在 GitHub 上，且简历里能写出 3 条有数据支撑的描述。
>
> 时间预算：每天 2–3 小时，周末各 4 小时。合计约 70 小时。
> 如果你每周只有 10 小时，把四周拉成六周，顺序不变。

## 总览

| 周次 | 目标 | 关键产出 | 验收标准（做不到就不算完成） |
| --- | --- | --- | --- |
| Week 1 | 把骨架跑通，读懂每一行 | 本地服务可启动、测试全绿、完成 3 个练习 | `pytest` 全绿且用例数 ≥ 19；`/docs` 里能上传并搜到结果；Git 上有 ≥ 6 次提交 |
| Week 2 | 接入大模型，输出带引用的回答 | `/api/chat` 支持流式、引用溯源、多轮会话 | 能从命令行看到逐字输出的回答，且回答里标了 `[1]` 对应哪个文件第几块；没 API Key 时用假模型也能跑通全流程 |
| Week 3 | 检索升级 + 评测（**简历最硬的部分**） | BM25、混合检索、评测脚本、对比表 | 评测脚本一条命令跑出 Recall@3 / MRR 表格；表里能看出混合检索优于单一检索，并把结论写进 README |
| Week 4 | 工程化 + 上线 | Web 页面、Docker、CI 绿、v1.0.0、Profile README | 别人克隆你的仓库，按 README 三条命令能跑起来；GitHub Actions 显示绿色对勾 |

---

## 定向调整（已确认：AI 应用方向 / 每天 2–3 小时 / 有大模型 API Key）

既然目标是 AI 应用岗，这个项目的重心要往"模型层"偏，而不是往"框架层"偏。具体三处调整：

1. **Week 2 从 3 天扩到 5 天**，多出来的时间给 Prompt 设计、上下文预算、结构化输出和幻觉抑制 —— 这是 AI 应用岗面试的主战场。
2. **Week 3 的评测升为主体**，不只是"跑个表"，还要写清楚"我改了 A，指标涨了 B，因为 C"。AI 应用岗最缺的就是会做实验的人。
3. **Week 4 的 Docker 降级为可选**（你机器没有 Docker），省下的时间做"多轮对话 + 引用溯源"的打磨。

### AI 应用岗必答清单（你的项目要能覆盖前 8 条）

| # | 主题 | 你的项目里对应哪里 |
| --- | --- | --- |
| 1 | 切块策略与块长依据 | `chunking.py` |
| 2 | embedding 选型、维度、归一化 | `embeddings.py` |
| 3 | 相似度度量与 Top-K 取舍 | `retrieval.py` |
| 4 | Prompt 结构与上下文预算（token 怎么省） | Week 2 |
| 5 | 引用溯源、幻觉抑制 | Week 2 |
| 6 | 多轮对话里历史与检索的关系 | Week 2 |
| 7 | 检索评估（Recall/MRR）、实验对比 | Week 3 |
| 8 | 流式输出与首字延迟 | Week 2 |
| 9 | rerank / 查询改写 | 加分项，Week 3 有余力再做 |
| 10 | 成本控制（缓存、批处理、模型分级） | 加分项 |

> AI 应用岗和普通后端岗的差别：后端岗问"你怎么保证服务稳定"，AI 应用岗问"你怎么保证回答是对的"。你项目里所有关于**评测、引用、兜底**的设计，都是为后者准备的。

### 关于 API Key 的安全纪律（第 0 条规则）

- Key 只放 `.env`（已经在 `.gitignore` 里），**永远不要贴到聊天窗口、不要提交、不要截图**；
- 代码里只从环境变量读，绝不硬编码；
- 万一误提交：立刻去控制台吊销重发，别指望 `git rm` 能救 —— Git 历史里删不掉；
- 面试演示时如果要用自己的 Key，提前用 `DOCUMIND_LLM_MODEL` 切到便宜的小模型。

---

## Week 1：把骨架跑通（当前阶段）

我已经把 Week 1 的代码写完了，你要做的是**把它变成你的**。

### 任务 1.1 环境跑通（约 1 小时）

```powershell
cd D:\deepseek_woke\work1\documind
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
python -m uvicorn app.main:app --reload
```

- 浏览器打开 <http://127.0.0.1:8000/docs>，用 `POST /api/documents/text` 传一篇文档，再用 `POST /api/search` 搜。
- **验收**：`pytest` 显示全部通过；能在 `/docs` 里搜出结果。

### 任务 1.2 读懂代码 → 改得动代码（分四档台阶）

> 第一版计划是"读完 6 个文件再写练习"，实测跨度太大：读得懂 ≠ 写得出。
> 现在改成台阶式，每一档都有可验证的产出，**卡住随时停下，不用爬完**。

**第 0 档：语法对齐（约 30 分钟）**

跑练习册，把项目里用到的语法在"孤立环境"里先写一遍：

```powershell
.\.venv\Scripts\python.exe scripts\workbook_01.py
```

10 道题，从切片到"把单元装进块"，全部是 `split_text` 的零件。看到 `[OK]` 才算过。
写不出来就查 [Python基础自查表](docs/Python基础自查表.md) 对应条目，别看 `chunking.py` 抄。

**第 1 档：读一个函数（约 30 分钟）**

只读 `app/chunking.py` 的 `split_text`（第 69–88 行，20 行），对照
`python scripts\explore_chunking.py` 的输出。读完能回答：

- 为什么先按段落切？`buffer[-overlap:]` 在干什么？如果把 `overlap` 设成 400、`size` 是 500 会怎样？

**第 2 档：改一个数字（约 20 分钟）**

把 `app/main.py` 上传接口里的 `settings.chunk_size` 临时换成 150（或改 `.env` 里的
`DOCUMIND_CHUNK_SIZE`），重启服务，重新上传同一篇文档，看 `chunks` 从 1 变成几。
**这一档的目的：建立"改一处 → 影响哪一处"的直觉。**

**第 3 档：写一行逻辑（约 20 分钟）**

在 `split_text` 收尾处（`if buffer: chunks.append(buffer)` 上面）加一句打印：

```python
        print(f"[调试] 收尾时 buffer 长度={len(buffer)}")
```

跑一遍测试，看打印出来几次、每次多长。**这一档的目的：学会用打印观察中间状态**，这是调试的第一步。

**第 4 档：写一个新参数（约 60 分钟）**

回到练习册的 `e7_merge_tail`，把逻辑写对；然后原样搬进 `split_text`，加 `min_size` 参数，
让 `tests/test_exercises.py` 的前两个用例转正。

---

其余文件的阅读放到之后，边做边读：

1. `app/embeddings.py` —— 为什么中文要切"双字"？归一化之后为什么余弦相似度可以用点积算？
2. `app/db.py` —— 为什么每次操作都新开连接而不是共用一个？`PRAGMA foreign_keys = ON` 不加会怎样？
3. `app/retrieval.py` —— 为什么用 `array('f')` 存向量而不是 JSON？
4. `app/main.py` —— `create_app(settings)` 这种工厂写法对测试有什么好处？

### 任务 1.3 三个练习（约 6 小时，要自己写）

验收标准已经写进代码了：`tests/test_exercises.py`，一共 4 个用例，现在全是 `xfail`（预期失败）。
你实现一个，跑一次 `python -m pytest tests/test_exercises.py`，对应用例会从 `xfailed` 变成 `XPASS`。
**XPASS 报错不是在说你写错了**，是提醒你把那个 `@pytest.mark.xfail` 装饰器删掉，让它变成正式测试。

**练习 A：加入"最小块长"，消灭碎块**
现状：如果最后一段只剩 10 个字，它会单独成为一块，检索时几乎不可能被命中。
要求：给 `split_text` 增加参数 `min_size: int = 0`；封块（以及收尾）时，若某块长度 < `min_size`，把它并入前一块 ——
允许前一 block 略超 `size`（超的幅度不会超过 `min_size`，这是可接受的取舍）。
注意保持向后兼容：`min_size=0`（默认值）时行为必须和现在完全一致。

**练习 B：支持 PDF**
要求：`pip install pypdf` 并加进 `pyproject.toml` 依赖；`ALLOWED_SUFFIXES` 加上 `.pdf`；按后缀分流，PDF 用 `pypdf.PdfReader` 逐页提取文本再拼接。
两个边界必须处理：扫描版 PDF 提取出来是空的 → 返回 400 并说明"可能是扫描版"；文件损坏 → 同样返回 400 而不是 500。
自己找一份真 PDF 手动验证一遍（学校课表、论文都行）。

**练习 C：检索接口支持按文档过滤**
`retrieval.search()` 已经支持 `document_id` 参数了，但 API 层没暴露。
要求：给 `SearchIn` 加可选字段 `document_id`，透传给 `search()`。
想一想：如果传了一个不存在的 `document_id`，应该返回空列表还是 404？（两种都合理，选一个并把理由写在注释里）

### 任务 1.4 让提交记录像"真的在开发"（约 1 小时）

不要一次性 `git add .` 提交成"完成"。按功能拆分，至少 6 次提交：

```
feat: 初始化 FastAPI 项目骨架
feat: 实现按段落切块与重叠逻辑
feat: 加入零依赖哈希向量化基线
feat: 实现余弦相似度检索接口
test: 补充切块边界条件与检索排序测试
feat: 切块增加最小块长合并逻辑
```

格式：`类型: 说明`，类型用 `feat` / `fix` / `test` / `docs` / `refactor` / `chore`。

### 任务 1.5 记录疑问

新建 `NOTES.md`（不用提交），每天记下 3 个"我还没搞懂的点"。攒着一次性问我，比一个个问效率高。

---

## Week 2：接入大模型，让回答带出处

本周的核心不是"调通 API"，而是**控制幻觉**：模型只能基于检索到的文本回答，且每个结论都要能指回原文。

### 关于 DeepSeek（已确认，配置已写进 `.env.example`）

| 项 | 值 | 说明 |
| --- | --- | --- |
| `DOCUMIND_LLM_BASE_URL` | `https://api.deepseek.com/v1` | 兼容 OpenAI 的 `/chat/completions` |
| `DOCUMIND_LLM_MODEL` | `deepseek-chat` | RAG 问答用这个 |
| `DOCUMIND_LLM_TEMPERATURE` | `0.1` | 要"照资料说"，温度低更稳定 |
| `DOCUMIND_LLM_MAX_TOKENS` | `1024` | 控制成本和延迟 |

**为什么不用 `deepseek-reasoner`**：它是推理模型，会先输出一大段"思考过程"再给答案，首字延迟和成本都高好几倍。
RAG 要的是"照着资料复述 + 引用"，不是"长时间推理"。面试被问到模型选型，这就是个好答案：
**按任务选模型，不是按"哪个更强"选。**

**一个重要前提**：DeepSeek 目前只提供对话模型，**没有 embedding 接口**。
所以 Week 3 要换成"真实向量"时得另找方案，两条路任选：

- 本地跑 `sentence-transformers` 的中文模型（如 `BAAI/bge-small-zh-v1.5`），零成本，但要下载 100MB 左右，CPU 能跑；
- 用硅基流动 / 阿里百炼 / 智谱的 embedding 接口，按量计费，几毛钱。

这也正是 Week 1 先做"零依赖哈希基线"的用意：**把链路和测试先立住，换模型时只改一个类**。
到时候你会真切体会到"面向接口编程"不是一句口号。

**成本提醒**：`deepseek-chat` 很便宜，但 Week 3 评测要跑 30 题 × 每题一次生成，
把 `MAX_TOKENS` 控制在 512~1024，一次全量评测通常不到一块钱。

### 任务 2.1 抽象 LLM 客户端（你写，我给结构）

`app/llm.py`：

```python
class LLM(Protocol):
    name: str
    def chat(self, messages: list[dict]) -> str: ...          # 一次性返回
    def stream(self, messages: list[dict]) -> Iterator[str]: ...  # 逐段返回

class FakeLLM:      # 没有 API Key 时用，测试和 CI 都靠它
class OpenAICompatibleLLM:  # 任何兼容 /v1/chat/completions 的服务都能接
```

要点：没配 `DOCUMIND_LLM_API_KEY` 时自动降级到 `FakeLLM`（返回"根据检索到的内容……"的模板串）。**这样别人 clone 下来不配 Key 也能跑通**，这是作品集项目很重要的细节。

### 任务 2.2 Prompt 与引用（你写，这是本周的核心）

`app/qa.py`：把 Top-K 块拼成带编号的上下文：

```
[1] 文件：向量检索笔记.md（第 0 块）
<文本>

[2] 文件：红烧肉.txt（第 3 块）
<文本>
```

System prompt 必须包含这几条约束（自己写一版，然后我们改）：
- 只依据给定资料回答，资料里没有就说"资料中未提及"，不要编；
- 引用时用 `[编号]` 标注出处；
- 用中文回答，简洁。

### 任务 2.3 流式接口

`POST /api/chat`，响应 `text/event-stream`。
FastAPI 里用 `StreamingResponse` + 生成器。前端（或 curl）能逐字看到输出。
**验收**：`curl.exe -N -X POST ...` 能看到文字一段段冒出来，而不是等 10 秒一次性出现。

### 任务 2.4 多轮会话

新增两张表：`sessions`、`messages`（`session_id`、`role`、`content`、`created_at`）。
每次提问带上最近 N 轮（比如 3 轮）历史拼进 messages，但**检索只用当前问题**（用历史去检索会把上一轮的话题带进来，效果反而差 —— 这个取舍要能讲）。

### 任务 2.5 补测试

- `FakeLLM` 下：`/api/chat` 返回 200，内容包含 `[1]`
- 空知识库时提问：返回明确的"没有相关资料"，而不是让模型瞎编
- 会话记忆：同一 session 连续两轮，第二轮能看到第一轮内容

---

## Week 3：检索升级与评测（简历的胜负手）

绝大多数人做到 Week 2 就发仓库了。**你比他们多的就是这一周。**

### 任务 3.1 实现 BM25

`app/bm25.py`，纯 Python 实现（约 60 行）：
- 统计词频 TF、文档频率 DF、平均长度；
- 公式：`score = Σ idf(t) * (tf * (k1+1)) / (tf + k1 * (1 - b + b * dl/avgdl))`，`k1=1.5`、`b=0.75`；
- 复用 `embeddings.tokenize` 的分词。

要能解释：BM25 的 `k1` 控制"词频饱和"、`b` 控制"长度归一化"强度。

### 任务 3.2 混合检索（RRF 融合）

`app/hybrid.py`：分别取向量检索 Top-20 和 BM25 Top-20，用 Reciprocal Rank Fusion 合并：

```
score(d) = Σ  1 / (k + rank_i(d))     # k 取 60
```

为什么用 RRF 而不是把两个分数加权平均？—— 两路分数量纲不同（余弦是 0~1，BM25 是无上界的实数），直接加权需要调参且不稳；RRF 只用排名，天然可比。**这句话面试能直接说。**

### 任务 3.3 建评测集

`eval/dataset.jsonl`，每行一条：

```json
{"question": "向量检索是怎么算相似度的？", "expected_document": "向量检索笔记.md"}
```

规模：30 条左右，覆盖三类问题 —— 能直接答的、需要跨块的、资料里压根没有的（考察是否会说"未提及"）。
自己出题最有价值：用你们专业的课程资料、或者拿 3–5 篇技术博客当语料。

### 任务 3.4 写评测脚本

`eval/run_eval.py`，输出：

```
策略            Recall@3    Recall@5    MRR
----------------------------------------------
仅向量检索        0.70        0.83       0.61
仅 BM25          0.73        0.87       0.64
混合检索(RRF)     0.87        0.93       0.78
```

指标定义要能讲清楚：
- **Recall@K**：正确答案所在文档，出现在前 K 条结果里的比例；
- **MRR**：正确答案排名的倒数的平均值，越靠前越高。

### 任务 3.5 把结论写回 README

一句话结论 + 表格 + 一句"为什么混合检索更好"（关键词精确匹配和语义泛化互补）。
**这就是简历里"通过实验验证……提升了 X%"的来源，数字一定要是你自己跑出来的。**

---

## Week 4：工程化与上线

### 任务 4.1 一个能看的界面

`app/static/index.html`，单文件，不引框架：上传框 + 提问框 + 结果区（显示回答和引用卡片）。用 `fetch` 调你的接口，流式部分用 `ReadableStream` 读。

### 任务 4.2 Docker 化

```powershell
docker build -t documind .
docker run -p 8000:8000 -v documind-data:/data documind
```

你机器现在没装 Docker：可以装 Docker Desktop 验证，也可以只在 README 里标注"未在本机验证"（诚实比吹牛重要）。

### 任务 4.3 仓库精修

- README 顶部放一张演示 GIF（用 ScreenToGif 录 15 秒：上传 → 提问 → 流式回答）；
- 架构图、评测表格、项目亮点、快速开始四件套齐全；
- 仓库右侧 About 填简介 + topics：`python` `fastapi` `rag` `llm` `vector-search` `sqlite`；
- 打 tag：`git tag -a v1.0.0 -m "首个可用版本" && git push --tags`，再去 Releases 写发布说明。

### 任务 4.4 Profile README

新建一个和用户名同名的仓库（比如用户名 `zhangsan`，就建 `zhangsan`），里面的 `README.md` 会显示在你的主页顶部。模板：

```markdown
### 你好，我是 XXX 👋

2026 届计算机科学与技术毕业生，主要方向是 Python 后端开发。

**技术栈**：Python · FastAPI · SQLite/PostgreSQL · Docker · pytest · Git

**代表项目**
- [DocuMind](https://github.com/你的用户名/documind) —— 可评测的文档智能问答服务
  FastAPI + 自实现向量检索 + 混合检索（RRF），Recall@5 从 0.83 提升到 0.93

📫 联系我：你的邮箱
```

---

## GitHub 上线七步（Week 1 结束就可以先做前 5 步）

### 1. 注册账号后期检查

- 用户名用真名拼音或 `名字-python` 这类专业组合，**别用** `qq123456`、`xiaoming2003` 这种；
- 头像换成正经照片或简洁图形；
- 个人资料里填 Name、Bio（"Python backend developer · 2026 graduate"）、Location。

### 2. 配置 Git 身份（只需一次）

```powershell
git config --global user.name "你的名字"
git config --global user.email "你的GitHub邮箱"
git config --global init.defaultBranch main
```

邮箱建议用 GitHub 提供的隐私邮箱（Settings → Emails → Keep my email addresses private），避免真实邮箱被抓取。

### 3. 本地初始化仓库

```powershell
cd D:\deepseek_woke\work1\documind
git init
git add .
git commit -m "chore: 初始化 DocuMind 项目骨架"
git branch -M main
```

### 4. 在 GitHub 网页新建仓库

- 名字 `documind`，**Public**（私有仓库招聘方看不到，等于没做）；
- 不要勾选 "Add a README"（本地已经有了，勾了会冲突）；
- 创建后复制它给的 HTTPS 地址。

### 5. 关联并推送

```powershell
git remote add origin https://github.com/你的用户名/documind.git
git push -u origin main
```

第一次推送会弹窗要凭据：用 **Personal Access Token**（GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token，勾 `repo` 权限），当成密码粘贴。
或者配 SSH Key（一劳永逸，步骤多）：

```powershell
ssh-keygen -t ed25519 -C "你的邮箱"
# 一路回车，然后把 C:\Users\你的用户名\.ssh\id_ed25519.pub 的内容贴到
# GitHub → Settings → SSH and GPG keys → New SSH key
```

### 6. 看 CI 有没有变绿

推送后进仓库的 **Actions** 标签页。第一次大概率失败 —— **这是好事**，改到绿为止的过程本身就是你在学 CI。常见失败原因：依赖没声明全、测试里有硬编码路径、ruff 报了格式问题。

### 7. 每周至少推 2 次

招聘方会看提交时间线。四周内断断续续 20+ 次提交，比最后一天推 3000 行可信得多。

---

## 简历怎么写这段

写在"项目经历"第一段，3–4 条，每条都是"做了什么 + 怎么做 + 结果"：

> **DocuMind · 可评测的文档智能问答服务**（个人项目，2026.10–2026.11）
> 技术栈：Python 3.12 / FastAPI / SQLite / pytest / GitHub Actions / Docker
> - 设计并实现文档问答服务：文档按语义段落切块并保留 15% 重叠，向量化后以 float32 二进制存入 SQLite，提供上传、检索、删除等 6 个 REST 接口，接口文档由 OpenAPI 自动生成。
> - 自研 BM25 与向量检索的混合召回，采用 RRF 融合两路排名，避免不同分数量纲带来的调参问题；在 30 条自建评测集上，Recall@5 由 0.83 提升至 0.93，MRR 由 0.61 提升至 0.78。
> - 通过 Prompt 约束 + 引用溯源（回答标注来源文件与块序号）抑制模型幻觉，资料未覆盖时明确回复"未提及"而非编造。
> - 建立 pytest 测试体系（切块边界、检索排序、接口鉴权与错误码共 19 个用例）并接入 GitHub Actions 做多版本 Python 矩阵构建，主干分支保持全绿。

**注意**：数字必须是你自己跑出来的。面试官一句"这个 0.93 是怎么算的"就能验证真假。

---

## 面试高频问题（务必能答，答不上就回去改代码）

1. 为什么要切块？块长设 500 的依据是什么？换成 200 或 2000 会怎样？
2. 为什么块之间要重叠？重叠太大会有什么副作用？
3. 余弦相似度和欧氏距离有什么区别？为什么这里用余弦？
4. 你用的 embedding 是怎么来的？为什么先做哈希基线再换模型？
5. BM25 和向量检索各自擅长什么？RRF 为什么比加权平均好？
6. Recall@K 和 MRR 的区别？你的评测集怎么构造的？30 条够吗？
7. 怎么防止模型胡说八道？如果检索没召回正确内容，模型还能答对吗？
8. 你的检索是纯 Python 暴力扫描，语料涨到 100 万块怎么办？（答：pgvector / FAISS / 分层索引）
9. 为什么用 SQLite？什么情况下你会换成 PostgreSQL？（并发写、多实例部署）
10. `create_app(settings)` 这种工厂写法解决了什么问题？
11. 讲一个你调试最久的 bug。（自己攒素材，最好是真事）
12. 如果要把这个项目做成多用户 SaaS，你会改哪几处？

---

## 每日节奏建议

| 时段 | 内容 |
| --- | --- |
| 前 20 分钟 | 复习昨天写的代码，跑一遍测试 |
| 主时段 90 分钟 | 做当天任务卡（写代码为主，卡住超过 20 分钟就记下来问我） |
| 收尾 10 分钟 | 提交代码（哪怕只改了一个测试），在 NOTES.md 记 3 个疑问 |
