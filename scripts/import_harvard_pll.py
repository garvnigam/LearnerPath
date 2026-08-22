#!/usr/bin/env python3
"""
Import Harvard PLL scraped data into your catalog.py format.
Run after scraping: python scripts/import_harvard_pll.py
"""

import json
import re
from pathlib import Path


def clean_field(value: str | None) -> str | None:
    """Clean up field values from scraped data."""
    if not value:
        return None
    # Remove label prefixes like "Duration", "Pace", "Modality", "Time Commitment"
    value = re.sub(r'^(Duration|Pace|Modality|Time Commitment)\s*', '', value, flags=re.IGNORECASE)
    # Remove extra whitespace
    value = re.sub(r'\s+', ' ', value).strip()
    return value if value else None


def map_level(level: str | None) -> str:
    """Map PLL difficulty to our level system."""
    if not level:
        return "intermediate"
    level = level.lower()
    if level in ("introductory", "beginner", "intro"):
        return "beginner"
    if level in ("advanced", "expert"):
        return "advanced"
    return "intermediate"


def map_topics(topics: list) -> list:
    """Clean and normalize topics."""
    if not topics:
        return []
    # Filter out generic ones, keep CS-relevant
    generic = {"course", "free", "paid", "online", "self-paced", "harvard", "university"}
    cleaned = []
    for t in topics:
        t = t.strip().lower()
        if t and t not in generic and len(t) > 2:
            cleaned.append(t.title() if t.islower() else t)
    return list(dict.fromkeys(cleaned))  # dedupe


def import_harvard_pll():
    scraped_file = Path("scripts/harvard_pll_courses.json")
    if not scraped_file.exists():
        print(f"Error: {scraped_file} not found. Run scrape_harvard_pll.py first.")
        return

    with open(scraped_file) as f:
        data = json.load(f)

    courses = data.get("courses", [])
    print(f"Loaded {len(courses)} scraped courses")

    catalog_entries = []
    for c in courses:
        # Only include courses with meaningful CS/tech relevance
        topics = map_topics(c.get("topics", []) + c.get("subjects", []))
        
        # Filter for CS/tech/business relevance
        cs_keywords = {
            "computer science", "programming", "python", "ai", "machine learning",
            "data science", "statistics", "algorithms", "data structures",
            "web development", "javascript", "react", "node", "sql", "database",
            "cybersecurity", "security", "cloud", "devops", "mlops",
            "deep learning", "nlp", "computer vision", "tinyml",
            "probability", "mathematics", "linear algebra", "calculus",
            "business", "finance", "entrepreneurship", "leadership",
            "data analysis", "analytics", "visualization", "r", "pandas",
            "tensorflow", "pytorch", "transformer", "llm", "generative ai",
            "quantum", "robotics", "automation", "software engineering"
        }
        
        is_relevant = any(kw in " ".join(topics).lower() for kw in cs_keywords)
        if not is_relevant and c.get("price") == "paid":
            # Skip non-CS paid courses
            continue

        entry = {
            "title": c["title"],
            "provider": f"Harvard {c.get('school', 'University')}",
            "url": c["url"],
            "level": map_level(c.get("level")),
            "description": c["description"][:500] if c.get("description") else f"Harvard {c.get('school', 'Online')} course on {', '.join(topics[:3])}.",
            "duration": clean_field(c.get("duration")) or "self-paced",
            "topics": topics,
            "format": "course",
            "price_type": c["price"],  # free or paid
            "price_amount": c.get("price_amount"),
            "currency": c.get("currency", "USD"),
            "certificate_price": c.get("certificate_price"),
            "platform": c.get("platform"),
            "pace": clean_field(c.get("pace")),
            "modality": clean_field(c.get("modality")),
            "language": clean_field(c.get("language")),
            "image_url": c.get("image_url"),
            "time_commitment": clean_field(c.get("time_commitment")),
            "source": "harvard_pll",
            "scraped_at": c.get("scraped_at"),
        }
        catalog_entries.append(entry)

    # Output as Python dict for catalog.py
    output_file = Path("scripts/harvard_pll_catalog_entries.py")
    with open(output_file, "w") as f:
        f.write("# Auto-generated from Harvard PLL scraper\n")
        f.write(f"# Generated at: {data.get('scraped_at')}\n")
        f.write(f"# Total courses: {len(catalog_entries)}\n\n")
        f.write("HARVARD_PLL_COURSES = ")
        json.dump(catalog_entries, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Generated {len(catalog_entries)} catalog entries")
    print(f"Output: {output_file}")
    
    # Print summary
    free = sum(1 for e in catalog_entries if e["price_type"] == "free")
    paid = sum(1 for e in catalog_entries if e["price_type"] == "paid")
    print(f"  Free: {free}")
    print(f"  Paid: {paid}")
    
    # Show sample
    if catalog_entries:
        print("\nSample entry:")
        print(json.dumps(catalog_entries[0], indent=2))


if __name__ == "__main__":
    import_harvard_pll()