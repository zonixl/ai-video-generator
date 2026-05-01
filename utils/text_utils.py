"""文本工具：清洗、分段、chunk切分。"""

import re

from langchain_text_splitters import RecursiveCharacterTextSplitter


def clean_text(text: str) -> str:
    """基础文本清洗：去多余空白、统一换行。"""
    text = text.strip()
    text = re.sub(r"\n{3,}", "\n\n", text)   # 最多保留一个空行
    text = re.sub(r"[ \t]{2,}", " ", text)    # 多余空格合并
    return text


def chunk_by_paragraphs(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """使用 RecursiveCharacterTextSplitter 按中文语义边界切分文本。"""
    splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        keep_separator=True,
    )
    return splitter.split_text(text)


def word_count(text: str) -> int:
    """中文字数统计（混合中英文）。"""
    chinese_chars = len(re.findall(r"[一-鿿]", text))
    english_words = len(re.findall(r"[a-zA-Z]+", text))
    return chinese_chars + english_words
