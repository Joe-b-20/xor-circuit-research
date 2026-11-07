#!/usr/bin/env python3
"""Step 3: evaluate the candidate NEW quantities / rows on every canonical phase of the 303 real circuits
(bridge/profiles.json: reconstructed with profile_real.reconstruct) and of the package's 13 control circuits,
with the package's own Circuit / analyse / canonical_transpose.

Per phase we record, besides the package's (x,y,h,q,z,F,...):
  n3        full helpers (r = 3)                      -> candidate row n3 <= N3max
  y0        even+even gates with all three signals represented
  y1        even+even gates with exactly one missing signal, that label bright (has an H-B edge at an anchored helper)
  y2        the other even+even gates
  Gstar_R6  slack of (G*) with J = R6:  y2 + z + D0 - qD + sum_bright kR6_l - (32 - rho6)   (must be >= 0)
  L12star   slack of  rho6 - sum (r-1)_+ - y0                                                  (must be >= 0)
  L7star    slack of  7q - W - y1
  eeinc     slack of  4q + 2F - U - 2F_H - (y1 + y2)
  q0rule    for q = 0: z - (32 - rho6) - n_r0  (M); Lemma 10.3(ii) for Mt
usage: python3 circuit_check.py [N_REAL]   (default all 303)
"""
import sys, json, glob, itertools, time
from collections import Counter, defaultdict
from math import comb
from pathlib import Path
SPRINT = Path.home()/'xs-campaigns/2026-11-07-sprint'
sys.path.insert(0, str(SPRINT/'lb76/pkg_copy/source/lower_bounds/checks'))
sys.path.insert(0, str(SPRINT/'bridge'))
from stress import Circuit, BOUNDARY, parity  # noqa: E402
from profile_real import reconstruct, read_ncff  # noqa: E402

RHO6 = {'M': 20, 'Mt': 28}
SIG = {k: v['sigma_pairs'] for k, v in json.load(open(SPRINT/'qbound/pair_sigma.json')).items()}   # sigma(P) per boundary pair 'i,j'

def rank2(vectors):
    piv = {}
    for v in vectors:
        while v:
            h = v.bit_length() - 1
            if h in piv: v ^= piv[h]
            else: piv[h] = v; break
    return len(piv)
class Basis:
    def __init__(self): self.piv = {}
    def reduce(self, v):
        while v:
            h = v.bit_length() - 1
            if h in self.piv: v ^= self.piv[h]
            else: return v
        return 0
    def add(self, v):
        v = self.reduce(v)
        if v: self.piv[v.bit_length() - 1] = v; return True
        return False
    def copy(self):
        b = Basis(); b.piv = dict(self.piv); return b
    def dim(self): return len(self.piv)

# boundary tables per orientation: index of each boundary mask, R6 basis, forms (2- and 4-subsets by XOR)
TAB = {}
def tables(ori):
    if ori in TAB: return TAB[ori]
    B = BOUNDARY[ori]; idx = {b: i for i, b in enumerate(B)}
    trip = defaultdict(list)
    for i, j, k in itertools.combinations(range(64), 3):
        trip[B[i] ^ B[j] ^ B[k]].append((1 << i) | (1 << j) | (1 << k))
    six = set()
    for ts in trip.values():
        if len(ts) >= 2:
            for a, b in itertools.combinations(ts, 2): six.add(a | b)
    R6 = Basis()
    for w in six: R6.add(w)
    assert R6.dim() == RHO6[ori]
    forms = defaultdict(list)       # label value -> list of boundary subsets (as 64-bit masks) with that XOR, sizes 2 and 4
    for i, j in itertools.combinations(range(64), 2): forms[B[i] ^ B[j]].append((1 << i) | (1 << j))
    for S in itertools.combinations(range(64), 4):
        v = 0; m = 0
        for i in S: v ^= B[i]; m |= 1 << i
        forms[v].append(m)
    TAB[ori] = dict(B=B, idx=idx, R6=R6, forms=forms, trip=trip)
    return TAB[ori]

def kR6(ori, label):
    """dim((K_l + R6)/R6) where K_l = span of differences of the 2/4-forms of the label."""
    T = tables(ori); fs = T['forms'].get(label, [])
    if len(fs) < 2: return 0
    bs = T['R6'].copy(); k = 0
    for f in fs[1:]:
        if bs.add(fs[0] ^ f): k += 1
    return k

def phase_quantities(C, I):
    """new quantities for one phase; C a package Circuit, I = C.analyse()."""
    ori = C.ori; T = tables(ori); B = I['B']; H = set(I['H'])
    # edges and labels as analyse() builds them
    edges = []
    for k, (a, b) in enumerate(C.gates):
        s = 32 + k
        if C.odd[a] and C.odd[b]: edges.append((a, b, s))
        elif C.odd[a] != C.odd[b]:
            o, e = (a, b) if C.odd[a] else (b, a); edges.append((o, s, e))
    evens = [v for v in range(32, C.n) if not C.odd[v]]
    bb = {}
    for p, q, e in edges:
        if p in B and q in B: bb[e] = (p, q)
    missing = {e for e in evens if e not in bb}
    # helper types and anchoring
    rtype = {v: [0, 0, 0] for v in H}; bright = set(); UB = Counter()
    for p, q, e in edges:
        hs = [v for v in (p, q) if v in H]
        if len(hs) == 2:
            for v in hs: rtype[v][2] += 1
        elif len(hs) == 1:
            v = hs[0]
            if e in bb: rtype[v][0] += 1
            else: rtype[v][1] += 1; UB[v] += 1
    anchored = {v for v in H if rtype[v][0] >= 1}
    for p, q, e in edges:
        hs = [v for v in (p, q) if v in H]
        if len(hs) == 1 and e not in bb and hs[0] in anchored: bright.add(e)
    n3 = sum(1 for v in H if rtype[v][0] == 3)
    n_r0 = sum(1 for v in H if rtype[v][0] == 0)
    U0 = sum(rtype[v][1] for v in H if rtype[v][0] == 0)
    D0 = U0 - n_r0
    qD = len(missing - bright)
    W = sum(rtype[v][0] * rtype[v][1] for v in H)
    Zx = sum(max(0, rtype[v][0] - 1) for v in H)
    # even+even gates classification
    y0 = y1 = y2 = 0
    for k, (a, b) in enumerate(C.gates):
        s = 32 + k
        if not C.odd[a] and not C.odd[b]:
            miss = [e for e in (a, b, s) if e in missing]
            if not miss: y0 += 1
            elif len(miss) == 1 and miss[0] in bright: y1 += 1
            else: y2 += 1
    assert y0 + y1 + y2 == I['y']
    # (G*) with J = R6
    sumk = sum(kR6(ori, C.mask[e]) for e in bright)
    Gstar_R6 = y2 + I['z'] + D0 - qD + sumk - (32 - RHO6[ori])
    # also the exact dimension check: residual boundary relations of the retained family lie in R6 + sum K_l
    L12star = RHO6[ori] - Zx - y0
    L7star = 7 * I['q'] - W - y1
    N1slack = (len(evens) - I['q']) - 3 * n3
    # (N7) every represented label at an r >= 2 helper is rich (sigma >= 2); count the helper-label incidences
    sig = SIG[ori]
    poor_at_r2 = 0
    for p, q_, e in edges:
        hs = [v for v in (p, q_) if v in H]
        if len(hs) == 1 and e in bb and rtype[hs[0]][0] >= 2:
            b1, b2 = bb[e]; key = f'{min(T["idx"][C.mask[b1]], T["idx"][C.mask[b2]])},{max(T["idx"][C.mask[b1]], T["idx"][C.mask[b2]])}'
            if sig[key] < 2: poor_at_r2 += 1
    U = sum(rtype[v][1] for v in H)
    eeinc = 4 * I['q'] + 2 * I['F'] - U - 2 * I['F_H'] - (y1 + y2)
    q0rule = None
    if I['q'] == 0:
        q0rule = I['z'] - (32 - RHO6[ori]) - n_r0
    # label-level: forms count per missing label (H-B at anchored + ee one-missing) vs rank(C_l)
    return dict(ori=ori, n3=n3, N1slack=N1slack, poor_at_r2=poor_at_r2, n_r0=n_r0, D0=D0, qD=qD, y0=y0, y1=y1, y2=y2, sumk=sumk, Gstar_R6=Gstar_R6,
                L12star=L12star, L7star=L7star, eeinc=eeinc, q0rule=q0rule, W=W, U=U,
                deg_hist=dict(Counter(sum(rtype[v]) for v in H)))

def orbit(gates, steps=4):
    C = Circuit(gates, 'M'); recs = []
    for step in range(steps):
        I = C.analyse()
        rec = dict(step=step, ori=C.ori, G=C.G, x=I['x'], y=I['y'], h=I['h'], q=I['q'], z=I['z'], s=I['s'], F=I['F'], F_H=I['F_H'])
        rec.update(phase_quantities(C, I))
        recs.append(rec)
        if step + 1 < steps:
            C, _ = C.canonical_transpose(I)
    return recs

def main():
    nreal = int(sys.argv[1]) if len(sys.argv) > 1 else 10 ** 9
    t0 = time.time()
    d = json.load(open(SPRINT/'bridge/profiles.json'))
    jobs = []
    for r in d['results'][:nreal]:
        if 'error' in r: continue
        jobs.append((r['tag'], r['values'], None))
    out = []
    for fn in sorted(glob.glob(str(SPRINT/'lb76/pkg_copy/source/circuits/*.json'))):
        dd = json.load(open(fn)); g = dd['gates'] if isinstance(dd, dict) else dd
        out.append(dict(tag='ctrl:' + Path(fn).name, phases=orbit(g)))
    print('controls done', time.time() - t0, flush=True)
    for i, (tag, values, _) in enumerate(jobs):
        gates, order, info = reconstruct(values, 'ymax', 0, True)
        out.append(dict(tag=tag, phases=orbit(gates)))
        if (i + 1) % 50 == 0: print(i + 1, 'real done', f'{time.time()-t0:.0f}s', flush=True)
    json.dump(out, open(SPRINT/'qbound/circuit_check.json', 'w'), indent=0)
    # summary
    def summarize(sel, label):
        ph = [p for r in sel for p in r['phases'] if p['step'] >= 1]      # canonical phases only
        raw = [p for r in sel for p in r['phases'] if p['step'] == 0]
        print(f'\n== {label}: {len(sel)} circuits, {len(ph)} canonical phases (+{len(raw)} raw) ==')
        for key in ('n3', 'N1slack', 'poor_at_r2', 'y0', 'y1', 'y2', 'Gstar_R6', 'L12star', 'L7star', 'eeinc', 'n_r0', 'q', 'z', 's'):
            for ori in ('M', 'Mt'):
                v = [p[key] for p in ph if p['ori'] == ori and p[key] is not None]
                if v: print(f'  {key:9s} {ori:2s} canonical: min {min(v):3d} median {sorted(v)[len(v)//2]:3d} max {max(v):3d}')
            v = [p[key] for p in raw if p[key] is not None]
            if v: print(f'  {key:9s}    raw      : min {min(v):3d} max {max(v):3d}')
        viol = [(r['tag'], p['step'], k) for r in sel for p in r['phases'] for k in ('Gstar_R6', 'L12star', 'L7star', 'eeinc', 'N1slack') if p[k] < 0] + [(r['tag'], p['step'], 'poor_at_r2') for r in sel for p in r['phases'] if p['poor_at_r2'] > 0]
        print('  violations of the new rows (must be none):', viol[:10], len(viol))
        q0 = [(r['tag'], p['step'], p['q0rule']) for r in sel for p in r['phases'] if p['q0rule'] is not None]
        print('  q = 0 phases:', q0[:10], len(q0))
    summarize([r for r in out if r['tag'].startswith('ctrl')], 'package controls')
    summarize([r for r in out if not r['tag'].startswith('ctrl')], 'real circuits')
    print(f'total {time.time()-t0:.0f}s')

if __name__ == '__main__':
    main()
