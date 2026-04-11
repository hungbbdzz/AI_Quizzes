from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.routers import auth, documents, quiz, flashcards, explain


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🚀 {settings.APP_NAME} đang khởi động...")
    yield
    print("🛑 Server đang tắt...")


app = FastAPI(
    title="AI Quiz & Flashcard System",
    description=(
        "Backend API cho hệ thống học tập thông minh: upload tài liệu, "
        "AI tạo quiz và flashcard, chấm điểm và giải thích lỗi sai."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — cho phép React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gắn tất cả routers vào prefix /api
app.include_router(auth.router,       prefix="/api/auth",       tags=["Auth"])
app.include_router(documents.router,  prefix="/api/documents",  tags=["Documents"])
app.include_router(quiz.router,       prefix="/api/quiz",       tags=["Quiz"])
app.include_router(flashcards.router, prefix="/api/flashcards", tags=["Flashcards"])
app.include_router(explain.router,    prefix="/api/explain",    tags=["Explain"])


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {"message": f"Welcome to {settings.APP_NAME}", "status": "running"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
