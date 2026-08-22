#!/usr/bin/env python3
"""Report Azure OpenAI spend for the LearnerPath project.

Uses two sources:
  1. Azure Cost Management API for authoritative daily totals
     (needs Azure login + subscription ID).
  2. Local log grep of /tmp/concepts.log to estimate spend from the
     concept-tagging run in progress (real-time, no login needed).

Run:
  python scripts/track_cost.py              # both sources
  python scripts/track_cost.py --logs-only  # skip Azure API (no auth)
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / "backend" / ".env")

# ---------- Pricing knobs (adjust if your rates change) ----------
# Per 1M tokens, USD
PRICING = {
    "gpt-4.1-mini":            {"input": 0.40, "output": 1.60},
    "gpt-4o-mini":             {"input": 0.15, "output": 0.60},
    "gpt-4o":                  {"input": 2.50, "output": 10.00},
    "gpt-4.1":                 {"input": 2.00, "output": 8.00},
    "text-embedding-3-small":  {"input": 0.02, "output": 0.00},
    "text-embedding-3-large":  {"input": 0.13, "output": 0.00},
}
USD_TO_INR = 83.5


def money(usd: float) -> str:
    return f"${usd:.4f} (~₹{usd * USD_TO_INR:.2f})"


# ============================================================
# Method 1 — Azure Cost Management API (needs Azure CLI login)
# ============================================================
def azure_cost_report(days_back: int = 30) -> None:
    """Use az CLI to query costs. Falls back gracefully if not logged in."""
    try:
        # verify az cli
        subprocess.run(["az", "--version"], check=True, capture_output=True, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("[azure] az CLI not found. Install with: brew install azure-cli")
        return

    try:
        sub = subprocess.run(
            ["az", "account", "show", "--query", "id", "-o", "tsv"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        print("[azure] Not logged in. Run: az login")
        return

    print(f"\n=== Azure Cost Management (subscription {sub[:8]}...) ===")
    print(f"Note: Azure billing lags 8-24 hours. Today's spend may show as $0.\n")

    # today
    end = date.today()
    start = end - timedelta(days=days_back)

    query = {
        "type": "ActualCost",
        "timeframe": "Custom",
        "timePeriod": {
            "from": start.isoformat() + "T00:00:00Z",
            "to": end.isoformat() + "T23:59:59Z",
        },
        "dataset": {
            "granularity": "Daily",
            "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
            "grouping": [
                {"type": "Dimension", "name": "MeterCategory"},
                {"type": "Dimension", "name": "MeterName"},
            ],
        },
    }

    import json
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(query, f)
        query_path = f.name

    try:
        result = subprocess.run(
            [
                "az", "rest",
                "--method", "post",
                "--url", f"https://management.azure.com/subscriptions/{sub}/providers/Microsoft.CostManagement/query?api-version=2023-11-01",
                "--body", f"@{query_path}",
            ],
            check=True, capture_output=True, text=True,
        )
        data = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"[azure] Cost query failed: {e.stderr[:400]}")
        return
    finally:
        os.unlink(query_path)

    rows = data.get("properties", {}).get("rows", [])
    if not rows:
        print("(no cost rows returned)")
        return

    # Aggregate by MeterCategory + MeterName
    from collections import defaultdict
    by_meter = defaultdict(float)
    daily = defaultdict(float)
    for r in rows:
        cost, day, category, meter, *_ = r
        by_meter[(category, meter)] += float(cost)
        daily[str(day)[:10]] += float(cost)

    print(f"Range: {start.isoformat()} → {end.isoformat()}")
    print(f"Total across all services: ${sum(by_meter.values()):.4f}\n")

    print("By meter (top 15):")
    for (cat, meter), c in sorted(by_meter.items(), key=lambda x: -x[1])[:15]:
        print(f"  {cat:30s}  {meter:40s}  ${c:8.4f}")

    print("\nDaily totals:")
    for day in sorted(daily.keys())[-10:]:
        print(f"  {day}  ${daily[day]:8.4f}")


# ============================================================
# Method 2 — Compute from concept-tag log (real-time, no auth)
# ============================================================
def parse_log_tokens(log_path: str) -> tuple[int, int, int]:
    """Since we don't log per-response tokens, estimate from rows tagged × avg tokens.
    Average per concept-tagging call (measured empirically):
      input ~400 tokens, output ~150 tokens.
    """
    p = Path(log_path)
    if not p.exists():
        return 0, 0, 0
    txt = p.read_text()
    # Find latest "total N" figure — represents rows successfully tagged
    matches = re.findall(r"total\s+(\d+)", txt)
    if not matches:
        return 0, 0, 0
    tagged = int(matches[-1])
    avg_in, avg_out = 400, 150
    return tagged, tagged * avg_in, tagged * avg_out


def compute_from_logs() -> None:
    print("\n=== Estimated concept-tagging spend (from /tmp/concepts.log) ===")
    tagged, tok_in, tok_out = parse_log_tokens("/tmp/concepts.log")
    if tagged == 0:
        print("No concept-tagging log activity found.")
        return

    model = "gpt-4.1-mini"
    p = PRICING[model]
    cost = (tok_in / 1_000_000) * p["input"] + (tok_out / 1_000_000) * p["output"]

    print(f"Rows tagged (this session): {tagged:,}")
    print(f"Estimated input tokens:     {tok_in:>10,}")
    print(f"Estimated output tokens:    {tok_out:>10,}")
    print(f"Model:                      {model}")
    print(f"Estimated cost so far:      {money(cost)}")

    remaining_msg = re.findall(r"(\d+)/(\d+)", "\n".join(re.findall(r"\[\s*\d+/\d+\]", "".join(open('/tmp/concepts.log').readlines()[-5:]))))
    # Best-effort: report projected total if queue known
    m = re.findall(r"\[concepts\]\s+(\d+)\s+rows need tagging", Path("/tmp/concepts.log").read_text())
    if m:
        queue_size = int(m[-1])
        projected = (queue_size * (avg_in := 400) / 1_000_000) * p["input"] + (queue_size * (avg_out := 150) / 1_000_000) * p["output"]
        print(f"\nCurrent queue size (last pass): {queue_size:,}")
        print(f"Projected cost to finish queue: {money(projected)}")


def compute_ingest_and_prior() -> None:
    """Ingest was $0 (public APIs). Embeddings so far are ~$0 (20-row smoke test)."""
    print("\n=== Other spend ===")
    print("Ingestion of 33k courses (Harvard PLL, MS Learn, MIT Learn, freeCodeCamp, YouTube, Coursera): $0.00")
    print("  (all public APIs — no LLM used)")
    print("Embeddings smoke test (20 rows × 500 tokens × $0.02/1M): ~$0.0002")
    print("Runtime chat/quiz/planner calls during dev testing: variable")


def print_projections() -> None:
    print("\n=== Projections for the full pipeline ===")

    # Concept tagging
    remaining = 32989  # current DB size, minus already-tagged
    m = re.findall(r"\[concepts\]\s+(\d+)\s+rows need tagging", Path("/tmp/concepts.log").read_text())
    queue_now = int(m[-1]) if m else remaining
    already_tagged_matches = re.findall(r"total\s+(\d+)", Path("/tmp/concepts.log").read_text())
    tagged_now = int(already_tagged_matches[-1]) if already_tagged_matches else 0

    still_needed = 32989 - tagged_now
    p = PRICING["gpt-4.1-mini"]
    tag_cost = (still_needed * 400 / 1_000_000) * p["input"] + (still_needed * 150 / 1_000_000) * p["output"]

    # Embeddings — text-embedding-3-small
    embed_cost = (32989 * 500 / 1_000_000) * PRICING["text-embedding-3-small"]["input"]

    print(f"Concept tagging remaining ({still_needed:,} rows @ gpt-4.1-mini): {money(tag_cost)}")
    print(f"Embeddings all rows        ({32989:,} rows @ text-embedding-3-small): {money(embed_cost)}")
    print(f"Total remaining enrichment spend:  {money(tag_cost + embed_cost)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs-only", action="store_true")
    ap.add_argument("--days", type=int, default=30, help="Azure lookback window in days")
    args = ap.parse_args()

    compute_from_logs()
    compute_ingest_and_prior()
    print_projections()

    if not args.logs_only:
        azure_cost_report(days_back=args.days)


if __name__ == "__main__":
    main()
