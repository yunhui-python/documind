"""检索与 API 的集成测试：走完整的 HTTP 请求链路，验证"上传 → 检索 → 删除"。"""

from __future__ import annotations

import io

import pytest

VECTOR_DOC = (
    "向量检索通过把文本映射成高维向量，用余弦相似度衡量语义接近程度。"
    "常见做法是先做文本切块，再对每个块向量化，查询时同样向量化后做最近邻搜索。"
)
COOKING_DOC = (
    "红烧肉的做法：五花肉切块焯水，热锅下冰糖炒出糖色，加入肉块翻炒上色，"
    "再加生抽老抽料酒和姜片，倒入热水没过肉，小火慢炖四十分钟后大火收汁。"
)


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["documents"] == 0
    assert body["chunks"] == 0


def test_upload_text_document_and_list(client):
    response = client.post(
        "/api/documents/text",
        json={"name": "向量检索笔记.md", "text": VECTOR_DOC},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["chunks"] >= 1
    assert body["document_id"] == 1

    listed = client.get("/api/documents").json()["items"]
    assert len(listed) == 1
    assert listed[0]["name"] == "向量检索笔记.md"
    assert listed[0]["chunk_count"] == body["chunks"]


def test_upload_file_endpoint(client):
    files = {"file": ("cooking.txt", io.BytesIO(COOKING_DOC.encode("utf-8")), "text/plain")}
    response = client.post("/api/documents", files=files)
    assert response.status_code == 201
    assert response.json()["name"] == "cooking.txt"


def test_upload_rejects_unsupported_suffix(client):
    files = {"file": ("report.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")}
    response = client.post("/api/documents", files=files)
    assert response.status_code == 415


def test_upload_rejects_non_utf8(client):
    files = {"file": ("gbk.txt", io.BytesIO("中文".encode("gbk")), "text/plain")}
    response = client.post("/api/documents", files=files)
    assert response.status_code == 400


def test_empty_document_is_rejected(client):
    response = client.post("/api/documents/text", json={"name": "空文档", "text": "   "})
    assert response.status_code in (400, 422)


def test_search_ranks_relevant_document_first(client):
    """这是整个项目最核心的断言：问一句关于向量的中文问题，能不能把向量那篇排到第一。"""
    client.post("/api/documents/text", json={"name": "向量检索笔记.md", "text": VECTOR_DOC})
    client.post("/api/documents/text", json={"name": "红烧肉.txt", "text": COOKING_DOC})

    response = client.post("/api/search", json={"query": "向量检索是怎么实现的", "top_k": 3})
    assert response.status_code == 200

    hits = response.json()["hits"]
    assert hits, "检索结果不应该为空"
    assert hits[0]["document_name"] == "向量检索笔记.md"
    # 分数应当是降序排列的
    scores = [hit["score"] for hit in hits]
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 <= score <= 1.0 + 1e-6 for score in scores)


def test_search_with_document_filter(client):
    first = client.post(
        "/api/documents/text", json={"name": "A.md", "text": VECTOR_DOC}
    ).json()["document_id"]
    client.post("/api/documents/text", json={"name": "B.txt", "text": COOKING_DOC})

    response = client.post("/api/search", json={"query": "五花肉怎么做", "top_k": 5})
    assert response.json()["hits"][0]["document_name"] == "B.txt"

    # 直接校验过滤能力（API 层暂时没暴露 document_id 参数，Week 2 会加）
    app = client.app
    from app.retrieval import search

    hits = search(
        app.state.repo,
        app.state.embedder.embed_query("肉"),
        top_k=5,
        document_id=first,
    )
    assert all(hit.document_id == first for hit in hits)


@pytest.mark.parametrize(
    "payload",
    [{"query": ""}, {"query": "x", "top_k": 0}, {"query": "x", "top_k": 99}],
)
def test_search_validates_input(client, payload):
    assert client.post("/api/search", json=payload).status_code == 422


def test_delete_document_cascades_chunks(client):
    document_id = client.post(
        "/api/documents/text", json={"name": "临时.md", "text": VECTOR_DOC}
    ).json()["document_id"]
    assert client.get("/api/health").json()["chunks"] > 0

    assert client.delete(f"/api/documents/{document_id}").status_code == 200
    assert client.get("/api/health").json()["chunks"] == 0
    assert client.delete(f"/api/documents/{document_id}").status_code == 404
