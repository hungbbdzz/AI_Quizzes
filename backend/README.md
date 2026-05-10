# AI Quiz & Flashcard System - Backend

Dự án FastAPI cung cấp Backend cho ứng dụng AI học tập. 
Website cho phép người dùng upload tài liệu học tập (PDF, DOCX, TXT), AI tự động tóm tắt nội dung, tạo bộ câu hỏi trắc nghiệm và flashcard. Người dùng làm bài, hệ thống chấm điểm và giải thích lý do sai ("Tại sao tôi sai?") bằng cách đối chiếu lại tài liệu gốc.

## Tech Stack

- **Backend Framework**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL + pgvector)
- **Authentication**: Supabase Auth
- **Storage**: Supabase Storage
- **AI Models**: Google Gemini (`gemini-1.5-pro` và `text-embedding-004`) qua LangChain
- **ML Difficulty Classifier**: PhoBERT + BiLSTM (Local)
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

## Hệ thống Phân loại Độ khó (Machine Learning)

Hệ thống sử dụng mô hình **PhoBERT** kết hợp với **BiLSTM** để dự đoán độ khó của câu hỏi trắc nghiệm (Easy, Medium, Hard).

### 1. Huấn luyện mô hình (Training)

Nếu bạn có bộ dữ liệu mới, có thể huấn luyện lại mô hình:

```bash
# Di chuyển vào thư mục backend
cd backend

# Chạy script training
python -m app.ml.train --data app/ml/data/triethoc_mln_new.csv --epochs 6 --batch-size 8
```

Các tham số chính:
- `--data`: Đường dẫn file CSV (cần có cột `cau_hoi` và `do_kho`).
- `--epochs`: Số lượt huấn luyện (khuyến nghị: 6-10).
- `--lr`: Learning rate (mặc định: 2e-5).

### 2. Cấu trúc mô hình

Mô hình được định nghĩa tại `app/ml/model.py`:
- **Encoder**: PhoBERT (VinAI) để trích xuất đặc trưng ngôn ngữ tiếng Việt.
- **Classifier**: Bidirectional LSTM để hiểu ngữ cảnh câu hỏi, kết hợp với Dropout và Linear layer để phân loại.

### 3. Sử dụng mô hình

Mô hình sau khi train sẽ được lưu tại `app/ml/artifacts/model.pt`. Service `difficulty_service.py` sẽ tự động load mô hình này để dự đoán khi người dùng làm bài tập hoặc khi AI sinh câu hỏi mới.
