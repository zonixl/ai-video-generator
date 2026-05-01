"""文本工具：清洗、分段、chunk切分。"""

import re


def clean_text(text: str) -> str:
    """基础文本清洗：去多余空白、统一换行。"""
    text = text.strip()
    text = re.sub(r"\n{3,}", "\n\n", text)   # 最多保留一个空行
    text = re.sub(r"[ \t]{2,}", " ", text)    # 多余空格合并
    return text


def chunk_by_paragraphs(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """按段落优先分割文本，超过 chunk_size 的段落才按句子切。

    返回chunk列表，每个chunk控制在 chunk_size 字符左右。
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) <= chunk_size:
            current = (current + "\n\n" + para).strip() if current else para
        else:
            if current:
                chunks.append(current)
            # 如果段落自身超过chunk_size，按句子切
            if len(para) > chunk_size:
                sub_chunks = _split_long_paragraph(para, chunk_size, overlap)
                chunks.extend(sub_chunks)
                current = ""
            else:
                current = para

    if current:
        chunks.append(current)

    return chunks


def _split_long_paragraph(text: str, chunk_size: int, overlap: int) -> list[str]:
    """将超长段落按句子边界切分，带重叠。"""
    sentences = re.split(r"(?<=[。！？.!?])\s*", text)
    chunks = []
    current = ""

    for sent in sentences:
        if not sent.strip():
            continue
        if len(current) + len(sent) <= chunk_size:
            current += sent
        else:
            if current:
                chunks.append(current.strip())
            # 保留overlap：取上一句的部分内容拼到新chunk开头
            overlap_text = current[-overlap:] if current and len(current) > overlap else ""
            current = overlap_text + sent

    if current.strip():
        chunks.append(current.strip())

    return chunks


def word_count(text: str) -> int:
    """中文字数统计（混合中英文）。"""
    chinese_chars = len(re.findall(r"[一-鿿]", text))
    english_words = len(re.findall(r"[a-zA-Z]+", text))
    return chinese_chars + english_words
