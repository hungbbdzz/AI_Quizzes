"""
AI Service — tất cả các lời gọi Gemini tập trung tại đây.
Model: gemini-1.5-pro (text generation), text-embedding-004 (embeddings).
"""

import json
import re
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.prompts import PromptTemplate
from fastapi import HTTPException, status

from app.config import settings
from app.db.supabase_client import get_supabase_admin_client


# ---------------------------------------------------------------------------
# Model factories
# ---------------------------------------------------------------------------

def _get_llm(temperature: float = 0.7) -> ChatGoogleGenerativeAI:
    """Trả về LangChain wrapper cho Gemini 1.5 Pro."""
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=temperature,
    )


def _get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Trả về model embedding text-embedding-004 (768 dims)."""
    return GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=settings.GEMINI_API_KEY,
    )


# ---------------------------------------------------------------------------
# Helper: parse JSON từ Gemini (loại bỏ markdown fences nếu có)
# ---------------------------------------------------------------------------

def _parse_json_response(raw: str) -> list | dict:
    """Parse JSON response từ Gemini, xử lý cả trường hợp có markdown code fence."""
    raw = raw.strip()
    # Loại bỏ ```json ... ``` hoặc ``` ... ```
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw.strip())


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------

async def create_embedding(text: str) -> list[float]:
    """
    Tạo vector embedding cho 1 đoạn text.
    Dùng Gemini text-embedding-004 (768 chiều).
    """
    try:
        model = _get_embeddings()
        return model.embed_query(text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Không thể tạo embedding: {e}",
        )


async def create_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Tạo embeddings cho nhiều đoạn text cùng lúc.
    Dùng embed_documents() để tối ưu API calls.
    """
    try:
        model = _get_embeddings()
        return model.embed_documents(texts)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Không thể tạo embeddings: {e}",
        )


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

async def generate_summary(raw_text: str) -> str:
    """
    Tóm tắt nội dung tài liệu bằng Gemini.
    Nếu text > 30000 ký tự: chunk và tóm tắt nhiều lần rồi tổng hợp lại.
    """
    llm = _get_llm(temperature=0.3)

    SUMMARY_PROMPT = PromptTemplate(
        input_variables=["raw_text"],
        template="""Hãy tóm tắt nội dung tài liệu sau đây một cách ngắn gọn, súc tích, giữ lại các ý chính và kiến thức quan trọng. Trả lời bằng ngôn ngữ của tài liệu (tiếng Việt hoặc tiếng Anh).

Tài liệu:
{raw_text}""",
    )

    try:
        if len(raw_text) <= 30000:
            chain = SUMMARY_PROMPT | llm
            response = chain.invoke({"raw_text": raw_text})
            return response.content.strip()

        # Text dài: chunk và tóm tắt từng phần
        chunks = [raw_text[i:i+25000] for i in range(0, len(raw_text), 25000)]
        partial_summaries = []

        for chunk in chunks:
            chain = SUMMARY_PROMPT | llm
            resp = chain.invoke({"raw_text": chunk})
            partial_summaries.append(resp.content.strip())

        # Tóm tắt lại từ các partial summaries
        combined = "\n\n---\n\n".join(partial_summaries)
        final_prompt = PromptTemplate(
            input_variables=["raw_text"],
            template="""Dưới đây là nhiều bản tóm tắt từng phần của một tài liệu dài. Hãy tổng hợp thành một bản tóm tắt hoàn chỉnh, súc tích:

{raw_text}""",
        )
        chain = final_prompt | llm
        response = chain.invoke({"raw_text": combined})
        return response.content.strip()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Không thể tóm tắt tài liệu: {e}",
        )


# ---------------------------------------------------------------------------
# Quiz generation
# ---------------------------------------------------------------------------

async def generate_quiz(raw_text: str, num_questions: int, difficulty: str) -> list[dict]:
    """
    Sinh câu hỏi trắc nghiệm từ nội dung tài liệu.
    Retry tối đa 2 lần nếu JSON response không hợp lệ.
    
    Returns:
        list[dict]: [{"question": "...", "options": {"A":...,"B":...,"C":...,"D":...}, "correct_answer": "A"}]
    """
    llm = _get_llm(temperature=0.5)

    QUIZ_PROMPT = PromptTemplate(
        input_variables=["num_questions", "difficulty", "raw_text"],
        template="""Dựa trên nội dung tài liệu sau, hãy tạo {num_questions} câu hỏi trắc nghiệm mức độ {difficulty}.

Yêu cầu:
- Mỗi câu có đúng 4 đáp án (A, B, C, D), chỉ 1 đáp án đúng
- Câu hỏi phải bám sát nội dung tài liệu, không bịa đặt
- Độ khó: easy=ghi nhớ trực tiếp, medium=hiểu và áp dụng, hard=phân tích và tổng hợp
- Trả về JSON hợp lệ, KHÔNG có markdown, KHÔNG có giải thích thêm

Format JSON bắt buộc:
[
  {{
    "question": "nội dung câu hỏi",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "correct_answer": "A"
  }}
]

Tài liệu:
{raw_text}""",
    )

    chain = QUIZ_PROMPT | llm
    last_error = None

    for attempt in range(3):  # Retry tối đa 2 lần (3 lần tổng cộng)
        try:
            response = chain.invoke({
                "num_questions": num_questions,
                "difficulty": difficulty,
                "raw_text": raw_text[:12000],
            })
            questions = _parse_json_response(response.content)

            # Validate cấu trúc
            if not isinstance(questions, list):
                raise ValueError("Response phải là JSON array")
            for q in questions:
                if not all(k in q for k in ["question", "options", "correct_answer"]):
                    raise ValueError(f"Câu hỏi thiếu trường: {q}")
                if q["correct_answer"] not in ["A", "B", "C", "D"]:
                    raise ValueError(f"correct_answer phải là A/B/C/D, nhận: {q['correct_answer']}")
                if set(q["options"].keys()) != {"A", "B", "C", "D"}:
                    raise ValueError(f"options phải có đúng 4 key A,B,C,D")

            return questions[:num_questions]

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            last_error = e
            if attempt < 2:
                continue

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Gemini trả về JSON không hợp lệ sau 3 lần thử: {last_error}",
    )


# ---------------------------------------------------------------------------
# Flashcard generation
# ---------------------------------------------------------------------------

async def generate_flashcards(raw_text: str, num_flashcards: int) -> list[dict]:
    """
    Sinh flashcards từ nội dung tài liệu.
    Retry tối đa 2 lần nếu JSON không hợp lệ.
    
    Returns:
        list[dict]: [{"front": "...", "back": "..."}]
    """
    llm = _get_llm(temperature=0.6)

    FLASHCARD_PROMPT = PromptTemplate(
        input_variables=["num_flashcards", "raw_text"],
        template="""Dựa trên nội dung tài liệu sau, hãy tạo {num_flashcards} thẻ ghi nhớ (flashcard) để ôn tập.

Yêu cầu:
- Mặt trước (front): thuật ngữ, khái niệm, hoặc câu hỏi ngắn
- Mặt sau (back): định nghĩa, giải thích, hoặc đáp án
- Trả về JSON hợp lệ, KHÔNG có markdown

Format JSON bắt buộc:
[{{"front": "...", "back": "..."}}]

Tài liệu:
{raw_text}""",
    )

    chain = FLASHCARD_PROMPT | llm
    last_error = None

    for attempt in range(3):
        try:
            response = chain.invoke({
                "num_flashcards": num_flashcards,
                "raw_text": raw_text[:12000],
            })
            cards = _parse_json_response(response.content)

            if not isinstance(cards, list):
                raise ValueError("Response phải là JSON array")
            for card in cards:
                if "front" not in card or "back" not in card:
                    raise ValueError(f"Flashcard thiếu trường front/back: {card}")

            return cards[:num_flashcards]

        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            if attempt < 2:
                continue

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Gemini trả về JSON không hợp lệ sau 3 lần thử: {last_error}",
    )


# ---------------------------------------------------------------------------
# RAG — tìm chunks liên quan bằng pgvector
# ---------------------------------------------------------------------------

async def find_relevant_chunks(question_text: str, document_id: str, top_k: int = 3) -> list[str]:
    """
    Tìm top_k đoạn tài liệu liên quan nhất đến câu hỏi.
    Dùng Gemini embedding + pgvector cosine similarity search.
    """
    try:
        # Embed câu hỏi
        question_embedding = await create_embedding(question_text)

        # Gọi pgvector similarity search qua Supabase RPC
        admin = get_supabase_admin_client()
        result = admin.rpc(
            "match_document_chunks",
            {
                "query_embedding": question_embedding,
                "filter_document_id": document_id,
                "match_count": top_k,
            },
        ).execute()

        if result.data:
            return [row["chunk_text"] for row in result.data]
        return []

    except Exception as e:
        # Không raise error — fallback về empty list nếu RAG thất bại
        print(f"[WARN] RAG search thất bại: {e}")
        return []


# ---------------------------------------------------------------------------
# Explain wrong answer
# ---------------------------------------------------------------------------

async def explain_wrong_answer(
    question_text: str,
    correct_answer: str,
    user_answer: str,
    relevant_chunks: list[str],
) -> str:
    """
    Giải thích tại sao câu trả lời của người dùng sai.
    Đối chiếu với relevant_chunks từ tài liệu gốc.
    """
    llm = _get_llm(temperature=0.4)

    chunks_text = "\n\n---\n\n".join(relevant_chunks) if relevant_chunks else "(Không tìm thấy đoạn liên quan)"

    EXPLAIN_PROMPT = PromptTemplate(
        input_variables=["question_text", "correct_answer", "user_answer", "relevant_chunks"],
        template="""Người dùng vừa trả lời sai một câu hỏi trắc nghiệm. Hãy giải thích tại sao câu trả lời của họ sai và tại sao đáp án đúng lại đúng, dựa trên nội dung tài liệu.

Câu hỏi: {question_text}
Đáp án đúng: {correct_answer}
Đáp án người dùng chọn: {user_answer}

Đoạn tài liệu liên quan:
{relevant_chunks}

Hãy giải thích rõ ràng, dễ hiểu bằng tiếng Việt (hoặc ngôn ngữ của câu hỏi). Chỉ ra cụ thể lỗ hổng kiến thức và dẫn chứng từ tài liệu.""",
    )

    try:
        chain = EXPLAIN_PROMPT | llm
        response = chain.invoke({
            "question_text": question_text,
            "correct_answer": correct_answer,
            "user_answer": user_answer,
            "relevant_chunks": chunks_text,
        })
        return response.content.strip()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Không thể tạo giải thích: {e}",
        )
