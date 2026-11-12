"""CHECK: the block-2-cancelling gate of a circuit, its operands, and its readers (recursively, 2 levels).
usage: python3 exituse.py FILE LINE"""
import sys
from show_tri import load, circuit, desc, classes, mc
fn, ln = sys.argv[1], int(sys.argv[2]); g = load(fn, ln); vals, anc, outn = circuit(g); cl = classes(g, vals, 2)
rd = {}
for i, (a, b) in enumerate(g):
    rd.setdefault(a, []).append(32 + i); rd.setdefault(b, []).append(32 + i)
S = lambda w: "%s[%s]%s s%s" % ("g%d" % w if w >= 32 else "x%d" % w, desc(vals[w]), outn.get(w, ""), "".join(map(str, sorted(anc.get(w, ())))))
for w, c in cl.items():
    if c != "EXIT": continue
    a, b = g[w - 32]
    print("EXIT", S(w), "=", S(a), "+", S(b))
    for x in (a, b):
        if x >= 32: print("  operand", S(x), "=", S(g[x-32][0]), "+", S(g[x-32][1]))
    for r1 in rd.get(w, []):
        o = [y for y in g[r1 - 32] if y != w]
        print("  reader", S(r1), "other operand", S(o[0]) if o else "self")
        for r2 in rd.get(r1, []):
            print("    reader", S(r2))
