#!/usr/bin/env python3
"""Ingest curated top YouTube channels' playlists into unified `courses` table.

Each playlist becomes one row (format="playlist"). We do NOT ingest every
individual video — playlists are the right granularity for a learning path.

Source: YouTube Data API v3 (needs YOUTUBE_API_KEY in backend/.env)
Free tier: 10,000 units/day quota.
  - playlists.list: 1 unit per call (returns up to 50 playlists)
  - playlistItems.list: 1 unit per call (returns up to 50 videos per playlist)
We only need playlists.list here, so ~200 calls total = well within quota.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
from dotenv import load_dotenv

from sources.base import build_row, clean_text, get_client, upsert_courses

load_dotenv(Path(__file__).resolve().parents[2] / "backend" / ".env")
API_KEY = os.getenv("YOUTUBE_API_KEY")
if not API_KEY:
    print("ERROR: YOUTUBE_API_KEY not set in backend/.env")
    sys.exit(1)


# Curated top educational channels — CS heavy but also math, physics, business.
# Each entry: (channel_id, provider_name, subject_hint, level_hint)
CHANNELS: list[dict] = [
    {"id": "UCEBb1b_L6zDS3xTUrIALZOw", "provider": "MIT OpenCourseWare", "school": "MIT", "subjects": ["computer science", "mathematics", "physics", "engineering"], "level": "advanced"},
    {"id": "UCcabW7890RKJzL968QWEykA", "provider": "Stanford", "school": "Stanford", "subjects": ["computer science", "mathematics"], "level": "advanced"},
    {"id": "UCbYRs-EwrOfXqLyDGSt2S5w", "provider": "Yale Courses", "school": "Yale", "subjects": ["humanities", "economics", "finance"], "level": "advanced"},
    {"id": "UChiKamRQ3-cadEeUeJK8YEA", "provider": "Harvard University", "school": "Harvard", "subjects": ["humanities", "medicine", "computer science"], "level": "intermediate"},
    {"id": "UCiaHqFrxoHTaUUcAQeSnAeQ", "provider": "Princeton University", "school": "Princeton", "subjects": ["computer science", "engineering"], "level": "advanced"},
    {"id": "UCYO_jab_esuFRV4b17AJtAw", "provider": "3Blue1Brown", "school": "3Blue1Brown", "subjects": ["mathematics"], "level": "beginner"},
    {"id": "UCoxcjq-8xIDTYp3uz647V5A", "provider": "Numberphile", "school": "Numberphile", "subjects": ["mathematics"], "level": "beginner"},
    {"id": "UCbfYPyITQ-7l4upoX8nvctg", "provider": "Two Minute Papers", "school": "Two Minute Papers", "subjects": ["ai", "computer science"], "level": "intermediate"},
    {"id": "UCX6b17PVsYBQ0ip5gyeme-Q", "provider": "CrashCourse", "school": "CrashCourse", "subjects": ["computer science", "history", "humanities", "science"], "level": "beginner"},
    {"id": "UCsBjURrPoezykLs9EqgamOA", "provider": "Fireship", "school": "Fireship", "subjects": ["web development", "computer science"], "level": "intermediate"},
    {"id": "UCWv7vMbMWH4-V0ZXdmDpPBA", "provider": "Programming with Mosh", "school": "Mosh Hamedani", "subjects": ["programming", "web development"], "level": "beginner"},
    {"id": "UC0e3QhIYukixgh5VVpKHH9Q", "provider": "Code Bullet", "school": "Code Bullet", "subjects": ["computer science", "ai"], "level": "intermediate"},
    {"id": "UCtYLUTtgS3k1Fg4y5tAhLbw", "provider": "StatQuest with Josh Starmer", "school": "StatQuest", "subjects": ["statistics", "machine learning"], "level": "intermediate"},
    {"id": "UCWN3xxRkmTPmbKwht9FuE5A", "provider": "Siraj Raval", "school": "Siraj Raval", "subjects": ["machine learning", "ai"], "level": "intermediate"},
    {"id": "UCkw4JCwteGrDHIsyIIKo4tQ", "provider": "Welch Labs", "school": "Welch Labs", "subjects": ["mathematics", "machine learning"], "level": "intermediate"},
    {"id": "UCUyeluBRhGPCW4rPe_UvBZQ", "provider": "The Coding Train", "school": "Daniel Shiffman", "subjects": ["programming", "creative coding"], "level": "beginner"},
    {"id": "UCsooa4yRKGN_zEE8iknghZA", "provider": "TED-Ed", "school": "TED-Ed", "subjects": ["general", "science", "history"], "level": "beginner"},
]


API_BASE = "https://www.googleapis.com/youtube/v3"


def fetch_playlists(channel_id: str) -> list[dict]:
    """Fetch all playlists for a channel. Uses pagination."""
    playlists = []
    page_token = None
    with httpx.Client(timeout=30.0) as client:
        while True:
            params = {
                "part": "snippet,contentDetails",
                "channelId": channel_id,
                "maxResults": 50,
                "key": API_KEY,
            }
            if page_token:
                params["pageToken"] = page_token
            r = client.get(f"{API_BASE}/playlists", params=params)
            if r.status_code != 200:
                print(f"    ! HTTP {r.status_code}: {r.text[:200]}")
                break
            data = r.json()
            playlists.extend(data.get("items", []))
            page_token = data.get("nextPageToken")
            if not page_token:
                break
            time.sleep(0.2)
    return playlists


def normalize(playlist: dict, channel: dict) -> dict | None:
    snippet = playlist.get("snippet", {})
    content = playlist.get("contentDetails", {})
    pid = playlist.get("id")
    if not pid:
        return None

    title = snippet.get("title") or "Untitled Playlist"
    description = clean_text(snippet.get("description"))
    thumbnails = snippet.get("thumbnails", {}) or {}
    image_url = (thumbnails.get("high") or thumbnails.get("medium") or thumbnails.get("default") or {}).get("url")
    video_count = content.get("itemCount", 0)

    # Skip very short playlists (usually not real courses)
    if video_count < 3:
        return None

    subjects = channel["subjects"]
    topics = subjects + [s.lower() for s in title.split()[:6] if len(s) > 3]

    # Rough estimate: 20 min per video
    duration_hours = round((video_count * 20) / 60, 1) if video_count else None

    return build_row(
        source="youtube",
        external_id=pid,
        url=f"https://www.youtube.com/playlist?list={pid}",
        title=title,
        description=description or f"YouTube playlist from {channel['provider']} — {video_count} videos.",
        provider=channel["provider"],
        school=channel["school"],
        platform="YouTube",
        level=channel["level"],
        topics=topics,
        subjects=subjects,
        tags=[f"channel:{channel['provider']}", f"{video_count} videos"],
        format="playlist",
        pace="self-paced",
        modality="online",
        language="en",
        duration_hours=duration_hours,
        price_type="free",
        image_url=image_url,
    )


def main():
    supabase = get_client()
    total_upserted = 0
    total_errors = 0

    for ch in CHANNELS:
        print(f"[youtube] fetching playlists for {ch['provider']} ({ch['id']}) ...")
        playlists = fetch_playlists(ch["id"])
        if not playlists:
            print(f"    (no playlists)")
            continue

        rows = []
        for p in playlists:
            row = normalize(p, ch)
            if row:
                rows.append(row)
        print(f"[youtube]   normalized {len(rows)} / {len(playlists)}")

        up, err = upsert_courses(supabase, rows, batch_size=100)
        total_upserted += up
        total_errors += err

    print(f"[youtube] done: upserted={total_upserted}, errors={total_errors}")


if __name__ == "__main__":
    main()
