#!/usr/bin/env python3
"""Critical-path / slack analysis of AES S-box circuits (low gate depth).

    python3 depth.py FILE [FILE ...] [--cap D]

For each circuit: gate level of every signal, required level for a GD cap D (default: GD-1),
the gates that are too deep for D (level > required), where they sit (top linear layer = linear
gates with no AND in their fan-in; AND gates by AND level; linear gates after AND level k), and
the per-output critical path written as the sequence of regions it crosses.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
from boolflux import core   # noqa: E402

AND = 8


def analyse(c, cap=None):
    n = c.n; S = n + len(c.gates)
    lv = [0] * S; al = [0] * S; fo = [[] for _ in range(S)]
    for j, (op, a, b) in enumerate(c.gates):
        s = n + j
        lv[s] = 1 + max(lv[a], lv[b])
        al[s] = (1 if op == AND else 0) + max(al[a], al[b])
        fo[a].append(s)
        if b != a: fo[b].append(s)
    GD = max(lv[o] for o in c.outputs)
    D = GD - 1 if cap is None else cap
    req = [10 ** 9] * S
    for o in c.outputs: req[o] = min(req[o], D)
    for s in range(S - 1, n - 1, -1):
        op, a, b = c.gates[s - n]
        for x in (a, b):
            req[x] = min(req[x], req[s] - 1)
    def region(s):
        if s < n: return 'in'
        op = c.gates[s - n][0]
        if op == AND: return 'A%d' % al[s]
        return 'L%d' % al[s]          # linear gate after AND level al (L0 = top layer)
    return lv, al, req, GD, D, region, fo


def crit_path(c, lv, o):
    n = c.n; path = [o]; s = o
    while s >= n:
        op, a, b = c.gates[s - n]
        s = a if lv[a] >= lv[b] else b
        path.append(s)
    return path[::-1]


def report(path, cap=None):
    c = core.read_ncff(str(path))
    m = c.metrics()
    lv, al, req, GD, D, region, fo = analyse(c, cap)
    n = c.n
    print('=' * 100)
    print('%s  G=%d A=%d GD=%d AD=%d  (analysis for cap %d)' % (Path(path).name, m['G'], m['A'], GD, m['AD'], D))
    # region profile: count and level range
    prof = {}
    for s in range(n, n + len(c.gates)):
        r = region(s); p = prof.setdefault(r, [0, 99, 0]); p[0] += 1; p[1] = min(p[1], lv[s]); p[2] = max(p[2], lv[s])
    print('regions (count, min level, max level):', ' '.join('%s:%d[%d-%d]' % (k, *v) for k, v in sorted(prof.items(), key=lambda kv: (kv[0][1:], kv[0][0]))))
    # AND levels: operand levels
    for k in range(1, m['AD'] + 1):
        ands = [s for s in range(n, n + len(c.gates)) if c.gates[s - n][0] == AND and al[s] == k]
        ls = sorted(lv[s] for s in ands)
        print('  AND level %d: %d ANDs at gate levels %s' % (k, len(ands), ls))
    bad = [s for s in range(n, n + len(c.gates)) if lv[s] > req[s]]
    print('too deep for cap %d: %d gates; by region: %s' % (D, len(bad), sorted({region(s): sum(1 for t in bad if region(t) == region(s)) for s in bad}.items())))
    # how many outputs violate
    viol = [j for j, o in enumerate(c.outputs) if lv[o] > D]
    print('outputs over cap: %s (levels %s)' % (viol, [lv[o] for o in c.outputs]))
    for j, o in enumerate(c.outputs):
        p = crit_path(c, lv, o)
        segs = []
        for s in p:
            r = region(s)
            if segs and segs[-1][0] == r: segs[-1][1] += 1
            else: segs.append([r, 1])
        print('  S%d L%d: %s' % (j, lv[o], ' '.join('%s*%d' % (r, k) for r, k in segs)))
    # slack histogram of the top-layer forms feeding ANDs of level 1
    return c


if __name__ == '__main__':
    args = sys.argv[1:]; cap = None
    if '--cap' in args:
        i = args.index('--cap'); cap = int(args[i + 1]); del args[i:i + 2]
    for f in args: report(f, cap)
