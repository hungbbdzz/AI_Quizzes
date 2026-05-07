from fastapi import APIRouter, Depends, status
from supabase import Client

from app.dependencies import get_supabase_admin, get_current_user
from app.models.flashcard import FlashcardGenerateRequest, FlashcardListResponse
from app.services import flashcard_service

router = APIRouter()


@router.post("/generate", response_model=FlashcardListResponse, status_code=status.HTTP_201_CREATED)
async def generate_flashcards(
    body: FlashcardGenerateRequest,
    current_user: dict = Depends(get_current_user),
    admin: Client = Depends(get_supabase_admin),
):
    """
    Tạo flashcards từ tài liệu bằng Gemini AI.
    - num_flashcards: số lượng thẻ muốn tạo (max 100)
    """
    return await flashcard_service.generate_flashcards(admin, body, current_user["id"])


@router.get("/{document_id}", response_model=FlashcardListResponse)
async def get_flashcards(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    admin: Client = Depends(get_supabase_admin),
):
    """Lấy toàn bộ flashcard của 1 tài liệu. Phải là chủ sở hữu tài liệu."""
    return await flashcard_service.get_flashcards_by_document(admin, document_id, current_user["id"])
