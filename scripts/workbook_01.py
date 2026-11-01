"""练习册 01：把 Python 语法和本项目的代码一一对上。

怎么用：
    1. 只在每个函数里 "# 你的答案"下面写代码，其它地方一个字都别改
    2. 运行：.\.venv\Scripts\python.exe scripts\workbook_01.py
    3. 看到 [OK] 就过了；[X] 会打印期望值和你的实际值，照着改
    4. 全过之后，最后一个 E7 的答案可以直接搬进 app/chunking.py

为什么这么设计：这些函数不是练习题，是 split_text 的零件。
E1~E6 拼起来就是 split_text 的骨架，E7 就是练习 A 要加的逻辑。
先在练习册里跑通、看得见结果，再搬进真代码，你就不用"凭空写"。
"""

from __future__ import annotations


def e1_slice_tail(text: str, n: int) -> str:
    """取字符串的最后 n 个字符。

    对应 chunking.py 第 81 行：buffer[-overlap:]
    提示：负数索引从右往左数，[-n:] 表示"从倒数第 n 个取到最后"。
    """
    # 你的答案（替换 None）
    return text[-n:]


def e2_slice_head(text: str, size: int) -> str:
    """取字符串的前 size 个字符。

    对应 chunking.py 第 40 行附近：paragraph[start:start + size]
    提示：切片是"左闭右开"，[:3] 取下标 0、1、2。
    """
    # 你的答案（替换 None）
    return text[:size]


def e3_split_paragraphs(text: str) -> list[str]:
    """按空行把文本拆成段落，并丢掉空字符串。

    对应 chunking.py 第 61-63 行。
    提示：用 text.split("\\n\\n") 拿到列表，再过滤掉空字符串。
    过滤的两种写法都行：[p for p in ... if p]  或 用 if 判断后 append。
    """
    # 你的答案（替换 None）
    return text.split()


def e4_join(buffer: str, unit: str) -> str:
    """用两个换行把两段拼起来。

    对应 chunking.py 第 77 行：f"{buffer}\\n\\n{unit}"
    """
    # 你的答案（替换 None）
    return f"{buffer}\n\n{unit}"


def e5_fit(buffer: str, unit: str, size: int) -> str:
    """装得下就把 unit 拼到 buffer 后面，装不下就只返回 unit。

    对应 chunking.py 第 76 行：
        if len(buffer) + 2 + len(unit) <= size:
    注意那个 +2，是拼接时插入的两个换行符。
    """
    # 你的答案（替换 None）
    if len(buffer) + 2 + len(unit) <= size:
        return f"{buffer}\n\n{unit}"
    else :
        return f"{unit}"


def e6_pack(units: list[str], size: int) -> list[str]:
    """把若干单元装进块：能装就装，装不下就封块。先不管 overlap。

    这是 split_text 第二步（第 70-87 行）的骨架，去掉"种子"和"超长段落"之后的样子。
    提示：需要一个 buffer 变量和一个 chunks 列表，遍历 units：
          没东西就放进去；装得下就拼；装不下就先存旧的、再让 buffer 变成新的。
    """
    # 你的答案（替换 None）
    chunks = []
    buffer = ""
    for unit in units:
      if not buffer:
        buffer = unit
        continue
      if len(buffer) + 2 + len(unit) <= size:
        buffer = buffer + "\n\n" + unit
        continue
      chunks.append(buffer)
      buffer = unit
    if buffer:
      chunks.append(buffer)
    return chunks
    

def e7_merge_tail(chunks: list[str], min_size: int) -> list[str]:
    """如果最后一块比 min_size 还短，就把它并进前一块（用两个换行连接）。

    这就是练习 A 的核心逻辑。三种情况都要兼顾：
      - 最后一块够长 → 原样返回
      - 最后一块太短且有前一块 → 合并
      - 只有一块（没有前一块可并）→ 原样返回
    """
    # 你的答案（替换 None）
    if len(chunks) < 2 or len(chunks[-1]) >= min_size:
      return chunks
    return chunks[:-2] + [f"{chunks[-2]}\n\n{chunks[-1]}"]

def main() -> None:
    cases = [
        ("E1 取最后 4 个字符", e1_slice_tail("0123456789", 4), "6789"),
        ("E2 取前 3 个字符", e2_slice_head("abcdef", 3), "abc"),
        ("E3 按空行切段落", e3_split_paragraphs("a\n\nb\n\n\n\nc"), ["a", "b", "c"]),
        ("E4 用两个换行拼接", e4_join("A", "B"), "A\n\nB"),
        ("E5 装得下就拼", e5_fit("A" * 5, "B" * 5, 20), "A" * 5 + "\n\n" + "B" * 5),
        ("E5 装不下只要新块", e5_fit("A" * 10, "B" * 10, 20), "B" * 10),
        (
            "E6 把 4 个单元装进 3 块",
            e6_pack(["a" * 30, "b" * 30, "c" * 30, "d" * 30], 100),
            ["a" * 30 + "\n\n" + "b" * 30 + "\n\n" + "c" * 30, "d" * 30],
        ),
        (
            "E7 尾块太短要合并",
            e7_merge_tail(["A" * 180, "B" * 30], 60),
            ["A" * 180 + "\n\n" + "B" * 30],
        ),
        ("E7 尾块够长不动", e7_merge_tail(["A" * 180, "B" * 40], 30), ["A" * 180, "B" * 40]),
        ("E7 只有一块时不动", e7_merge_tail(["only"], 100), ["only"]),
    ]

    passed = 0
    for label, actual, expected in cases:
        if actual == expected:
            print(f"  [OK] {label}")
            passed += 1
        else:
            print(f"  [X ] {label}")
            print(f"        期望: {expected!r}")
            print(f"        实际: {actual!r}")

    print(f"\n通过 {passed}/{len(cases)}")
    if passed == len(cases):
        print("全部通过。现在把 E7 的逻辑搬进 app/chunking.py，练习 A 就完成一半了。")


if __name__ == "__main__":
    main()
