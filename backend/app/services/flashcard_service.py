"""
Flashcard Service — tạo và lấy flashcards từ tài liệu.
"""

from fastapi import HTTPException, status
from supabase import Client

from app.models.flashcard import (
    FlashcardGenerateRequest,
    FlashcardResponse,
    FlashcardListResponse,
)
from app.services import ai_service


async def generate_flashcards(
    admin: Client,
    body: FlashcardGenerateRequest,
    user_id: str,
) -> FlashcardListResponse:
    """
    Tạo flashcards từ tài liệu:
    1. Kiểm tra quyền truy cập tài liệu
    2. Gọi AI sinh flashcards
    3. Lưu vào bảng flashcards
    """
    # Kiểm tra tài liệu tồn tại và thuộc về user
    doc_result = (
        admin.table("documents")
        .select("id, user_id, raw_text, file_name, status")
        .eq("id", body.document_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not doc_result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài liệu.")

    doc = doc_result.data
    if doc["status"] != "ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tài liệu chưa sẵn sàng (status: {doc['status']}).",
        )

    raw_text = doc.get("raw_text", "")
    if not raw_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tài liệu không có nội dung.")

    # Gọi AI
    cards_data = await ai_service.generate_flashcards(
        raw_text=raw_text,
        num_flashcards=body.num_flashcards,
    )

    # Lưu vào DB
    card_records = [
        {
            "document_id": body.document_id,
            "front_text": card["front"],
            "back_text": card["back"],
        }
        for card in cards_data
    ]
    result = admin.table("flashcards").insert(card_records).execute()
    flashcards = [FlashcardResponse(**c) for c in result.data]

    return FlashcardListResponse(flashcards=flashcards, total=len(flashcards))


async def get_flashcards_by_document(
    admin: Client,
    document_id: str,
    user_id: str,
) -> FlashcardListResponse:
    """
    Lấy toàn bộ flashcard của 1 tài liệu.
    Kiểm tra quyền truy cập tài liệu trước.
    """
    # Kiểm tra quyền
    doc_result = (
        admin.table("documents")
        .select("id")
        .eq("id", document_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not doc_result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài liệu.")

    result = (
        admin.table("flashcards")
        .select("*")
        .eq("document_id", document_id)
        .order("created_at")
        .execute()
    )
    flashcards = [FlashcardResponse(**c) for c in result.data]
    return FlashcardListResponse(flashcards=flashcards, total=len(flashcards))
