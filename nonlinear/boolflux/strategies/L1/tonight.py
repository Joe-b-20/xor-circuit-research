#!/usr/bin/env python3
"""Score tonight's agents (2026-11-15 study) with the L1 measures.

    python3 tonight.py [--budget SECONDS]      (incremental: rerun until 'pending 0')

Scans ~/xs-campaigns/2026-11-15-study/<AGENT>/ for circuit files (*.circ.txt, *.bfx), skipping archive
files whose id is already in the long hub archive (snapshot copies).  Every new file is parsed and
checked here with boolflux.core on all 256 inputs (AES S-box, NIST gate library); this is ONE verifier,
not aes_check (the 'aes' column says whether a JSON sidecar next to the file records an aes_check OK).
Baseline = long hub archive at its stop (01:30 UTC) + pinned published set.  A circuit is a
'front point' if no baseline tuple and no earlier (file mtime) circuit of tonight dominates or equals it.
Cache: ~/xs-campaigns/2026-11-15-study/L1/tonight-cache.json
"""
import argparse
import hashlib
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

HOME = Path.home()
sys.path.insert(0, str(HOME / 'xcr-boolflux' / 'nonlinear'))
from boolflux import core, targets                      # noqa: E402
from l1_lib import GOALS, tier, improvement, leq, fmt, table, goal_near   # noqa: E402

STUDY = HOME / 'xs-campaigns' / '2026-11-15-study'
LONG = HOME / 'xs-campaigns' / '2026-11-14-hub' / 'long' / 'archive'
AGENTS = ['T1', 'T2', 'T3', 'T4', 'X1', 'X2', 'R1', 'R2', 'H1', 'H2', 'H3', 'H4']
CACHE = STUDY / 'L1' / 'tonight-cache.json'
MODEL = core.Model.load('nist')
SBOX = list(targets.aes_sbox())
NIST_OPS = MODEL.ops()


def scan(agent):
    root = STUDY / agent
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in ('funcbank', 'bin', '__pycache__')]
        for f in fn:
            if f.endswith('.circ.txt') or f.endswith('.bfx'):
                yield Path(dp) / f


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--budget', type=float, default=80)
    a = ap.parse_args()
    t0 = time.time()
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    long_ids = {f.stem for f in LONG.glob('*.bfx')}
    pending = 0; nfiles = defaultdict(int)
    for ag in AGENTS:
        for p in scan(ag):
            nfiles[ag] += 1
            if p.suffix == '.bfx' and p.stem in long_ids: continue          # snapshot copy
            if p.name in ('start.bfx',): continue                            # job inputs
            st = p.stat(); key = str(p)
            if key in cache and cache[key]['mtime'] == st.st_mtime: continue
            if time.time() - t0 > a.budget: pending += 1; continue
            e = {'mtime': st.st_mtime, 'agent': ag}
            try:
                c = core.from_kernel(p.read_text(), p.stem) if p.suffix == '.bfx' else core.read_ncff(str(p))
                e['id'] = hashlib.sha1(core.to_kernel(c).encode()).hexdigest()[:12]
                if c.n != 8 or c.m != 8: e['err'] = 'not 8x8'
                elif e['id'] in long_ids: e['dup_long'] = True
                else:
                    m = c.metrics(MODEL)
                    e['m'] = [m['A'], m['AD'], m['G'], m['GD']]
                    e['ok'] = list(c.value_table()) == SBOX and not ({g[0] for g in c.gates} - NIST_OPS)
            except Exception as ex:
                e['err'] = repr(ex)[:80]
            cache[key] = e
    CACHE.write_text(json.dumps(cache))
    print('files scanned per agent', dict(nfiles), '| cached', len(cache), '| pending', pending)
    if pending: return

    from boolflux.hub.common import published
    base = [tuple(p) for p in published()]
    for f in LONG.glob('*.json'):
        if f.name == 'cells.json': continue
        r = json.loads(f.read_text()); base.append((r['A'], r['AD'], r['G'], r['GD']))
    base = sorted(set(base))
    basefront = [p for p in base if not any(q != p and leq(q, p) for q in base)]

    # distinct verified new circuits, earliest file per id
    by_id = {}
    stats = defaultdict(lambda: defaultdict(int))
    for path, e in cache.items():
        ag = e['agent']
        if e.get('dup_long'): stats[ag]['copies of long-archive circuits'] += 1; continue
        if 'err' in e: stats[ag]['unreadable / not a circuit of the S-box shape'] += 1; continue
        if not e.get('ok'): stats[ag]['wrong function or library'] += 1; continue
        stats[ag]['verified new files'] += 1
        if e['id'] not in by_id or e['mtime'] < by_id[e['id']][1]['mtime']: by_id[e['id']] = (path, e)
    pts = list(basefront); rows = []; front = []
    gbest = {g[0]: [(p[2], p[3]) for p in base if p[0] <= g[1] and p[1] <= g[2]] for g in GOALS}
    for i, (path, e) in sorted(by_id.items(), key=lambda kv: kv[1][1]['mtime']):
        m = tuple(e['m']); ag = e['agent']
        stats[ag]['distinct verified new circuits'] += 1
        imp = improvement(m, pts)
        if imp:
            side = Path(path[:-9] + '.json') if path.endswith('.circ.txt') else Path(path[:-4] + '.json')
            aes = ''
            if side.exists():
                try:
                    sj = json.loads(side.read_text()); ac = sj.get('aes_check')
                    aes = 'OK' if (ac is True or ac == 'OK' or (isinstance(ac, dict) and ac.get('ok'))) else ('?' if ac is None else str(ac)[:12])
                except Exception:
                    aes = 'sidecar unreadable'
            near = []
            for g in GOALS:
                if m[0] <= g[1] and m[1] <= g[2] and not any(q[0] <= m[2] and q[1] <= m[3] for q in gbest[g[0]]) and goal_near(m, g):
                    d = max(0, m[2] - g[3]) + max(0, m[3] - g[4]); near.append('%s%s' % (g[0], '(MET)' if d == 0 else '(+%d)' % d))
            V = tier(m[0], m[1]) * imp[1]
            front.append((ag, m, imp, V, near, aes, path, e['mtime']))
            stats[ag]['front points'] += 1; stats[ag]['V'] += V
            stats[ag]['front points A<=31'] += m[0] <= 31; stats[ag]['goal-near'] += bool(near); stats[ag]['goal met'] += any('MET' in x for x in near)
            pts.append(m)
        for g in GOALS:
            if m[0] <= g[1] and m[1] <= g[2]: gbest[g[0]].append((m[2], m[3]))
    print('\n### per agent (files; front points vs long archive + pin + earlier files of tonight)')
    keys = ['verified new files', 'distinct verified new circuits', 'front points', 'front points A<=31', 'goal-near', 'goal met', 'V', 'copies of long-archive circuits', 'wrong function or library', 'unreadable / not a circuit of the S-box shape']
    print(table([[ag] + [('%.0f' % stats[ag][k]) if k == 'V' else stats[ag][k] for k in keys] for ag in AGENTS], ['agent'] + keys))
    print('\n### tonight\'s front points (time order, UTC)')
    print(table([[time.strftime('%H:%M', time.gmtime(t)), ag, fmt(m), imp[0], imp[2], '%.0f' % V, ' '.join(near), aes, path.replace(str(STUDY) + '/', '')]
                 for ag, m, imp, V, near, aes, path, t in front], ['time', 'agent', 'A/AD/G/GD', 'kind', 'delta', 'V', 'goal-near', 'aes_check in sidecar', 'file']))
    # goal boxes: baseline vs now
    allnow = base + [tuple(e['m']) for p, e in by_id.values()]
    print('\n### goal boxes: non-dominated (G, GD) points of each goal class within 6 gates / 4 levels, baseline vs now')
    rows = []
    for g in GOALS:
        def near_pts(S):
            cl = sorted({(p[2], p[3]) for p in S if p[0] <= g[1] and p[1] <= g[2]})
            nd = [p for p in cl if not any(q != p and q[0] <= p[0] and q[1] <= p[1] for q in cl)]
            return [p for p in nd if p[0] <= g[3] + 6 and p[1] <= g[4] + 4]
        b = near_pts(base); n = near_pts(allnow)
        dist = lambda L: min([max(0, p[0] - g[3]) + max(0, p[1] - g[4]) for p in L] or [99])
        rows.append(['%s %d/%d/%d/%d' % g, ' '.join('%d@%d' % p for p in b), dist(b), ' '.join('%d@%d' % p for p in n if p not in b) or '-', dist(n)])
    print(table(rows, ['goal', 'baseline points G@GD', 'baseline min excess (G+GD)', 'new points tonight', 'min excess now']))
    amin = min(p[0] for p in allnow); print('smallest A in baseline %d, now %d' % (min(p[0] for p in base), amin))
    for A in (28, 29):
        b = min([p[1] for p in base if p[0] <= A] or [99]); n = min([p[1] for p in allnow if p[0] <= A] or [99])
        print('smallest AD at A <= %d: baseline %d, now %d' % (A, b, n))


if __name__ == '__main__':
    main()
