#!/usr/bin/env python3
"""Bottom transplant: keep a base circuit's front and inversion (e.g. NIST 116), take
the AND-level-4 products and output XORs of a donor (e.g. NIST 141@GD12, whose bottom is one
level shallower).  Donor signals feeding its bottom are mapped to base signals of equal function;
missing y-combinations are built as XORs of base y signals; missing top-layer forms (linear in
the inputs) as XOR trees of base signals found by table lookup, else the donor's cone is copied.

    python3 botsplice.py BASE DONOR OUT.circ.txt
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3])); sys.path.insert(0, str(HERE))
from boolflux import aesfn, core   # noqa: E402
from depth import analyse   # noqa: E402


ONES = (1 << 256) - 1


def build(base, donor):
    n = base.n
    gates = list(base.gates)
    tabs = base.tables(); lv = [0] * n
    for op, a, b in gates: lv.append(1 + max(lv[a], lv[b]))
    fmap = {}
    for s, t in enumerate(tabs):
        if t not in fmap or lv[s] < lv[fmap[t]]: fmap[t] = s
    def add(op, a, b):
        t = core.op_apply(op, tabs[a], tabs[b], ONES); l = 1 + max(lv[a], lv[b])
        h = fmap.get(t)
        if h is not None and lv[h] <= l: return h
        gates.append((op, a, b)); tabs.append(t); lv.append(l); s = n + len(gates) - 1
        if h is None or l < lv[h]: fmap[t] = s
        return s
    def xor_build(t):
        """t as XOR of two existing signals (min level), else of three."""
        best = None
        for s in list(fmap.values()):
            o = fmap.get(t ^ tabs[s])
            if o is not None and o != s:
                k = max(lv[s], lv[o])
                if best is None or k < best[0]: best = (k, s, o)
        if best: return add(6, best[1], best[2])
        o = fmap.get(t ^ ONES)
        if o is not None: return add(3, o, o)
        return None
    # donor structure
    dlv, dal, _, _, _, dreg, _ = analyse(donor, 99)
    dt = donor.tables()
    mp = {i: i for i in range(n)}
    def get(s):
        if s in mp: return mp[s]
        t = dt[s]
        if dal[s] < 4:
            if t in fmap: mp[s] = fmap[t]; return mp[s]
            x = xor_build(t)
            if x is not None: mp[s] = x; return x
        op, a, b = donor.gates[s - n]
        mp[s] = add(op, get(a), get(b)); return mp[s]
    sys.setrecursionlimit(10000)
    # build the donor's bottom (AND level 4 and linear after it)
    outs = [get(o) for o in donor.outputs]
    c = core.Circuit(n, donor.m, gates, outs, 'botsplice', base.in_names, base.out_names).live()
    return c


if __name__ == '__main__':
    base = core.read_ncff(sys.argv[1]); donor = core.read_ncff(sys.argv[2])
    c = build(base, donor)
    m = c.metrics(); ok = tuple(c.value_table()) == aesfn.table()
    print('G=%d A=%d GD=%d AD=%d ok=%s' % (m['G'], m['A'], m['GD'], m['AD'], ok))
    if ok and len(sys.argv) > 3:
        Path(sys.argv[3]).write_text(core.write_ncff(c, core.Model.load(str(core.MODELS / 'nist.json'))))
