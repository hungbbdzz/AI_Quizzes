"""
Utilities cho document pipeline (Giai doan 4 - Vu) de dung trong backend upload flow.

Muc tieu:
- Trich xuat text PDF/DOCX/TXT
- Lam sach text giu Unicode
- Chunk theo cau (sentence-aware)
- Tao normalized_text de dedup
"""

from __future__ import annotations

import html
import io
import re
import unicodedata
from typing import Any

from docx import Document
from docx.oxml.ns import qn
from fastapi import HTTPException, status

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MULTI_BLANK_LINES_RE = re.compile(r"\n{3,}")
_MULTI_SPACE_RE = re.compile(r"[ \t]+")

_SENTENCE_END_RE = re.compile(r"(?<=[.!?。！？])\s+")

_VIETNAMESE_CHARS_RE = re.compile(
    r"[àáâãèéêìíòóôõùúýăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỷỹỵ"
    r"ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĂĐƠƯẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼẾỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỶỸỴ]",
    re.UNICODE,
)


def clean_raw_text(text: str) -> str:
    """Lam sach text thô nhung van giu Unicode tieng Viet."""
    if not text:
        return ""

    text = html.unescape(text)
    text = _CONTROL_CHARS_RE.sub("", text)
    text = unicodedata.normalize("NFC", text)

    lines = text.split("\n")
    lines = [_MULTI_SPACE_RE.sub(" ", line).rstrip() for line in lines]
    text = "\n".join(lines)
    text = _MULTI_BLANK_LINES_RE.sub("\n\n", text)

    return text.strip()


def normalize_text_value(value: Any) -> str:
    """Tao chuoi ASCII lowercase de dedup/search."""
    if value is None:
        return ""

    text = unicodedata.normalize("NFD", str(value))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    text = re.sub(r"\s+", " ", text).strip()
    return text


def detect_language_hint(text: str) -> str:
    """Phat hien ngon ngu heuristic don gian."""
    if _VIETNAMESE_CHARS_RE.search(text):
        return "vi"
    return "en"


def extract_text_from_upload(file_name: str, content_type: str, content: bytes) -> str:
    """Trich xuat text tu bytes upload (PDF/DOCX/TXT)."""
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    ctype = (content_type or "").lower()

    if "pdf" in ctype or ext == "pdf":
        text = _extract_pdf(content)
    elif "docx" in ctype or "word" in ctype or ext == "docx":
        text = _extract_docx(content)
    elif "text" in ctype or ext == "txt":
        text = _extract_txt(content)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dinh dang file khong duoc ho tro: {file_name}. Chi chap nhan PDF, DOCX, TXT.",
        )

    cleaned = clean_raw_text(text)
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File '{file_name}' khong co noi dung text co the trich xuat.",
        )
    return cleaned


def _extract_pdf(content: bytes) -> str:
    """Trich text PDF bang pdfplumber (tot hon cho tieng Viet co dau)."""
    try:
        import pdfplumber

        with pdfplumber.open(io.BytesIO(content)) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text() or ""
                text = clean_raw_text(text)
                if len(text) >= 20:
                    pages.append(text)
            return "\n\n".join(pages)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Khong the doc file PDF: {exc}",
        )


def _extract_docx(content: bytes) -> str:
    """Trich text DOCX gom paragraph va table, giu thu tu xuat hien."""
    try:
        doc = Document(io.BytesIO(content))
        body = doc.element.body
        segments: list[str] = []

        for child in body:
            if child.tag == qn("w:p"):
                raw = "".join(node.text or "" for node in child.iter() if node.tag == qn("w:t")).strip()
                if raw:
                    segments.append(raw)
            elif child.tag == qn("w:tbl"):
                table_lines: list[str] = []
                for row in child.iter(qn("w:tr")):
                    cells = []
                    for cell in row.iter(qn("w:tc")):
                        cell_text = "".join(
                            node.text or "" for node in cell.iter() if node.tag == qn("w:t")
                        ).strip()
                        cells.append(cell_text)
                    if any(cells):
                        table_lines.append(" | ".join(cells))
                if table_lines:
                    segments.append("\n".join(table_lines))

        return "\n\n".join(segment for segment in segments if segment.strip())
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Khong the doc file DOCX: {exc}",
        )


def _extract_txt(content: bytes) -> str:
    """Doc TXT voi nhieu encoding pho bien."""
    encodings_to_try = ["utf-8", "utf-8-sig", "utf-16", "latin-1", "cp1252"]

    for enc in encodings_to_try:
        try:
            return content.decode(enc)
        except (UnicodeDecodeError, UnicodeError):
            continue

    return content.decode("utf-8", errors="replace")


def _split_into_sentences(text: str) -> list[str]:
    parts = _SENTENCE_END_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def chunk_text_sentence_aware(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """
    Chia text theo cau de giam viec cat dut y.
    Fallback hard-cut neu mot cau qua dai.
    """
    text = re.sub(r"[ \t]+", " ", text).strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    sentences = _split_into_sentences(text)
    if not sentences:
        return [text[:chunk_size]]

    chunks: list[str] = []
    current_chunk: list[str] = []
    current_len = 0

    step = max(1, chunk_size - chunk_overlap)

    for sentence in sentences:
        sentence_len = len(sentence)

        if sentence_len > chunk_size:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_len = 0

            for i in range(0, sentence_len, step):
                part = sentence[i : i + chunk_size].strip()
                if part:
                    chunks.append(part)
            continue

        if current_len + sentence_len + 1 > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))

            overlap_sents: list[str] = []
            overlap_len = 0
            for sent in reversed(current_chunk):
                if overlap_len + len(sent) + 1 <= chunk_overlap:
                    overlap_sents.insert(0, sent)
                    overlap_len += len(sent) + 1
                else:
                    break
            current_chunk = overlap_sents
            current_len = overlap_len

        current_chunk.append(sentence)
        current_len += sentence_len + 1

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def build_clean_chunks(
    raw_text: str,
    chunk_size: int,
    chunk_overlap: int,
    min_chunk_length: int,
) -> list[dict[str, Any]]:
    """Tao danh sach chunk da clean + dedup dua tren normalized_text."""
    chunks = chunk_text_sentence_aware(raw_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    rows: list[dict[str, Any]] = []
    for idx, chunk in enumerate(chunks):
        cleaned = clean_raw_text(chunk)
        if len(cleaned) < min_chunk_length:
            continue
        normalized = normalize_text_value(cleaned)
        if not normalized:
            continue

        rows.append(
            {
                "chunk_index": idx,
                "chunk_text": cleaned,
                "normalized_text": normalized,
                "char_length": len(cleaned),
                "word_count": len(cleaned.split()),
                "language": detect_language_hint(cleaned),
            }
        )

    seen: set[str] = set()
    dedup_rows: list[dict[str, Any]] = []
    for row in rows:
        key = row["normalized_text"]
        if key in seen:
            continue
        seen.add(key)
        dedup_rows.append(row)

    return dedup_rows
