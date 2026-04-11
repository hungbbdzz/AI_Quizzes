# AI Quiz & Flashcard System - Backend

Dự án FastAPI cung cấp Backend cho ứng dụng AI học tập. 
Website cho phép người dùng upload tài liệu học tập (PDF, DOCX, TXT), AI tự động tóm tắt nội dung, tạo bộ câu hỏi trắc nghiệm và flashcard. Người dùng làm bài, hệ thống chấm điểm và giải thích lý do sai ("Tại sao tôi sai?") bằng cách đối chiếu lại tài liệu gốc.

## Tech Stack

- **Backend Framework**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL + pgvector)
- **Authentication**: Supabase Auth
- **Storage**: Supabase Storage
- **AI Models**: Google Gemini (`gemini-1.5-pro` và `text-embedding-004`) qua LangChain
- **File Processing**: `pdfplumber` (hỗ trợ tiếng Việt tốt), `python-docx`

## Cấu trúc thư mục lõi

```
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── documents.py
│   │   ├── quiz.py
│   │   ├── flashcards.py
│   │   └── explain.py
│   ├── services/
│   │   ├── document_service.py
│   │   ├── quiz_service.py
│   │   ├── flashcard_service.py
│   │   └── ai_service.py
│   ├── models/
│   │   ├── auth.py
│   │   ├── document.py
│   │   ├── quiz.py
│   │   └── flashcard.py
│   └── db/
│       ├── supabase_client.py
│       └── migrations/
│           └── 001_init.sql      # Schema mới nhất 9 bảng
├── tests/
├── .env                  # Tự tạo dựa trên .env.example
├── requirements.txt
└── README.md
```

## Chạy dự án (Local Development)

### 1. Requirements

- Python 3.10+
- Database: Supabase Project (bật extension pgvector)
- API Key: Google Gemini AI

### 2. Thiết lập Môi trường

```bash
# Tao Virtual Environment
python -m venv venv
venv\Scripts\activate   # Trên Windows

# Cài đặt thư viện
pip install -r requirements.txt
```

Sao chép file `.env.example` thành `.env` và điền cấu hình thực tế:

```
SUPABASE_URL=...
SUPABASE_KEY=...             # anon / public key
SUPABASE_SERVICE_KEY=...     # Service role key
GEMINI_API_KEY=...
```

### 3. Khởi tạo Database

Truy cập trang **SQL Editor** trong dự án Supabase của bạn và chạy toàn bộ nội dung file `app/db/migrations/001_init.sql`.

### 4. Chạy Server FastAPI

```bash
uvicorn app.main:app --reload
```

Vào trình duyệt ở <http://localhost:8000/docs> để test các API thông qua giao diện Swagger UI.

## Quy trình RAG (Retrieval-Augmented Generation)

Chức năng **Tại sao tôi sai? (Explain)** sử dụng hệ thống RAG:

1. Request lên `/api/explain/{answer_id}`
2. Trích xuất câu hỏi, câu trả lời đúng, và câu trả lời sai của User từ DB
3. Lấy `document_id` tương ứng
4. Tạo Vector Embedding cho *câu hỏi* bằng `text-embedding-004`
5. Dùng `pgvector` COSINE SIMILARITY để gọi Store Procedure `match_document_chunks` trên Supabase
6. Lấy top 3 chunks gần nhất với ngữ cảnh để prompt lên `gemini-1.5-pro`
7. Gemini sẽ phân tích chuyên sâu tại sao user trả lời sai dựa trên context gốc
8. Phản hồi API và cache lại vào Database để tối ưu hiệu suất cho lần truy vấn sau
