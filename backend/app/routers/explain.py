from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from supabase import Client

from app.dependencies import get_supabase_admin, get_current_user
from app.services import ai_service

router = APIRouter()


class ExplainResponse(BaseModel):
    answer_id: str
    explanation: str


@router.post("/{answer_id}", response_model=ExplainResponse)
async def explain_answer(
    answer_id: str,
    current_user: dict = Depends(get_current_user),
    admin: Client = Depends(get_supabase_admin),
):
    """
    Giải thích tại sao câu trả lời sai, dùng RAG:
    1. Lấy thông tin câu hỏi + câu trả lời từ DB
    2. Tìm document_id liên quan
    3. pgvector similarity search để tìm chunks liên quan nhất
    4. Gọi Gemini với context chunks để giải thích
    5. Lưu explanation vào user_answers
    """
    # Bước 1: Lấy user_answer kèm question và submission info
    answer_result = (
        admin.table("user_answers")
        .select(
            "id, selected_answer, is_correct, ai_explanation, "
            "questions(id, question_text, correct_answer, quiz_set_id, "
            "  quiz_sets(document_id)), "
            "submissions(user_id)"
        )
        .eq("id", answer_id)
        .single()
        .execute()
    )

    if not answer_result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy câu trả lời.")

    answer = answer_result.data

    # Kiểm tra quyền — chỉ user sở hữu submission mới được xem giải thích
    submission_user_id = answer.get("submissions", {}).get("user_id")
    if submission_user_id != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền xem giải thích này.")

    # Nếu đã có cached explanation thì trả về ngay
    if answer.get("ai_explanation"):
        return ExplainResponse(answer_id=answer_id, explanation=answer["ai_explanation"])

    # Câu trả lời đúng thì không cần giải thích sai
    if answer.get("is_correct"):
        explanation = "Bạn đã trả lời đúng! Không cần giải thích thêm."
        admin.table("user_answers").update({"ai_explanation": explanation}).eq("id", answer_id).execute()
        return ExplainResponse(answer_id=answer_id, explanation=explanation)

    # Lấy thông tin câu hỏi
    question = answer.get("questions", {})
    question_text = question.get("question_text", "")
    correct_answer = question.get("correct_answer", "")
    selected_answer = answer.get("selected_answer", "")

    # Lấy document_id từ quiz_sets
    quiz_set = question.get("quiz_sets", {})
    document_id = quiz_set.get("document_id")

    # Bước 2: RAG — tìm chunks liên quan
    relevant_chunks = []
    if document_id:
        relevant_chunks = await ai_service.find_relevant_chunks(
            question_text=question_text,
            document_id=document_id,
            top_k=3,
        )

    # Bước 3: Gọi Gemini giải thích
    explanation = await ai_service.explain_wrong_answer(
        question_text=question_text,
        correct_answer=correct_answer,
        user_answer=selected_answer,
        relevant_chunks=relevant_chunks,
    )

    # Bước 4: Lưu vào DB (cache)
    admin.table("user_answers").update({"ai_explanation": explanation}).eq("id", answer_id).execute()

    return ExplainResponse(answer_id=answer_id, explanation=explanation)
