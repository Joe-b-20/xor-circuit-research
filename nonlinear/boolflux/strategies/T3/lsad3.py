#!/usr/bin/env python3
"""list archive records with AD<=3, A<=35, sorted by G (T3)"""
import json, sys, glob, collections
d = sys.argv[1] if len(sys.argv) > 1 else '/home/joebachir20/xs-campaigns/2026-11-14-hub/long/archive'
rows = []
for f in glob.glob(d + '/*.json'):
    try: r = json.load(open(f))
    except Exception: continue
    if 'A' not in r: continue
    if r['AD'] <= 3 and r['A'] <= 35:
        rows.append((r['G'], r['GD'], r['A'], r['id'], r.get('operator'), r.get('parents')))
rows.sort()
ops = collections.Counter(x[4] for x in rows)
print(len(rows), ops)
for x in rows[:40]: print(x)
