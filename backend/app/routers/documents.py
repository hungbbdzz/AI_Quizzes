from fastapi import APIRouter, Depends, UploadFile, File, status
from supabase import Client

from app.dependencies import get_supabase_admin, get_current_user
from app.models.document import DocumentResponse, DocumentListResponse, SummarizeResponse
from app.services import document_service

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    admin: Client = Depends(get_supabase_admin),
):
    """
    Upload file PDF/DOCX/TXT, trích xuất text, tạo embeddings và lưu DB.
    Giới hạn: tối đa 10MB. Xử lý bất đồng bộ.
    """
    doc = await document_service.process_upload(file, current_user["id"])
    return DocumentResponse(**doc)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    current_user: dict = Depends(get_current_user),
    admin: Client = Depends(get_supabase_admin),
):
    """Lấy danh sách tất cả tài liệu của user hiện tại."""
    return await document_service.get_user_documents(admin, current_user["id"])


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user),
    admin: Client = Depends(get_supabase_admin),
):
    """Lấy chi tiết 1 tài liệu. Chỉ truy cập được tài liệu của chính mình."""
    return await document_service.get_document_by_id(admin, doc_id, current_user["id"])


@router.post("/{doc_id}/summarize", response_model=SummarizeResponse)
async def summarize_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user),
    admin: Client = Depends(get_supabase_admin),
):
    """
    Gọi Gemini tóm tắt nội dung tài liệu.
    Kết quả được lưu vào cột summary_text trong DB.
    """
    return await document_service.summarize_document(admin, doc_id, current_user["id"])


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user),
    admin: Client = Depends(get_supabase_admin),
):
    """Xoá tài liệu và tất cả dữ liệu liên quan (cascade)."""
    await document_service.delete_document(admin, doc_id, current_user["id"])
