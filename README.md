# AI Quizzes - Trợ lý học tập thông minh

![AI Quizzes Banner](https://img.shields.io/badge/AI_Quizzes-Học_thông_minh_cùng_AI-8b5cf6?style=for-the-badge&logo=google-gemini&logoColor=white)

AI Quizzes là một nền tảng học tập toàn diện được hỗ trợ bởi Trí tuệ nhân tạo (Google Gemini). Nền tảng cho phép người dùng tải lên các tài liệu học tập (PDF, DOCX, TXT) và tự động tạo ra các bài trắc nghiệm (Quiz) cũng như thẻ ghi nhớ (Flashcard) để tối ưu hoá việc ôn tập.

## ✨ Tính năng nổi bật

- 📄 **Xử lý tài liệu thông minh**: Hỗ trợ trích xuất văn bản từ nhiều định dạng file (`.pdf`, `.docx`, `.txt`).
- 🧠 **Tạo Quiz bằng AI**: Tự động tạo bài trắc nghiệm với độ khó tuỳ chỉnh (Dễ, Trung bình, Khó) dựa trên nội dung tài liệu.
- ⚡ **Giải thích từ AI**: Nếu bạn trả lời sai, AI sẽ tự động phân tích và giải thích cặn kẽ lý do sai để bạn rút kinh nghiệm.
- 📇 **Thẻ ghi nhớ (Flashcards)**: Tự động tạo các bộ thẻ ghi nhớ với chế độ lật 3D tương tác giúp ôn tập nhanh chóng.
- 🌍 **Cộng đồng chia sẻ**: Chia sẻ bộ câu hỏi của bạn lên kho dữ liệu cộng đồng hoặc khám phá các bộ câu hỏi từ người dùng khác.
- 👤 **Hệ thống tài khoản & Guest Demo**: Hỗ trợ đăng ký/đăng nhập bằng email. Chế độ "Dùng thử" (Guest Mode) cho phép trải nghiệm toàn bộ tính năng mà không cần tài khoản.
- 🎨 **Giao diện hiện đại**: UI cao cấp với hệ thống màu sắc tuỳ chỉnh, Dark Glassmorphism / Material Design kết hợp TailwindCSS.

## 🛠️ Công nghệ sử dụng

### 💻 Frontend
- **Framework**: React 19 + Vite
- **Styling**: Tailwind CSS (UI hiện đại)
- **State Management**: Zustand
- **Icons**: Lucide React / Google Material Symbols
- **Routing**: React Router DOM v7

### ⚙️ Backend
- **Framework**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL) với `supabase-py`
- **AI Engine**: Google Gemini 1.5 Flash (thông qua `google-genai`)
- **Authentication**: JWT (JSON Web Tokens), `passlib`, `bcrypt`
- **Xử lý file**: `pdfplumber` (PDF), `python-docx` (DOCX)

## 🚀 Hướng dẫn cài đặt & Chạy cục bộ

Dự án yêu cầu **Node.js** (v18+) và **Python** (v3.10+).

### 1. Clone repository
```bash
git clone https://github.com/hungbbdzz/AI_Quizzes.git
cd AI_Quizzes
```

> **Lưu ý:** Giao diện thiết kế mới nhất (Sử dụng Tailwind CSS hiện đại) đang nằm trên nhánh `feature/modern-ui`. Nếu bạn muốn tải và trải nghiệm giao diện mới này, hãy chuyển nhánh:
> ```bash
> git checkout feature/modern-ui
> ```

### 2. Thiết lập Backend
```bash
cd backend
python -m venv venv
# Kích hoạt môi trường ảo:
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

pip install -r requirements.txt
```
Tạo file `.env` trong thư mục `backend/` với các khoá:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_jwt_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 3. Thiết lập Frontend
```bash
cd ../frontend
npm install
```

### 4. Khởi chạy toàn bộ dự án
Bạn có thể sử dụng file script có sẵn ở thư mục gốc để khởi chạy cả Backend và Frontend cùng lúc:
```bash
# Trên Windows
.\start.bat
```
Hoặc chạy riêng lẻ:
- **Backend**: `cd backend && uvicorn app.main:app --reload` (Cổng 8000)
- **Frontend**: `cd frontend && npm run dev` (Cổng 5173)

---
*Dự án được xây dựng với 🩵 để hỗ trợ giáo dục thông minh và cá nhân hoá cho tất cả mọi người.*
