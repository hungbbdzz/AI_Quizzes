from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AI Quiz & Flashcard System"
    DEBUG: bool = False

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str           # anon key — dùng cho auth từ client
    SUPABASE_SERVICE_KEY: str   # service role key — dùng cho admin operations

    # Google Gemini AI
    GEMINI_API_KEY: str

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Storage
    SUPABASE_STORAGE_BUCKET: str = "documents"
    MAX_FILE_SIZE_MB: int = 10

    # AI / Chunking settings
    CHUNK_SIZE: int = 500       # tokens per chunk
    CHUNK_OVERLAP: int = 50
    MIN_CHUNK_LENGTH: int = 50

    # Validation limits
    MIN_QUESTIONS: int = 5
    MAX_QUESTIONS: int = 50
    MAX_FLASHCARDS: int = 100

    # Embedding dimension (Gemini text-embedding-004)
    EMBEDDING_DIM: int = 768

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
