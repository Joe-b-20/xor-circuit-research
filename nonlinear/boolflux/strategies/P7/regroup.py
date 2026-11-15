#!/usr/bin/env python3
"""P7: replace one N-coordinate group of a 59@10-shaped stage 1 by another decomposition.

    regroup.py CIRCUIT SUMSIG 'l,a,m,b;l,a,m,b;...' OUT.circ.txt

SUMSIG = signal computing the group sum (e.g. 79 in NIST 59@10: 1+a5+a6+a7+a8).  The new
products (l+a)(m+b) (masks over inputs, my labelling: input signal i = bit i) are built from
inputs (reusing any existing top-layer gate with the same function), summed by a balanced XOR
tree, the constant fixed by XNOR, all consumers of SUMSIG redirected, dead gates removed.
The result is checked on all 256 inputs.
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s1lib as L  # noqa: E402
core = L.core
XOR, XNOR, NOT, AND = 6, 9, 3, 8


def build(c, sumsig, prods, reuse=True):
    sums = sumsig if isinstance(sumsig, (list, tuple)) else [sumsig]
    sumsig = sums[0]
    """node graph: old signals keep their numbers; new nodes get ids 10000+k; topological emit."""
    n = c.n
    T, lg, la = L.sim(c)
    target = T[sumsig]
    nodes = {}                     # id -> (op, a, b)
    tab = {}                       # id -> table (inputs, old, new)
    for i in range(n): tab[i] = L.VAR[i]
    for j, g in enumerate(c.gates): nodes[n + j] = g; tab[n + j] = T[n + j]
    byt = {}
    if reuse:
        for j, (op, a, b) in enumerate(c.gates):
            s = n + j
            if op not in core.NONLINEAR_OPS and la[s] == 0 and lg[s] <= 1:
                byt.setdefault(T[s], s)
    for i in range(n): byt[L.VAR[i]] = i
    nid = [10000]

    def add(op, a, b):
        k = nid[0]; nid[0] += 1
        nodes[k] = (op, a, b); tab[k] = core.op_apply(op, tab[a], tab[b], L.ONES)
        return k

    def operand(mask, pol):
        t = L.lin_table(mask) ^ (L.ONES if pol else 0)
        if t in byt: return byt[t]
        vs = [i for i in range(8) if (mask >> i) & 1]
        s = add(NOT, vs[0], vs[0]) if len(vs) == 1 else add(XNOR if pol else XOR, vs[0], vs[1])
        byt[t] = s
        return s

    lv = {}
    def glev(s):
        if s < n: return 0
        if s not in lv:
            op, a, b = nodes[s]; lv[s] = 1 + max(glev(a), glev(b))
        return lv[s]
    P = [add(AND, operand(l, a), operand(m, b)) for (l, a, m, b) in prods]
    items = list(P)
    while len(items) > 1:
        items.sort(key=glev)
        a = items.pop(0); b = items.pop(0)
        items.append(add(XOR, a, b))
    top = items[0]
    if tab[top] != target:
        assert tab[top] ^ L.ONES == target, 'new group does not compute the old sum'
        op, a, b = nodes[top]; nodes[top] = (XNOR, a, b); tab[top] ^= L.ONES
    # redirect consumers of every sum signal (old gates) to top or its complement twin
    red = {sumsig: top}
    for s2 in sums[1:]:
        if T[s2] == tab[top]: red[s2] = top
        else:
            assert T[s2] == tab[top] ^ L.ONES
            op, a, b = nodes[top]
            red[s2] = add(XNOR if op == XOR else XOR, a, b)
    for s, (op, a, b) in list(nodes.items()):
        if s >= 10000: continue
        nodes[s] = (op, red.get(a, a), red.get(b, b))
    outs = [red.get(o, o) for o in c.outputs]
    # topological emit from outputs
    order = []; seen = set()
    def visit(s):
        if s < n or s in seen: return
        stack = [(s, 0)]
        while stack:
            x, st = stack.pop()
            if x < n or (st == 0 and x in seen): continue
            if st == 0:
                seen.add(x); stack.append((x, 1))
                op, a, b = nodes[x]
                for y in (b, a):
                    if y >= n and y not in seen: stack.append((y, 0))
            else:
                order.append(x)
    for o in outs: visit(o)
    idx = {i: i for i in range(n)}
    gates = []
    for s in order:
        op, a, b = nodes[s]
        idx[s] = n + len(gates); gates.append((op, idx[a], idx[b]))
    return core.Circuit(n, c.m, gates, [idx[o] for o in outs], c.name).live()


def parse(spec):
    out = []
    for item in spec.split(';'):
        l, a, m, b = [int(x, 0) for x in item.split(',')]
        out.append((l, a, m, b))
    return out


def main():
    c = L.load(sys.argv[1]); sumsig = [int(x) for x in sys.argv[2].split(',')]; prods = parse(sys.argv[3])
    nc = build(c, sumsig, prods)
    from boolflux import targets
    assert nc.value_table() == targets.aes_sbox(), 'wrong function'
    model = core.Model.load(str(core.MODELS / 'nist.json'))
    m = nc.metrics(model)
    print('A AD G GD =', m['A'], m['AD'], m['G'], m['GD'], m['counts'])
    Path(sys.argv[4]).write_text(core.write_ncff(nc, model, comments=['P7 regroup.py from %s, group %d -> %s' % (sys.argv[1], sumsig, sys.argv[3])]))


if __name__ == '__main__':
    main()
