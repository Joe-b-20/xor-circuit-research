#!/usr/bin/env python3
"""Helper counts (h_e, h_o) among the G=75 survivors of the package LP model (trivial arithmetic)."""
import json
from collections import Counter
from pathlib import Path
d = json.load(open(Path.home()/'xs-campaigns/2026-11-07-sprint/lb76/g75_survivors.json'))
S = d['survivor_list']
print('survivors', len(S))
print('h_even range', min(s['he'] for s in S), '..', max(s['he'] for s in S))
print('h_odd  range', min(s['ho'] for s in S), '..', max(s['ho'] for s in S))
print('min(h_e,h_o) histogram', sorted(Counter(min(s['he'], s['ho']) for s in S).items()))
print('survivors with min(h_e,h_o) <= 2:', sum(1 for s in S if min(s['he'], s['ho']) <= 2))
print('survivors with min(h_e,h_o) <= 4:', sum(1 for s in S if min(s['he'], s['ho']) <= 4))
print('x=a,b range', min(s['a'] for s in S), max(s['a'] for s in S), min(s['b'] for s in S), max(s['b'] for s in S))
