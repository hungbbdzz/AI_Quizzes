from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class FlashcardGenerateRequest(BaseModel):
    document_id: str
    num_flashcards: int = Field(default=15, ge=1, le=100)

    class Config:
        json_schema_extra = {
            "example": {"document_id": "uuid-here", "num_flashcards": 15}
        }


class FlashcardResponse(BaseModel):
    id: str
    document_id: str
    front_text: str
    back_text: str
    created_at: datetime

    class Config:
        from_attributes = True


class FlashcardListResponse(BaseModel):
    flashcards: List[FlashcardResponse]
    total: int
