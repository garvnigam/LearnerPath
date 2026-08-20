from pydantic import BaseModel, Field
from typing import Literal, Optional


class TopicInput(BaseModel):
    user_id: Optional[str] = None
    subjects: list[str] = Field(..., description="e.g. ['Computer Science', 'Mathematics']")
    duration_months: int = Field(..., ge=1, le=36)
    hours_per_day: float = Field(..., ge=0.25, le=16)
    goal: Optional[str] = None


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    user_id: Optional[str] = None
    session_id: str
    topic_input: TopicInput
    messages: list[ChatMessage]


class ChatResponse(BaseModel):
    message: ChatMessage
    ready_for_assessment: bool = False
    focus_areas: list[str] = []


class MCQOption(BaseModel):
    key: Literal["A", "B", "C", "D"]
    text: str


class MCQ(BaseModel):
    id: int
    question: str
    options: list[MCQOption]
    correct: Literal["A", "B", "C", "D"]
    explanation: str
    difficulty: Literal["beginner", "intermediate", "advanced"]


class AssessmentRequest(BaseModel):
    session_id: str
    topic_input: TopicInput
    focus_areas: list[str]


class AssessmentResponse(BaseModel):
    questions: list[MCQ]


class ScoreRequest(BaseModel):
    user_id: Optional[str] = None
    session_id: str
    topic_input: TopicInput
    focus_areas: list[str]
    questions: list[MCQ]
    answers: dict[int, Literal["A", "B", "C", "D"]]


class Course(BaseModel):
    title: str
    provider: str
    url: str
    level: str
    description: str
    duration: Optional[str] = None
    image: Optional[str] = None
    topics: list[str] = []
    format: Optional[Literal["course", "playlist", "lectures"]] = "course"


class RecommendationResponse(BaseModel):
    level: Literal["beginner", "intermediate", "advanced"]
    score: int
    total: int
    strengths: list[str]
    gaps: list[str]
    weekly_plan: str
    courses: list[Course]
