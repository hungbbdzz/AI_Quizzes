from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Literal, Dict


Difficulty = Literal["easy", "medium", "hard"]


# ---- Request models ----

class QuizGenerateRequest(BaseModel):
    document_id: str
    num_questions: int = Field(default=10, ge=5, le=50)
    difficulty: Difficulty = "medium"
    title: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "uuid-here",
                "num_questions": 10,
                "difficulty": "medium",
            }
        }


class AnswerSubmission(BaseModel):
    question_id: str
    selected_answer: str  # "A" | "B" | "C" | "D"


class QuizSubmitRequest(BaseModel):
    answers: List[AnswerSubmission]


# ---- Response models ----

class QuestionResponse(BaseModel):
    id: str
    quiz_set_id: str
    question_text: str
    options: Dict[str, str]   # {"A": "...", "B": "...", "C": "...", "D": "..."}
    correct_answer: Optional[str] = None  # chỉ trả về sau khi nộp bài

    class Config:
        from_attributes = True


class QuizSetResponse(BaseModel):
    id: str
    document_id: str
    title: Optional[str]
    difficulty: Difficulty
    num_questions: int
    is_shared: bool
    questions: Optional[List[QuestionResponse]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class QuizListResponse(BaseModel):
    quizzes: List[QuizSetResponse]
    total: int


class UserAnswerResult(BaseModel):
    question_id: str
    selected_answer: str
    is_correct: bool
    correct_answer: str


class SubmissionResponse(BaseModel):
    id: str
    quiz_set_id: str
    user_id: str
    score: float
    total_questions: int
    correct_count: int
    submitted_at: datetime
    results: List[UserAnswerResult]
