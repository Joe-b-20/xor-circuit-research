"""Independent SAT check of the three-term sheet (Theorem 9.1) and of the 8-input local lemma.

usage: python3 sat91.py MODEL G [--sym] [--enum N]
  MODEL = lemma  (blocks a (free), b; targets [b:E_c]+[a:s_c])
        = three  (blocks a, k (pure vectors free), b; targets [b:E_c]+[a:s_c]+[k:s_c])
Bits: a = 0..3, k = 4..7, b = 8..11 (lemma: a = 0..3, b = 8..11, k unused).
Operands: a free vector on a (any, incl. 0), a free vector on k, a unit of b, or an earlier gate.
WLOG constraints (all valid): gate values pairwise distinct, not free, not a unit of b, not 0;
operand option indices strictly increasing. --sym adds the canonical-order break: if gate i+1 does
not read gate i then value(i) < value(i+1) (as integers).
"""
import sys
from itertools import combinations
from pysat.solvers import Solver
from pysat.card import CardEnc, EncType


class Enc:
    def __init__(self):
        self.n = 0
        self.cl = []

    def var(self):
        self.n += 1
        return self.n


def build(model, G, sym=False):
    e = Enc()
    NB = 12
    A = list(range(0, 4))
    K = list(range(4, 8)) if model == "three" else []
    Bb = list(range(8, 12))
    used = A + K + Bb
    E = [15 ^ (1 << c) for c in range(4)]
    s = [(1 << c) | (1 << ((c + 1) % 4)) for c in range(4)]
    T = []
    for c in range(4):
        t = (E[c] << 8) | s[c]
        if model == "three":
            t |= s[c] << 4
        T.append(t)
    v = [[e.var() for _ in range(NB)] for _ in range(G)]
    opts_base = ["FA"] + (["FK"] if model == "three" else []) + ["U%d" % l for l in range(4)]
    selv = []
    for i in range(G):
        opts = opts_base + ["G%d" % j for j in range(i)]
        sel = [[e.var() for _ in opts] for _ in range(2)]
        f = [[e.var() for _ in range(4)] for _ in range(2)]
        w = [[e.var() for _ in range(NB)] for _ in range(2)]
        for p in range(2):
            cnf = CardEnc.equals(lits=sel[p], bound=1, top_id=e.n, encoding=EncType.seqcounter)
            e.n = max(e.n, cnf.nv)
            e.cl += cnf.clauses
            for oi, o in enumerate(opts):
                x = sel[p][oi]
                for bit in used:
                    if o == "FA":
                        if bit in A:
                            e.cl += [[-x, -w[p][bit], f[p][bit]], [-x, w[p][bit], -f[p][bit]]]
                        else:
                            e.cl.append([-x, -w[p][bit]])
                    elif o == "FK":
                        if bit in K:
                            e.cl += [[-x, -w[p][bit], f[p][bit - 4]], [-x, w[p][bit], -f[p][bit - 4]]]
                        else:
                            e.cl.append([-x, -w[p][bit]])
                    elif o[0] == "U":
                        l = int(o[1:])
                        e.cl.append([-x, w[p][bit]] if bit == 8 + l else [-x, -w[p][bit]])
                    else:
                        j = int(o[1:])
                        e.cl += [[-x, -w[p][bit], v[j][bit]], [-x, w[p][bit], -v[j][bit]]]
        # strictly increasing option index: forbid sel0 = oi, sel1 = oj with oj <= oi
        for oi in range(len(opts)):
            for oj in range(oi + 1):
                e.cl.append([-sel[0][oi], -sel[1][oj]])
        for bit in range(NB):
            if bit not in used:
                e.cl.append([-v[i][bit]])
                continue
            a_, b_, c_ = w[0][bit], w[1][bit], v[i][bit]
            e.cl += [[-a_, -b_, -c_], [a_, b_, -c_], [a_, -b_, c_], [-a_, b_, c_]]
        selv.append((opts, sel))
        # not free: nonzero on b, or (nonzero on a and nonzero on k)
        if model == "three":
            za, zk = e.var(), e.var()   # za -> some a bit set ; zk -> some k bit
            e.cl.append([-za] + [v[i][b] for b in A])
            e.cl.append([-zk] + [v[i][b] for b in K])
            m = e.var()
            e.cl += [[-m, za], [-m, zk]]
            e.cl.append([m] + [v[i][b] for b in Bb])
        else:
            e.cl.append([v[i][b] for b in Bb])
        # not a unit of b with zero elsewhere (units are inputs): value != unit
        for l in range(4):
            u = 1 << (8 + l)
            e.cl.append([(-v[i][b] if (u >> b) & 1 else v[i][b]) for b in used])
    # distinct values
    for i, j in combinations(range(G), 2):
        d = []
        for b in used:
            x = e.var()
            e.cl += [[-x, v[i][b], v[j][b]], [-x, -v[i][b], -v[j][b]]]
            d.append(x)
        e.cl.append(d)
    # targets
    for t in T:
        eqs = []
        for i in range(G):
            x = e.var()
            for b in used:
                e.cl.append([-x, v[i][b] if (t >> b) & 1 else -v[i][b]])
            eqs.append(x)
        e.cl.append(eqs)
    if sym:
        for i in range(G - 1):
            opts, sel = selv[i + 1]
            gi = opts.index("G%d" % i)
            reads = [sel[0][gi], sel[1][gi]]
            # if not reads: val(i) < val(i+1), lexicographic from top bit
            bits = sorted(used, reverse=True)
            # eq prefix chain
            prev_eq = None
            lt_terms = []
            for b in bits:
                x, y = v[i][b], v[i + 1][b]
                lt = e.var()   # lt -> prefix equal and x=0,y=1
                e.cl += [[-lt, -x], [-lt, y]]
                if prev_eq is not None:
                    e.cl.append([-lt, prev_eq])
                lt_terms.append(lt)
                eq = e.var()  # eq -> prefix equal including b
                e.cl += [[-eq, -x, y], [-eq, x, -y]]
                if prev_eq is not None:
                    e.cl.append([-eq, prev_eq])
                prev_eq = eq
            e.cl.append(reads + lt_terms)
    return e, v, selv, T


def decode(model, G, sol, v, selv):
    S = set(l for l in sol if l > 0)
    vals = [sum(1 << b for b in range(12) if v[i][b] in S) for i in range(G)]
    return vals


def main():
    model, G = sys.argv[1], int(sys.argv[2])
    sym = "--sym" in sys.argv
    nenum = int(sys.argv[sys.argv.index("--enum") + 1]) if "--enum" in sys.argv else 0
    e, v, selv, T = build(model, G, sym)
    with Solver(name="cadical153", bootstrap_with=e.cl) as s:
        r = s.solve()
        print(model, G, "sym" if sym else "nosym", "SAT" if r else "UNSAT", flush=True)
        if r:
            vals = decode(model, G, s.get_model(), v, selv)
            print("values:", [hex(x) for x in vals])
    if nenum:
        import json
        out = []
        with Solver(name="cadical153", bootstrap_with=e.cl) as s:
            while len(out) < nenum and s.solve():
                m = s.get_model()
                S = set(l for l in m if l > 0)
                vals = decode(model, G, m, v, selv)
                ops = []
                for i, (opts, sel) in enumerate(selv):
                    pr = []
                    for p in range(2):
                        oi = [k for k in range(len(opts)) if sel[p][k] in S][0]
                        pr.append(opts[oi])
                    ops.append(pr)
                # need actual free operand values: recompute as value xor other operand
                out.append({"vals": vals, "ops": ops})
                # block this wiring (selectors)
                blk = []
                for opts, sel in selv:
                    for p in range(2):
                        for k in range(len(opts)):
                            if sel[p][k] in S:
                                blk.append(-sel[p][k])
                s.add_clause(blk)
        json.dump(out, open("enum_%s_%d.json" % (model, G), "w"))
        print("enumerated", len(out))


if __name__ == "__main__":
    main()
