"""Middle-stage fitting for walk solutions (track G).

For last layers found by llay over E0 = span(1, x, fixed level-1 products of --l1, all functions of
N) (relax.py make --l1 FILE --alln --j 0), test whether a middle stage of --m ANDs (functions of N
only) provides n = N^-1 and the outputs' N-function residues: a 4-bit problem (inv_fit.py),
solved by nlb (and confirmed by building the full circuit + aes_check on a hit).

usage: python3 midfit.py --l1 FILE --sols GLOB --m 5 [--secs 20] [--found DIR] [--log OUT.jsonl]
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
from nlbprob import Problem                         # noqa: E402
from aes_prob import load_circuit, sbox_tables, n_coords   # noqa: E402
from ll_prob import ninv_coords, build_tables       # noqa: E402
import inv_fit as IF                                # noqa: E402

ONES = (1 << 256) - 1
O = list(gf.X) + n_coords() + ninv_coords()


def lin(m, basis):
    t = 0
    for i in range(len(basis)):
        if (m >> i) & 1: t ^= basis[i]
    return t


def read_ll(path):
    lines = Path(path).read_text().split('\n')
    h = lines[0].split(); K = int(h[h.index('K') + 1])
    return [tuple(lin(int(v, 16), O) for v in lines[1 + k].split()) for k in range(K)]


def mid_problem(L1tabs, LL, m):
    T = sbox_tables()
    base1 = [ONES] + list(gf.X) + L1tabs
    Wx = base1 + [a & b for a, b in LL]
    r = IF.components(T, Wx)
    if r is None: return None, {'error': 'T not in Wx + V0'}
    idx, _ = IF.coord_index()
    r16 = [IF.to16(t, idx) for t in r]
    n16 = [IF.to16(t, idx) for t in ninv_coords()]
    Ar = [IF.to16(t, idx) for t in IF.intersect_v0(Wx)]
    An = [IF.to16(t, idx) for t in IF.intersect_v0(base1)]
    P = Problem(4)
    for _ in range(m): P.add_slot()
    P.add_group(n16, An)
    P.add_group(r16, Ar)
    return P, {}


def middle_pairs_from_sol(solpath, m):
    """nlb 4-bit solution -> list of (Ltab, Rtab) 256-point operand tables (functions of N)"""
    lines = Path(solpath).read_text().split('\n')
    elems = [ONES] + n_coords()                 # 4-bit inputs i = N coordinate i
    pairs = []
    for k in range(m):
        a, b = (int(v, 16) for v in lines[1 + k].split())
        ta = lin(a, elems); tb = lin(b, elems)
        pairs.append((ta, tb)); elems.append(ta & tb)
    return pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--l1', required=True); ap.add_argument('--sols', required=True)
    ap.add_argument('--m', type=int, default=5); ap.add_argument('--secs', type=float, default=20)
    ap.add_argument('--found', default=os.path.expanduser('~/xs-campaigns/2026-11-14-G/found'))
    ap.add_argument('--log', default=None); ap.add_argument('--seeds', type=int, default=1)
    a = ap.parse_args()
    _, lev, ands = load_circuit(a.l1)
    L1pairs = [(A['Ltab'], A['Rtab']) for A in ands if A['level'] == 1]
    L1tabs = [x & y for x, y in L1pairs]
    seen = set()
    log = open(a.log, 'a') if a.log else None
    for sp in sorted(glob.glob(a.sols)):
        LL = read_ll(sp)
        key = tuple(sorted(x & y for x, y in LL))
        if key in seen: continue
        seen.add(key)
        P, info = mid_problem(L1tabs, LL, a.m)
        rec = {'sol': os.path.basename(sp), 'm': a.m, **info}
        if P is not None:
            pf = sp + '.mid.prob'; P.write(pf)
            best = None; solved = False
            for s in range(1, a.seeds + 1):
                pre = sp + '.mid-s%d' % s
                for ext in ('.log', '.sol', '.best'):
                    if os.path.exists(pre + ext): os.unlink(pre + ext)
                subprocess.run([str(HERE / 'nlb'), pf, pre, str(s), str(a.secs), 'init=0', 'report=1000'])
                for line in Path(pre + '.log').read_text().split('\n'):
                    if ' best ' in line:
                        try: best = float(line.split(' best ')[1].split()[0])
                        except ValueError: pass
                if os.path.exists(pre + '.sol'): solved = True; break
            rec.update({'mid_solved': solved, 'mid_best': 0.0 if solved else best})
            if solved:
                mids = middle_pairs_from_sol(pre + '.sol', a.m)
                c = build_tables(L1pairs + mids + LL, sbox_tables())
                Path(a.found).mkdir(parents=True, exist_ok=True)
                stem = 'G-midfit-%s-%d' % (Path(sp).name, int(time.time()))
                f = Path(a.found) / (stem + '.circ.txt')
                f.write_text(write_ncff(c, comments=['track G: walk last layer + fitted middle (%d ANDs)' % a.m]),
                             encoding='utf-8', newline='\n')
                chk = subprocess.run([sys.executable, str(HERE.parents[1] / 'campaigns' / 'aes_check.py'), str(f)],
                                     capture_output=True, text=True)
                (Path(a.found) / (stem + '.check.txt')).write_text(chk.stdout + chk.stderr)
                mm = c.metrics()
                side = {'method': 'track G llay walk over fixed level-1 + free N-functions, middle fitted by nlb',
                        'l1': a.l1, 'sol': sp, 'A': mm['A'], 'G': mm['G'], 'check_rc': chk.returncode,
                        'time_utc': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}
                (Path(a.found) / (stem + '.json')).write_text(json.dumps(side, indent=1))
                rec['circuit'] = side
        print(json.dumps(rec), flush=True)
        if log: log.write(json.dumps(rec) + '\n'); log.flush()


if __name__ == '__main__':
    main()
