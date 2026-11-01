"""Week 1 三个练习的验收测试。

用法：你先把 `split_text` / 上传接口 / 检索接口按 ROADMAP 的要求改好，
然后运行 `python -m pytest tests/test_exercises.py`。

现在它们被标成了 xfail(strict=True)，意思是"预期会失败"：
- 还没做 → 显示 xfailed，不拖累 CI，属于正常状态；
- 做完了 → 会显示 **XPASS(strict)** 并报错。这不是你写错了，
  而是提醒你：**把下面这三个 xfail 标记删掉**，让它们变成正式测试提交上去。

为什么要这么绕？因为"先写测试再写实现"是工程习惯里最值钱的一条。
你以后跟面试官讲"我给每个功能都先定义了验收标准"，比说"我写了测试"扎实得多。
"""

from __future__ import annotations

import pytest

from app.chunking import split_text

VECTOR_DOC = (
    "向量检索把文本映射成高维向量，用余弦相似度衡量语义接近程度。"
    "查询时先向量化问题，再与库中所有块比较，取最相似的若干个作为上下文。"
)
COOKING_DOC = (
    "红烧肉：五花肉切块焯水，冰糖炒糖色，加生抽老抽和姜片，"
    "倒热水没过肉，小火炖四十分钟，最后大火收汁。"
)

def test_min_size_merges_short_tail():
    """练习 A：尾块太短时应当并回上一块。

    构造：180 字的段落 + 30 字的段落，size=200 → 天然会切成 [180, 30] 两块。
    要求：传入 min_size=60 后，30 字的尾块（< 60）被并入前一块，只剩 1 块。
    """
    text = "A" * 180 + "\n\n" + "B" * 30
    chunks = split_text(text, size=200, overlap=0, min_size=60)
    assert len(chunks) == 1
    assert len(chunks[0]) == 212  # 180 + "\n\n" + 30

def test_min_size_keeps_adequate_tail():
    """练习 A 的反向用例：尾块够长时不该被合并，否则就是在"过度合并"。"""
    text = "A" * 180 + "\n\n" + "B" * 40
    chunks = split_text(text, size=200, overlap=0, min_size=30)
    assert len(chunks) == 2


@pytest.mark.xfail(strict=True, reason="Week 1 练习 B：上传 .pdf 时交给 PDF 解析器")
def test_pdf_upload_is_routed_to_parser(client):
    """练习 B：.pdf 应该被接受然后走解析流程，而不是被 415 直接拒掉。

    这里故意传一个损坏的 PDF：期望结果是 400（解析失败，并告诉用户原因），
    而不是 415（格式不支持）。两者的区别说明"你确实写了 PDF 分支"。
    """
    files = {"file": ("scan.pdf", b"%PDF-1.4\nthis is not a real pdf", "application/pdf")}
    response = client.post("/api/documents", files=files)
    assert response.status_code == 400


@pytest.mark.xfail(strict=True, reason="Week 1 练习 C：检索接口支持 document_id 过滤")
def test_search_can_filter_by_document(client):
    """练习 C：在指定文档范围内检索，结果不应混入其它文档。"""
    first = client.post(
        "/api/documents/text", json={"name": "向量.md", "text": VECTOR_DOC}
    ).json()["document_id"]
    client.post("/api/documents/text", json={"name": "红烧肉.txt", "text": COOKING_DOC})

    response = client.post(
        "/api/search",
        json={"query": "五花肉怎么做", "top_k": 5, "document_id": first},
    )
    assert response.status_code == 200

    hits = response.json()["hits"]
    assert hits  # 向量那篇里也有字面重合，不应该一条都没有
    assert all(hit["document_id"] == first for hit in hits)
