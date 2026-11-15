#!/usr/bin/env python3
"""Q3: productive ancestors.  Root (base) circuits and intermediate hubs by descendant value; AND structure.

AND structure per circuit (boolflux.core on the archive .bfx):
  profile   ANDs per AND level, e.g. 9|2|4|13
  span id   hash of the reduced basis of span(1, x, AND outputs): two circuits with the same id have the
            same nonlinear space (same products up to GF(2)-linear recombination)
  s1 id     the same for the level-1 ANDs only (stage-1 space)
"""
import hashlib
import json
import sys
from collections import defaultdict, Counter
from pathlib import Path
from l1_lib import Data, CAMPS, fmt, table, tier, HOME, OUT, GOALS, goal_near

sys.path.insert(0, str(HOME / 'xcr-boolflux' / 'nonlinear'))
from boolflux import core

HUB = HOME / 'xs-campaigns' / '2026-11-14-hub'
D = Data()
ONES = (1 << 256) - 1


def rref_id(tabs):
    rows = []
    for t in tabs:
        for p, r in rows:
            if (t >> p) & 1: t ^= r
        if t:
            p = t.bit_length() - 1
            rows = [(q, r ^ t if (r >> p) & 1 else r) for q, r in rows]
            rows.append((p, t)); rows.sort(key=lambda x: -x[0])
    h = hashlib.sha1(b''.join(r.to_bytes(32, 'big') for p, r in rows)).hexdigest()[:8]
    return h, len(rows)


SC = OUT / 'struct.json'
struct = json.loads(SC.read_text()) if SC.exists() else {}


def structure(i):
    if i in struct: return struct[i]
    f = None
    for c in ['long'] + CAMPS + ['main']:
        p = HUB / c / 'archive' / (i + '.bfx')
        if p.exists(): f = p; break
    c = core.from_kernel(f.read_text(), i)
    tabs = c.tables(); n = c.n
    la = [0] * n; prof = Counter(); ands = []; l1 = []
    for j, (op, a, b) in enumerate(c.gates):
        nl = op in core.NONLINEAR_OPS
        la.append((1 if nl else 0) + max(la[a], la[b]))
        if nl:
            prof[la[-1]] += 1; ands.append(tabs[n + j])
            if la[-1] == 1: l1.append(tabs[n + j])
    base = [ONES] + tabs[:n]
    sid, dim = rref_id(base + ands)
    s1, d1 = rref_id(base + l1)
    struct[i] = {'profile': '|'.join(str(prof[k]) for k in sorted(prof)), 'span': sid, 'dim': dim, 's1': s1, 'd1': d1}
    return struct[i]


for i in D.recs: structure(i)
SC.write_text(json.dumps(struct))

# ---- value by root (base circuit) and by any ancestor -----------------------------------------
byroot = defaultdict(lambda: defaultdict(float)); byanc = defaultdict(lambda: defaultdict(float))
tot = 0
for (c, i), x in D.val.items():
    anc = D.ancestors(i) | {i}
    tot += x['V']
    for a in anc:
        d = byroot if D.op(a) == 'base' else byanc
        d[a]['V'] += x['V']; d[a]['n'] += 1
        if D.m[i][0] <= 31: d[a]['nA31'] += 1
desc = defaultdict(int)
for i in D.recs:
    for a in D.ancestors(i): desc[a] += 1


def src(i):
    r = D.recs[i]; f = (r.get('operator_settings') or {}).get('file')
    if f:
        p = Path(f); return p.parent.parent.name + '/' + p.parent.name + '/' + p.name[:60] if 'nist' not in f else 'NIST ' + p.name[:60]
    return D.chain(i, 3)


print('total V %.0f over %d front admissions' % (tot, len(D.val)))
rows = []
for a, s in sorted(byroot.items(), key=lambda kv: -kv[1]['V'])[:30]:
    st = struct[a]
    rows.append([a, fmt(D.m[a]), st['profile'], st['span'], st['s1'], '%.0f' % s['V'], '%.0f%%' % (100 * s['V'] / tot), int(s['n']), int(s['nA31']), desc[a], src(a)])
print('\n### base (seed/ingest) circuits by value of the front admissions descending from them (a point with two roots counts for both)')
print(table(rows, ['root id', 'A/AD/G/GD', 'AND profile', 'span', 's1', 'V desc', 'share', 'front adm desc', 'A<=31', 'all desc', 'source']))
nroots = sum(1 for i in D.recs if D.op(i) == 'base')
used = len(byroot)
cum = 0; k50 = k90 = None
# greedy cover: how few roots cover the value (a point is covered if ANY of its roots is in the set is too generous; use all-roots)
print('roots in archives: %d, with >= 1 front-admission descendant: %d, with any descendant: %d' % (nroots, used, sum(1 for i in D.recs if D.op(i) == 'base' and desc[i])))

rows = []
for a, s in sorted(byanc.items(), key=lambda kv: -kv[1]['V'])[:40]:
    st = struct[a]
    rows.append([a, fmt(D.m[a]), st['profile'], st['span'], '%.0f' % s['V'], int(s['n']), int(s['nA31']), desc[a], D.chain(a, 3)])
print('\n### hub-made circuits by value of front admissions at or below them (incl. themselves)')
print(table(rows, ['id', 'A/AD/G/GD', 'AND profile', 'span', 'V', 'front adm', 'A<=31', 'all desc', 'lineage (depth 3)']))

# ---- structure classes of the front admissions ------------------------------------------------
S = defaultdict(lambda: defaultdict(float))
for (c, i), x in D.val.items():
    st = struct[i]; k = (D.m[i][0], D.m[i][1], st['profile'])
    S[k]['n'] += 1; S[k]['V'] += x['V']; S[k].setdefault('spans', set()); S[k]['spans'].add(st['span']); S[k].setdefault('s1', set()); S[k]['s1'].add(st['s1'])
rows = [[k[0], k[1], k[2], int(s['n']), '%.0f' % s['V'], len(s['spans']), len(s['s1'])] for k, s in sorted(S.items(), key=lambda kv: -kv[1]['V'])]
print('\n### front admissions by (A, AD, AND-level profile)')
print(table(rows, ['A', 'AD', 'profile', 'front adm', 'V', 'distinct AND spans', 'distinct stage-1 spans']))

# ---- does an operator change the AND space? -----------------------------------------------------
S = defaultdict(Counter)
for i, r in D.recs.items():
    o = D.op(i)
    if o == 'base': continue
    ps = [p for p in r['parents'] if p in struct]
    if not ps: continue
    st = struct[i]
    same_span = any(struct[p]['span'] == st['span'] for p in ps)
    same_s1 = any(struct[p]['s1'] == st['s1'] for p in ps)
    same_prof = any(struct[p]['profile'] == st['profile'] for p in ps)
    dA = D.m[i][0] - min(D.m[p][0] for p in ps)
    S[o]['n'] += 1; S[o]['same span'] += same_span; S[o]['same s1'] += same_s1; S[o]['same profile'] += same_prof
    S[o]['A lower'] += dA < 0; S[o]['A higher'] += dA > 0
    known = st['span'] in {struct[p]['span'] for p in D.recs if D.recs[p]['t_admit'] < r['t_admit']} if False else None
rows = [[o, s['n'], s['same span'], s['same s1'], s['same profile'], s['A lower'], s['A higher']] for o, s in sorted(S.items())]
print('\n### admitted children vs their parent(s): AND space kept?')
print(table(rows, ['op', 'admitted', 'same AND span as a parent', 'same stage-1 span', 'same level profile', 'A lower than every parent', 'A higher than min parent']))

# first appearance of each AND span among A<=31 records: which op introduced it
first = {}
for i in sorted(D.recs, key=lambda i: D.recs[i]['t_admit']):
    sp = struct[i]['span']
    if sp not in first: first[sp] = i
S = Counter(); SV = defaultdict(float)
valspans = defaultdict(float)
for (c, i), x in D.val.items(): valspans[struct[i]['span']] += x['V']
for sp, i in first.items():
    S[D.op(i)] += 1; SV[D.op(i)] += valspans.get(sp, 0)
print('\n### who introduced each distinct AND span (first record with it), and the value of front admissions having that span')
print(table([[o, S[o], '%.0f' % SV[o]] for o in sorted(S, key=lambda o: -SV[o])], ['introduced by', 'distinct AND spans', 'V of front admissions with these spans']))
print('distinct spans', len(first), 'spans with value', len(valspans))
rows = []
for sp, v in sorted(valspans.items(), key=lambda kv: -kv[1])[:25]:
    i = first[sp]; n = sum(1 for (c, j) in D.val if struct[j]['span'] == sp)
    rows.append([sp, '%.0f' % v, n, struct[i]['profile'], fmt(D.m[i]), i, D.chain(i, 4) if D.op(i) != 'base' else src(i)])
print('\n### AND spans by value')
print(table(rows, ['span', 'V', 'front adm', 'profile', 'first record', 'id', 'made by']))

# ---- provenance of BEST.md and the long front ----------------------------------------------------
print('\n### long/front.json: maker of each front circuit')
fr = json.loads((HUB / 'long' / 'front.json').read_text())
cnt = Counter()
rows = []
for d in fr:
    i = d['id']; o = D.op(i); cnt[o] += 1
    if d['m'][0] <= 31 or any(goal_near(d['m'], g) for g in GOALS):
        rows.append([fmt(d['m']), i, struct[i]['profile'], struct[i]['span'], D.chain(i, 99) if o != 'base' else 'base: ' + src(i)])
print(cnt)
print(table(rows, ['A/AD/G/GD', 'id', 'profile', 'span', 'lineage']))
