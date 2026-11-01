# DocuMind · 可评测的文档智能问答服务

[![CI](https://github.com/yunhui-python/documind/actions/workflows/ci.yml/badge.svg)](https://github.com/yunhui-python/documind/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

> 上传文档 → 自动切块建索引 → 用自然语言提问 → 得到**带引用来源**的回答。

一个面向求职作品集的 Python 全栈项目：FastAPI 后端 + SQLite 存储 + 自实现向量检索 + 可插拔大模型 + 检索效果评测 + GitHub Actions CI。

**为什么这个项目值得写进简历**：市面上的 RAG demo 大多只是"调个 API 拼个 prompt"，跑通就发。
这个项目刻意补上了工程侧的三件事 —— 可测试（pytest 覆盖切块/检索/接口）、可衡量（Recall@K、MRR 评测脚本）、可复现（一条命令起服务 + CI 全绿）。面试时这三件事才是能聊下去的部分。

---

## 功能

| 功能 | 状态 |
| --- | --- |
| 文档上传（`.txt` / `.md` 等文本格式） | ✅ 已实现 |
| 按段落切块 + 重叠（overlap）防截断 | ✅ 已实现 |
| 零依赖哈希向量化基线（离线可用） | ✅ 已实现 |
| 余弦相似度语义检索 + 分数排序 | ✅ 已实现 |
| 文档列表 / 删除（级联清理文本块） | ✅ 已实现 |
| 引用溯源（回答里标注出自哪个文件第几块） | 🚧 Week 2 |
| 接入真实大模型 + SSE 流式输出 | 🚧 Week 2 |
| 多轮对话记忆 | 🚧 Week 2 |
| BM25 + 向量混合检索（RRF 融合） | 🚧 Week 3 |
| 检索评测（Recall@K / MRR）与对比实验 | 🚧 Week 3 |
| 简易 Web 界面、Docker 化 | 🚧 Week 4 |

---

## 架构

```
                    ┌──────────────────────────────────────────┐
   HTTP 请求  ────▶ │  FastAPI (app/main.py)                    │
                    │  路由 / 参数校验 / 错误码                  │
                    └───────────────┬──────────────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
    ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
    │ chunking.py      │  │ embeddings.py    │  │ retrieval.py     │
    │ 按段落切块+重叠   │  │ 文本→向量         │  │ 余弦相似度 Top-K  │
    └──────────────────┘  │ (可插拔 Embedder) │  └────────┬─────────┘
                          └──────────────────┘           │
              ┌───────────────────────────────────────────┘
              ▼
    ┌──────────────────────────────────────────────────────────┐
    │ db.py · Repository（SQLite）                              │
    │  documents 表 ── 一对多 ──▶ chunks 表(text + embedding BLOB) │
    └──────────────────────────────────────────────────────────┘
```

**数据流**：文件字节 → 解码成文本 → 切块 → 每块向量化 → 存 `chunks.embedding`（float32 BLOB）；
查询时把问题向量化，与所有块的向量算余弦相似度，取 Top-K。

---

## 技术选型与理由

| 选择 | 理由 |
| --- | --- |
| **FastAPI** | 自带 OpenAPI 文档（`/docs` 可直接试接口）、Pydantic 做参数校验、原生 async —— 是当前 Python 后端岗位出现频率最高的框架之一 |
| **SQLite** | 单文件、零部署，一条命令就能跑起来。本项目数据量撑死几万块，上 PostgreSQL 是过度设计 |
| **自己实现余弦检索** | 几千个块用纯 Python 暴力扫描只要几十毫秒，没必要引向量库。顺便能讲清楚"向量检索到底是什么" |
| **HashingEmbedder 基线** | 不依赖模型和网络，CI 里也能跑，且方便和真实 embedding 做效果对比 |
| **pytest + GitHub Actions** | 让"代码是能跑的"有客观证据，而不是靠嘴说 |

---

## 快速开始（Windows）

前置：Python 3.12+（本项目在 3.14 上验证过）。

```powershell
# 1. 进入项目目录
cd D:\deepseek_woke\work1\documind

# 2. 创建虚拟环境（第一次执行）
py -m venv .venv

# 3. 激活虚拟环境（每次打开新终端都要执行）
.\.venv\Scripts\Activate.ps1
# 如果提示"禁止运行脚本"，先执行这一行，再重新激活：
# Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# 4. 安装依赖
python -m pip install -e ".[dev]"

# 5. 启动服务
python -m uvicorn app.main:app --reload
```

打开 <http://127.0.0.1:8000/docs> 就是交互式接口文档，点 "Try it out" 就能直接调接口。

### 跑一遍试试

最省事的方式：打开 <http://127.0.0.1:8000/docs>，展开 `POST /api/documents/text` → 点 "Try it out" → 填 JSON → Execute。

命令行方式（Windows 上中文容易乱码，所以把 JSON 写成 UTF-8 无 BOM 文件再发）：

```powershell
$json = '{"name":"笔记.md","text":"向量检索把文本映射成向量，用余弦相似度衡量语义接近程度。"}'
[IO.File]::WriteAllText("$PWD\body.json", $json, [Text.UTF8Encoding]::new($false))

curl.exe -X POST http://127.0.0.1:8000/api/documents/text -H "Content-Type: application/json" --data-binary "@body.json"

$query = '{"query":"向量检索原理","top_k":3}'
[IO.File]::WriteAllText("$PWD\body.json", $query, [Text.UTF8Encoding]::new($false))
curl.exe -X POST http://127.0.0.1:8000/api/search -H "Content-Type: application/json" --data-binary "@body.json"
```

### 第一次上手：在 `/docs` 页面点一遍（不用命令行）

`/docs` 是 FastAPI 根据代码自动生成的接口文档，**能直接当客户端用**。顺序是"先入库，再检索"：

**第 1 步：上传文档**

1. 点开 `POST /api/documents` 这一行 → 点右上角 **Try it out**
2. `file` 那一栏点 **Choose File**，选项目里的 `examples/01-向量检索原理.md`
3. 点蓝色 **Execute**
4. 往下看 **Server response**，`Code` 是 **201** 就成功了，`Response body` 里能看到
   `{"document_id": 1, "chunks": 1, ...}` —— `chunks` 表示这篇文档被切成了几块

**第 2 步：检索**

1. 点开 `POST /api/search` → **Try it out**
2. 请求体里本来是 `{"query": "string", "top_k": 5}`，把 `"string"` 换成你的问题，例如
   `{"query": "向量为什么要做归一化", "top_k": 3}`
3. 点 **Execute**，看 `Response body` 里的 `hits` 数组

`hits` 里每条的含义：`score` 是相似度（0~1，越大越像）、`document_name` 是来源文件、
`ordinal` 是这篇文档的第几块、`text` 是命中的原文。

**JSON 只要记住三条语法**：字符串用双引号、键值对之间用逗号、最后一项后面不能有逗号。
写错了不会崩，会返回 **422**，报错信息里会指出是第几个字符有问题。

**推荐先试这三个问题**（配合 `examples/` 里的三篇文档）：

| 问题 | 应该命中 |
| --- | --- |
| `k1 参数是干什么的` | `02-BM25关键词检索.md` |
| `向量为什么要做归一化` | `01-向量检索原理.md` |
| `Recall@K 是什么意思` | `03-RAG工程实践.md` |

然后试试 `怎么防止模型胡说八道` —— 你会发现它命中了错的那篇。
这不是 bug，是当前哈希基线的真实水平：**它只会字面匹配，换个说法就失手**。
这正是 Week 3 要量化解决的问题，也是你简历里那句"提升了 X%"的来源。

**常见状态码**：`200` 查询成功 / `201` 创建成功 / `400` 内容有问题 / `413` 文件超 5MB /
`415` 格式不支持 / `422` 请求参数格式错误。

### 在 IDEA / PyCharm 里打开

- **IDEA Ultimate**：`File → Open` 选中 `documind` 文件夹；然后 `File → Project Structure → Project SDK → Add SDK → Python SDK → Existing`，选 `documind\.venv\Scripts\python.exe`。
- **IDEA Community 没有 Python 支持**（装了 Python 插件也没用）。请改用免费的 **PyCharm Community** 或 **VS Code + Python 扩展**，用同样的方式指定 `.venv` 里的解释器。
- 指定解释器后，`app/main.py` 里 `from .chunking import ...` 这种相对导入才能被正确解析，右键 `tests/` 目录可以直接运行 pytest。

### 运行测试

```powershell
python -m pytest
```

### 代码风格检查

```powershell
python -m ruff check .
```

---

## 接口一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查，返回文档数、块数、当前 embedding 实现 |
| POST | `/api/documents` | 上传文本文件（multipart/form-data，字段名 `file`） |
| POST | `/api/documents/text` | 以 JSON 提交文档正文 |
| GET | `/api/documents` | 文档列表（含每篇的块数） |
| DELETE | `/api/documents/{id}` | 删除文档，级联删除其所有块 |
| POST | `/api/search` | 语义检索，返回 Top-K 块与相似度分数 |

---

## 目录结构

```
documind/
├── app/
│   ├── config.py       # 配置（环境变量）
│   ├── chunking.py     # 切块：段落优先 + 滑动窗口 + 重叠
│   ├── embeddings.py   # 向量化（Embedder 协议 + 哈希基线）
│   ├── retrieval.py    # 向量序列化 + 余弦检索
│   ├── db.py           # SQLite 访问层 Repository
│   └── main.py         # FastAPI 路由与依赖装配
├── tests/
│   ├── conftest.py     # 临时数据库 + 测试客户端 fixture
│   ├── test_chunking.py
│   └── test_api.py     # 走完整 HTTP 链路的集成测试
├── .github/workflows/ci.yml
├── Dockerfile
├── pyproject.toml
└── ROADMAP.md          # 四周开发计划与验收标准
```

---

## 开发计划

见 [ROADMAP.md](ROADMAP.md)：Week 1 骨架跑通 → Week 2 接大模型与流式回答 → Week 3 混合检索与评测 → Week 4 工程化与发布。

## 许可证

[MIT](LICENSE)
