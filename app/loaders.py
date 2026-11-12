"""把各种格式的文件字节流变成纯文本。

main.py 只负责路由和校验，具体的"怎么从二进制里抠出文字"放在这里。
以后要支持 .docx、.xlsx，就往这个文件里加函数。
"""

from __future__ import annotations

import io

from pypdf import PdfReader


def extract_pdf_text(raw: bytes) -> str:
    """从 PDF 的字节流里提取纯文本。

    Args:
        raw: 文件的原始字节。

    Returns:
        提取出的文本，各页之间用两个换行连接。

    Raises:
        ValueError: 文件损坏无法解析，或整份 PDF 里没有可提取的文字（通常是扫描件）。
    """
    try:
        reader = PdfReader(io.BytesIO(raw))
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
    except Exception:
        raise ValueError("PDF 解析失败，文件可能已损坏") from None

    text = "\n\n".join(page for page in pages if page)
    if not text:
        raise ValueError("PDF 里没有可提取的文字，可能是扫描件")
    return text
