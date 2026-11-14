"""Calibration of the nlb local search on small functions with known / SAT-computed MC.

usage:
  python3 small.py sat NAME K              exact SAT (track C's CHM encoding, CaDiCaL) for MC <= K
  python3 small.py ls NAME K SEEDS SECS [level1] [nlb k=v ...]
                                           nlb runs (any depth unless 'level1'); prints a JSON line
NAME: any targets.py name (4-bit S-boxes, gf16-inv, gf16-mul, ...) or 'norm16' (x -> x^17
coordinates, 8 -> 4 bits) or 'aes'.
"""
from __future__ import annotations

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
import targets                                   # noqa: E402
from core import tables_from_values              # noqa: E402
from nlbprob import Problem                      # noqa: E402

OUT = Path(os.path.expanduser('~/xs-campaigns/2026-11-14-G/small'))


def gfmul8(a, b):
    r = 0
    while b:
        if b & 1: r ^= a
        b >>= 1; a <<= 1
        if a & 0x100: a ^= 0x11B
    return r


def gfpow8(a, e):
    r = 1
    while e:
        if e & 1: r = gfmul8(r, a)
        a = gfmul8(a, a); e >>= 1
    return r


def load(name):
    if name == 'norm16':
        # x -> x^17 lies in GF(16); its 4 coordinates (basis-independent span) as 4 targets
        vals = [gfpow8(x, 17) for x in range(256)]
        sub = sorted(set(vals))
        basis = []
        span = {0}
        for v in sub:
            if v not in span:
                basis.append(v); span |= {s ^ v for s in span}
        # coordinates w.r.t. basis
        idx = {}
        for c in range(16):
            v = 0
            for i in range(4):
                if (c >> i) & 1: v ^= basis[i]
            idx[v] = c
        table = [idx[v] for v in vals]
        return 8, 4, table
    n, m, table, _ = targets.load(name)
    return n, m, table


def build(name, K, level1=False):
    n, m, table = load(name)
    P = Problem(n)
    for _ in range(K):
        P.add_slot(allow=P.x_mask() if level1 else None)
    P.add_group(tables_from_values(n, m, table))
    return P


def run_ls(name, K, seeds, secs, level1=False, extra=()):
    OUT.mkdir(parents=True, exist_ok=True)
    P = build(name, K, level1)
    tag = '%s-k%d%s' % (name, K, '-l1' if level1 else '')
    pf = OUT / (tag + '.prob'); P.write(pf)
    res = []
    for s in seeds:
        pre = OUT / ('%s-s%d' % (tag, s))
        for ext in ('.log', '.sol', '.best'):
            p = Path(str(pre) + ext)
            if p.exists(): p.unlink()
        t0 = time.time()
        subprocess.run([str(HERE / 'nlb'), str(pf), str(pre), str(s), str(secs), 'init=0'] + list(extra))
        dt = time.time() - t0
        solved = Path(str(pre) + '.sol').exists()
        best = None
        for line in Path(str(pre) + '.log').read_text().split('\n'):
            if line.startswith('END') or ' best ' in line:
                try: best = float(line.split(' best ')[1].split()[0])
                except Exception: pass
        res.append({'seed': s, 'solved': solved, 'secs': round(dt, 2), 'best': 0.0 if solved else best})
    out = {'name': name, 'K': K, 'level1': level1, 'secs_limit': secs, 'runs': res,
           'solved': sum(r['solved'] for r in res), 'n': len(res),
           'median_secs_solved': sorted(r['secs'] for r in res if r['solved'])[len([r for r in res if r['solved']]) // 2] if any(r['solved'] for r in res) else None}
    print(json.dumps(out), flush=True)
    with open(OUT / 'calibration.jsonl', 'a') as f: f.write(json.dumps(out) + '\n')
    return out


def run_sat(name, K):
    import mc_small
    import qmc
    n, m, table = load(name)
    f = mc_small.encode(table, n, m, K)
    ok, model, dt = qmc.solve(f, 'cadical153')
    out = {'name': name, 'K': K, 'sat': ok, 'secs': round(dt, 1)}
    print(json.dumps(out), flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / 'sat.jsonl', 'a') as fo: fo.write(json.dumps(out) + '\n')
    return out


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'sat':
        run_sat(sys.argv[2], int(sys.argv[3]))
    elif cmd == 'ls':
        name, K = sys.argv[2], int(sys.argv[3])
        a, b = sys.argv[4].split('-') if '-' in sys.argv[4] else (sys.argv[4], sys.argv[4])
        seeds = range(int(a), int(b) + 1)
        secs = float(sys.argv[5])
        rest = sys.argv[6:]
        level1 = 'level1' in rest
        extra = [r for r in rest if '=' in r]
        run_ls(name, K, seeds, secs, level1, extra)
