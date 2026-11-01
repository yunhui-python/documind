"""环境体检：一条命令看清"我现在到底处于什么状态"。

在项目根目录运行：
    .\\.venv\\Scripts\\python.exe scripts\\check_setup.py

它只读不写，不会改动你的数据。看不懂某一行就整段发我。
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def check_python() -> None:
    print("【1】Python 环境")
    print(f"    解释器   : {sys.executable}")
    print(f"    版本     : {sys.version.split()[0]}")
    in_venv = sys.prefix != sys.base_prefix
    print(f"    虚拟环境 : {'是' if in_venv else '否  ← 建议先 .\\.venv\\Scripts\\Activate.ps1'}")
    print(f"    当前目录 : {Path.cwd()}")
    if Path.cwd() != ROOT:
        print(f"    ⚠ 建议在项目根目录运行：{ROOT}")


def check_env_file() -> None:
    print("\n【2】.env 文件")
    env_path = ROOT / ".env"
    if not env_path.exists():
        print("    不存在  ← 先执行：Copy-Item .env.example .env")
        return

    from dotenv import dotenv_values

    values = {k: v for k, v in dotenv_values(env_path).items() if k}
    print(f"    存在，解析出 {len(values)} 个键")
    key = values.get("DOCUMIND_LLM_API_KEY") or ""
    if key:
        print(f"    API Key  : 已填写（{len(key)} 字符）")
    else:
        print("    API Key  : 未填写（Week 2 才需要，现在不填也行）")


def check_settings() -> None:
    print("\n【3】配置是否真的生效（走 app.config.load_settings）")
    from app.config import load_settings

    settings = load_settings()
    print(f"    数据库路径   : {settings.db_path}")
    print(f"    块长 / 重叠  : {settings.chunk_size} / {settings.chunk_overlap}")
    print(f"    向量维度     : {settings.embedding_dim}")


def check_database() -> None:
    print("\n【4】数据库里有什么")
    from app.config import load_settings
    from app.db import Repository

    repo = Repository(load_settings().db_path)
    repo.init_schema()
    documents = repo.list_documents()
    print(f"    文档数 : {len(documents)}    文本块数 : {repo.count_chunks()}")
    for document in documents[:5]:
        print(f"      - id={document['id']}  {document['name']}  块数={document['chunk_count']}")


def check_server() -> None:
    print("\n【5】服务是否在运行（127.0.0.1:8000）")
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=3) as response:
            body = json.loads(response.read().decode("utf-8"))
        print(f"    在运行 ✓  {json.dumps(body, ensure_ascii=False)}")
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        print("    没在运行 ✗  ← 另开一个窗口执行：python -m uvicorn app.main:app --reload")
    except Exception as exc:  # noqa: BLE001
        print(f"    状态未知：{exc}")


def main() -> None:
    print("=" * 62)
    print("DocuMind 环境体检")
    print("=" * 62)
    check_python()
    check_env_file()
    check_settings()
    check_database()
    check_server()
    print("\n" + "=" * 62)
    print("全部检查完毕。哪一项和预期不符，把这一整段发我。")


if __name__ == "__main__":
    main()
