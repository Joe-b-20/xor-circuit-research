#!/usr/bin/env python3
"""Linear-region resynthesis with XORFlux (track F).

A convex region R of linear gates (trb.pick_region: bottom / top / mid / random, or 'layer:k')
is cut out; its targets are affine forms over its leaves.  The pure linear part (targets without
constants, duplicates and single-leaf targets removed) is written as a 0/1 matrix and optimised
by XORFlux (`search/xorflux quick`, gates objective, optional uniform depth cap).  Every record
XORFlux writes is tried, cheapest first: spliced back (constants as XNOR/NOT on the target's
root), and kept only if every target meets its exact required level for the circuit's cap D
(so the whole circuit meets D).  Result is checked on all 256 inputs.

    python3 linres.py FILE --cap D --region mid --seconds 60 --seed 1 [--depth-cap K] [--out OUT]
"""
import argparse
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2])); sys.path.insert(0, str(HERE))
from boolflux import core, targets   # noqa: E402
import trb   # noqa: E402

XORFLUX = Path.home() / 'xor-circuit-research' / 'search' / 'xorflux'
AND, XOR, XNOR, NOT = 8, 6, 9, 3


def region_of(c, D, kind, rng):
    lv, al, req, fo = trb.struct(c, D)
    if kind.startswith('layer:'):
        k = int(kind[6:]); n = c.n
        R = {s for s in range(n, n + len(c.gates)) if c.gates[s - n][0] != AND and al[s] == k}
    else:
        R = trb.pick_region(c, kind, rng, lv, al, fo)
    return R, lv, req, fo


def extract(c, R, fo):
    n = c.n
    leaves = sorted({x for s in R for x in c.gates[s - n][1:] if x not in R})
    li = {x: i for i, x in enumerate(leaves)}
    form = {}
    for s in sorted(R):
        op, a, b = c.gates[s - n]
        fa = form[a] if a in R else (1 << (1 + li[a]))
        fb = form[b] if b in R else (1 << (1 + li[b]))
        form[s] = fa ^ fb ^ (1 if op == XNOR else 0) if op != NOT else fa ^ 1
    outset = set(c.outputs)
    tg = [s for s in sorted(R) if s in outset or any(y not in R for y in fo[s])]
    return leaves, form, tg


def solve(c, D, kind, rng, seconds=60, depth_cap=None, seed=1, workdir=None, region=None):
    n = c.n
    R, lv, req, fo = region_of(c, D, kind, rng) if region is None else (region,) + trb.struct(c, D)[0:3:2] + (trb.struct(c, D)[3],)
    if len(R) < 3: return None, {'skipped': 'small region'}
    leaves, form, tg = extract(c, R, fo)
    # distinct pure-linear rows
    rows = []; rowidx = {}
    for t in tg:
        f = form[t] & ~1
        if bin(f).count('1') <= 1: continue
        if f not in rowidx: rowidx[f] = len(rows); rows.append(f)
    if len(rows) < 2: return None, {'skipped': 'no linear map'}
    L = len(leaves)
    wd = Path(workdir or tempfile.mkdtemp(prefix='linres-'))
    wd.mkdir(parents=True, exist_ok=True)
    mat = wd / 'region.mat.txt'
    mat.write_text('1\n%d %d\n' % (len(rows), L) + ''.join(' '.join('1' if (f >> (1 + j)) & 1 else '0' for j in range(L)) + '\n' for f in rows))
    cmd = [sys.executable, str(XORFLUX), 'quick', str(mat), '--seconds', str(seconds), '--seed', str(seed), '--out', str(wd / 'xf')]
    if depth_cap: cmd += ['--depth-cap', str(depth_cap)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0: return None, {'error': (r.stdout + r.stderr)[-400:]}
    recs = [json.loads(l) for l in (wd / 'xf' / 'workers' / 'quick-00' / 'records.jsonl').read_text().splitlines() if l.strip()]
    recs.sort(key=lambda r: (r['gates'], r['depth']))
    old_lin = len(R)
    for rec in recs:
        d = json.loads((wd / 'xf' / rec['path']).read_text())
        nc = splice(c, R, leaves, form, tg, rows, rowidx, d, lv, req)
        if nc is None: continue
        m = nc.metrics()
        if m['GD'] <= max(D, 0) and nc.value_table() == targets.aes_sbox():
            return nc, {'region_gates': old_lin, 'leaves': L, 'rows': len(rows), 'xorflux_gates': rec['gates'],
                        'xorflux_depth': rec['depth'], 'G_before': len(c.gates), 'G_after': len(nc.gates)}
    return None, {'region_gates': old_lin, 'leaves': L, 'rows': len(rows), 'no_feasible_record': len(recs)}


def splice(c, R, leaves, form, tg, rows, rowidx, d, lv, req):
    """XORFlux circuit d (inputs = leaves, outputs = rows) -> new full circuit, or None if a
    target misses its required level."""
    n = c.n; L = len(leaves)
    gates = []; level = {}
    # new signals: leaf j -> circuit signal leaves[j]; XORFlux gate k -> new XOR
    sig = {j: leaves[j] for j in range(L)}
    newgates = []
    for k, (a, b) in enumerate(d['gates']):
        newgates.append((a, b))
    outsig = d['outputSignals']
    # polarity: every XOR gate may be an XNOR; give each target root the polarity its constant asks for
    want = {}
    for t in tg:
        f = form[t]; lin = f & ~1
        if bin(lin).count('1') > 1: want.setdefault(outsig[rowidx[lin]], set()).add(f & 1)
    pol = {j: 0 for j in range(L)}
    for k, (a, b) in enumerate(newgates):
        sgl = L + k; w = want.get(sgl, {0})
        pol[sgl] = 1 if w == {1} else 0
    built = {}
    mp = {i: i for i in range(n)}
    def xf(s):
        if s < L: return mp_get(leaves[s])
        if s in built: return built[s]
        a, b = newgates[s - L]
        x, y = xf(a), xf(b)
        op = XNOR if (pol[s] ^ pol[a] ^ pol[b]) else XOR
        gates.append((op, x, y)); built[s] = n + len(gates) - 1
        return built[s]
    tmap = {}
    def mp_get(s):
        if s < n: return s
        if s in mp: return mp[s]
        if s in R:
            if s in tmap: return tmap[s]
            f = form[s]; cst = f & 1; lin = f & ~1
            if bin(lin).count('1') == 1:
                j = lin.bit_length() - 2; g = mp_get(leaves[j]); p = 0
            else:
                xs = outsig[rowidx[lin]]; g = xf(xs); p = pol[xs]
            if cst != p:
                gates.append((NOT, g, g)); g = n + len(gates) - 1
            tmap[s] = g; return g
        op, a, b = c.gates[s - n]
        x, y = mp_get(a), mp_get(b)
        gates.append((op, x, y)); mp[s] = n + len(gates) - 1
        return mp[s]
    sys.setrecursionlimit(20000)
    outs = [mp_get(o) for o in c.outputs]
    nc = core.Circuit(n, c.m, gates, outs, c.name, c.in_names, c.out_names).live()
    return nc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file'); ap.add_argument('--cap', type=int, required=True)
    ap.add_argument('--region', default='mid'); ap.add_argument('--seconds', type=float, default=60)
    ap.add_argument('--seed', type=int, default=1); ap.add_argument('--depth-cap', type=int)
    ap.add_argument('--out')
    a = ap.parse_args()
    c = core.read_ncff(a.file)
    nc, info = solve(c, a.cap, a.region, random.Random(a.seed), a.seconds, a.depth_cap, a.seed)
    print(info)
    if nc is not None:
        m = nc.metrics(); print('G=%d A=%d GD=%d AD=%d' % (m['G'], m['A'], m['GD'], m['AD']))
        if a.out: Path(a.out).write_text(core.write_ncff(nc, core.Model.load(str(core.MODELS / 'nist.json'))))


if __name__ == '__main__':
    main()
