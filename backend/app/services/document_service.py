"""
Document Service — upload, trích xuất text, chunking, embedding.
Hỗ trợ PDF (pdfplumber), DOCX (python-docx), TXT.
"""

import uuid
import asyncio
import logging
from fastapi import UploadFile, HTTPException, status
from supabase import Client

from app.config import settings
from app.db.supabase_client import get_supabase_admin_client
from app.models.document import DocumentResponse, DocumentListResponse, SummarizeResponse
from app.services import document_pipeline
from app.services import ai_service

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

async def extract_text_from_file(file: UploadFile) -> str:
    """
    Trích xuất text từ file upload.
    - PDF: dùng pdfplumber (tốt hơn PyPDF2 cho tiếng Việt)
    - DOCX: dùng python-docx
    - TXT: đọc với encoding UTF-8
    Raise 422 nếu file rỗng hoặc không đọc được.
    """
    content = await file.read()
    await file.seek(0)

    return document_pipeline.extract_text_from_upload(
        file_name=file.filename or "",
        content_type=file.content_type or "",
        content=content,
    )


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Chia text thành các đoạn ~500 ký tự với overlap 50 ký tự.
    Dùng LangChain RecursiveCharacterTextSplitter.
    """
    return document_pipeline.chunk_text_sentence_aware(
        text,
        chunk_size=chunk_size,
        chunk_overlap=overlap,
    )


# ---------------------------------------------------------------------------
# Main upload pipeline
# ---------------------------------------------------------------------------

async def _run_embedding_background(document_id: str, raw_text: str, chunk_size: int, chunk_overlap: int, min_chunk_length: int):
    """
    Tạo embeddings và lưu document_chunks — chạy dưới background.
    Cập nhật status document thành 'ready' khi xong, 'error' nếu thất bại.
    """
    admin = get_supabase_admin_client()
    try:
        cleaned_chunks = document_pipeline.build_clean_chunks(
            raw_text=raw_text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            min_chunk_length=min_chunk_length,
        )

        chunks = [row["chunk_text"] for row in cleaned_chunks]
        if not chunks:
            logger.warning(f"[Embedding] Document {document_id}: không có chunks nào.")
            admin.table("documents").update({"status": "ready"}).eq("id", document_id).execute()
            return

        embeddings = await ai_service.create_embeddings_batch(chunks)

        chunk_records = [
            {
                "document_id": document_id,
                "chunk_text": row["chunk_text"],
                "embedding": emb,
                "chunk_index": row["chunk_index"],
            }
            for row, emb in zip(cleaned_chunks, embeddings)
        ]

        admin.table("document_chunks").insert(chunk_records).execute()
        logger.info(f"[Embedding] Document {document_id}: đã lưu {len(chunk_records)} chunks.")

    except Exception as e:
        logger.error(f"[Embedding] Document {document_id} thất bại: {e}")
        admin.table("documents").update({"status": "error"}).eq("id", document_id).execute()


async def process_upload(file: UploadFile, user_id: str) -> dict:
    """
    Pipeline upload:
    1. Kiểm tra kích thước file (max 10MB)
    2. Upload file lên Supabase Storage
    3. Extract text
    4. Lưu document vào DB với status='ready'
    5. Tạo embeddings ở BACKGROUND (không block response)
    6. Trả về document metadata ngay lập tức
    """
    admin = get_supabase_admin_client()

    # --- Bước 1: Kiểm tra kích thước ---
    file_bytes = await file.read()
    await file.seek(0)

    if len(file_bytes) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File vượt quá giới hạn {settings.MAX_FILE_SIZE_MB}MB.",
        )

    # Xác định file_type
    file_name = file.filename or "unknown"
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else "txt"
    if ext not in ["pdf", "docx", "txt"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chỉ chấp nhận file PDF, DOCX hoặc TXT.",
        )

    # --- Bước 2: Upload lên Supabase Storage ---
    storage_path = f"{user_id}/{uuid.uuid4()}_{file_name}"
    try:
        admin.storage.from_(settings.SUPABASE_STORAGE_BUCKET).upload(
            storage_path, file_bytes, {"content-type": file.content_type or "application/octet-stream"}
        )
        file_url = admin.storage.from_(settings.SUPABASE_STORAGE_BUCKET).get_public_url(storage_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Không thể upload file lên storage: {e}",
        )

    # --- Bước 3: Extract text ---
    raw_text = await extract_text_from_file(file)

    # --- Bước 4: Lưu document vào DB với status='ready' ngay ---
    doc_record = {
        "user_id": user_id,
        "file_name": file_name,
        "file_url": file_url,
        "file_type": ext,
        "raw_text": raw_text,
        "status": "ready",
    }
    try:
        doc_result = admin.table("documents").insert(doc_record).execute()
        document = doc_result.data[0]
        document_id = document["id"]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Không thể lưu document vào DB: {e}",
        )

    # --- Bước 5: Tạo embeddings ở background (không block response) ---
    asyncio.create_task(
        _run_embedding_background(
            document_id=document_id,
            raw_text=raw_text,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            min_chunk_length=settings.MIN_CHUNK_LENGTH,
        )
    )

    logger.info(f"[Upload] Document {document_id} đã lưu, embedding đang chạy nền.")
    return document



# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------

async def get_user_documents(admin: Client, user_id: str) -> DocumentListResponse:
    """Lấy danh sách tất cả tài liệu của user."""
    result = await asyncio.to_thread(
        lambda: admin.table("documents")
            .select("id, user_id, file_name, file_url, file_type, summary_text, status, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
    )
    docs = [DocumentResponse(**d) for d in result.data]
    return DocumentListResponse(documents=docs, total=len(docs))


async def get_document_by_id(admin: Client, document_id: str, user_id: str) -> DocumentResponse:
    """Lấy chi tiết 1 tài liệu, kiểm tra quyền truy cập."""
    result = await asyncio.to_thread(
        lambda: admin.table("documents")
            .select("id, user_id, file_name, file_url, file_type, summary_text, status, created_at")
            .eq("id", document_id)
            .eq("user_id", user_id)
            .single()
            .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài liệu.")
    return DocumentResponse(**result.data)


async def summarize_document(admin: Client, document_id: str, user_id: str) -> SummarizeResponse:
    """
    Gọi Gemini tóm tắt nội dung tài liệu.
    Lưu summary_text vào DB và trả về.
    """
    # Lấy raw_text
    result = await asyncio.to_thread(
        lambda: admin.table("documents")
            .select("id, user_id, raw_text, status")
            .eq("id", document_id)
            .eq("user_id", user_id)
            .single()
            .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài liệu.")

    doc = result.data
    if doc["status"] != "ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tài liệu chưa sẵn sàng (status: {doc['status']}).",
        )

    raw_text = doc.get("raw_text", "")
    if not raw_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài liệu không có nội dung text.",
        )

    summary = await ai_service.generate_summary(raw_text)

    # Lưu vào DB (to_thread)
    await asyncio.to_thread(
        lambda: admin.table("documents").update({"summary_text": summary}).eq("id", document_id).execute()
    )

    return SummarizeResponse(document_id=document_id, summary_text=summary)


async def delete_document(admin: Client, document_id: str, user_id: str):
    """Xoá tài liệu, kiểm tra quyền truy cập trước."""
    await get_document_by_id(admin, document_id, user_id)
    # chunks và liên kết khác sẽ bị xoá cascade
    await asyncio.to_thread(
        lambda: admin.table("documents").delete().eq("id", document_id).execute()
    )
