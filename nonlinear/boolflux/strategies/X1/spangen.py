#!/usr/bin/env python3
"""New AND spaces at the same AND count: walk (bfw) from FILE, dump circuits whose product span differs
from the start's (same A, sideways moves = split + flips + merge), rebuild their XOR network
(x1lib.materialise) and polish each with the hub kernel.

    python3 spangen.py FILE OUT_DIR [--walk 30] [--n 20] [--polish 90] [--adcap AD|0] [--seed 1] [--plus 2] [--psplit 0.05]
Every circuit is checked on all 256 inputs; results in OUT_DIR/span-*.bfx (+ .json), table on stdout."""
import json, random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import x1lib as X, x1walkc as W
from boolflux.hub import ops as HO
from boolflux.hub.common import load, metrics, sbox, core

a = sys.argv[1:]
def opt(name, d): return type(d)(a[a.index(name) + 1]) if name in a else d
f = a[0]; out = Path(a[1]); out.mkdir(parents=True, exist_ok=True)
walk = opt('--walk', 30.0); n = opt('--n', 20); pol = opt('--polish', 90.0); seed = opt('--seed', 1)
c = load(f); m0 = metrics(c); adcap = opt('--adcap', m0[1])
tag = 'sg'
res, log = W.run(c, out / 'w', walk, seed, opt('--plus', 2), opt('--psplit', 0.05), 5000, 0.2, tag, adcap, n)
print(Path(f).name, m0, 'adcap', adcap); print(log.strip().splitlines()[-2:], flush=True)
rows = []
for k, pf in enumerate(sorted((out / 'w').glob('%s-s%d.span*.prog' % (tag, seed)))):
    A = int(pf.name.split('.A')[1].split('.')[0])
    q = W.read_prog(pf, c.n, c.m)
    if not X.check(q, W.TARGET): print('wrong program', pf); continue
    lv = q.and_levels(); prof = {}
    for b, l in lv.items(): prof[l] = prof.get(l, 0) + 1
    profile = '|'.join(str(prof[l]) for l in sorted(prof))
    nc = X.materialise(q, random.Random(seed + k))
    if tuple(nc.value_table()) != sbox(): print('wrong circuit', pf); continue
    m1 = metrics(nc)
    sd = out / ('pol%03d' % k); sd.mkdir(exist_ok=True)
    cs, info = HO._kernel(nc, {'A': m1[0], 'AD': m1[1], 'GD': None}, HO.DEFAULT_OBJECTIVE, seed + k, pol, sd, out)
    best = nc
    for pc in cs:
        if tuple(pc.value_table()) == sbox(): best = pc
    m2 = metrics(best)
    name = 'span-a%d-ad%d-g%d-gd%d-%03d' % (m2 + (k,))
    (out / (name + '.bfx')).write_text(core.to_kernel(best))
    (out / (name + '.json')).write_text(json.dumps({'method': 'x1 spangen: bfw sideways walk (new product span) + materialise + kernel polish %.0f s' % pol,
        'source': f, 'source_metrics': m0, 'seed': seed, 'and_levels': profile, 'rebuilt': m1, 'metrics': m2,
        'time': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}))
    rows.append((m2, profile))
    print('span %3d levels %-14s rebuilt %s -> polished %s' % (k, profile, m1, m2), flush=True)
print('DONE', len(rows), 'spans; best by G:', sorted(rows)[:5])
