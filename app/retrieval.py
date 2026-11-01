"""向量存储格式与相似度检索。

两个实现细节值得记住（面试高频）：
1. 向量用 array('f') 存成二进制 BLOB，比存 JSON 文本小 3 倍以上，读写也更快。
   代价是可读性差 —— 但向量本来就不是给人看的。
2. 因为入库前做了 L2 归一化，余弦相似度 = 点积，省掉两次开方和除法。
   语料几千块以内，纯 Python 暴力扫描只要几十毫秒，完全没必要上向量数据库。
   等语料涨到十万级，再换 pgvector / FAISS —— 这个"什么时候该换"的判断本身就是加分项。
"""

from __future__ import annotations

import math
from array import array
from dataclasses import asdict, dataclass

from .db import Repository


def pack(vector: list[float]) -> bytes:
    return array("f", vector).tobytes()


def unpack(blob: bytes) -> list[float]:
    values = array("f")
    values.frombytes(blob)
    return list(values)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """通用余弦相似度。已归一化的向量可以直接用 dot_product，会更快。"""
    if len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


@dataclass(frozen=True)
class Hit:
    """一条检索结果。带上 document_name 和 ordinal，是为了在回答里给用户"引用来源"。"""

    chunk_id: int
    document_id: int
    document_name: str
    ordinal: int
    text: str
    score: float

    def to_dict(self) -> dict:
        return asdict(self)


def search(
    repo: Repository,
    query_vector: list[float],
    top_k: int = 5,
    document_id: int | None = None,
    min_score: float = 0.0,
) -> list[Hit]:
    """暴力扫描所有文本块，按余弦相似度排序，返回前 top_k 条。"""
    if top_k <= 0:
        return []

    hits: list[Hit] = []
    for row in repo.fetch_chunks(document_id=document_id):
        vector = unpack(row["embedding"])
        if len(vector) != len(query_vector):
            # 维度不一致说明换了 embedding 模型但没重建索引，直接跳过而不是算错分
            continue
        score = cosine_similarity(query_vector, vector)
        if score < min_score:
            continue
        hits.append(
            Hit(
                chunk_id=int(row["id"]),
                document_id=int(row["document_id"]),
                document_name=str(row["document_name"]),
                ordinal=int(row["ordinal"]),
                text=str(row["text"]),
                score=score,
            )
        )

    hits.sort(key=lambda hit: hit.score, reverse=True)
    return hits[:top_k]
