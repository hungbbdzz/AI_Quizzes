import pytest

from app.services.document_pipeline import (
    build_clean_chunks,
    chunk_text_sentence_aware,
    clean_raw_text,
    detect_language_hint,
    normalize_text_value,
)


class TestTextCleaning:
    def test_clean_raw_text_keeps_vietnamese(self):
        text = "Học sinh    cần ôn tập bài hôm nay"
        cleaned = clean_raw_text(text)
        assert "Học sinh" in cleaned
        assert "  " not in cleaned

    def test_normalize_text_value_ascii(self):
        normalized = normalize_text_value("Học sinh cần ôn tập")
        assert normalized == "hoc sinh can on tap"

    def test_detect_language_hint(self):
        assert detect_language_hint("Đây là tiếng Việt") == "vi"
        assert detect_language_hint("This is English text") == "en"


class TestChunking:
    def test_chunk_short_text(self):
        text = "Đây là đoạn ngắn."
        chunks = chunk_text_sentence_aware(text, chunk_size=100, chunk_overlap=20)
        assert chunks == [text]

    def test_chunk_long_text(self):
        text = "Câu hỏi trắc nghiệm giúp học nhanh. " * 80
        chunks = chunk_text_sentence_aware(text, chunk_size=250, chunk_overlap=50)
        assert len(chunks) > 1

    def test_build_clean_chunks_deduplicates(self):
        text = "Học sinh cần ôn tập. Hoc sinh can on tap. Học sinh cần ôn tập."
        rows = build_clean_chunks(
            raw_text=text,
            chunk_size=120,
            chunk_overlap=30,
            min_chunk_length=5,
        )
        assert len(rows) >= 1
        normalized_values = [row["normalized_text"] for row in rows]
        assert len(normalized_values) == len(set(normalized_values))


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("", ""),
        ("   ", ""),
        ("Q&amp;A", "Q&A"),
    ],
)
def test_clean_raw_text_parametrized(raw, expected):
    assert clean_raw_text(raw) == expected
