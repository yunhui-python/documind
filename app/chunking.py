"""文本切块：把长文档切成适合建索引和检索的小片段。

面试里这三个问题一定要能答上来：
1. 为什么按"段落"切，而不是按固定字数硬切？
   —— 段落是天然的语义边界。硬切会把一句话劈成两半，
      检索命中后拼给大模型的上下文也是断的，回答质量直接掉。
2. 为什么块之间要重叠（overlap）？
   —— 防止关键信息正好落在切分点上。代价是索引变大、可能重复命中，
      所以 overlap 一般取块长的 10%~20%。
3. 为什么块长取 500 字左右？
   —— 太短：一句话说不完整，语义碎片化；
      太长：一块里混了好几个主题，向量被"平均"掉，检索精度下降，还浪费 token。
"""

from __future__ import annotations

import re

DEFAULT_SIZE = 500
DEFAULT_OVERLAP = 80


def normalize(text: str) -> str:
    """统一换行符、合并多余空白，避免不同来源的文档格式差异影响切块。"""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_long_paragraph(paragraph: str, size: int, overlap: int) -> list[str]:
    """超长段落（例如整篇没有空行的英文）退化成滑动窗口切分。"""
    step = max(1, size - overlap)
    parts: list[str] = []
    start = 0
    while start < len(paragraph):
        parts.append(paragraph[start : start + size])
        if start + size >= len(paragraph):
            break
        start += step
    return parts


def split_text(
    text: str,
    size: int = DEFAULT_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    min_size: int = 0,
) -> list[str]:
    """把文本切成若干块。

    每块长度不超过 size，相邻块尽量重叠 overlap 个字符；
    最后一块若短于 min_size，则并入前一块（允许合并后超过 size）。

    Args:
        text: 待切分的原始文本。
        size: 每块最大字符数，必须大于 0。
        overlap: 相邻块重叠的字符数，必须 >= 0 且小于 size。
        min_size: 尾块最小字符数，默认 0 表示不合并。

    Raises:
        ValueError: 参数不合法时抛出。
    """
    if size <= 0:
        raise ValueError("size 必须大于 0")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap 必须 >= 0 且小于 size")
    if min_size < 0:
        raise ValueError("min_size 不能为负数")

    text = normalize(text)
    if not text:
        return []

    # 第一步：把文本拆成"不可再分的最小单元"——普通段落，或超长段落的滑窗片段
    units: list[str] = []
    for paragraph in (p.strip() for p in text.split("\n\n")):
        if not paragraph:
            continue
        if len(paragraph) <= size:
            units.append(paragraph)
        else:
            units.extend(_split_long_paragraph(paragraph, size, overlap))

    # 第二步：贪心地把单元装进块里，装不下就封块，并用块尾 overlap 个字符作为下一块的种子
    chunks: list[str] = []
    buffer = ""
    for unit in units:
        if not buffer:
            buffer = unit
            continue
        if len(buffer) + 2 + len(unit) <= size:  # +2 是并入时补的 "\n\n"
            buffer = f"{buffer}\n\n{unit}"
            continue

        chunks.append(buffer)
        seed = buffer[-overlap:].lstrip() if overlap else ""
        buffer = f"{seed}\n\n{unit}" if seed else unit
        if len(buffer) > size:  # 种子太长装不下，宁可不重叠也不能超长
            buffer = unit

    if buffer:
        chunks.append(buffer)
    if len(chunks) < 2 or len(chunks[-1]) >= min_size:
        return chunks
    return chunks[:-2] + [f"{chunks[-2]}\n\n{chunks[-1]}"]
