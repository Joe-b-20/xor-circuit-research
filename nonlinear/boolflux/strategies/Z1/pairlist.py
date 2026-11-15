#!/usr/bin/env python3
"""List parallel (equal-usage) last-layer pairs and the AND-span key of circuits (.circ.txt/.bfx),
to pick distinct full-operand pair windows for r1enum.  key = hash of span(1, x, all AND tables)
(two circuits with the same key have the same product span; a pair window then has the same
W and target up to which AND is dropped).  usage: pairlist.py FILE...  -> json lines"""
import sys, os, json, hashlib, tempfile
sys.path.insert(0, os.path.expanduser('~/xcr-boolflux/nonlinear'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from boolflux import core
import staircode as SC

model = core.Model.load('nist')


def key(vs):
    rows = {}
    for v in vs:
        while v:
            h = v.bit_length() - 1
            if h in rows: v ^= rows[h]
            else: rows[h] = v; break
    for h in sorted(rows):
        for k in rows:
            if k != h and (rows[k] >> h) & 1: rows[k] ^= rows[h]
    return hashlib.sha1(','.join('%x' % rows[h] for h in sorted(rows)).encode()).hexdigest()[:12]


for f in sys.argv[1:]:
    tmp = None
    try:
        path = f
        if f.endswith('.bfx'):
            c = core.from_kernel(open(f).read())
            tmp = tempfile.NamedTemporaryFile('w', suffix='.circ.txt', delete=False)
            tmp.write(core.write_ncff(c, model)); tmp.close(); path = tmp.name
        r = SC.core_and_code(path)
        d = {}
        for j, v in zip(r['Lidx'], r['cols']):
            d.setdefault(v, []).append(j)
        pairs = [g for g in d.values() if len(g) > 1]
        k = key([r['val'][o] for o, _, _ in r['ands']] + [sc for sc in [(1 << 256) - 1]] + [r['val'][n] for n in r['ins']])
        lv = r['lvl']
        per = [sum(1 for x in lv if x == L) for L in range(1, max(lv) + 1)]
        print(json.dumps(dict(file=f, A=r['A'], E=r['E'], K=len(r['Lidx']), levels=per, pairs=pairs, key=k)), flush=True)
    except Exception as e:
        print(json.dumps(dict(file=f, error=repr(e)[:120])), flush=True)
    finally:
        if tmp is not None: os.unlink(tmp.name)
