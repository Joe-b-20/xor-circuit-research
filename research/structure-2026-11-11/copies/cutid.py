"""CHECK (phase 10, main agent): the first-exit (cut) identity of COPIES.md section 4, on specified circuits.

For a node set A containing all inputs and closed under ancestors (here: the inputs and the first t gates, for
every t), every row satisfies
    val(o_r) = sum over cut edges (p -> g), p in A, g not in A, with rho(g)_r = 1, of val(p)
               + [o_r in A] val(o_r),
where o_r is the node computing row r and rho(v)_r is the parity of the directed paths from v to o_r (the
trivial path counts when v = o_r). Direct evaluation of a stated identity; no search.
usage: python3 cutid.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ST = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ST, "compose", "compat"))
from clib import ROWS, load  # noqa: E402


def check(name, n, gates, rows):
    vals = [1 << i for i in range(n)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    N = len(vals)
    onode = {r: vals.index(v, n) for r, v in enumerate(rows)}
    rho = [0] * N
    readers = [[] for _ in range(N)]
    for gi, (a, b) in enumerate(gates):
        readers[a].append(n + gi)
        readers[b].append(n + gi)
    isout = {}
    for r, o in onode.items():
        isout[o] = isout.get(o, 0) | (1 << r)
    for v in range(N - 1, -1, -1):
        acc = isout.get(v, 0)
        for g in readers[v]:
            acc ^= rho[g]
        rho[v] = acc
    bad = 0
    for t in range(len(gates) + 1):
        inA = n + t
        acc = [0] * len(rows)
        for gi, (a, b) in enumerate(gates):
            g = n + gi
            if g < inA:
                continue
            for p in (a, b):
                if p < inA:
                    for r in range(len(rows)):
                        if rho[g] >> r & 1:
                            acc[r] ^= vals[p]
        for r, o in onode.items():
            if o < inA:
                acc[r] ^= vals[o]
        bad += sum(acc[r] != rows[r] for r in range(len(rows)))
    print("%s: identity checked at %d cuts, %d failures" % (name, len(gates) + 1, bad))


if __name__ == "__main__":
    rows = list(ROWS.values())
    for s in ("r88", os.path.join(ST, "cancel", "witness", "witness_mc_block.json")):
        g = [tuple(x) for x in json.load(open(s))] if s.endswith(".json") else load(s)
        check("MixColumns " + os.path.basename(s), 32, g, rows)
