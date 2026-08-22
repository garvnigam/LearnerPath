#!/usr/bin/env python3
"""
Import Harvard PLL catalog entries into Supabase.
Run: python scripts/import_harvard_pll_to_supabase.py
"""

import json
import os
import sys
from pathlib import Path

# Add project root to path for supabase client
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE must be set in backend/.env")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)

CATALOG_FILE = Path(__file__).parent / "harvard_pll_catalog_entries.py"


def load_catalog_entries():
    """Load the generated catalog entries."""
    if not CATALOG_FILE.exists():
        print(f"Error: {CATALOG_FILE} not found. Run import_harvard_pll.py first.")
        return []

    # Import the HARVARD_PLL_COURSES variable
    # The file contains JSON with null values - replace with None for Python
    namespace = {}
    with open(CATALOG_FILE) as f:
        content = f.read()
        # Replace JSON null with Python None
        content = content.replace(": null", ": None")
        exec(content, namespace)
    
    return namespace.get("HARVARD_PLL_COURSES", [])


def transform_entry(entry: dict) -> dict:
    """Transform catalog entry to Supabase row format."""
    return {
        "title": entry["title"],
        "url": entry["url"],
        "provider": entry.get("provider", "Harvard University"),
        "school": entry.get("school", "Harvard University"),
        "description": entry.get("description"),
        "duration": entry.get("duration"),
        "time_commitment": entry.get("time_commitment"),
        "pace": entry.get("pace"),
        "modality": entry.get("modality"),
        "language": entry.get("language"),
        "level": entry.get("level", "intermediate"),
        "topics": entry.get("topics", []),
        "subjects": entry.get("subjects", entry.get("topics", [])),
        "platform": entry.get("platform"),
        "format": entry.get("format", "course"),
        "source": entry.get("source", "harvard_pll"),
        "price_type": entry.get("price_type", "free"),
        "price_amount": entry.get("price_amount"),
        "price_currency": entry.get("currency", "USD"),
        "certificate_price": entry.get("certificate_price"),
        "image_url": entry.get("image_url"),
        "scraped_at": entry.get("scraped_at"),
    }


def import_to_supabase():
    """Import all catalog entries to Supabase."""
    entries = load_catalog_entries()
    if not entries:
        print("No entries to import")
        return

    print(f"Loaded {len(entries)} catalog entries")
    
    transformed = [transform_entry(e) for e in entries]
    
    # Upsert in batches
    batch_size = 50
    total_upserted = 0
    total_errors = 0
    
    for i in range(0, len(transformed), batch_size):
        batch = transformed[i:i+batch_size]
        try:
            result = supabase.table("harvard_pll_courses").upsert(
                batch, 
                on_conflict="url"
            ).execute()
            
            if result.data:
                total_upserted += len(result.data)
                print(f"  Batch {i//batch_size + 1}: upserted {len(result.data)} courses")
            else:
                print(f"  Batch {i//batch_size + 1}: no data returned")
                
        except Exception as e:
            total_errors += 1
            print(f"  Batch {i//batch_size + 1} ERROR: {e}")
    
    print(f"\nDone! Upserted: {total_upserted}, Errors: {total_errors}")
    
    # Verify
    try:
        count_result = supabase.table("harvard_pll_courses").select("*", count="exact", head=True).execute()
        print(f"Total rows in table: {count_result.count}")
    except Exception as e:
        print(f"Could not verify count: {e}")


if __name__ == "__main__":
    import_to_supabase()