import logging
import traceback

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
load_dotenv()

from .config import settings
from .schemas import (
    ChatRequest, ChatResponse, ChatMessage,
    AssessmentRequest, AssessmentResponse, MCQ,
    ScoreRequest, RecommendationResponse, Course,
)
from .azure_client import chat_json
from .prompts import CHAT_SYSTEM, ASSESSMENT_SYSTEM, RECOMMEND_SYSTEM
from .catalog import CURATED, filter_catalog
from .mit_learn import fetch_mit_courses
from .supabase_client import save_session
from .auth import Principal, require_user
from .quota import start_session, enforce_active_session

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("learnpath")

app = FastAPI(title="Personalized Learning API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    log.error("Unhandled error on %s %s\n%s", request.method, request.url.path, tb)
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {exc}"},
    )


@app.get("/health")
def health():
    return {
        "ok": True,
        "azure_configured": bool(settings.azure_openai_key),
        "supabase_configured": bool(settings.supabase_url and settings.supabase_service_role),
        "auth_configured": bool(
            settings.entra_tenant_id and settings.entra_tenant_subdomain and settings.entra_api_client_id
        ),
    }


@app.post("/api/session/start")
def session_start(request: Request, user: Principal = Depends(require_user)):
    result = start_session(user, request)
    if not result.allowed:
        raise HTTPException(status_code=403, detail=result.reason or "login_not_allowed")
    return {
        "allowed": True,
        "is_unlimited": result.is_unlimited,
        "ttl_seconds": result.ttl_seconds,
        "session_expires_at": result.session_expires_at,
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest, user: Principal = Depends(enforce_active_session)):
    if not settings.azure_openai_key:
        raise HTTPException(500, "Azure OpenAI not configured")

    context = f"""Learner profile:
- Subjects: {', '.join(req.topic_input.subjects)}
- Duration: {req.topic_input.duration_months} months
- Hours per day: {req.topic_input.hours_per_day}
- Goal: {req.topic_input.goal or 'not specified'}
Conversation so far follows."""

    messages = [{"role": "system", "content": context}]
    for m in req.messages:
        messages.append({"role": m.role, "content": m.content})

    try:
        data = chat_json(CHAT_SYSTEM, messages, temperature=0.5)
    except Exception as e:
        raise HTTPException(500, f"Azure OpenAI error: {e}")

    reply = data.get("reply", "Could you tell me a bit more about what you want to focus on?")
    ready = bool(data.get("ready_for_assessment", False))
    focus = data.get("focus_areas", []) or []

    save_session(user.subject or req.user_id, req.session_id, {
        "stage": "chat",
        "topic_input": req.topic_input.model_dump(),
        "messages": [m.model_dump() for m in req.messages] + [{"role": "assistant", "content": reply}],
        "focus_areas": focus,
    })

    return ChatResponse(
        message=ChatMessage(role="assistant", content=reply),
        ready_for_assessment=ready,
        focus_areas=focus,
    )


@app.post("/api/assessment", response_model=AssessmentResponse)
def assessment(req: AssessmentRequest, user: Principal = Depends(enforce_active_session)):
    if not settings.azure_openai_key:
        raise HTTPException(500, "Azure OpenAI not configured")

    user_msg = f"""Generate 10 MCQs for:
- Subjects: {', '.join(req.topic_input.subjects)}
- Focus areas: {', '.join(req.focus_areas) or 'general'}
- Learner's stated background: unspecified
- Goal: {req.topic_input.goal or 'general learning'}
"""
    try:
        data = chat_json(ASSESSMENT_SYSTEM, [{"role": "user", "content": user_msg}], temperature=0.4)
    except Exception as e:
        raise HTTPException(500, f"Azure OpenAI error: {e}")

    qs = data.get("questions", [])
    if len(qs) < 10:
        raise HTTPException(500, "Assessment generation returned <10 questions")
    questions = [MCQ(**q) for q in qs[:10]]

    save_session(user.subject, req.session_id, {
        "stage": "assessment",
        "topic_input": req.topic_input.model_dump(),
        "focus_areas": req.focus_areas,
        "questions": [q.model_dump() for q in questions],
    })
    return AssessmentResponse(questions=questions)


@app.post("/api/score", response_model=RecommendationResponse)
async def score(req: ScoreRequest, user: Principal = Depends(enforce_active_session)):
    if not settings.azure_openai_key:
        raise HTTPException(500, "Azure OpenAI not configured")

    correct_count = 0
    wrong_topics = []
    right_topics = []
    for q in req.questions:
        picked = req.answers.get(q.id)
        if picked == q.correct:
            correct_count += 1
            right_topics.append(q.question[:80])
        else:
            wrong_topics.append(f"Q{q.id} ({q.difficulty}): {q.question[:80]}")

    # provisional level
    if correct_count <= 3:
        provisional = "beginner"
    elif correct_count <= 7:
        provisional = "intermediate"
    else:
        provisional = "advanced"

    # gather candidate courses
    mit = await fetch_mit_courses(req.topic_input.subjects + req.focus_areas, limit=12)
    curated = filter_catalog(req.topic_input.subjects + req.focus_areas, provisional)
    candidates = (mit + curated)[:40]

    candidate_lines = [
        f"- [{c['level']}] ({c.get('format','course')}) {c['title']} — {c['provider']} -> {c['url']}"
        for c in candidates
    ]

    prompt = f"""Learner:
- Subjects: {', '.join(req.topic_input.subjects)}
- Focus: {', '.join(req.focus_areas)}
- Duration: {req.topic_input.duration_months} months, {req.topic_input.hours_per_day} hrs/day
- Goal: {req.topic_input.goal or 'general'}

Quiz: {correct_count}/{len(req.questions)} correct (provisional level: {provisional})
Correct topics: {right_topics[:5]}
Wrong topics: {wrong_topics[:5]}

Candidate courses (prefer these, use exact URLs). You may also add up to 3 world-class extras (top university lecture series or highly reputable YouTube playlists) if they fit better:
{chr(10).join(candidate_lines)}
"""
    try:
        data = chat_json(RECOMMEND_SYSTEM, [{"role": "user", "content": prompt}], temperature=0.3)
    except Exception as e:
        raise HTTPException(500, f"Azure OpenAI error: {e}")

    picked_urls = set(data.get("picked_course_urls", []))
    picked_courses = [Course(**c) for c in candidates if c["url"] in picked_urls]

    # Merge LLM-suggested extras (must have url + title; dedupe by url)
    seen_urls = {c.url for c in picked_courses}
    for extra in data.get("extra_courses", []) or []:
        try:
            if not extra.get("url") or not extra.get("title"):
                continue
            if extra["url"] in seen_urls:
                continue
            extra.setdefault("level", provisional)
            extra.setdefault("description", "")
            extra.setdefault("topics", [])
            extra.setdefault("format", "course")
            picked_courses.append(Course(**extra))
            seen_urls.add(extra["url"])
        except Exception:
            continue

    if not picked_courses:
        picked_courses = [Course(**c) for c in candidates[:6]]

    resp = RecommendationResponse(
        level=data.get("level", provisional),
        score=correct_count,
        total=len(req.questions),
        strengths=data.get("strengths", []),
        gaps=data.get("gaps", []),
        weekly_plan=data.get("weekly_plan", ""),
        courses=picked_courses,
    )

    save_session(user.subject or req.user_id, req.session_id, {
        "stage": "recommendation",
        "topic_input": req.topic_input.model_dump(),
        "focus_areas": req.focus_areas,
        "score": correct_count,
        "level": resp.level,
        "courses": [c.model_dump() for c in resp.courses],
    })
    return resp
