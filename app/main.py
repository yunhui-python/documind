"""FastAPI 应用入口。

用工厂函数 create_app(settings) 而不是模块级单例，好处是：
测试时可以传入临时数据库的配置，不会污染你的真实数据 —— 这是可测试性的关键设计。

启动方式（在项目根目录）：
    py -m uvicorn app.main:app --reload
然后打开 http://127.0.0.1:8000/docs 就能看到自动生成的交互文档。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from . import __version__
from .chunking import split_text
from .config import Settings, load_settings
from .db import Repository
from .embeddings import HashingEmbedder
from .retrieval import pack, search

# 允许上传的文本后缀。PDF/Word 解析是 Week 1 的练习题。
ALLOWED_SUFFIXES = (".txt", ".md", ".markdown", ".log", ".csv")


class TextDocumentIn(BaseModel):
    name: str = Field(min_length=1, max_length=200, description="文档名，用于引用溯源")
    text: str = Field(min_length=1, description="文档纯文本内容")


class SearchIn(BaseModel):
    query: str = Field(min_length=1, max_length=2000, description="查询语句")
    top_k: int = Field(default=5, ge=1, le=20, description="返回条数")
    document_id: int | None = Field(
        default=None,
        description="只在这篇文档内检索；文档不存在时返回空列表，不报错",
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()

    repo = Repository(settings.db_path)
    repo.init_schema()
    embedder = HashingEmbedder(dim=settings.embedding_dim)

    app = FastAPI(
        title="DocuMind",
        version=__version__,
        description="上传文档 → 自动切块建索引 → 自然语言检索 → （Week 2）带引用来源的回答",
    )
    app.state.settings = settings
    app.state.repo = repo
    app.state.embedder = embedder

    def ingest(name: str, text: str) -> dict:
        """把一篇文档切块、向量化、入库。所有写入口都复用它。"""
        chunks = split_text(text, size=settings.chunk_size, overlap=settings.chunk_overlap)
        if not chunks:
            raise HTTPException(status_code=400, detail="文档没有有效内容")

        vectors = embedder.embed_documents(chunks)
        payload = [(chunk, pack(vector)) for chunk, vector in zip(chunks, vectors, strict=True)]
        document_id = repo.add_document(name=name, size=len(text), chunks=payload)
        return {"document_id": document_id, "name": name, "chunks": len(chunks), "size": len(text)}

    # ---------- 健康检查 ----------

    @app.get("/api/health", tags=["system"], summary="健康检查")
    def health() -> dict:
        return {
            "status": "ok",
            "version": __version__,
            "embedder": embedder.name,
            "embedding_dim": embedder.dim,
            "documents": len(repo.list_documents()),
            "chunks": repo.count_chunks(),
        }

    # ---------- 文档管理 ----------

    @app.post(
        "/api/documents/text",
        status_code=201,
        tags=["documents"],
        summary="以 JSON 提交文档",
    )
    def create_from_text(payload: TextDocumentIn) -> dict:
        return ingest(payload.name, payload.text)

    @app.post("/api/documents", status_code=201, tags=["documents"], summary="上传文本文件")
    async def upload_document(
        file: Annotated[UploadFile, File(description="UTF-8 编码的文本文件")],
    ) -> dict:
        filename = file.filename or "untitled.txt"
        if not filename.lower().endswith(ALLOWED_SUFFIXES):
            raise HTTPException(
                status_code=415,
                detail=f"目前只支持这些格式：{', '.join(ALLOWED_SUFFIXES)}",
            )

        raw = await file.read()
        if len(raw) > settings.max_upload_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"文件超过 {settings.max_upload_bytes // 1024 // 1024}MB 限制",
            )
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="文件不是 UTF-8 编码，请另存为 UTF-8 后重试",
            ) from None

        return ingest(filename, text)

    @app.get("/api/documents", tags=["documents"], summary="文档列表")
    def list_documents() -> dict:
        return {"items": repo.list_documents()}

    @app.delete("/api/documents/{document_id}", tags=["documents"], summary="删除文档")
    def delete_document(document_id: int) -> dict:
        if not repo.delete_document(document_id):
            raise HTTPException(status_code=404, detail="文档不存在")
        return {"deleted": document_id}

    # ---------- 检索 ----------

    @app.post("/api/search", tags=["search"], summary="语义检索（暂未接入大模型）")
    def do_search(payload: SearchIn) -> dict:
        hits = search(
            repo,
            query_vector=embedder.embed_query(payload.query),
            top_k=payload.top_k,
            document_id=payload.document_id,
        )
        return {
            "query": payload.query,
            "document_id": payload.document_id,
            "count": len(hits),
            "hits": [hit.to_dict() for hit in hits],
        }

    return app


app = create_app()
