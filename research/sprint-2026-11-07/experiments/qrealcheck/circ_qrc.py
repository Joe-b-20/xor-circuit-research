#!/usr/bin/env python3
"""qrealcheck: own re-check of the qreal rows (Lemma H1 / HUB, Lemma O1, the dark-split rows, the occurrence
budgets, (I'), y2m <= C(q,2)) on real circuits and their canonical transposes.

Reused: stress.Circuit (normalization asserts, output detection, canonical_transpose) and profile_real.reconstruct /
read_ncff (gate lists).  Everything else (odd graph, labels, types, bright/dark, kinds, adjoints and f_v, cap(h) by
DFS, the O1 chronology) is written here from the definitions in PROOF.md / qreal REPORT.md.  Rows are checked in
their STRONG per-helper / per-label form where one exists.
usage: python3 circ_qrc.py [N_REAL] [N_RAND]
"""
import sys, json, glob, itertools, time
from collections import Counter, defaultdict
from math import comb
from pathlib import Path
SPRINT = Path.home()/'xs-campaigns/2026-11-07-sprint'
sys.path.insert(0, str(SPRINT/'lb76/pkg_copy/source/lower_bounds/checks'))
sys.path.insert(0, str(SPRINT/'bridge'))
import stress
from stress import Circuit
from profile_real import reconstruct, read_ncff
T0 = time.time()
def log(*a): print(f'[{time.time()-T0:6.1f}s]', *a, flush=True)
OUT = SPRINT/'qrealcheck'
MAT = Path.home()/'xor-circuit-research/circuits/aes-mixcolumns/aes-mixcolumns.mat.txt'
lines = [l.split() for l in open(MAT).read().strip().split('\n') if l.strip()]
lines = lines[lines.index(['32', '32']):]
ROWS = [sum(int(b) << c for c, b in enumerate(l)) for l in lines[1:33]]
COLS = [sum(((ROWS[r] >> c) & 1) << r for r in range(32)) for c in range(32)]
UNITS = [1 << i for i in range(32)]
BND = {'M': UNITS + ROWS, 'Mt': UNITS + COLS}
assert BND['M'] == stress.BOUNDARY['M'] and BND['Mt'] == stress.BOUNDARY['Mt']
RHO6 = {'M': 20, 'Mt': 28}; RHO = {'M': 8, 'Mt': 4}; EPS = {'M': 2, 'Mt': 0}; KAPPA = 4
def parity(m): return bin(m).count('1') & 1
def wt(m): return bin(m).count('1')
class Basis:
    def __init__(self, piv=None): self.piv = dict(piv) if piv else {}
    def reduce(self, v):
        while v:
            hb = v.bit_length() - 1
            if hb in self.piv: v ^= self.piv[hb]
            else: return v
        return 0
    def add(self, v):
        v = self.reduce(v)
        if v: self.piv[v.bit_length() - 1] = v; return True
        return False
def rank(vs):
    b = Basis()
    for v in vs: b.add(v)
    return len(b.piv)

TAB = {}
def tables(ori):
    if ori in TAB: return TAB[ori]
    B = BND[ori]; idx = {b: i for i, b in enumerate(B)}
    pairvals = {B[i] ^ B[j] for i, j in itertools.combinations(range(64), 2)}
    trip = defaultdict(list)
    for i, j, k in itertools.combinations(range(64), 3):
        trip[B[i] ^ B[j] ^ B[k]].append((1 << i) | (1 << j) | (1 << k))
    full = {v: ts for v, ts in trip.items() if len(ts) == 3}
    # forms E_l + D (D a 2- or 4-subset of B with XOR l), for rank(C_l) and K_l
    forms = defaultdict(list)
    for i, j in itertools.combinations(range(64), 2): forms[B[i] ^ B[j]].append((1 << i) | (1 << j))
    for c in itertools.combinations(range(64), 4):
        forms[B[c[0]] ^ B[c[1]] ^ B[c[2]] ^ B[c[3]]].append((1 << c[0]) | (1 << c[1]) | (1 << c[2]) | (1 << c[3]))
    six = set()
    for ts in trip.values():
        if len(ts) >= 2:
            for a, b in itertools.combinations(ts, 2): six.add(a | b)
    R6 = Basis()
    for s in six: R6.add(s)
    assert len(R6.piv) == RHO6[ori]
    J = Basis(R6.piv)
    if ori == 'M':   # F9: J = R6 + sum of K_l over labels with rank(C_l) = 7
        for l, fs in forms.items():
            if rank([f | (1 << 64) for f in fs]) == 7:
                for f in fs[1:]: J.add(fs[0] ^ f)
    assert len(J.piv) == 32 - RHO[ori], (ori, len(J.piv))
    cache = {}
    def kl(l):   # dim((K_l + J)/J)
        if l not in cache:
            b = Basis(J.piv); fs = forms.get(l, []); c = 0
            for f in fs[1:]:
                if b.add(fs[0] ^ f): c += 1
            cache[l] = c
        return cache[l]
    capc = {}
    def capl(l):
        if l not in capc: capc[l] = rank([f | (1 << 64) for f in forms.get(l, [])])
        return capc[l]
    N = defaultdict(set)
    for f in full:
        for p in pairvals: N[f ^ p].add(f)
    def cap(hmask):   # hub capacity of a value, exhaustive DFS
        fs = sorted(N.get(hmask, ())); n = len(fs); best = [0]
        def rec(i, bs, k):
            best[0] = max(best[0], k)
            if k + n - i <= best[0]: return
            for t in range(i, n):
                if k + n - t <= best[0]: return
                nb = Basis(bs.piv); ok = all(nb.add(T | (1 << (64 + k))) for T in full[fs[t]])
                if ok: rec(t + 1, nb, k + 1)
        rec(0, Basis(), 0); return best[0]
    TAB[ori] = dict(B=B, idx=idx, pairvals=pairvals, trip=trip, full=full, kl=kl, capl=capl, cap=cap, Nh=N)
    return TAB[ori]

def f_min(r, u, v): return max(0, (r + u + v - 3) // 2)

def phase(C):
    ori = C.ori; T = tables(ori); B = T['B']; bidx = T['idx']
    n = C.n; mask = C.mask; odd = [parity(m) for m in mask]
    outs = set(C.out_index); Bset = set(range(32)) | outs
    H = [v for v in range(32, n) if odd[v] and v not in outs]; Hset = set(H); h = len(H)
    bco = {v: bidx[mask[v]] for v in Bset}
    uses = [[] for _ in range(n)]
    for k, (a, b) in enumerate(C.gates): uses[a].append(32 + k); uses[b].append(32 + k)
    d = [len(uses[v]) + (1 if v in outs else 0) for v in range(n)]
    # gates: equation {a, b, s}, result s
    edges = []; ee = []; x = y = 0
    for k, (a, b) in enumerate(C.gates):
        s = 32 + k
        if odd[a] and odd[b]: x += 1; edges.append((a, b, s, s))          # odd+odd: edge a-b, label s, result s
        elif odd[a] != odd[b]:
            o, e = (a, b) if odd[a] else (b, a); edges.append((o, s, e, s))  # odd+even: edge o-s, label e, result s
        else: y += 1; ee.append((a, b, s))
    assert C.G == 32 + x + y + h
    evens = [v for v in range(32, n) if not odd[v]]; assert len(evens) == x + y
    pair = {}; bbgate = {}
    for p, q_, e, res in edges:
        if p in Bset and q_ in Bset:
            assert e not in pair; pair[e] = (p, q_); bbgate[e] = res
    rep = set(pair); miss = [e for e in evens if e not in rep]; missset = set(miss); q = len(miss)
    HH = [(p, q_, e) for p, q_, e, res in edges if p in Hset and q_ in Hset]; z = len(HH)
    rr = Counter(); uu = Counter(); vv = Counter()
    rep_edges = defaultdict(list); mis_edges = defaultdict(list); lab_HB = defaultdict(list)
    for p, q_, e, res in edges:
        hs = [v for v in (p, q_) if v in Hset]
        if len(hs) == 2: vv[p] += 1; vv[q_] += 1
        elif len(hs) == 1:
            i = hs[0]; a = q_ if p == i else p
            lab_HB[e].append((i, a, res))
            if e in rep: rr[i] += 1; rep_edges[i].append((a, e, res))
            else: uu[i] += 1; mis_edges[i].append((a, e, res))
    for v in H: assert rr[v] + uu[v] + vv[v] == d[v] + 1
    assert sum(rr.values()) + sum(uu.values()) == 32 + h - y + q - z
    typ = {v: (rr[v], uu[v], vv[v]) for v in H}
    full = [v for v in H if rr[v] == 3]; n3 = len(full)
    anchored = {v for v in H if rr[v] >= 1}; h0 = h - len(anchored)
    bright = {e for e in miss if any(i in anchored for i, a, _ in lab_HB.get(e, []))}
    dark = missset - bright; qD = len(dark)
    # ---- adjoints -> f_v, F, F_H, Fb, Fd  (own computation, compared with analyse())
    adj = [0] * n
    for v in range(n - 1, -1, -1):
        a_ = 0
        for w in uses[v]: a_ ^= adj[w]
        if v in C.out_index: a_ ^= 1 << C.out_index[v]
        adj[v] = a_
    ff = [0] * n
    for v in range(n):
        kv = sum(parity(adj[w]) for w in uses[v]) + (1 if v in outs else 0)
        ff[v] = max(0, d[v] - (kv + 1) // 2 - 1); assert d[v] <= 3 + 2 * ff[v]
    F = sum(ff); F_H = sum(ff[v] for v in H); Fb = sum(ff[e] for e in bright); Fd = sum(ff[e] for e in dark)
    I = C.analyse()
    assert (I['q'], I['z'], I['y'], I['F'], I['F_H'], I['h']) == (q, z, y, F, F_H, h)
    assert Counter(typ.values()) == I['types']
    # ---- H1 / HUB (strong form with own cap of the actual helper mask; and the LP row)
    fullmet = Counter()
    for v in full:
        for a, e, _ in mis_edges[v]: fullmet[e] += 1
    assert all(c == 1 for c in fullmet.values()), 'Lemma 4.5: a missing label meets two full helpers'
    A = sum(uu[v] for v in full); assert A == len(fullmet)
    assert all(e in bright for e in fullmet), 'a full-met label is bright'
    hub_viol = 0; hub_slack = 99; capslack = 99; capmax = 0
    for v in H:
        if rr[v] == 3: continue
        fm = sum(1 for a, e, _ in mis_edges[v] if e in fullmet)
        cp = T['cap'](mask[v]); capmax = max(capmax, cp)
        if fm > cp or fm > KAPPA: hub_viol += 1
        # the lemma's actual statement: the full helpers met by v are an independent subset of N(h_v)
        met = {next(w for w in full if any(e2 == e for a2, e2, _ in mis_edges[w])) for a, e, _ in mis_edges[v] if e in fullmet}
        assert all(w in H and (mask[v] ^ mask[w]) in T['pairvals'] for w in met)
        hub_slack = min(hub_slack, KAPPA + q - A - uu[v]); capslack = min(capslack, cp - fm)
        if uu[v] > KAPPA + q - A: hub_viol += 1
    hublin = 4 * q + 2 * F - (sum(max(0, uu[v] - KAPPA) for v in H if rr[v] < 3) + 4 * A + 2 * F_H)
    # ---- O1 chronology
    o1_viol = 0; owned = []; per_full = []
    for v in full:
        defg = [g for g in range(32, n) if g == v]          # v's defining gate is gate v - 32, result v
        outs_v = []
        for a, e, res in rep_edges[v]:
            b1, b2 = pair[e]; tri = {a, b1, b2}
            if res == v: continue                            # the defining gate of v
            if res == a:
                if a not in outs: o1_viol += 1; continue
                outs_v.append(a)
            elif res == e:
                r2 = bbgate[e]
                if r2 not in (b1, b2) or r2 not in outs: o1_viol += 1; continue
                outs_v.append(r2)
            else: o1_viol += 1; continue
            if outs_v[-1] not in tri: o1_viol += 1
        if len(outs_v) < 2: o1_viol += 1
        if len(set(outs_v)) != len(outs_v): o1_viol += 1
        per_full.append(len(outs_v)); owned += outs_v
    if len(owned) != len(set(owned)): o1_viol += 1
    # ---- even+even kinds and dark quantities
    y0 = y1 = y2d = y2m = 0; Y_l = Counter(); ee_l = Counter(); pairs_seen = Counter()
    for a, b, s in ee:
        ms = [e for e in (a, b, s) if e in missset]
        for e in ms: ee_l[e] += 1
        if not ms: y0 += 1
        elif len(ms) == 1 and ms[0] in bright: y1 += 1; Y_l[ms[0]] += 1
        elif len(ms) == 1: y2d += 1
        else:
            y2m += 1
            for p2 in itertools.combinations(sorted(ms), 2): pairs_seen[p2] += 1
    y2 = y2d + y2m; assert y0 + y1 + y2 == y
    assert max(pairs_seen.values(), default=0) <= 1, 'two missing labels in two ee gates'
    # per-label occurrence counts
    U_l = Counter(); V_l = Counter(); UA_l = Counter()
    for e, inc in lab_HB.items():
        if e in missset:
            U_l[e] = len(inc); UA_l[e] = sum(1 for i, a, _ in inc if i in anchored)
    for p, q_, e in HH:
        if e in missset: V_l[e] += 1
    perlab_viol = 0
    for l in miss:
        assert U_l[l] + V_l[l] + ee_l[l] == d[l] + 1 <= 4 + 2 * ff[l]
        if l in bright:
            if UA_l[l] < 1: perlab_viol += 1
            if UA_l[l] + Y_l[l] > 4 + 2 * ff[l]: perlab_viol += 1
            # per-label (L7*) + F9: W_l + Y_l <= rank(C_l) <= 7 - 2 k_l
            W_l = sum(rr[i] for i, a, _ in lab_HB[l]); kl = T['kl'](mask[l]); cl = T['capl'](mask[l])
            if W_l + Y_l[l] > cl or cl + 2 * kl > 7: perlab_viol += 1
            Z_l = sum(max(0, rr[i] - 1) for i, a, _ in lab_HB[l])
            if Z_l + kl > 3: perlab_viol += 1
        else:
            if UA_l[l] != 0 or Y_l[l] != 0: perlab_viol += 1
            # dark label: all its ee occurrences with a single missing signal are y2d gates
    # ---- aggregates and the dark rows with the actual d = qD
    W = sum(rr[v] * uu[v] for v in H); Z = sum(max(0, rr[v] - 1) * uu[v] for v in H)
    E = sum(max(0, uu[v] - 2) for v in full); D0 = sum(uu[v] - 1 for v in H if rr[v] == 0)
    U = sum(uu.values()); Uanch = sum(uu[v] for v in anchored)
    rho = RHO[ori]; eps = EPS[ori]; dd = qD
    sumk = sum(T['kl'](mask[l]) for l in bright)
    rows = {
        'G*(F9 J)  rho <= y2+z+D0-qD+sum_bright k': y2 + z + D0 - qD + sumk - rho,
        'L13d': 7 * q - 9 * dd - 2 * rho + 2 * z + 2 * y2 - (W + y1 - 2 * D0),
        'L14d': 7 * q - 9 * dd - 2 * rho + 2 * z + 2 * y2 + eps - (W + A + y1 - 2 * D0),
        'L15d': 3 * q - 4 * dd - rho + z + y2 - (Z - D0),
        'bright_lower': Uanch - (q - dd),
        'bright_cap': 4 * (q - dd) + 2 * Fb - (Uanch + y1),
        'dark_cap': 4 * dd + 2 * Fd - y2d,
        'FbFdFH<=F': F - Fb - Fd - F_H,
        'y2m<=C(q,2)': comb(q, 2) - y2m,
        "I'": 4 * q + 2 * F - (y1 + y2d + 2 * y2m + U + 2 * F_H),
        'HUBlin': hublin,
    }
    if ori == 'M': rows['L17Md'] = 6 * q - 9 * dd - 3 * rho + 3 * z + 3 * y2 - (2 * Z + 2 * E - 3 * D0)
    else:
        rows['L17Td'] = 3 * q - 6 * dd - 3 * rho + 3 * z + 3 * y2 - (Z + E - 3 * D0)
        rows['L18d'] = 7 * q - 10 * dd - 3 * rho + 3 * z + 3 * y2 - (W + A - 3 * D0)
    if dd == q: rows['d=q: Fb=0'] = -Fb
    if dd == 0: rows['d=0: Fd=y2d=0'] = -(Fd + y2d)
    # the per-label strong forms behind L13d-L18d, summed over bright labels only (sanity: equals the aggregate)
    assert W == sum(sum(rr[i] for i, a, _ in lab_HB[l]) for l in bright)
    assert Z == sum(sum(max(0, rr[i] - 1) for i, a, _ in lab_HB[l]) for l in bright)
    assert y1 == sum(Y_l[l] for l in bright) and A == sum(1 for l in bright if l in fullmet)
    return dict(ori=ori, x=x, y=y, h=h, q=q, z=z, F=F, n3=n3, A=A, qD=qD, h0=h0, D0=D0, y0=y0, y1=y1, y2=y2, y2d=y2d, y2m=y2m, Fb=Fb, Fd=Fd,
                sumk=sumk, hub_viol=hub_viol, hub_slack=hub_slack, capslack=capslack, capmax=capmax, o1_viol=o1_viol, per_full=per_full,
                perlab_viol=perlab_viol, rows=rows, types={'%d,%d,%d' % t: c for t, c in Counter(typ.values()).items()})

def orbit(gates, steps=4):
    C = Circuit(gates, 'M'); out = []
    for st in range(steps):
        rec = phase(C); rec['step'] = st; out.append(rec)
        if st + 1 < steps:
            I = C.analyse(); C, _ = C.canonical_transpose(I)
    return out

def main():
    nreal = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    nrand = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    tables('M'); tables('Mt'); log('tables ready')
    jobs = []
    for fn in sorted(glob.glob(str(SPRINT/'lb76/pkg_copy/source/circuits/*.json'))):
        dd = json.load(open(fn)); g = dd['gates'] if isinstance(dd, dict) else dd
        jobs.append(('ctrl:' + Path(fn).name, [tuple(x) for x in g]))
    for name in ('xor88-depth5', 'xor89-depth4', 'xor97-depth3'):
        jobs.append(('repo:' + name, read_ncff(str(Path.home()/f'xor-circuit-research/circuits/aes-mixcolumns/aes-mixcolumns-{name}.circ.txt'))))
    d = json.load(open(SPRINT/'bridge/profiles.json'))
    vals = [(r['tag'], r['values']) for r in d['results'] if 'error' not in r]
    # 40 real circuits spread over the list (every 7th), ymax reconstruction; plus random-order reconstructions of 20 of them
    sel = vals[::max(1, len(vals) // nreal)][:nreal]
    for tag, v in sel:
        g, _, _ = reconstruct(v, 'ymax', 0, True); jobs.append(('ymax:' + tag, g))
    nr = 0
    for tag, v in sel[:nrand]:
        for sd in (3, 4):
            try:
                g, _, _ = reconstruct(v, 'rand', sd, True); Circuit(g, 'M'); jobs.append((f'rand{sd}:' + tag, g)); nr += 1
            except (ValueError, AssertionError): pass
    log('jobs', len(jobs), '(controls 13, repo 3, real ymax', len(sel), ', rand', nr, ')')
    out = []; fails = []
    for k, (tag, g) in enumerate(jobs):
        try: out.append(dict(tag=tag, phases=orbit(g)))
        except AssertionError as ex: fails.append((tag, str(ex))); log('FAIL', tag, str(ex))
        if (k + 1) % 25 == 0: log(k + 1, 'circuits done')
    json.dump(dict(fails=fails, circuits=out), open(OUT/'circ_qrc.json', 'w'), indent=0, default=str)
    ph = [p for r in out for p in r['phases']]
    log('circuits', len(out), 'phases', len(ph), 'assertion failures', len(fails))
    tot = {k: sum(p[k] for p in ph) for k in ('hub_viol', 'o1_viol', 'perlab_viol')}
    log('violation totals (must be 0):', tot)
    pf = Counter(n for p in ph for n in p['per_full'])
    log('outputs defined per full helper (must be >= 2):', dict(sorted(pf.items())))
    for ori in ('M', 'Mt'):
        sel_ = [p for p in ph if p['ori'] == ori]
        log(f'== {ori}: {len(sel_)} phases')
        for key in ('q', 'z', 'n3', 'A', 'qD', 'h0', 'y0', 'y1', 'y2', 'y2d', 'y2m', 'Fb', 'Fd', 'sumk', 'hub_slack', 'capslack', 'capmax'):
            v = [p[key] for p in sel_]
            log(f'   {key:9s} min {min(v):3d} median {sorted(v)[len(v)//2]:3d} max {max(v):3d}')
        for name in sorted({k for p in sel_ for k in p['rows']}):
            v = [p['rows'][name] for p in sel_ if name in p['rows']]
            log(f'   row {name:44s} min slack {min(v):3d}  tight on {sum(1 for t in v if t == 0):3d} of {len(v)}  {"VIOLATION" if min(v) < 0 else "ok"}')
    neg = [(r['tag'], p['step'], k, s) for r in out for p in r['phases'] for k, s in p['rows'].items() if s < 0]
    if fails or any(tot.values()) or neg:
        log('CIRCUIT CHECK: FAILURES', fails[:5], neg[:10]); sys.exit(1)
    log('CIRCUIT CHECK PASSED: no violation of any qreal row or lemma')

if __name__ == '__main__':
    main()
