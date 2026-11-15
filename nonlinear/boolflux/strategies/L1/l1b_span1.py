#!/usr/bin/env python3
"""L1b: span id of given circuit files, and which baseline (long archive / pin) circuits share it.
    python3 l1b_span1.py FILE ...
Span = span(1, x, AND outputs) as 256-bit tables (same id as q3_anc.py / l1b_score.py).  Also prints the
dimension of span(1, x, ANDs) - 9 (= A_eff, X1's rank count) and the AND profile by AND level."""
import json
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from l1b_score import span_of, load_circ, STRUCT, SPANC, LONG, core, ONES, rref_id   # noqa: E402

st = json.loads(STRUCT.read_text()); spc = json.loads(SPANC.read_text())
rev = {}
for i, s in st.items(): rev.setdefault(s['span'], []).append('long:' + i)
for k, s in spc.items():
    if k.startswith('pin:') or k.startswith('long:'): rev.setdefault(s, []).append(k)
for f in sys.argv[1:]:
    c = load_circ(f)
    tabs = c.tables(); n = c.n; la = [0] * n; prof = Counter(); ands = []
    for j, (op, a, b) in enumerate(c.gates):
        nl = op in core.NONLINEAR_OPS
        la.append((1 if nl else 0) + max(la[a], la[b]))
        if nl: prof[la[-1]] += 1; ands.append(tabs[n + j])
    sid = span_of(c)
    rows = []
    t = [ONES] + tabs[:n] + ands
    # rank
    piv = {}
    for v in t:
        while v:
            p = v.bit_length() - 1
            if p in piv: v ^= piv[p]
            else: piv[p] = v; break
    m = c.metrics(core.Model.load('nist'))
    print('%s  %d/%d/%d/%d  profile %s  span %s  A_eff %d  shared with baseline: %s' % (
        f, m['A'], m['AD'], m['G'], m['GD'], '|'.join(str(prof[k]) for k in sorted(prof)), sid, len(piv) - 9,
        ', '.join(rev.get(sid, [])[:6]) or 'NONE'))
