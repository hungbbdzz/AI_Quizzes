"""
Quiz Service — tạo quiz, lấy quiz, nộp bài và chấm điểm.
Dùng bảng quiz_sets, questions, submissions, user_answers.
"""

from fastapi import HTTPException, status
from supabase import Client

from app.models.quiz import (
    QuizGenerateRequest,
    QuizSetResponse,
    QuizListResponse,
    QuizSubmitRequest,
    SubmissionResponse,
    UserAnswerResult,
    QuestionResponse,
)
from app.services import ai_service


async def generate_quiz(admin: Client, body: QuizGenerateRequest, user_id: str) -> QuizSetResponse:
    """
    Tạo bộ câu hỏi từ tài liệu:
    1. Kiểm tra quyền truy cập tài liệu
    2. Gọi AI sinh câu hỏi
    3. Lưu quiz_set + questions vào DB
    """
    # Kiểm tra tài liệu tồn tại và thuộc về user
    doc_result = (
        admin.table("documents")
        .select("id, user_id, raw_text, file_name, status")
        .eq("id", body.document_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not doc_result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài liệu.")

    doc = doc_result.data
    if doc["status"] != "ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tài liệu chưa sẵn sàng (status: {doc['status']}).",
        )

    raw_text = doc.get("raw_text", "")
    if not raw_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tài liệu không có nội dung.")

    # Gọi Gemini sinh câu hỏi
    questions_data = await ai_service.generate_quiz(
        raw_text=raw_text,
        num_questions=body.num_questions,
        difficulty=body.difficulty,
    )

    # Lưu quiz_set
    quiz_set_record = {
        "document_id": body.document_id,
        "title": body.title or f"Quiz từ {doc['file_name']}",
        "difficulty": body.difficulty,
        "num_questions": len(questions_data),
        "is_shared": False,
    }
    quiz_result = admin.table("quiz_sets").insert(quiz_set_record).execute()
    quiz_set = quiz_result.data[0]
    quiz_set_id = quiz_set["id"]

    # Lưu questions
    question_records = [
        {
            "quiz_set_id": quiz_set_id,
            "question_text": q["question"],
            "options": q["options"],
            "correct_answer": q["correct_answer"],
        }
        for q in questions_data
    ]
    questions_result = admin.table("questions").insert(question_records).execute()
    quiz_set["questions"] = questions_result.data

    return QuizSetResponse(**quiz_set)


async def get_user_quizzes(admin: Client, user_id: str) -> QuizListResponse:
    """Lấy danh sách quiz của user (qua bảng documents để filter by user)."""
    # quiz_sets không có user_id trực tiếp — join qua documents
    result = (
        admin.table("quiz_sets")
        .select("*, documents!inner(user_id)")
        .eq("documents.user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    quizzes = []
    for q in result.data:
        q.pop("documents", None)  # Xoá nested object
        quizzes.append(QuizSetResponse(**q))
    return QuizListResponse(quizzes=quizzes, total=len(quizzes))


async def get_quiz_by_id(admin: Client, quiz_id: str, user_id: str) -> QuizSetResponse:
    """Lấy chi tiết quiz kèm danh sách câu hỏi (không trả về correct_answer)."""
    result = (
        admin.table("quiz_sets")
        .select("*, questions(*), documents!inner(user_id)")
        .eq("id", quiz_id)
        .eq("documents.user_id", user_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy quiz.")

    data = result.data
    data.pop("documents", None)

    # Ẩn correct_answer khi trả về câu hỏi (trước khi submit)
    if "questions" in data and data["questions"]:
        for q in data["questions"]:
            q.pop("correct_answer", None)

    return QuizSetResponse(**data)


async def get_community_quizzes(admin: Client) -> QuizListResponse:
    """Lấy danh sách quiz công khai (is_shared = true)."""
    result = (
        admin.table("quiz_sets")
        .select("*")
        .eq("is_shared", True)
        .order("created_at", desc=True)
        .execute()
    )
    quizzes = [QuizSetResponse(**q) for q in result.data]
    return QuizListResponse(quizzes=quizzes, total=len(quizzes))


async def submit_quiz(
    admin: Client,
    quiz_id: str,
    body: QuizSubmitRequest,
    user_id: str,
) -> SubmissionResponse:
    """
    Nộp bài, chấm điểm và lưu kết quả.
    1. Fetch quiz + correct answers
    2. So sánh từng câu trả lời
    3. Lưu submission + user_answers
    """
    # Lấy quiz kèm correct_answers (cần quyền admin để lấy đáp án đúng)
    quiz_result = (
        admin.table("quiz_sets")
        .select("*, questions(*)")
        .eq("id", quiz_id)
        .single()
        .execute()
    )
    if not quiz_result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy quiz.")

    questions = quiz_result.data.get("questions", [])
    questions_map = {q["id"]: q for q in questions}

    # Chấm điểm
    results = []
    correct_count = 0

    for answer in body.answers:
        question = questions_map.get(answer.question_id)
        if not question:
            continue

        is_correct = answer.selected_answer.upper() == question["correct_answer"].upper()
        if is_correct:
            correct_count += 1

        results.append({
            "question_id": answer.question_id,
            "selected_answer": answer.selected_answer,
            "is_correct": is_correct,
            "correct_answer": question["correct_answer"],
        })

    total = len(results)
    score = round((correct_count / total) * 100, 2) if total > 0 else 0.0

    # Lưu submission
    submission_record = {
        "quiz_set_id": quiz_id,
        "user_id": user_id,
        "score": score,
        "total_questions": total,
        "correct_count": correct_count,
    }
    sub_result = admin.table("submissions").insert(submission_record).execute()
    submission = sub_result.data[0]
    submission_id = submission["id"]

    # Lưu user_answers
    answer_records = [
        {
            "submission_id": submission_id,
            "question_id": r["question_id"],
            "selected_answer": r["selected_answer"],
            "is_correct": r["is_correct"],
        }
        for r in results
    ]
    if answer_records:
        admin.table("user_answers").insert(answer_records).execute()

    return SubmissionResponse(
        id=submission_id,
        quiz_set_id=quiz_id,
        user_id=user_id,
        score=score,
        total_questions=total,
        correct_count=correct_count,
        submitted_at=submission["submitted_at"],
        results=[UserAnswerResult(**r) for r in results],
    )
