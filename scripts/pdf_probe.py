"""B1：看看 pypdf 到底能从一份 PDF 里抠出什么。不碰项目代码。

用法：
    .\\.venv\\Scripts\\python.exe scripts\\pdf_probe.py examples\\sample.pdf

换一个你自己电脑上的 PDF（简历、论文、课件）也行，它只读不写。
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

from pypdf import PdfReader


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python scripts/pdf_probe.py <文件.pdf>")
        return

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"文件不存在: {path}")
        return

    raw = path.read_bytes()
    print(f"文件    : {path.name}")
    print(f"大小    : {len(raw)} 字节")

    # 关键：用 io.BytesIO 把内存里的字节包成一个"文件"，pypdf 就能读了。
    # 服务器上我们拿到的就是字节（不是磁盘路径），所以这里特意这么写。
    reader = PdfReader(io.BytesIO(raw))
    print(f"页数    : {len(reader.pages)}")

    total = 0
    for index, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        total += len(text)
        print(f"\n--- 第 {index} 页，提取到 {len(text)} 个字符 ---")
        print(text[:300] if text else "(空)")

    print(f"\n合计提取 {total} 字")
    if total == 0:
        print("⚠ 一个字都没提到：这份 PDF 多半是扫描件（整页图片），需要 OCR 才能读出文字。")


if __name__ == "__main__":
    main()
