"""SQLite 数据访问层。

为什么用 SQLite？
—— 单文件、零部署、Python 标准库直接支持。这个项目的数据量（几万块以内）
   完全用不着 PostgreSQL，而"能一条命令跑起来"对作品集项目是巨大优势。
   如果要做成多人服务，把 Repository 换成 pgvector 即可，上层代码不用动。

两个容易踩的坑，这里已经处理了：
1. sqlite3 的 Connection 默认不允许跨线程复用 —— 所以每次操作开一条新连接，
   用完立刻关闭，不共享连接对象。
2. 外键约束默认是关闭的 —— 必须每条连接都执行 PRAGMA foreign_keys = ON，
   否则删文档时不会级联删掉它的文本块。
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    size       INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    ordinal     INTEGER NOT NULL,
    text        TEXT    NOT NULL,
    embedding   BLOB    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);
"""


class Repository:
    """所有 SQL 都收敛在这里，API 层不直接碰数据库。"""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_schema(self) -> None:
        with self.connection() as conn:
            conn.executescript(SCHEMA)

    # ---------- 写入 ----------

    def add_document(self, name: str, size: int, chunks: list[tuple[str, bytes]]) -> int:
        """插入一篇文档及其所有文本块，返回文档 id。整篇文档在一个事务里，失败不会留半截数据。"""
        created_at = datetime.now(UTC).isoformat(timespec="seconds")
        with self.connection() as conn:
            cursor = conn.execute(
                "INSERT INTO documents (name, size, created_at) VALUES (?, ?, ?)",
                (name, size, created_at),
            )
            document_id = int(cursor.lastrowid)
            conn.executemany(
                "INSERT INTO chunks (document_id, ordinal, text, embedding) VALUES (?, ?, ?, ?)",
                [
                    (document_id, ordinal, text, embedding)
                    for ordinal, (text, embedding) in enumerate(chunks)
                ],
            )
        return document_id

    def delete_document(self, document_id: int) -> bool:
        with self.connection() as conn:
            cursor = conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            return cursor.rowcount > 0

    # ---------- 读取 ----------

    def list_documents(self) -> list[dict]:
        with self.connection() as conn:
            rows = conn.execute(
                """
                SELECT d.id, d.name, d.size, d.created_at, COUNT(c.id) AS chunk_count
                FROM documents AS d
                LEFT JOIN chunks AS c ON c.document_id = d.id
                GROUP BY d.id
                ORDER BY d.id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def fetch_chunks(self, document_id: int | None = None) -> list[sqlite3.Row]:
        """取出文本块（含 embedding 原始字节），供检索时遍历打分。"""
        sql = """
            SELECT c.id, c.document_id, c.ordinal, c.text, c.embedding, d.name AS document_name
            FROM chunks AS c
            JOIN documents AS d ON d.id = c.document_id
        """
        params: tuple = ()
        if document_id is not None:
            sql += " WHERE c.document_id = ?"
            params = (document_id,)
        sql += " ORDER BY c.document_id, c.ordinal"
        with self.connection() as conn:
            return conn.execute(sql, params).fetchall()

    def count_chunks(self) -> int:
        with self.connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM chunks").fetchone()
        return int(row["n"])
