#!/bin/bash
# Restore the Ordinary Union checkpoint from the deduplicated archive, using the
# public repo (read-only) for omitted public dependencies.
D=/home/joebachir20/xs-campaigns/2026-11-07-sprint/d3replay
ZIP=/home/joebachir20/xs-campaigns/2026-11-07-sprint/import/zip
cd "$D" || exit 9
echo "START $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "CMD: nice -n 8 timeout 1200 python3 -I $ZIP/tools/restore_checkpoint.py --archive-root $ZIP --source S000001 --destination $D/B/restored --public-repo /home/joebachir20/xor-circuit-research"
SECONDS=0
nice -n 8 timeout 1200 python3 -I "$ZIP/tools/restore_checkpoint.py" --archive-root "$ZIP" --source S000001 --destination "$D/B/restored" --public-repo /home/joebachir20/xor-circuit-research
RC=$?
echo "RC=$RC WALL=${SECONDS}s END $(date -u +%Y-%m-%dT%H:%M:%SZ)"
