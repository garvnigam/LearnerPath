"""MIT Learn / OCW public API integration."""
import httpx

BASE = "https://api.learn.mit.edu/api/v1"

# Topic name -> MIT Learn topic string
TOPIC_MAP = {
    "computer science": "Computer Science",
    "machine learning": "Machine Learning",
    "ai": "AI",
    "artificial intelligence": "AI",
    "deep learning": "Machine Learning",
    "data science": "Data Science",
    "programming": "Programming & Coding",
    "mathematics": "Mathematics",
    "math": "Mathematics",
    "physics": "Physics",
    "biology": "Biology",
    "chemistry": "Chemistry",
    "economics": "Economics",
    "engineering": "Engineering",
    "electrical engineering": "Electrical Engineering",
    "business": "Business",
    "management": "Management",
    "history": "History",
    "philosophy": "Philosophy",
    "psychology": "Psychology",
}


async def fetch_mit_courses(topics: list[str], limit: int = 20) -> list[dict]:
    mapped = []
    seen = set()
    for t in topics:
        m = TOPIC_MAP.get(t.lower().strip())
        if m and m not in seen:
            mapped.append(m)
            seen.add(m)
    if not mapped:
        return []

    out: list[dict] = []
    async with httpx.AsyncClient(timeout=15) as client:
        for topic in mapped:
            try:
                r = await client.get(
                    f"{BASE}/courses/",
                    params={
                        "platform": "ocw",
                        "topic": topic,
                        "limit": max(1, limit // len(mapped)),
                    },
                )
                if r.status_code != 200:
                    continue
                data = r.json()
                for item in data.get("results", []):
                    url = item.get("url")
                    if not url or url in {c["url"] for c in out}:
                        continue
                    level = "intermediate"
                    runs = item.get("runs") or []
                    if runs and runs[0].get("level"):
                        code = runs[0]["level"][0].get("code", "")
                        level = "beginner" if "undergraduate" in code else "advanced" if "graduate" in code else "intermediate"
                    out.append({
                        "title": item.get("title", ""),
                        "provider": "MIT OpenCourseWare",
                        "url": url,
                        "level": level,
                        "description": _strip_html(item.get("description", ""))[:400],
                        "duration": None,
                        "image": (item.get("image") or {}).get("url"),
                        "topics": item.get("ocw_topics", []),
                    })
            except Exception:
                continue
    return out


def _strip_html(s: str) -> str:
    import re
    return re.sub(r"<[^>]+>", "", s or "").strip()
