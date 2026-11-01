"""用眼睛看切块：把 split_text 的结果打印出来，包括相邻块的真实重叠长度。

改下面的参数或换掉 sample 文本，重新运行，观察输出怎么变。
运行：python scripts/explore_chunking.py
"""

from __future__ import annotations

from app.chunking import split_text


def build_long_text(target: int = 1200) -> str:
    """造一段约 target 字、没有空行、且每句都不重复的文本。

    为什么要"不重复"？如果文本是周期性的（比如同一句话重复 80 次），
    按固定步长滑窗切出来的块会彼此完全相同，测出来的重叠长度就全是假象。
    我第一版就踩了这个坑，你可以引以为戒：造测试数据比写代码更考验人。
    """
    parts: list[str] = []
    index = 0
    while sum(len(part) for part in parts) < target:
        parts.append(f"第{index}句说明向量{index * 7 % 13}与检索{index * 3 % 11}之间的关系，")
        index += 1
    return "".join(parts)[:target]


def real_overlap(previous: str, current: str) -> int:
    """算出前后两块真正重叠了多少字符（暴力比对后缀与前缀）。"""
    for length in range(min(len(previous), len(current)), 0, -1):
        if previous[-length:] == current[:length]:
            return length
    return 0


def show(title: str, chunks: list[str]) -> None:
    print(f"\n{'=' * 72}")
    print(f"【{title}】")
    if not chunks:
        print("  （空，切出 0 块）")
        return

    lengths = [len(chunk) for chunk in chunks]
    print(f"  块数={len(chunks)}  每块长度={lengths}  总字符={sum(lengths)}")
    for index, chunk in enumerate(chunks):
        overlap = real_overlap(chunks[index - 1], chunk) if index else 0
        head = chunk[:14].replace("\n", "⏎")
        tail = chunk[-14:].replace("\n", "⏎")
        print(f"  [{index}] len={len(chunk):4d} 与前块重叠={overlap:3d}  头={head!r} 尾={tail!r}")


def main() -> None:
    long_text = build_long_text(1200)
    print(f"样例 1：{len(long_text)} 字，无空行，每句都不重复")

    show("无空行 / size=500 overlap=80（默认值）", split_text(long_text, 500, 80))
    show("无空行 / size=500 overlap=0", split_text(long_text, 500, 0))
    show("无空行 / size=300 overlap=60", split_text(long_text, 300, 60))
    show("无空行 / size=300 overlap=250（接近 size）", split_text(long_text, 300, 250))

    paragraphs = [f"第{i}段：" + "内容" * 40 for i in range(6)]
    multi = "\n\n".join(paragraphs)
    print(f"\n\n样例 2：{len(multi)} 字，6 个段落")

    show("多段落 / size=200 overlap=50", split_text(multi, 200, 50))
    show("多段落 / size=200 overlap=0", split_text(multi, 200, 0))

    print(f"\n{'=' * 72}")
    print("观察 1：overlap 越大，总字符数越多 —— 这是索引膨胀的代价。")
    print("观察 2：超长段落的最后一块会比其它块长，因为它多继承了前一块的尾巴。")


if __name__ == "__main__":
    main()
