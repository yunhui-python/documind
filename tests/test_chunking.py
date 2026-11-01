"""切块逻辑的单元测试。

测试的原则：不要只测"能不能跑"，要测"边界条件"。
这里覆盖了空文本、纯空白、超长段落、参数非法、块长上限、重叠是否真的发生。
"""

from __future__ import annotations

import pytest

from app.chunking import normalize, split_text


def test_empty_text_returns_no_chunks():
    assert split_text("") == []
    assert split_text("   \n\n  \t ") == []


def test_short_text_is_single_chunk():
    chunks = split_text("这是一段很短的话。", size=200, overlap=40)
    assert chunks == ["这是一段很短的话。"]


def test_every_chunk_respects_size_limit():
    text = "中" * 1200
    chunks = split_text(text, size=300, overlap=60)
    assert len(chunks) >= 4
    assert all(len(chunk) <= 300 for chunk in chunks)


def test_consecutive_chunks_overlap():
    # 每段约 80 字、共 6 段，size=200 会切出多块
    paragraphs = "\n\n".join(f"第{index}段" + "内容" * 38 for index in range(6))
    chunks = split_text(paragraphs, size=200, overlap=50)
    assert len(chunks) >= 2
    for previous, current in zip(chunks, chunks[1:], strict=False):
        # 前一块的结尾应该出现在后一块的开头附近，说明重叠生效了
        assert previous[-20:] in current


def test_paragraph_boundary_is_preferred():
    first = "第一段" * 20   # 60 字
    second = "第二段" * 20  # 60 字
    # 60 + 2 + 60 = 122 > 100，两段装不进同一块，应当各成一块
    chunks = split_text(f"{first}\n\n{second}", size=100, overlap=0)
    assert len(chunks) == 2
    assert chunks[0] == first
    assert chunks[1] == second


@pytest.mark.parametrize(
    ("size", "overlap"),
    [(0, 0), (-10, 0), (100, 100), (100, 150), (100, -1)],
)
def test_invalid_parameters_raise(size: int, overlap: int):
    with pytest.raises(ValueError):
        split_text("一些文本", size=size, overlap=overlap)


def test_normalize_collapses_whitespace():
    assert normalize("a  \t b\r\n\r\n\r\n\r\nc  ") == "a b\n\nc"
