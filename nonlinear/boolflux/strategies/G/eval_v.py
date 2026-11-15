"""Evaluation of layers from the one-N-function walks (track G; relax.py make --ninv --qv0 --fquad
--j 1; llay feas=1).  A solution holds a last layer LL and one function v of N (junk slot) with
T in span(1, x, N, n, v, LL) + Wq for a quadratic junk space Wq of dimension d (the walk score).
27 = l + m + K needs (a) span(n, v) mod affine from an m-AND circuit on the 4 bits of N (nlb),
(b) U = V_N + Wq spanned by l level-1 products (cover_enum / SAT).  Builds and checks on success.

usage: python3 eval_v.py --sols GLOB --l L --m 5 [--found DIR] [--log OUT.jsonl] [--mid-secs 10]
"""
from __future__ import annotations

import argparse
import glob
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
import gf                                           # noqa: E402
from core import write_ncff                         # noqa: E402
from nlbprob import Span, Problem                   # noqa: E402
from aes_prob import sbox_tables, n_coords          # noqa: E402
from ll_prob import ninv_coords, build_tables       # noqa: E402
import inv_fit as IF                                # noqa: E402
from midfit import middle_pairs_from_sol            # noqa: E402
from eval3 import cover_sat                         # noqa: E402

ONES = (1 << 256) - 1
O = list(gf.X) + n_coords() + ninv_coords()
QM = [gf.X[i] & gf.X[j] for i in range(8) for j in range(i + 1, 8)]
V0 = None


def lin(m, basis):
    t = 0
    for i in range(len(basis)):
        if (m >> i) & 1: t ^= basis[i]
    return t


def read_q(probpath):
    """junk-slot basis Qt of an llay problem file (list or span mode)"""
    tok = Path(probpath).read_text().split('\n')
    i = 1

    def tabs(i):
        n = int(tok[i]); out = []
        for j in range(n):
            ws = [int(w, 16) for w in tok[i + 1 + j].split()]
            out.append(sum(w << (64 * k) for k, w in enumerate(ws)))
        return out, i + 1 + n
    _, i = tabs(i); _, i = tabs(i); _, i = tabs(i)
    i += 1                                   # K
    ns1 = int(tok[i]); i += 1
    assert ns1 == 0, 'stage-1 slots not supported here'
    nj, nq = (int(v) for v in tok[i].split()) if len(tok[i].split()) == 2 else (int(tok[i]), int(tok[i + 1]))
    if len(tok[i].split()) == 2: i += 1
    else: i += 2
    Q = []
    for j in range(nq):
        ws = [int(w, 16) for w in tok[i + j].split()]
        Q.append(sum(w << (64 * k) for k, w in enumerate(ws)))
    return Q


QBASIS = None


def read_sol(path):
    lines = Path(path).read_text().split('\n')
    h = lines[0].split()
    K = int(h[h.index('K') + 1]); nJ = int(h[h.index('nJ') + 1])
    LL = [tuple(lin(int(v, 16), O) for v in lines[1 + k].split()) for k in range(K)]
    J = [lin(int(lines[1 + K + s], 16), QBASIS) for s in range(nJ)]
    return LL, J


def quad_junk(B, T):
    """minimal Wq inside Quad with T in span(B) + Wq, or None"""
    S = Span()
    for t in B: S.add(t, 0)
    taus = []
    St = Span()
    # tau basis: T mod B
    for t in T:
        r, _ = S.reduce(t, 0)
        # full reduction
        while r:
            p = r.bit_length() - 1
            if p in S.rows: r ^= S.rows[p][0]
            else: break
    d = 0
    S2 = Span()
    for t in B: S2.add(t, 0)
    d = sum(1 for t in T if S2.add(t, 0))
    # combined: B + Quad; express each output as B-part + quad-part
    S3 = Span()
    for t in B: S3.add(t, 0)
    for j, q in enumerate(QM): S3.add(q, 1 << j)
    W = []
    for t in T:
        tag = S3.express(t)
        if tag is None: return None, d
        q = 0
        for j in range(28):
            if (tag >> j) & 1: q ^= QM[j]
        W.append(q)
    # reduce W modulo B to a basis of dimension d
    S4 = Span()
    for t in B: S4.add(t, 0)
    Wq = [q for q in W if S4.add(q, 0)]
    return Wq, d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sols', required=True); ap.add_argument('--l', type=int, default=9)
    ap.add_argument('--m', type=int, default=5); ap.add_argument('--mid-secs', type=float, default=10)
    ap.add_argument('--cover-limit', type=float, default=600)
    ap.add_argument('--found', default=os.path.expanduser('~/xs-campaigns/2026-11-14-G/found'))
    ap.add_argument('--log', default=None)
    ap.add_argument('--prob', required=True, help='the llay problem file (for the junk basis)')
    a = ap.parse_args()
    global QBASIS
    QBASIS = read_q(a.prob)
    log = open(a.log, 'a') if a.log else None
    idx, _ = IF.coord_index()
    T = sbox_tables()
    E0 = [ONES] + list(gf.X) + n_coords() + ninv_coords()
    seen = set()
    midcache = {}
    for sp in sorted(glob.glob(a.sols)):
        LL, J = read_sol(sp)
        key = (tuple(sorted(x & y for x, y in LL)), tuple(J))
        if key in seen: continue
        seen.add(key)
        rec = {'sol': os.path.basename(sp), 'K': len(LL)}
        B = E0 + J + [x & y for x, y in LL]
        Wq, d = quad_junk(B, T)
        if Wq is None:
            rec['error'] = 'infeasible with Quad'; print(json.dumps(rec), flush=True)
            if log: log.write(json.dumps(rec) + '\n')
            continue
        A = Span()
        for t in [ONES] + list(gf.X): A.add(t, 0)
        U = [t for t in n_coords() + Wq if A.add(t, 0)]
        rec.update({'d': d, 'dimU': len(U)})
        # middle: span(n, v) by m ANDs on the 4 bits of N
        n16 = [IF.to16(t, idx) for t in ninv_coords()]
        v16 = [IF.to16(t, idx) for t in J]
        mk = tuple(v16)
        rec['v16'] = ['%04x' % v for v in v16]
        if mk in midcache:
            mid_ok, mids = midcache[mk]
        else:
            # exact: DFS over all 5-AND circuits whose product span is span(n, v) (exact_mid.py)
            import exact_mid as XM
            S = XM.Sp([XM.ONES] + XM.INP)
            Sb = [t for t in n16 + v16 if S.add(t)]
            mids = None
            if len(Sb) == a.m == 5:
                f = XM.search(Sb)
                if f:
                    N = [gf.power(p, 17) for p in range(256)]
                    def to256(r):
                        t = 0
                        for p in range(256):
                            c = idx[N[p]]
                            xin = sum(((c >> i) & 1) << (3 - i) for i in range(4))
                            if (r >> xin) & 1: t |= 1 << p
                        return t
                    mids = [(to256(x), to256(y)) for x, y, _ in f[0]]
            elif len(Sb) < a.m:
                # n alone (v redundant): any 5-AND inversion works; take the AD5 file's middle
                from relax import middle_pairs
                mids = middle_pairs(str(HERE.parents[2] / 'nist' / 'aes-sbox' / 'aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt'))
            mid_ok = mids is not None
            midcache[mk] = (mid_ok, mids)
        rec['mid_ok'] = mid_ok
        if mid_ok and len(U) <= a.l:
            ok, pairs = cover_sat(U, a.l, a.cover_limit)
            rec['cover'] = {True: 'SAT', False: 'UNSAT', None: 'timeout'}[ok]
            if ok:
                c = build_tables(pairs + mids + LL, T)
                Path(a.found).mkdir(parents=True, exist_ok=True)
                stem = 'G-evalv-%s-%d' % (Path(sp).name, int(time.time()))
                f = Path(a.found) / (stem + '.circ.txt')
                f.write_text(write_ncff(c, comments=['track G: one-N-function walk layer + SAT stage 1 + nlb middle']),
                             encoding='utf-8', newline='\n')
                chk = subprocess.run([sys.executable, str(HERE.parents[1] / 'campaigns' / 'aes_check.py'), str(f)],
                                     capture_output=True, text=True)
                (Path(a.found) / (stem + '.check.txt')).write_text(chk.stdout + chk.stderr)
                mm = c.metrics()
                side = {'method': 'track G eval_v: llay walk (1 N-function slot, quad feasibility) + stage-1 cover + nlb middle',
                        'sol': sp, 'A': mm['A'], 'G': mm['G'], 'check_rc': chk.returncode,
                        'time_utc': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}
                (Path(a.found) / (stem + '.json')).write_text(json.dumps(side, indent=1))
                rec['circuit'] = side
        elif len(U) > a.l:
            rec['cover'] = 'impossible (dim U > l)'
        print(json.dumps(rec), flush=True)
        if log: log.write(json.dumps(rec) + '\n'); log.flush()


if __name__ == '__main__':
    main()
