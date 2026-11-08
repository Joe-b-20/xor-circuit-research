#!/bin/bash
# Which inv118 record files lack a "gates" field (skipped as "format" by collect118.py)?
cd ~/xs-campaigns/2026-11-05-inv118/runs/inv118/workers || exit 1
echo "total g118 files: $(ls */records/g118-d5-*.json | wc -l)"
echo "without gates field: $(grep -L '"gates"' */records/g118-d5-*.json | wc -l)"
f=$(grep -L '"gates"' */records/g118-d5-*.json | head -1)
echo "example: $f"; head -c 600 "$f"; echo
echo "with gates field: $(grep -l '"gates"' */records/g118-d5-*.json | wc -l)"
ls star-00/records | sed 's/-[0-9a-f]*\.json//' | sort | uniq -c | head
ls star-00/records | head -5
