"""P4: generic anatomy of a 9 + 5 + 18 tower circuit: level-1 ANDs, pre-inversion targets
(signals over x + level-1 products read by gates outside the pre layer), their product and x parts,
rank, transposition bound on the product part, the current pre / top sizes.

    python3 anat2.py CIRC
"""
import json
import sys

import circ
import prereach
import preinj


def anatomy(path):
    g = circ.read(path)
    s = circ.symbolic(g)
    xs = {f'x{i}' for i in range(8)}
    lvl1 = [o for op, o, ins in g if op == 'AND' and all(s[i][0] <= xs for i in ins)]
    allowed = xs | set(lvl1)
    top = [o for op, o, ins in g if op != 'AND' and s[o][0] <= xs]
    pre = [o for op, o, ins in g if op != 'AND' and s[o][0] <= allowed and not s[o][0] <= xs]
    preset = set(pre)
    readers = {}
    for op, o, ins in g:
        for i in ins:
            readers.setdefault(i, set()).add(o)
    tg = [o for o in pre if readers.get(o, set()) - preset]
    # level-1 products read directly by the inversion also count as targets (no gate needed)
    direct = [a for a in lvl1 if any(r not in preset and r not in lvl1 for r in readers.get(a, set()))]
    xm = lambda at: sum(1 << int(t[1:]) for t in at if t[0] == 'x')
    am = lambda at: sum(1 << lvl1.index(t) for t in at if t in lvl1)
    X = [xm(s[t][0]) for t in tg]
    P = [am(s[t][0]) for t in tg]
    cols = [sum(1 << j for j in range(len(tg)) if (P[j] >> i) & 1) for i in range(len(lvl1))]
    return dict(file=path, metrics=circ.metrics(g), lvl1=lvl1, top=len(top), pre=len(pre), targets=tg,
                direct_products=direct, rankX=preinj.rank(X), rankP=preinj.rank(P),
                X=[circ.fmt((frozenset(f'x{i}' for i in range(8) if v >> i & 1), 0)) for v in X],
                P=[[lvl1[i] for i in range(len(lvl1)) if p >> i & 1] for p in P], cols=cols,
                distinct_cols=len(set(cols)), zero_cols=cols.count(0))


if __name__ == '__main__':
    print(json.dumps(anatomy(sys.argv[1]), indent=1))
