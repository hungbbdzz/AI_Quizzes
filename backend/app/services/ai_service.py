"""
AI Service — tất cả các lời gọi Gemini tập trung tại đây.
Model: gemini-1.5-pro (text generation), text-embedding-004 (embeddings).

QUAN TRỌNG: Tất cả chain.invoke() và model.embed_*() là SYNCHRONOUS.
Dùng asyncio.to_thread() để chạy chúng trong thread pool,
tránh block event loop của FastAPI và làm treo toàn bộ server.
"""

import json
import re
import asyncio

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from fastapi import HTTPException, status

from app.config import settings
from app.db.supabase_client import get_supabase_admin_client


# ---------------------------------------------------------------------------
# Model factories
# ---------------------------------------------------------------------------

def _get_llm(temperature: float = 0.7, fallback_to_ollama: bool = True):
    """
    Trả về LLM dựa trên provider được cấu hình trong settings.
    Nếu fallback_to_ollama=True, sẽ cố gắng dùng Ollama nếu provider chính lỗi.
    """
    primary_provider = settings.AI_PROVIDER
    
    def create_gemini():
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=temperature,
        )
    
    def create_ollama():
        return ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=temperature,
        )

    if primary_provider == "ollama":
        return create_ollama()
    
    # Default to Gemini
    return create_gemini()

async def _invoke_llm_with_fallback(prompt, inputs, temperature=0.7, fallback_to_ollama=True):
    """
    Hàm wrapper để gọi LLM với cơ chế fallback.
    Nếu provider chính lỗi, sẽ thử chuyển sang provider còn lại.
    """
    original_provider = settings.AI_PROVIDER
    
    try:
        # Thử với provider chính
        llm = _get_llm(temperature=temperature)
        chain = prompt | llm
        return await asyncio.to_thread(chain.invoke, inputs)
    except Exception as e:
        if not fallback_to_ollama:
            raise e
        
        print(f"[AI SERVICE] Primary provider {original_provider} failed: {e}. Attempting fallback...")
        
        try:
            # Chuyển provider
            settings.AI_PROVIDER = "ollama" if original_provider == "gemini" else "gemini"
            llm = _get_llm(temperature=temperature)
            chain = prompt | llm
            result = await asyncio.to_thread(chain.invoke, inputs)
            return result
        except Exception as fallback_e:
            print(f"[AI SERVICE] Fallback provider also failed: {fallback_e}")
            raise e # Trả về lỗi của provider chính nếu cả hai đều lỗi
        finally:
            settings.AI_PROVIDER = original_provider


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
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw.strip())


# ---------------------------------------------------------------------------
# Embeddings — dùng asyncio.to_thread để không block event loop
# ---------------------------------------------------------------------------

async def create_embedding(text: str) -> list[float]:
    """Tạo vector embedding cho 1 đoạn text (chạy trong thread pool)."""
    try:
        model = _get_embeddings()
        return await asyncio.to_thread(model.embed_query, text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Không thể tạo embedding: {e}",
        )


async def create_embeddings_batch(texts: list[str], batch_size: int = 50) -> list[list[float]]:
    """
    Tạo embeddings cho nhiều đoạn text.
    Chia thành batch nhỏ và chạy trong thread pool để không block event loop.
    """
    try:
        model = _get_embeddings()
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = await asyncio.to_thread(model.embed_documents, batch)
            all_embeddings.extend(embeddings)
        return all_embeddings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Không thể tạo embeddings: {e}",
        )


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

async def generate_summary(raw_text: str) -> str:
    """Tóm tắt nội dung tài liệu (chạy trong thread pool)."""
    SUMMARY_PROMPT = PromptTemplate(
        input_variables=["raw_text"],
        template="""Hãy tóm tắt nội dung tài liệu sau đây một cách ngắn gọn, súc tích, giữ lại các ý chính và kiến thức quan trọng. Trả lời bằng ngôn ngữ của tài liệu (tiếng Việt hoặc tiếng Anh).

Tài liệu:
{raw_text}""",
    )

    try:
        if len(raw_text) <= 30000:
            response = await _invoke_llm_with_fallback(SUMMARY_PROMPT, {"raw_text": raw_text}, temperature=0.3)
            return response.content.strip()

        # Text dài: chunk và tóm tắt từng phần
        chunks = [raw_text[i:i+25000] for i in range(0, len(raw_text), 25000)]
        partial_summaries = []

        for chunk in chunks:
            resp = await _invoke_llm_with_fallback(SUMMARY_PROMPT, {"raw_text": chunk}, temperature=0.3)
            partial_summaries.append(resp.content.strip())

        combined = "\n\n---\n\n".join(partial_summaries)
        final_prompt = PromptTemplate(
            input_variables=["raw_text"],
            template="""Dưới đây là nhiều bản tóm tắt từng phần của một tài liệu dài. Hãy tổng hợp thành một bản tóm tắt hoàn chỉnh, súc tích:

{raw_text}""",
        )
        response = await _invoke_llm_with_fallback(final_prompt, {"raw_text": combined}, temperature=0.3)
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
    Sinh câu hỏi trắc nghiệm từ nội dung tài liệu (chạy trong thread pool).
    Retry tối đa 3 lần nếu JSON response không hợp lệ.
    """
    QUIZ_PROMPT = PromptTemplate(
        input_variables=["num_questions", "difficulty", "raw_text"],
        template="""Tạo {num_questions} câu trắc nghiệm độ khó {difficulty} từ tài liệu. Mỗi câu có 4 đáp án A/B/C/D, chỉ 1 đúng. Chỉ trả về JSON array, không markdown:
[{{"question":"...","options":{{"A":"...","B":"...","C":"...","D":"..."}},"correct_answer":"A"}}]

Tài liệu:
{raw_text}""",
    )

    last_error = None

    for attempt in range(3):
        try:
            response = await _invoke_llm_with_fallback(QUIZ_PROMPT, {
                "num_questions": num_questions,
                "difficulty": difficulty,
                "raw_text": raw_text[:8000],
            }, temperature=0.5)
            questions = _parse_json_response(response.content)

            if not isinstance(questions, list):
                raise ValueError("Response phải là JSON array")
            for q in questions:
                if not all(k in q for k in ["question", "options", "correct_answer"]):
                    raise ValueError(f"Câu hỏi thiếu trường: {q}")
                if q["correct_answer"] not in ["A", "B", "C", "D"]:
                    raise ValueError(f"correct_answer phải là A/B/C/D")
                if set(q["options"].keys()) != {"A", "B", "C", "D"}:
                    raise ValueError("options phải có đúng 4 key A,B,C,D")

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
    Sinh flashcards từ nội dung tài liệu (chạy trong thread pool).
    Retry tối đa 3 lần nếu JSON không hợp lệ.
    """
    FLASHCARD_PROMPT = PromptTemplate(
        input_variables=["num_flashcards", "raw_text"],
        template="""Tạo {num_flashcards} flashcard ôn tập từ tài liệu. Mặt trước: khái niệm/câu hỏi ngắn. Mặt sau: định nghĩa/giải thích. Chỉ trả về JSON array:
[{{"front":"...","back":"..."}}]

Tài liệu:
{raw_text}""",
    )

    last_error = None

    for attempt in range(3):
        try:
            response = await _invoke_llm_with_fallback(FLASHCARD_PROMPT, {
                "num_flashcards": num_flashcards,
                "raw_text": raw_text[:8000],
            }, temperature=0.6)
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
        question_embedding = await create_embedding(question_text)

        admin = get_supabase_admin_client()
        result = await asyncio.to_thread(
            lambda: admin.rpc(
                "match_document_chunks",
                {
                    "query_embedding": question_embedding,
                    "filter_document_id": document_id,
                    "match_count": top_k,
                },
            ).execute()
        )

        if result.data:
            return [row["chunk_text"] for row in result.data]
        return []

    except Exception as e:
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
    """Giải thích tại sao câu trả lời của người dùng sai (chạy trong thread pool)."""
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
        response = await _invoke_llm_with_fallback(EXPLAIN_PROMPT, {
            "question_text": question_text,
            "correct_answer": correct_answer,
            "user_answer": user_answer,
            "relevant_chunks": chunks_text,
        }, temperature=0.4)
        return response.content.strip()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Không thể tạo giải thích: {e}",
        )
