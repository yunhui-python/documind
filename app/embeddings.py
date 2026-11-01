"""文本向量化（把一段文字变成一组浮点数，让"语义相近"变成"向量夹角小"）。

默认实现是 HashingEmbedder，完全不依赖模型和网络：
- 用分词结果做"词袋"，再用 hashing trick 把每个词映射到 256 维空间里的一个下标；
- 最后做 L2 归一化，于是两个向量的点积就等于余弦相似度。

它的本事只有"字面重合"，同义词、改述会失手 —— 这不是缺陷，是设计：
Week 1 先用它把整条链路（切块 → 向量化 → 存储 → 检索 → 排序）跑通并写测试，
Week 3 再换成真实的 embedding 模型，用同一套评测脚本对比效果提升。
面试时这是很好的叙事："我先用一个零依赖的基线把链路跑通，再用评测证明换模型带来的收益。"

想接真实模型时，只要实现下面 Embedder 协议，其它代码一行都不用改（这就是"依赖抽象而不是实现"）。
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence
from typing import Protocol

_WORD = re.compile(r"[a-z0-9_]+")
_CJK = re.compile(r"[\u4e00-\u9fff]")


def tokenize(text: str) -> list[str]:
    """分词：英文/数字按词切，中文按"单字 + 相邻双字"切。

    中文为什么要双字？单字太碎（"的""是"到处都是，没有区分度），
    双字（bigram）不需要词典就能表达大部分词组，是最便宜的中文检索基线。
    """
    lowered = text.lower()
    tokens = _WORD.findall(lowered)
    cjk = _CJK.findall(lowered)
    tokens.extend(cjk)
    tokens.extend(a + b for a, b in zip(cjk, cjk[1:], strict=False))
    return tokens


class Embedder(Protocol):
    """向量化器的统一接口。换模型时实现它即可。"""

    name: str
    dim: int

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class HashingEmbedder:
    """零依赖的哈希词袋向量化器，用于跑通链路和做基线。"""

    name = "hashing-trick"

    def __init__(self, dim: int = 256) -> None:
        if dim <= 0:
            raise ValueError("dim 必须大于 0")
        self.dim = dim

    def _vectorize(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        for token in tokenize(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "little") % self.dim
            # 用哈希值的一位决定正负号（hashing trick），让不同词的碰撞互相抵消而不是叠加
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm > 0:
            vector = [value / norm for value in vector]
        return vector

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._vectorize(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vectorize(text)
