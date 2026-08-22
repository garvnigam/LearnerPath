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
    ScoreRequest, RecommendationResponse, Course, WeekPlan, SavedPlanResponse,
)
from .azure_client import chat_json
from .prompts import CHAT_SYSTEM, ASSESSMENT_SYSTEM, RECOMMEND_SYSTEM
from .catalog import CURATED, filter_catalog
from .hybrid_retrieval import gather_candidates
from .mit_learn import fetch_mit_courses
from .supabase_client import save_session, get_latest_recommendation
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

    round_no = req.round if req.round in (1, 2) else 1
    id_offset = 0 if round_no == 1 else len(req.prior_questions)

    # scale question count with number of subjects: 4 per subject per round, capped 20
    n_subjects = max(1, len(req.topic_input.subjects))
    per_subject = 4
    n_questions = min(20, per_subject * n_subjects)

    if round_no == 1:
        performance_note = "This is ROUND 1 — no prior performance yet."
    else:
        per_subject_perf: dict[str, list[bool]] = {}
        for q in req.prior_questions:
            correct = req.prior_answers.get(q.id) == q.correct
            per_subject_perf.setdefault(q.subject or "general", []).append(correct)
        lines = []
        for subj, results in per_subject_perf.items():
            acc = sum(results) / max(1, len(results))
            lines.append(f"  - {subj}: {sum(results)}/{len(results)} correct ({acc:.0%})")
        performance_note = "This is ROUND 2 — round 1 performance per subject:\n" + "\n".join(lines)

    user_msg = f"""Generate {n_questions} MCQs for:
- Subjects (test each one separately): {', '.join(req.topic_input.subjects)}
- Focus areas: {', '.join(req.focus_areas) or 'general'}
- Goal: {req.topic_input.goal or 'general learning'}

Distribute the {n_questions} questions EVENLY: approximately {per_subject} per subject.
Each question's "subject" field MUST be one of the listed subjects verbatim.

{performance_note}
"""
    try:
        data = chat_json(ASSESSMENT_SYSTEM, [{"role": "user", "content": user_msg}], temperature=0.4)
    except Exception as e:
        raise HTTPException(500, f"Azure OpenAI error: {e}")

    qs = data.get("questions", [])
    if len(qs) < max(3, n_questions // 2):
        raise HTTPException(500, f"Assessment generation returned only {len(qs)} questions")
    questions = []
    for i, q in enumerate(qs[:n_questions]):
        q = {**q, "id": id_offset + i + 1}
        questions.append(MCQ(**q))

    save_session(user.subject, req.session_id, {
        "stage": "assessment",
        "topic_input": req.topic_input.model_dump(),
        "focus_areas": req.focus_areas,
        "round": round_no,
        "questions": [q.model_dump() for q in (req.prior_questions + questions)],
    })
    return AssessmentResponse(questions=questions, round=round_no)


@app.post("/api/score", response_model=RecommendationResponse)
async def score(req: ScoreRequest, user: Principal = Depends(enforce_active_session)):
    if not settings.azure_openai_key:
        raise HTTPException(500, "Azure OpenAI not configured")

    correct_count = 0
    wrong_topics = []
    right_topics = []
    per_subject_counts: dict[str, list[int]] = {}  # subject -> [correct, total]
    for q in req.questions:
        picked = req.answers.get(q.id)
        subj = q.subject or (req.topic_input.subjects[0] if req.topic_input.subjects else "general")
        counts = per_subject_counts.setdefault(subj, [0, 0])
        counts[1] += 1
        if picked == q.correct:
            correct_count += 1
            counts[0] += 1
            right_topics.append(q.question[:80])
        else:
            wrong_topics.append(f"Q{q.id} ({q.difficulty}, {subj}): {q.question[:80]}")

    def level_from_ratio(correct: int, total: int) -> str:
        ratio = correct / total if total else 0
        if ratio <= 0.35:
            return "beginner"
        elif ratio <= 0.75:
            return "intermediate"
        return "advanced"

    provisional_by_subject = {
        subj: level_from_ratio(c, t) for subj, (c, t) in per_subject_counts.items()
    }
    # overall provisional = level of the subject the learner is weakest in (drives candidate filtering breadth)
    provisional = level_from_ratio(correct_count, len(req.questions)) if req.questions else "beginner"

    # gather candidate courses from DB + live APIs + curated + optional LLM fallback,
    # querying PER SUBJECT at that subject's own level so the pool reflects each subject's ceiling.
    candidates = await gather_candidates(
        subjects=req.topic_input.subjects,
        focus=req.focus_areas,
        level=provisional,
        budget=getattr(req.topic_input, "budget_type", "prefer_free"),
        total_target=40,
        allow_llm_fallback=True,
        level_by_subject=provisional_by_subject,
    )

    fmt_pref = ', '.join(req.topic_input.preferred_formats) or 'no preference'
    pace_pref = req.topic_input.pace or 'no preference'

    candidate_lines = [
        f"- [{c['level']}] ({c.get('format','course')}) {c['title']} — {c['provider']} -> {c['url']}"
        for c in candidates
    ]

    subject_level_lines = "\n".join(
        f"  - {subj}: {c}/{t} correct -> provisional {provisional_by_subject[subj]}"
        for subj, (c, t) in per_subject_counts.items()
    )

    prompt = f"""Learner:
- Subjects: {', '.join(req.topic_input.subjects)}
- Focus: {', '.join(req.focus_areas)}
- Duration: {req.topic_input.duration_months} months, {req.topic_input.hours_per_day} hrs/day
- Goal: {req.topic_input.goal or 'general'}
- Preferred formats: {fmt_pref}
- Preferred pace: {pace_pref}

Quiz: {correct_count}/{len(req.questions)} correct overall.
Per-subject provisional level:
{subject_level_lines}
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

    weekly_plan = []
    for i, wp in enumerate(data.get("weekly_plan", []) or []):
        try:
            wp.setdefault("week", i + 1)
            weekly_plan.append(WeekPlan(**wp))
        except Exception:
            continue

    level_by_subject = {
        subj: data.get("level_by_subject", {}).get(subj, provisional_by_subject.get(subj, provisional))
        for subj in req.topic_input.subjects
    }

    resp = RecommendationResponse(
        level=data.get("level", provisional),
        level_by_subject=level_by_subject,
        score=correct_count,
        total=len(req.questions),
        strengths=data.get("strengths", []),
        gaps=data.get("gaps", []),
        weekly_plan=weekly_plan,
        courses=picked_courses,
    )

    save_session(user.subject or req.user_id, req.session_id, {
        "stage": "recommendation",
        "topic_input": req.topic_input.model_dump(),
        "focus_areas": req.focus_areas,
        "score": correct_count,
        "total": resp.total,
        "level": resp.level,
        "level_by_subject": resp.level_by_subject,
        "strengths": resp.strengths,
        "gaps": resp.gaps,
        "weekly_plan": [w.model_dump() for w in resp.weekly_plan],
        "courses": [c.model_dump() for c in resp.courses],
    })
    return resp


@app.get("/api/plan/{user_id}", response_model=SavedPlanResponse)
def get_plan(user_id: str, user: Principal = Depends(enforce_active_session)):
    # When real auth is configured, always look up by the authenticated subject —
    # never trust the path param's user_id, or one user could read another's plan.
    lookup_id = user.subject if user.subject and user.subject != "anonymous" else user_id
    saved = get_latest_recommendation(lookup_id)
    if not saved or not saved.get("topic_input"):
        raise HTTPException(404, "No saved plan found for this user")
    try:
        return SavedPlanResponse(
            topic_input=saved["topic_input"],
            recommendation=RecommendationResponse(
                level=saved.get("level", "beginner"),
                level_by_subject=saved.get("level_by_subject", {}),
                score=saved.get("score", 0),
                total=saved.get("total", 0),
                strengths=saved.get("strengths", []),
                gaps=saved.get("gaps", []),
                weekly_plan=[WeekPlan(**w) for w in saved.get("weekly_plan", [])],
                courses=[Course(**c) for c in saved.get("courses", [])],
            ),
        )
    except Exception as e:
        raise HTTPException(500, f"Saved plan is malformed: {e}")
