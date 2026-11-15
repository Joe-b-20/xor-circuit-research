"""Relaxed last-layer walks (track G): stage 1 replaced by J free quadratic forms ("junk slots").

E0 = span(1, x, N coordinates, middle products of --inv FILE); J junk slots range over all
quadratic forms in x; K last-layer slots over O = span(x, N, N^-1).  A solution (deficit 0) is a
last layer plus a junk space; it becomes a circuit with l + i + K ANDs if U = V_N + junk can be
spanned by l level-1 products (l = 27 - i - K for a 27).  The cover test is track C's exact
cover_enum.run (complete when l - dim U <= 2).

usage:
  python3 relax.py make --inv FILE --k K --j J --out PROB
  python3 relax.py post --inv FILE --prob PROB --sols GLOB --l L [--found DIR]
      prune each solution's junk, compute U, run the exact cover test with l products; on success
      build the circuit, run aes_check, write NCFF + JSON to --found
"""
from __future__ import annotations

import argparse
import glob
import itertools
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent / 'C'))
import gf                                          # noqa: E402
from core import write_ncff                        # noqa: E402
from nlbprob import Span, words                    # noqa: E402
from aes_prob import load_circuit, sbox_tables, n_coords   # noqa: E402
from ll_prob import ninv_coords, build_tables      # noqa: E402

ONES = (1 << 256) - 1
PAIRS = list(itertools.combinations(range(8), 2))     # C's order; variable i = U_i = bit 7-i of x
QM = [gf.X[i] & gf.X[j] for (i, j) in PAIRS]


def middle_pairs(inv):
    _, lev, ands = load_circuit(inv)
    top = max(lev)
    return [(A['Ltab'], A['Rtab']) for A in ands if 1 < A['level'] < top]


def nfuncs():
    N = [gf.power(p, 17) for p in range(256)]
    out = []
    for v in sorted(set(N)):
        t = 0
        for p in range(256):
            if N[p] == v: t |= 1 << p
        out.append(t)
    return out


ALLN = False


L1FILE = None


def spaces(inv):
    mids = middle_pairs(inv) if inv else []
    E0 = [ONES] + list(gf.X) + n_coords() + [a & b for a, b in mids]
    if L1FILE:
        _, lev, ands = load_circuit(L1FILE)
        E0 += [A['tab'] for A in ands if A['level'] == 1]
    if ALLN: E0 += nfuncs()
    O = list(gf.X) + n_coords() + ninv_coords()
    return mids, E0, O


def lin(m, basis):
    t = 0
    for i in range(len(basis)):
        if (m >> i) & 1: t ^= basis[i]
    return t


def read_sol(path, O):
    lines = Path(path).read_text().split('\n')
    h = lines[0].split()
    K = int(h[h.index('K') + 1]); nJ = int(h[h.index('nJ') + 1]); nS1 = int(h[h.index('nS1') + 1])
    LL = []
    for k in range(K):
        l, m = (int(v, 16) for v in lines[1 + k].split())
        LL.append((lin(l, O), lin(m, O)))
    J = [int(lines[1 + K + nS1 + s], 16) for s in range(nJ)]
    return LL, J


def deficit(base, T):
    S = Span()
    for t in base: S.add(t, 0)
    return sum(1 for t in T if S.add(t, 0))


def anf_quad(t):
    """28-bit form (C's PAIRS order) of a function of degree <= 2 (asserted)"""
    f = [(t >> p) & 1 for p in range(256)]
    for i in range(8):
        for p in range(256):
            if p >> i & 1: f[p] ^= f[p ^ (1 << i)]
    w = 0
    for k, (i, j) in enumerate(PAIRS):
        u = (1 << (7 - i)) | (1 << (7 - j))
        if f[u]: w |= 1 << k
    for p in range(256):
        if f[p] and bin(p).count('1') > 2: raise ValueError('not quadratic')
    return w


def form_to_pair(w):
    """rank-2 alternating form -> two x-linear forms (as tables) whose product has this form"""
    rows = [0] * 8
    for k, (i, j) in enumerate(PAIRS):
        if (w >> k) & 1: rows[i] |= 1 << j; rows[j] |= 1 << i
    nzr = [r for r in rows if r]
    a = nzr[0]
    b = next(r for r in nzr if r != a)
    def tab(v):
        t = 0
        for i in range(8):
            if (v >> i) & 1: t ^= gf.X[i]
        return t
    return tab(a), tab(b)


def cmd_make(a):
    mids, E0, O = spaces(a.inv)
    if a.ninv: E0 = E0 + ninv_coords()
    if a.quad: E0 = E0 + QM
    Q = nfuncs() if a.qv0 else QM
    if a.qboth: Q = QM + nfuncs()
    if a.qfile:
        # 16-point class representatives (inv_classes.py) -> 256-point functions of N
        import inv_fit as IF
        idx, _ = IF.coord_index()
        N = [gf.power(p, 17) for p in range(256)]
        reps = [int(h, 16) for h in json.loads(Path(a.qfile).read_text())['classes']]
        Q = []
        for r in reps:
            t = 0
            for p in range(256):
                c = idx[N[p]]
                xin = sum(((c >> i) & 1) << (3 - i) for i in range(4))
                if (r >> xin) & 1: t |= 1 << p
            Q.append(t)
    T = sbox_tables()
    L = ['4 256', str(len(E0))] + [words(t, 4) for t in E0]
    L += [str(len(O))] + [words(t, 4) for t in O]
    L += [str(len(T))] + [words(t, 4) for t in T] + [str(a.k)]
    L += ['0', str(a.j), str(len(Q))] + [words(t, 4) for t in Q]
    if a.fquad:
        L += [str(len(QM))] + [words(t, 4) for t in QM]
    Path(a.out).write_text('\n'.join(L) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'out': a.out, 'K': a.k, 'J': a.j, 'nE0': len(E0), 'deficit_T_mod_E0': deficit(E0, T)}))


def cmd_post(a):
    import cover_enum
    mids, E0, O = spaces(a.inv)
    T = sbox_tables()
    VN = [anf_quad(t) for t in n_coords()]
    found_dir = Path(a.found) if a.found else None
    seen = set()
    out = []
    for path in sorted(glob.glob(a.sols)):
        LL, J = read_sol(path, O)
        lltabs = [x & y for x, y in LL]
        jt = [lin(c, QM) for c in J]
        base = E0 + lltabs
        if deficit(base + jt, T) != 0:
            out.append({'sol': path, 'error': 'not a solution'}); continue
        # prune junk greedily
        keep = list(range(len(jt)))
        for s in list(keep):
            trial = [jt[q] for q in keep if q != s]
            if deficit(base + trial, T) == 0: keep.remove(s)
        # also prune last-layer products that are not needed
        needed_ll = [k for k in range(len(LL))
                     if deficit(E0 + [lltabs[q] for q in range(len(LL)) if q != k] + [jt[q] for q in keep], T) > 0]
        U = list(VN)
        sp = gf.Span()
        Ub = []
        for w in VN + [anf_quad(jt[q]) for q in keep]:
            if sp.add(w): Ub.append(w)
        key = (tuple(sorted(Ub)), tuple(sorted(lltabs)))
        if key in seen: continue
        seen.add(key)
        rec = {'sol': os.path.basename(path), 'K': len(LL), 'K_needed': len(needed_ll), 'J': len(keep),
               'dimU': len(Ub), 'l': a.l}
        if len(Ub) > a.l:
            rec['cover'] = 'impossible (dim U > l)'
        elif a.l - len(Ub) > 2:
            rec['cover'] = 'not tested (l - dim U > 2)'
        else:
            info, fnd = cover_enum.run(Ub, a.l)
            rec['cover'] = 'FOUND' if fnd else 'none'
            rec['cover_info'] = {k: info[k] for k in ('d', 'e', 'in_U', 'points') if k in info}
            if fnd and found_dir:
                rec['circuit'] = build_hit(fnd[0], Ub, a.l, mids, LL, T, found_dir, path, a)
        out.append(rec)
        print(json.dumps(rec), flush=True)
    return out


def build_hit(Y, Ub, l, mids, LL, T, found_dir, path, a):
    import cover_enum
    # recover the forms of the plane Y and keep a spanning set of <= l forms
    R = cover_enum.rank2_forms()
    import qmc
    Nu = qmc.Normal(Ub)
    forms = [w for w in R if Nu.nf(w) in set(Y) | {0}]
    sp = gf.Span(); sel = []
    for w in forms:
        if sp.add(w): sel.append(w)
    sel = sel[:l] if len(sel) > l else sel
    pairs = [form_to_pair(w) for w in sel] + mids + LL
    c = build_tables(pairs, T)
    found_dir.mkdir(parents=True, exist_ok=True)
    stem = 'G-relax-%s-%d' % (Path(path).stem, int(time.time()))
    f = found_dir / (stem + '.circ.txt')
    f.write_text(write_ncff(c, comments=['track G relaxed walk + exact cover']), encoding='utf-8', newline='\n')
    chk = subprocess.run([sys.executable, str(HERE.parents[1] / 'campaigns' / 'aes_check.py'), str(f)],
                         capture_output=True, text=True)
    (found_dir / (stem + '.check.txt')).write_text(chk.stdout + chk.stderr)
    m = c.metrics()
    (found_dir / (stem + '.json')).write_text(json.dumps({'method': 'track G relaxed llay walk + exact cover (cover_enum)',
                                                          'sol': path, 'A': m['A'], 'G': m['G'],
                                                          'time_utc': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}))
    return {'file': str(f), 'A': m['A'], 'check_rc': chk.returncode}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd'); ap.add_argument('--inv'); ap.add_argument('--k', type=int); ap.add_argument('--j', type=int)
    ap.add_argument('--out'); ap.add_argument('--prob'); ap.add_argument('--sols'); ap.add_argument('--l', type=int)
    ap.add_argument('--found')
    ap.add_argument('--alln', action='store_true', help='E0 also contains every function of N')
    ap.add_argument('--l1', default=None, help='fixed level-1 products of this file in E0')
    ap.add_argument('--k5', type=int, default=5, help='middle AND budget tested by midpost')
    ap.add_argument('--ninv', action='store_true', help='E0 also contains the coordinates of N^-1')
    ap.add_argument('--quad', action='store_true', help='E0 also contains every quadratic form in x')
    ap.add_argument('--qboth', action='store_true', help='junk slots range over Quad + V0')
    ap.add_argument('--qfile', default=None, help='junk candidates: inv_classes.py JSON (list mode)')
    ap.add_argument('--fquad', action='store_true', help='feasibility space F = Quad (llay feas=1)')
    ap.add_argument('--qv0', action='store_true', help='junk slots range over functions of N (not quadratics)')
    a = ap.parse_args()
    global ALLN, L1FILE
    ALLN = a.alln
    L1FILE = a.l1
    {'make': cmd_make, 'post': cmd_post}[a.cmd](a)


if __name__ == '__main__':
    main()
