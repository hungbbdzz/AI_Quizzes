"""
Document Service — upload, trích xuất text, chunking, embedding.
Hỗ trợ PDF (pdfplumber), DOCX (python-docx), TXT.
"""

import io
import uuid
from fastapi import UploadFile, HTTPException, status
from supabase import Client

from app.config import settings
from app.db.supabase_client import get_supabase_admin_client
from app.models.document import DocumentResponse, DocumentListResponse, SummarizeResponse
from app.services import ai_service
from langchain.text_splitter import RecursiveCharacterTextSplitter


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

    file_name = file.filename or ""
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""

    # Xác định loại file từ content_type hoặc extension
    content_type = file.content_type or ""

    if "pdf" in content_type or ext == "pdf":
        return _extract_pdf(content, file_name)
    elif "docx" in content_type or "word" in content_type or ext == "docx":
        return _extract_docx(content, file_name)
    elif "text" in content_type or ext == "txt":
        return _extract_txt(content, file_name)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Định dạng file không được hỗ trợ: {file_name}. Chỉ chấp nhận PDF, DOCX, TXT.",
        )


def _extract_pdf(content: bytes, file_name: str) -> str:
    """Trích xuất text từ PDF dùng pdfplumber."""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            pages_text = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
            result = "\n\n".join(pages_text).strip()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Không thể đọc file PDF '{file_name}': {e}",
        )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File PDF '{file_name}' không có nội dung text có thể trích xuất.",
        )
    return result


def _extract_docx(content: bytes, file_name: str) -> str:
    """Trích xuất text từ DOCX dùng python-docx."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(content))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        result = "\n\n".join(paragraphs).strip()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Không thể đọc file DOCX '{file_name}': {e}",
        )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File DOCX '{file_name}' không có nội dung.",
        )
    return result


def _extract_txt(content: bytes, file_name: str) -> str:
    """Đọc file TXT với encoding UTF-8."""
    try:
        result = content.decode("utf-8", errors="replace").strip()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Không thể đọc file TXT '{file_name}': {e}",
        )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File '{file_name}' rỗng.",
        )
    return result


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Chia text thành các đoạn ~500 ký tự với overlap 50 ký tự.
    Dùng LangChain RecursiveCharacterTextSplitter.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    return splitter.split_text(text)


# ---------------------------------------------------------------------------
# Main upload pipeline
# ---------------------------------------------------------------------------

async def process_upload(file: UploadFile, user_id: str) -> dict:
    """
    Pipeline upload đầy đủ:
    1. Kiểm tra kích thước file (max 10MB)
    2. Upload file lên Supabase Storage
    3. Extract text
    4. Chunk text
    5. Tạo embeddings và lưu document_chunks
    6. Lưu document vào DB với status='ready'
    7. Trả về document metadata
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

    # --- Bước 4: Lưu document ban đầu với status='processing' ---
    doc_record = {
        "user_id": user_id,
        "file_name": file_name,
        "file_url": file_url,
        "file_type": ext,
        "raw_text": raw_text,
        "status": "processing",
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

    # --- Bước 5: Chunk + Embed + Lưu document_chunks ---
    try:
        chunks = chunk_text(raw_text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
        embeddings = await ai_service.create_embeddings_batch(chunks)

        chunk_records = [
            {
                "document_id": document_id,
                "chunk_text": chunk,
                "embedding": emb,
                "chunk_index": i,
            }
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
        ]

        if chunk_records:
            admin.table("document_chunks").insert(chunk_records).execute()
    except Exception as e:
        # Không fail hoàn toàn — đánh dấu error nhưng vẫn có document
        admin.table("documents").update({"status": "error"}).eq("id", document_id).execute()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tạo embeddings: {e}",
        )

    # --- Bước 6: Cập nhật status thành 'ready' ---
    admin.table("documents").update({"status": "ready"}).eq("id", document_id).execute()
    document["status"] = "ready"

    return document


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------

async def get_user_documents(admin: Client, user_id: str) -> DocumentListResponse:
    """Lấy danh sách tất cả tài liệu của user."""
    result = (
        admin.table("documents")
        .select("id, user_id, file_name, file_url, file_type, summary_text, status, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    docs = [DocumentResponse(**d) for d in result.data]
    return DocumentListResponse(documents=docs, total=len(docs))


async def get_document_by_id(admin: Client, document_id: str, user_id: str) -> DocumentResponse:
    """Lấy chi tiết 1 tài liệu, kiểm tra quyền truy cập."""
    result = (
        admin.table("documents")
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
    result = (
        admin.table("documents")
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

    # Lưu vào DB
    admin.table("documents").update({"summary_text": summary}).eq("id", document_id).execute()

    return SummarizeResponse(document_id=document_id, summary_text=summary)


async def delete_document(admin: Client, document_id: str, user_id: str):
    """Xoá tài liệu, kiểm tra quyền truy cập trước."""
    doc = await get_document_by_id(admin, document_id, user_id)
    # chunks và liên kết khác sẽ bị xoá cascade
    admin.table("documents").delete().eq("id", document_id).execute()
