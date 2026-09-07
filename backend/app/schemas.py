from pydantic import BaseModel, Field
from typing import Literal, Optional

GoalType = Literal["job", "certification", "project", "curiosity", "exam_prep"]
FormatPref = Literal["video", "text", "hands-on"]
PacePref = Literal["solo", "cohort", "paced"]


BudgetPref = Literal["strictly_free", "free_and_audit", "free_and_paid"]


class TopicInput(BaseModel):
    user_id: Optional[str] = None
    subjects: list[str] = Field(..., description="e.g. ['Computer Science', 'Mathematics']")
    duration_months: int = Field(..., ge=1, le=36)
    hours_per_day: float = Field(..., ge=0.25, le=16)
    goal: Optional[GoalType] = None
    preferred_formats: list[FormatPref] = []
    pace: Optional[PacePref] = None
    budget: BudgetPref = "strictly_free"


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
    concepts: list[str] = []  # 1-3 fine-grained skills this question tests


class AssessmentRequest(BaseModel):
    session_id: str
    topic_input: TopicInput
    focus_areas: list[str]
    round: int = 1
    prior_questions: list[MCQ] = []
    prior_answers: dict[int, Literal["A", "B", "C", "D"]] = {}


class AdaptiveAssessmentRequest(BaseModel):
    session_id: str
    topic_input: TopicInput
    focus_areas: list[str]
    answered_questions: list[MCQ] = []
    answers: dict[int, Literal["A", "B", "C", "D"]] = {}


class AssessmentResponse(BaseModel):
    questions: list[MCQ]
    round: int = 1


class AdaptiveAssessmentResponse(BaseModel):
    question: Optional[MCQ] = None
    is_complete: bool = False
    questions_per_subject: dict[str, int] = {}  # track count per subject
    message: Optional[str] = None


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
    format: Optional[Literal["course", "playlist", "lectures", "specialization", "module", "track", "nanodegree"]] = "course"
    price_type: Optional[Literal["free", "audit_free", "paid", "freemium"]] = "free"
    price_amount: Optional[float] = None
    price_currency: Optional[str] = "USD"
    certificate_price: Optional[float] = None


class WeekPlan(BaseModel):
    week: int
    focus: str
    primary_resource: str
    secondary_resource: Optional[str] = None
    checkpoint: str


WEEK_TEST_TOTAL = 10
WEEK_TEST_PASSING = 8


class WeekTestRequest(BaseModel):
    """Ask for the 10-mark checkpoint test that gates one week of the plan."""
    user_id: Optional[str] = None
    session_id: str
    topic_input: TopicInput
    week: int = Field(..., ge=1)
    week_focus: str = ""
    resources: list[str] = []          # titles of the week's course(s)
    subjects: list[str] = []           # subjects this week covers; defaults to all
    level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    attempt: int = Field(1, ge=1)
    weak_concepts: list[str] = []      # from the previous failed attempt — retest these
    covered_concepts: list[str] = []   # already-asked concepts, avoid repeats


class WeekTestResponse(BaseModel):
    week: int
    attempt: int
    total: int = WEEK_TEST_TOTAL
    passing_score: int = WEEK_TEST_PASSING
    questions: list[MCQ]


class WeekTestSubmitRequest(BaseModel):
    """Score a week test and, on failure, build the targeted refresher for that same week."""
    user_id: Optional[str] = None
    session_id: str
    topic_input: TopicInput
    week: int = Field(..., ge=1)
    week_focus: str = ""
    resources: list[str] = []
    attempt: int = Field(1, ge=1)
    questions: list[MCQ]
    answers: dict[int, Literal["A", "B", "C", "D"]] = {}


class RefresherResource(BaseModel):
    title: str
    kind: Literal["text", "video", "practice"] = "text"
    url: Optional[str] = None
    provider: Optional[str] = None
    why: str = ""                      # what gap this closes


class RefresherModule(BaseModel):
    week: int
    title: str
    weak_concepts: list[str] = []
    summary: str = ""
    notes: str = ""                    # textual refresher the learner can read inline
    est_minutes: int = 60
    resources: list[RefresherResource] = []


class WeekTestSubmitResponse(BaseModel):
    week: int
    attempt: int
    score: int
    total: int = WEEK_TEST_TOTAL
    passing_score: int = WEEK_TEST_PASSING
    passed: bool
    correct_concepts: list[str] = []
    weak_concepts: list[str] = []
    refresher: Optional[RefresherModule] = None


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
