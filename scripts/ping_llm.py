"""验证大模型 API Key 能不能用（Week 2 之前的连通性测试）。

用法：
    .\\.venv\\Scripts\\python.exe scripts\\ping_llm.py

只发一句话，消耗的 token 可以忽略。成功会打印模型回复的一句话。
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import app.config  # noqa: E402, F401  —— 导入即触发 load_dotenv，把 .env 读进环境变量


def main() -> None:
    base_url = (os.getenv("DOCUMIND_LLM_BASE_URL") or "").rstrip("/")
    api_key = os.getenv("DOCUMIND_LLM_API_KEY") or ""
    model = os.getenv("DOCUMIND_LLM_MODEL") or "deepseek-chat"

    print(f"接口地址 : {base_url or '（未配置）'}")
    print(f"模型     : {model}")
    print(f"API Key  : {'已读入，长度 ' + str(len(api_key)) if api_key else '（未配置）'}")
    print()

    if not base_url or not api_key:
        print("缺少配置。请在 .env 里填好 DOCUMIND_LLM_BASE_URL 和 DOCUMIND_LLM_API_KEY。")
        return

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "用一句话回答：1+1 等于几？"}],
        "max_tokens": 64,
        "temperature": 0.1,
    }
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"请求失败：HTTP {exc.code}")
        print(exc.read().decode("utf-8", errors="replace")[:500])
        return
    except Exception as exc:  # noqa: BLE001
        print(f"请求失败：{exc}")
        return

    content = body["choices"][0]["message"]["content"]
    print(f"模型回复    ：{content}")
    print(f"token 消耗  ：{body.get('usage', {})}")
    print()
    print("Key 可用，Week 2 可以开始了。")


if __name__ == "__main__":
    main()
