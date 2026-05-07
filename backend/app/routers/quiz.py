from fastapi import APIRouter, Depends, status
from supabase import Client

from app.dependencies import get_supabase_admin, get_current_user
from app.models.quiz import (
    QuizGenerateRequest,
    QuizSetResponse,
    QuizListResponse,
    QuizSubmitRequest,
    SubmissionResponse,
)
from app.services import quiz_service

router = APIRouter()


@router.post("/generate", response_model=QuizSetResponse, status_code=status.HTTP_201_CREATED)
async def generate_quiz(
    body: QuizGenerateRequest,
    current_user: dict = Depends(get_current_user),
    admin: Client = Depends(get_supabase_admin),
):
    """
    Tạo bộ câu hỏi từ tài liệu bằng Gemini AI.
    - num_questions: 5-50 câu
    - difficulty: easy | medium | hard
    """
    return await quiz_service.generate_quiz(admin, body, current_user["id"])


@router.get("", response_model=QuizListResponse)
async def list_quizzes(
    current_user: dict = Depends(get_current_user),
    admin: Client = Depends(get_supabase_admin),
):
    """Lấy danh sách tất cả quiz của user (qua tài liệu thuộc về user)."""
    return await quiz_service.get_user_quizzes(admin, current_user["id"])


@router.get("/community", response_model=QuizListResponse)
async def get_community_quizzes(admin: Client = Depends(get_supabase_admin)):
    """Lấy danh sách quiz công khai (is_shared = true). Không cần auth."""
    return await quiz_service.get_community_quizzes(admin)


@router.get("/{quiz_id}", response_model=QuizSetResponse)
async def get_quiz(
    quiz_id: str,
    current_user: dict = Depends(get_current_user),
    admin: Client = Depends(get_supabase_admin),
):
    """Lấy chi tiết quiz kèm câu hỏi (không có đáp án đúng — chỉ hiển thị khi làm bài)."""
    return await quiz_service.get_quiz_by_id(admin, quiz_id, current_user["id"])


@router.post("/{quiz_id}/submit", response_model=SubmissionResponse)
async def submit_quiz(
    quiz_id: str,
    body: QuizSubmitRequest,
    current_user: dict = Depends(get_current_user),
    admin: Client = Depends(get_supabase_admin),
):
    """
    Nộp bài làm, chấm điểm và lưu kết quả.
    Trả về score, số câu đúng và kết quả từng câu.
    """
    return await quiz_service.submit_quiz(admin, quiz_id, body, current_user["id"])

from pydantic import BaseModel
class ShareRequest(BaseModel):
    is_shared: bool

@router.patch("/{quiz_id}/share")
async def share_quiz(
    quiz_id: str,
    body: ShareRequest,
    current_user: dict = Depends(get_current_user),
    admin: Client = Depends(get_supabase_admin),
):
    """Bật/tắt chế độ public cho quiz."""
    return await quiz_service.toggle_share_quiz(admin, quiz_id, body.is_shared, current_user["id"])
