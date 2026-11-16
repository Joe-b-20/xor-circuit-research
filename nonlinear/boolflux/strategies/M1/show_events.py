#!/usr/bin/env python3
"""Print the event tables written by harvest.py (argv[1] = data dir)."""
import json, sys, os
D = sys.argv[1]
ev = [json.loads(l) for l in open(os.path.join(D, 'events.jsonl'))]
ev4 = [json.loads(l) for l in open(os.path.join(D, 'events4.jsonl'))]
print('== (G, GD) frontier events (time order per target)')
for e in ev:
    print(e['ev_target'], e['utc'][11:16], e['agent'], e['tuple'], e['cls'], e['cert'], e['file'][:70])
two = set((e['ev_target'], e['file']) for e in ev)
print('== (A, AD, G, GD) Pareto events not in the (G, GD) list')
for e in ev4:
    if (e['ev_target'], e['file']) not in two:
        print(e['ev_target'], e['utc'][11:16], e['agent'], e['tuple'], e['cert'], e['file'][:70])
