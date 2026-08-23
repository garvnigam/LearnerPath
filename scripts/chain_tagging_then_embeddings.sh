#!/usr/bin/env bash
# Wait for concept tagging to finish (or plateau), then start embeddings pass.
# Uses Supabase counts to determine "done": <= 1% untagged rows remaining.

set -e
cd "$(dirname "$0")/.."
source backend/.venv/bin/activate

echo "[chain] waiting for concept tagging to complete..."

get_untagged() {
    python -c "
from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv('backend/.env')
sb = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE'))
tag = sb.table('courses').select('id', count='exact').not_.eq('concepts','{}').limit(1).execute().count
tot = sb.table('courses').select('id', count='exact').limit(1).execute().count
print(tot - tag)
" 2>/dev/null
}

prev=999999
same_count=0
while true; do
    remaining=$(get_untagged || echo "999999")
    echo "[chain] untagged rows: $remaining"
    if [[ "$remaining" -eq 0 ]]; then
        echo "[chain] tagging done."
        break
    fi
    if [[ "$remaining" -eq "$prev" ]]; then
        same_count=$((same_count + 1))
        if [[ $same_count -ge 3 ]]; then
            echo "[chain] no progress for 3 checks. Assuming plateau."
            break
        fi
    else
        same_count=0
    fi
    prev=$remaining
    sleep 60
done

echo "[chain] starting embeddings pass..."
python -u scripts/enrich_embeddings.py 2>&1 | tee /tmp/embeddings.log
echo "[chain] embeddings pass finished."
