#!/usr/bin/env python3
"""Ingest freeCodeCamp curriculum superblocks into unified `courses` table.

Source: https://api.github.com/repos/freeCodeCamp/freeCodeCamp/contents/curriculum/structure/superblocks
Yields ~98 major learning tracks (Responsive Web Design, JS Algorithms, Python DSA, etc).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

from sources.base import build_row, get_client, upsert_courses

GITHUB_API = "https://api.github.com/repos/freeCodeCamp/freeCodeCamp/contents/curriculum/structure/superblocks"
FCC_LEARN_ROOT = "https://www.freecodecamp.org/learn"


# Curated known mapping — superblock filename → (title, description, level, topics, format)
# Anything not listed still gets ingested with sensible defaults.
KNOWN_TRACKS: dict[str, dict] = {
    "2022-responsive-web-design": {
        "title": "Responsive Web Design",
        "description": "Learn HTML, CSS, Flexbox, Grid, and accessibility to build modern responsive websites.",
        "level": "beginner",
        "topics": ["html", "css", "web development", "responsive design", "accessibility"],
        "duration_hours": 300,
    },
    "javascript-algorithms-and-data-structures-v8": {
        "title": "JavaScript Algorithms and Data Structures",
        "description": "Learn fundamental programming concepts in JavaScript: variables, arrays, objects, functional programming, OOP, and algorithms.",
        "level": "beginner",
        "topics": ["javascript", "algorithms", "data structures", "programming"],
        "duration_hours": 300,
    },
    "javascript-algorithms-and-data-structures": {
        "title": "JavaScript Algorithms and Data Structures (Legacy)",
        "description": "Legacy edition of JS algorithms & data structures.",
        "level": "beginner",
        "topics": ["javascript", "algorithms", "data structures"],
        "duration_hours": 300,
    },
    "front-end-development-libraries-v9": {
        "title": "Front End Development Libraries",
        "description": "Bootstrap, jQuery, Sass, React, and Redux — modern frontend tooling.",
        "level": "intermediate",
        "topics": ["react", "redux", "sass", "bootstrap", "jquery", "web development"],
        "duration_hours": 300,
    },
    "data-visualization": {
        "title": "Data Visualization with D3",
        "description": "Build data visualizations using D3.js, JSON, and APIs.",
        "level": "intermediate",
        "topics": ["d3", "data visualization", "javascript", "svg"],
        "duration_hours": 300,
    },
    "back-end-development-and-apis-v9": {
        "title": "Back End Development and APIs",
        "description": "Node.js, Express, MongoDB — build REST APIs.",
        "level": "intermediate",
        "topics": ["nodejs", "express", "mongodb", "rest api", "backend"],
        "duration_hours": 300,
    },
    "quality-assurance-v2": {
        "title": "Quality Assurance",
        "description": "Chai testing, Advanced Node & Express, WebSockets.",
        "level": "intermediate",
        "topics": ["testing", "chai", "websockets", "nodejs"],
        "duration_hours": 300,
    },
    "scientific-computing-with-python-v8": {
        "title": "Scientific Computing with Python",
        "description": "Learn Python fundamentals through building projects.",
        "level": "beginner",
        "topics": ["python", "programming", "scientific computing"],
        "duration_hours": 300,
    },
    "data-analysis-with-python": {
        "title": "Data Analysis with Python",
        "description": "Numpy, Pandas, Matplotlib, Seaborn — data analysis fundamentals.",
        "level": "intermediate",
        "topics": ["python", "pandas", "numpy", "data analysis", "matplotlib"],
        "duration_hours": 300,
    },
    "machine-learning-with-python": {
        "title": "Machine Learning with Python",
        "description": "TensorFlow, neural networks, image classification, recommender systems.",
        "level": "intermediate",
        "topics": ["machine learning", "python", "tensorflow", "neural networks"],
        "duration_hours": 300,
    },
    "information-security-v7": {
        "title": "Information Security",
        "description": "HelmetJS, penetration testing, information security fundamentals.",
        "level": "intermediate",
        "topics": ["cybersecurity", "information security", "penetration testing"],
        "duration_hours": 300,
    },
    "coding-interview-prep": {
        "title": "Coding Interview Prep",
        "description": "Algorithms, data structures, take-home projects, Project Euler, Rosetta Code.",
        "level": "advanced",
        "topics": ["algorithms", "data structures", "interview prep", "coding challenges"],
        "duration_hours": 500,
    },
    "college-algebra-with-python": {
        "title": "College Algebra with Python",
        "description": "Foundations of algebra taught through Python.",
        "level": "beginner",
        "topics": ["algebra", "mathematics", "python"],
        "duration_hours": 300,
    },
    "foundational-c-sharp-with-microsoft": {
        "title": "Foundational C# with Microsoft",
        "description": "Learn C# programming in partnership with Microsoft.",
        "level": "beginner",
        "topics": ["c#", "csharp", ".net", "programming"],
        "duration_hours": 100,
    },
    "the-odin-project": {
        "title": "The Odin Project",
        "description": "Full-stack web development curriculum (partner track).",
        "level": "beginner",
        "topics": ["web development", "javascript", "ruby on rails", "full stack"],
        "duration_hours": 1000,
    },
    "full-stack-developer": {
        "title": "Full Stack Developer",
        "description": "Comprehensive full-stack track covering everything from HTML to deployment.",
        "level": "intermediate",
        "topics": ["full stack", "web development", "html", "css", "javascript", "backend", "databases"],
        "duration_hours": 1500,
    },
    "a2-english-for-developers": {
        "title": "A2 English for Developers",
        "description": "English language skills for developers, A2 level.",
        "level": "beginner",
        "topics": ["english", "language learning", "developers"],
        "duration_hours": 200,
    },
    "b1-english-for-developers": {
        "title": "B1 English for Developers",
        "description": "English language skills for developers, B1 level.",
        "level": "intermediate",
        "topics": ["english", "language learning", "developers"],
        "duration_hours": 200,
    },
    "rosetta-code": {
        "title": "Rosetta Code",
        "description": "Solve classic programming tasks in many languages.",
        "level": "intermediate",
        "topics": ["programming challenges", "algorithms"],
        "duration_hours": 100,
    },
    "project-euler": {
        "title": "Project Euler",
        "description": "Mathematical and computational problem solving.",
        "level": "advanced",
        "topics": ["mathematics", "algorithms", "problem solving"],
        "duration_hours": 300,
    },
    "workshop-classroom-of-tomorrow": {
        "title": "Classroom of Tomorrow Workshop",
        "description": "Interactive workshop for classroom applications.",
        "level": "beginner",
        "topics": ["education", "workshop"],
        "duration_hours": 40,
    },
}


def slug_to_title(slug: str) -> str:
    return slug.replace("-", " ").replace("_", " ").title()


def normalize_superblock(filename: str) -> dict | None:
    slug = filename.replace(".json", "")
    known = KNOWN_TRACKS.get(slug, {})

    url = f"{FCC_LEARN_ROOT}/{slug}/"
    title = known.get("title") or slug_to_title(slug)
    description = known.get("description") or f"freeCodeCamp curriculum track: {title}. Free interactive learning with certifications."
    level = known.get("level", "beginner")
    topics = known.get("topics", ["programming", "web development"])
    duration_hours = known.get("duration_hours")

    # infer subjects
    subjects = []
    lower = title.lower()
    if any(k in lower for k in ["web", "html", "css", "javascript", "react", "front", "back", "full stack"]):
        subjects.append("web development")
    if any(k in lower for k in ["python", "data", "machine learning", "algorithm"]):
        subjects.append("computer science")
    if any(k in lower for k in ["math", "algebra", "calculus"]):
        subjects.append("mathematics")
    if "security" in lower:
        subjects.append("cybersecurity")
    if not subjects:
        subjects = ["computer science"]

    return build_row(
        source="freecodecamp",
        external_id=slug,
        url=url,
        title=title,
        description=description,
        provider="freeCodeCamp",
        school="freeCodeCamp",
        platform="freeCodeCamp",
        level=level,
        topics=topics,
        subjects=subjects,
        tags=["interactive", "certification", "project-based"],
        format="course",
        pace="self-paced",
        modality="online",
        language="en",
        duration_hours=duration_hours,
        price_type="free",
        certificate_available=True,
        image_url="https://www.freecodecamp.org/icons/icon-512x512.png",
    )


def main():
    print("[freecodecamp] fetching superblock list ...")
    with httpx.Client(timeout=30.0, headers={"Accept": "application/vnd.github.v3+json"}) as client:
        r = client.get(GITHUB_API)
        r.raise_for_status()
        superblocks = r.json()

    filenames = [item["name"] for item in superblocks if item["name"].endswith(".json")]
    print(f"[freecodecamp] found {len(filenames)} superblocks")

    rows: list[dict] = []
    for fn in filenames:
        row = normalize_superblock(fn)
        if row:
            rows.append(row)

    print(f"[freecodecamp] normalized {len(rows)} rows")
    supabase = get_client()
    upserted, errors = upsert_courses(supabase, rows, batch_size=50)
    print(f"[freecodecamp] done: upserted={upserted}, errors={errors}")


if __name__ == "__main__":
    main()
