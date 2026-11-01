"""测试用的公共 fixture。

关键点：每个测试用独立的临时数据库（tmp_path 由 pytest 自动创建和清理），
这样测试之间互不影响，也不会弄脏你本地的 data/documind.db。
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture()
def settings(tmp_path) -> Settings:
    return Settings(
        db_path=tmp_path / "test.db",
        chunk_size=200,
        chunk_overlap=40,
        top_k=3,
        embedding_dim=128,
        max_upload_bytes=1024 * 1024,
    )


@pytest.fixture()
def client(settings):
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client
