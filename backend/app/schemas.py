from pydantic import BaseModel, Field
from typing import Literal, Optional

GoalType = Literal["job", "certification", "project", "curiosity", "exam_prep"]
FormatPref = Literal["video", "text", "hands-on"]
PacePref = Literal["solo", "cohort", "paced"]


class TopicInput(BaseModel):
    user_id: Optional[str] = None
    subjects: list[str] = Field(..., description="e.g. ['Computer Science', 'Mathematics']")
    duration_months: int = Field(..., ge=1, le=36)
    hours_per_day: float = Field(..., ge=0.25, le=16)
    goal: Optional[GoalType] = None
    preferred_formats: list[FormatPref] = []
    pace: Optional[PacePref] = None


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
    subject: str = ""
    question: str
    options: list[MCQOption]
    correct: Literal["A", "B", "C", "D"]
    explanation: str
    difficulty: Literal["beginner", "intermediate", "advanced"]


class AssessmentRequest(BaseModel):
    session_id: str
    topic_input: TopicInput
    focus_areas: list[str]
    round: int = 1
    prior_questions: list[MCQ] = []
    prior_answers: dict[int, Literal["A", "B", "C", "D"]] = {}


class AssessmentResponse(BaseModel):
    questions: list[MCQ]
    round: int = 1


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


class WeekPlan(BaseModel):
    week: int
    focus: str
    primary_resource: str
    secondary_resource: Optional[str] = None
    checkpoint: str


class RecommendationResponse(BaseModel):
    level: Literal["beginner", "intermediate", "advanced"]
    level_by_subject: dict[str, Literal["beginner", "intermediate", "advanced"]] = {}
    score: int
    total: int
    strengths: list[str]
    gaps: list[str]
    weekly_plan: list[WeekPlan] = []
    courses: list[Course]


class SavedPlanResponse(BaseModel):
    topic_input: TopicInput
    recommendation: RecommendationResponse
