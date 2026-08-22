#!/usr/bin/env bash
# Migrate courses table from Supabase to Azure PostgreSQL.
# Requires: pg_dump, psql, plus a .env with both connection strings.
#
# .env format:
#   SUPABASE_PG_URL=postgresql://postgres:<pw>@db.<proj>.supabase.co:5432/postgres
#   AZURE_PG_URL=postgresql://<user>@<server>:<pw>@<server>.postgres.database.azure.com:5432/postgres?sslmode=require
set -euo pipefail
source "$(dirname "$0")/../backend/.env"

DUMP=/tmp/supabase_courses.sql

echo "[*] Dumping Supabase courses tables..."
pg_dump "$SUPABASE_PG_URL" \
  --no-owner --no-privileges \
  -t 'public.harvard_pll_courses' \
  -t 'public.courses' 2>/dev/null || true \
  > "$DUMP" || true

echo "[*] Restoring into Azure PostgreSQL..."
psql "$AZURE_PG_URL" -f "$DUMP"

echo "[*] Verifying row counts..."
psql "$AZURE_PG_URL" -c "select count(*) from harvard_pll_courses;"

echo "[✓] Migration complete."
