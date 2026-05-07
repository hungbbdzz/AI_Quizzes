from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Literal


DocumentStatus = Literal["processing", "ready", "error"]
FileType = Literal["pdf", "docx", "txt"]


class DocumentResponse(BaseModel):
    id: str
    user_id: str
    file_name: str
    file_url: Optional[str] = None
    file_type: Optional[FileType] = None
    summary_text: Optional[str] = None
    status: DocumentStatus
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int


class SummarizeResponse(BaseModel):
    document_id: str
    summary_text: str
