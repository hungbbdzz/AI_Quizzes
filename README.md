# AI Quiz & Flashcard System

Hệ thống học tập thông minh sử dụng AI để hỗ trợ ôn tập và kiểm tra kiến thức.

## Tính năng chính

- **Upload tài liệu**: Hỗ trợ PDF, DOCX, TXT.
- **AI Summary**: Tóm tắt nội dung tài liệu tự động.
- **AI Quiz Generation**: Tự động tạo câu hỏi trắc nghiệm từ tài liệu.
- **AI Flashcards**: Tạo bộ thẻ ghi nhớ để ôn tập.
- **Phân loại độ khó (ML)**: Sử dụng mô hình PhoBERT + BiLSTM để đánh giá độ khó câu hỏi (Dễ, Trung bình, Khó).
- **Giải thích AI (RAG)**: Giải thích lý do tại sao người dùng làm sai dựa trên ngữ cảnh tài liệu gốc.
- **Cộng đồng**: Chia sẻ bộ Quiz cho mọi người cùng ôn tập.

## Cấu trúc dự án

- `/frontend`: Ứng dụng React + Vite.
- `/backend`: API FastAPI (Python) + ML (PhoBERT).

## Cách chạy dự án

### 1. Backend
Yêu cầu Python 3.10+.
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
*Chi tiết cấu hình xem tại [backend/README.md](backend/README.md).*

### 2. Frontend
Yêu cầu Node.js.
```bash
cd frontend
npm install
npm run dev
```

### 3. Chạy nhanh (Windows)
Sử dụng file `start.bat` ở thư mục gốc để chạy cả 2 service cùng lúc.

## Machine Learning

Hệ thống tích hợp mô hình phân loại độ khó tự huấn luyện.
- **Mô hình**: PhoBERT-base + BiLSTM.
- **Training**: Hướng dẫn chi tiết tại [backend/README.md](backend/README.md#hệ-thống-phân-loại-độ-khó-machine-learning).
