import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL") or "http://127.0.0.1:54321" # Fallback if needed, but we should read from .env
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

from dotenv import load_dotenv
load_dotenv(".env")

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")
print(f"URL: {url}")
supabase = create_client(url, key)

def seed_data():
    user_id = "ff0dc005-10af-42f2-b34a-f7f754bd7b67"
    print(f"Using user_id: {user_id}")

    quizzes_data = [
        {
            "doc_title": "Lịch Sử Việt Nam - Triều Đại Nhà Trần",
            "quiz_title": "Trắc nghiệm Lịch sử: Nhà Trần",
            "difficulty": "medium",
            "questions": [
                {"q": "Ai là người sáng lập vương triều Trần?", "opts": ["Trần Thái Tông", "Trần Thủ Độ", "Trần Hưng Đạo", "Trần Nhân Tông"], "ans": "A"},
                {"q": "Hội nghị Diên Hồng diễn ra dưới thời vua nào?", "opts": ["Trần Thái Tông", "Trần Thánh Tông", "Trần Nhân Tông", "Trần Anh Tông"], "ans": "C"},
                {"q": "Trận Bạch Đằng năm 1288 do ai chỉ huy?", "opts": ["Lê Hoàn", "Ngô Quyền", "Trần Hưng Đạo", "Lý Thường Kiệt"], "ans": "C"}
            ]
        },
        {
            "doc_title": "Kiến Thức Vũ Trụ 101",
            "quiz_title": "Khám Phá Hệ Mặt Trời",
            "difficulty": "easy",
            "questions": [
                {"q": "Hành tinh nào lớn nhất trong Hệ Mặt Trời?", "opts": ["Trái Đất", "Sao Hỏa", "Sao Mộc", "Sao Thổ"], "ans": "C"},
                {"q": "Sao nào được gọi là hành tinh Đỏ?", "opts": ["Sao Kim", "Sao Thủy", "Sao Hỏa", "Sao Diêm Vương"], "ans": "C"},
                {"q": "Hành tinh nào gần Mặt Trời nhất?", "opts": ["Sao Thủy", "Sao Kim", "Trái Đất", "Sao Hỏa"], "ans": "A"}
            ]
        },
        {
            "doc_title": "Nhập môn Machine Learning",
            "quiz_title": "Machine Learning Cơ Bản",
            "difficulty": "hard",
            "questions": [
                {"q": "Supervised Learning là gì?", "opts": ["Học có giám sát (có nhãn)", "Học không giám sát", "Học tăng cường", "Học sâu"], "ans": "A"},
                {"q": "Overfitting trong ML có nghĩa là gì?", "opts": ["Mô hình học chưa đủ", "Mô hình quá khớp với tập huấn luyện", "Thuật toán chạy quá lâu", "Dữ liệu bị thiếu"], "ans": "B"},
                {"q": "Thuật toán nào thường dùng để phân cụm (Clustering)?", "opts": ["Linear Regression", "K-Means", "Decision Tree", "Random Forest"], "ans": "B"},
                {"q": "Loss function dùng để làm gì?", "opts": ["Đo lường sai số của mô hình", "Tăng tốc độ huấn luyện", "Xử lý dữ liệu ngoại lai", "Tối ưu hóa phần cứng"], "ans": "A"}
            ]
        }
    ]

    for item in quizzes_data:
        # Insert document
        doc_res = supabase.table("documents").insert({
            "user_id": user_id,
            "file_name": item["doc_title"],
            "file_url": "",
            "file_type": "txt",
            "raw_text": "Nội dung mẫu về " + item["doc_title"],
            "status": "ready"
        }).execute()
        doc_id = doc_res.data[0]["id"]

        # Insert quiz_set
        qs_res = supabase.table("quiz_sets").insert({
            "document_id": doc_id,
            "title": item["quiz_title"],
            "difficulty": item["difficulty"],
            "num_questions": len(item["questions"]),
            "is_shared": True
        }).execute()
        qs_id = qs_res.data[0]["id"]

        # Insert questions
        qs_records = []
        for q in item["questions"]:
            qs_records.append({
                "quiz_set_id": qs_id,
                "question_text": q["q"],
                "options": q["opts"],
                "correct_answer": q["ans"]
            })
        supabase.table("questions").insert(qs_records).execute()
        print(f"Seeded quiz successfully!")

    print("Data seeded successfully!")

if __name__ == "__main__":
    seed_data()
