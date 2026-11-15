"""Three-stage evaluation of a last layer (track G).

For a last layer LL (K products over O = span(x, N, N^-1)), write every output as
    t = (LL part) + q + r + affine,   q a quadratic form in x, r a function of N
(unique up to the overlaps; checked).  A circuit with l + m + K ANDs exists if
  (a) U = span(V_N, q_1..q_8) is spanned by l level-1 products (exact SAT, track C's qmc model), and
  (b) span(N^-1 coordinates, r_1..r_8) lies in span(1, N, m products) of a circuit on the 4 bits of
      N (nlb, 4-bit; exact SAT available in sat_small.py).
On (a) and (b) the circuit is built and checked (aes_check) and stored in --found.

usage: python3 eval3.py --sols GLOB [--l 9] [--m 5] [--cover-limit 300] [--mid-secs 10]
                        [--found DIR] [--log OUT.jsonl]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent / 'C'))
import gf                                           # noqa: E402
import qmc                                          # noqa: E402
from core import write_ncff                         # noqa: E402
from nlbprob import Span, Problem                   # noqa: E402
from aes_prob import sbox_tables, n_coords          # noqa: E402
from ll_prob import ninv_coords, build_tables       # noqa: E402
import inv_fit as IF                                # noqa: E402
from midfit import read_ll, middle_pairs_from_sol   # noqa: E402

ONES = (1 << 256) - 1
QM = [gf.X[i] & gf.X[j] for i in range(8) for j in range(i + 1, 8)]


def decompose(LL):
    """q_i, r_i (256-bit tables) for each output, or None if T not in LL + Quad + V0 + affine"""
    T = sbox_tables()
    V0 = [t for _, t in IF.v0_basis()]
    S = Span()
    tags = []
    base = [ONES] + list(gf.X) + [a & b for a, b in LL]
    nb = len(base)
    for j, t in enumerate(base): S.add(t, 0)
    for j, t in enumerate(QM): S.add(t, 1 << j)
    for j, t in enumerate(V0): S.add(t, 1 << (28 + j))
    qs, rs = [], []
    for t in T:
        tag = S.express(t)
        if tag is None: return None, None
        q = 0; r = 0
        for j in range(28):
            if (tag >> j) & 1: q ^= QM[j]
        for j in range(16):
            if (tag >> (28 + j)) & 1: r ^= V0[j]
        qs.append(q); rs.append(r)
    return qs, rs


def cover_enum_pairs(U, l):
    """exact cover test via track C's cover_enum (valid for l - dim U <= 2); returns (ok, pairs)"""
    import cover_enum
    from relax import anf_quad, form_to_pair
    U28 = [anf_quad(t) for t in U]
    info, fnd = cover_enum.run(U28, l)
    if not fnd: return False, None
    Y = set(fnd[0]) | {0}
    Nu = qmc.Normal(U28)
    forms = [w for w in cover_enum.rank2_forms() if Nu.nf(w) in Y]
    sp = gf.Span(); sel = []
    for w in forms:
        if sp.add(w): sel.append(w)
    pairs = [form_to_pair(w) for w in sel]
    return True, pairs[:l] if len(pairs) <= l else None


def cover_sat(U, l, limit):
    if l - len(U) <= 2:
        return cover_enum_pairs(U, l)
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        fi = Path(td) / 'in.json'; fo = Path(td) / 'out.json'
        fi.write_text(json.dumps({'U': ['%x' % t for t in U], 'l': l}))
        try:
            subprocess.run([sys.executable, str(HERE / 'cover_cli.py'), str(fi), str(fo)], timeout=limit)
        except subprocess.TimeoutExpired:
            return None, None
        if not fo.exists(): return None, None
        r = json.loads(fo.read_text())
    if not r['sat']: return False, None
    return True, [(int(a, 16), int(b, 16)) for a, b in r['pairs']]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sols', required=True); ap.add_argument('--l', type=int, default=9)
    ap.add_argument('--m', type=int, default=5); ap.add_argument('--cover-limit', type=float, default=300)
    ap.add_argument('--mid-secs', type=float, default=10)
    ap.add_argument('--found', default=os.path.expanduser('~/xs-campaigns/2026-11-14-G/found'))
    ap.add_argument('--log', default=None)
    ap.add_argument('--skip-cover-if-mid-fails', action='store_true')
    a = ap.parse_args()
    log = open(a.log, 'a') if a.log else None
    seen = set()
    idx, _ = IF.coord_index()
    VN = n_coords()
    for sp in sorted(glob.glob(a.sols)):
        LL = read_ll(sp)
        key = tuple(sorted(x & y for x, y in LL))
        if key in seen: continue
        seen.add(key)
        rec = {'sol': os.path.basename(sp), 'K': len(LL)}
        qs, rs = decompose(LL)
        if qs is None:
            rec['error'] = 'T not in LL + Quad + V0'
        else:
            # U basis mod affine
            A = Span()
            for t in [ONES] + list(gf.X): A.add(t, 0)
            U = [t for t in VN + qs if A.add(t, 0)]
            # middle space mod affine-in-N
            n16 = [IF.to16(t, idx) for t in ninv_coords()]
            r16 = [IF.to16(t, idx) for t in rs]
            B = Span()
            for t in [0xFFFF] + [IF.to16(c, idx) for c in VN]: B.add(t, 0)
            mid = [t for t in n16 + r16 if B.add(t, 0)]
            rec.update({'dimU': len(U), 'dim_mid': len(mid)})
            # (b) middle by nlb
            P = Problem(4)
            for _ in range(a.m): P.add_slot()
            P.add_group(mid)
            pf = sp + '.mid3.prob'; P.write(pf)
            pre = sp + '.mid3'
            for ext in ('.log', '.sol', '.best'):
                if os.path.exists(pre + ext): os.unlink(pre + ext)
            mid_ok = False
            if len(mid) <= a.m:
                subprocess.run([str(HERE / 'nlb'), pf, pre, '1', str(a.mid_secs), 'init=0', 'report=1000'])
                mid_ok = os.path.exists(pre + '.sol')
            rec['mid_ok'] = mid_ok
            # (a) cover by SAT
            cov = None
            if len(U) <= a.l and (mid_ok or not a.skip_cover_if_mid_fails):
                t0 = time.time()
                ok, pairs = cover_sat(U, a.l, a.cover_limit)
                rec['cover'] = {True: 'SAT', False: 'UNSAT', None: 'timeout'}[ok]
                rec['cover_secs'] = round(time.time() - t0, 1)
                cov = pairs
            elif len(U) > a.l:
                rec['cover'] = 'impossible (dim U > l)'
            if cov and mid_ok:
                mids = middle_pairs_from_sol(pre + '.sol', a.m)
                c = build_tables(cov + mids + LL, sbox_tables())
                Path(a.found).mkdir(parents=True, exist_ok=True)
                stem = 'G-eval3-%s-%d' % (Path(sp).name, int(time.time()))
                f = Path(a.found) / (stem + '.circ.txt')
                f.write_text(write_ncff(c, comments=['track G: walk last layer + SAT stage 1 + nlb middle']),
                             encoding='utf-8', newline='\n')
                chk = subprocess.run([sys.executable, str(HERE.parents[1] / 'campaigns' / 'aes_check.py'), str(f)],
                                     capture_output=True, text=True)
                (Path(a.found) / (stem + '.check.txt')).write_text(chk.stdout + chk.stderr)
                mm = c.metrics()
                side = {'method': 'track G eval3: llay walk layer + exact stage-1 cover SAT + nlb middle',
                        'sol': sp, 'A': mm['A'], 'G': mm['G'], 'check_rc': chk.returncode,
                        'time_utc': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}
                (Path(a.found) / (stem + '.json')).write_text(json.dumps(side, indent=1))
                rec['circuit'] = side
        print(json.dumps(rec), flush=True)
        if log: log.write(json.dumps(rec) + '\n'); log.flush()


if __name__ == '__main__':
    main()
