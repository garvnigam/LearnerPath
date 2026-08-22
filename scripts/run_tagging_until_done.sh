#!/usr/bin/env bash
# Run concept tagging repeatedly until no untagged rows remain.
# Each iteration snapshots its own queue at the start (so it's a natural pause).
# Exits when a run reports 0 rows to tag.

set -e
cd "$(dirname "$0")/.."
source backend/.venv/bin/activate

while true; do
    output=$(python -u scripts/enrich_concepts.py 2>&1 | tee -a /tmp/concepts.log)
    if echo "$output" | grep -qE '^\[concepts\] 0 rows need tagging'; then
        echo "[orchestrator] no more untagged rows. done."
        break
    fi
    echo "[orchestrator] pass complete. Checking for more rows in 30s..."
    sleep 30
done
