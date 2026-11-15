#!/usr/bin/env python3
"""Applicability of the X1 moves on archive circuits (cell minima, one per (A, AD, GD) cell):
static dep / merge reductions, number of factor-sharing pairs (flip applicability), and the AND count
reached by a short walk (bfw) without and with the source's AND-depth cap.

    python3 survey2.py CAMPAIGN OUT_DIR [WALK_SECONDS=3]
Writes OUT_DIR/survey2.jsonl and OUT_DIR/survey2-summary.txt; walk results below the source A are
verified circuits (x1lib.materialise + 256-input check); those that lower the best A known at their AD
are saved to OUT_DIR/lower/."""
import json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import x1lib as X, x1patch as XP, x1walkc as W
from boolflux.hub.common import metrics, sbox
from boolflux.hub.archive import Archive
from boolflux import core

ar = Archive(sys.argv[1]); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
secs = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
(out / 'lower').mkdir(exist_ok=True)
bb = W.binary(out); W.binary = lambda o: bb
minA = {}
for (A, AD, GD) in ar.cells: minA[AD] = min(minA.get(AD, 99), A)
ids = sorted((k, v[0]) for k, v in ar.cells.items() if v)
rows = []
for (A, AD, GD), i in ids:
    if A > 54: continue
    c = ar.circuit(i); m = metrics(c)
    I = XP.Info(c); p = I.p
    nd = len(XP.null_space(I))
    u = p.usage(); groups = {}
    for k, s in u.items(): groups.setdefault(s, []).append(k)
    sp = {k: set(X.Prog.span3(*p.ands[k])) for k in p.ands}
    ks = sorted(p.ands)
    share = sum(1 for x in range(len(ks)) for y in range(x + 1, len(ks)) if sp[ks[x]] & sp[ks[y]])
    equ = sum(len(g) * (len(g) - 1) // 2 for g in groups.values())
    mg = sum(1 for g in groups.values() for a in g for b in g if a < b and sp[a] & sp[b])
    row = {'id': i, 'm': m, 'dep': nd, 'equal_usage_pairs': equ, 'merge_pairs': mg, 'sharing_pairs': share}
    for name, cap in (('walk', 0), ('walk_adcap', AD)):
        try:
            res, log = W.run(c, out / 'w', secs, 1, 1, 0.02, 20000, 0.2, 'sv-%s-%s' % (i, name), cap, 0)
        except Exception as e:
            row[name] = None; continue
        best = min([metrics(nc) for nc, a in res] + [m])
        row[name] = best
        st = [ln for ln in log.splitlines() if ln.startswith('end')]
        row[name + '_stats'] = st[-1] if st else None
        for nc, a in res:
            mm = metrics(nc)
            if mm[0] < minA.get(mm[1], 99):
                (out / 'lower' / ('lower-a%d-ad%d-g%d-gd%d-from-%s.bfx' % (mm + (i,)))).write_text(core.to_kernel(nc))
                print('LOWER A AT AD', mm, 'from', i, m, flush=True)
    for f in (out / 'w').glob('*'): f.unlink()
    rows.append(row)
    with open(out / 'survey2.jsonl', 'a') as fh: fh.write(json.dumps(row) + '\n')
    print(m, 'dep', nd, 'merge', mg, 'share', share, 'walk', row.get('walk'), 'adcap', row.get('walk_adcap'), flush=True)
# summary by A class
lines = []
for lo, hi in ((28, 28), (29, 29), (30, 31), (32, 32), (33, 35), (36, 40), (41, 54)):
    rs = [r for r in rows if lo <= r['m'][0] <= hi]
    if not rs: continue
    n = len(rs)
    lines.append('A %d-%d: cells %d | dep>0 %d | merge pair %d | flip applicable (sharing pairs > 0) %d, median pairs %d | walk %.0f s lowers A: %d (mean drop %.2f) | with AD cap: %d (mean drop %.2f)' % (
        lo, hi, n, sum(r['dep'] > 0 for r in rs), sum(r['merge_pairs'] > 0 for r in rs), sum(r['sharing_pairs'] > 0 for r in rs),
        sorted(r['sharing_pairs'] for r in rs)[n // 2], secs,
        sum(1 for r in rs if r.get('walk') and r['walk'][0] < r['m'][0]), sum(r['m'][0] - r['walk'][0] for r in rs if r.get('walk')) / n,
        sum(1 for r in rs if r.get('walk_adcap') and r['walk_adcap'][0] < r['m'][0]), sum(r['m'][0] - r['walk_adcap'][0] for r in rs if r.get('walk_adcap')) / n))
(out / 'survey2-summary.txt').write_text('\n'.join(lines) + '\n')
print('\n'.join(lines))
