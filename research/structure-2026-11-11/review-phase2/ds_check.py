"""Reviewer's tests of direct-sum/REPORT.md section 2 on random circuits over X + Y (block-diagonal
setting).  Random circuits, not optimal ones: this tests identities and per-circuit inequalities, never
a statement about L.  usage: python3 ds_check.py COUNT SEED"""
import random
import sys

from rp_lib import popcount, rank


def run(count, seed):
    rng = random.Random(seed)
    viol = {k: 0 for k in ["identity", "Hgraph", "lemma1", "lemma3a", "lemma3b", "span", "dbound", "thm2"]}
    maxd_ratio = 0
    tight = 0
    for it in range(count):
        nx = rng.randint(2, 6)
        ny = rng.randint(2, 6)
        G = rng.randint(3, 30)
        n = nx + ny
        xmask = (1 << nx) - 1
        sig = [1 << i for i in range(n)]
        bias = rng.random()
        for g in range(G):
            # bias towards recent signals and towards mixing
            L = len(sig)
            a = rng.randrange(L) if rng.random() < 0.5 else rng.randrange(max(0, L - 6), L)
            b = rng.randrange(L)
            if a == b:
                b = (b + 1) % L
            sig.append(sig[a] ^ sig[b])
            sig_ops = None
        # rebuild with operand records
        rng2 = random.Random(seed * 100003 + it)
        sig = [1 << i for i in range(n)]
        ops = []
        for g in range(G):
            L = len(sig)
            a = rng2.randrange(L) if rng2.random() < 0.5 else rng2.randrange(max(0, L - 6), L)
            b = rng2.randrange(L)
            if a == b:
                b = (b + 1) % L
            ops.append((a, b))
            sig.append(sig[a] ^ sig[b])
        X = lambda v: v & xmask
        Y = lambda v: v >> nx
        seenX = {0} | {1 << i for i in range(nx)}
        seenY = {0} | {1 << i for i in range(ny)}
        xnew, ynew = [], []
        NX = NY = d = w = 0
        # span lemma state
        Vbasis = []
        omega_mix = 0
        first_mixed_done = False
        d_Yparts = []
        for g in range(G):
            v = sig[n + g]
            a, b = ops[g]
            xn = X(v) not in seenX
            yn = Y(v) not in seenY
            # Lemma 1: an X-new gate's X-part is a sum of two values among units and earlier X-new X-parts
            if xn:
                okops = all(X(sig[o]) in ({1 << i for i in range(nx)} | set(xnew)) and X(sig[o]) != 0 for o in (a, b))
                if not okops:
                    viol["lemma1"] += 1
            mixed = X(v) != 0 and Y(v) != 0
            if xn and yn:
                d += 1
                # Lemma 3a
                ma = X(sig[a]) and Y(sig[a])
                mb = X(sig[b]) and Y(sig[b])
                if not (ma and mb and X(sig[a]) != X(sig[b]) and Y(sig[a]) != Y(sig[b])):
                    viol["lemma3a"] += 1
            if not xn and not yn:
                w += 1
            if mixed and not first_mixed_done:
                first_mixed_done = True
                pa = (X(sig[a]) and not Y(sig[a]) and Y(sig[b]) and not X(sig[b])) or \
                     (X(sig[b]) and not Y(sig[b]) and Y(sig[a]) and not X(sig[a]))
                if not (pa and not xn and not yn):
                    viol["lemma3b"] += 1
            if mixed and not xn:
                omega_mix += 1
                Vbasis.append(Y(v))
            if mixed:
                # span lemma: Y-part in span of Omega_mix Y-parts so far
                if rank(Vbasis + [Y(v)]) != rank(Vbasis):
                    viol["span"] += 1
            if xn and yn:
                d_Yparts.append(Y(v))
            if xn:
                NX += 1
                xnew.append(X(v))
            if yn:
                NY += 1
            seenX.add(X(v))
            seenY.add(Y(v))
        if G != NX + NY - d + w:
            viol["identity"] += 1
        # H-graph form
        Xv = {}
        Yv = {}
        edges = []
        for v in sig:
            xv = Xv.setdefault(X(v), len(Xv))
            yv = Yv.setdefault(Y(v), len(Yv))
            edges.append((xv, yv))
        if 0 not in Xv or 0 not in Yv:
            pass
        V = len(Xv) + len(Yv)
        parent = list(range(V))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for xv, yv in edges:
            ra, rb = find(xv), find(len(Xv) + yv)
            if ra != rb:
                parent[ra] = rb
        c = len({find(i) for i in range(V)})
        beta = len(edges) - V + c
        if G != NX + NY - (c - 2) + beta:
            viol["Hgraph"] += 1
        r = rank(Vbasis)
        if d > 2 ** r - r - 1:
            viol["dbound"] += 1
        if r >= 1 and d == 2 ** r - r - 1 and d > 0:
            tight += 1
        # Theorem 2 (per circuit form): #non-X-new >= n_B - c_B for B = Y-parts of weight >= 2 of pure-Y signals
        rows = {Y(v) for v in sig if X(v) == 0 and popcount(Y(v)) >= 2}
        if rows:
            coords = 0
            for rr in rows:
                coords |= rr
            nB = popcount(coords)
            par = {i: i for i in range(ny)}

            def f2(x):
                while par[x] != x:
                    x = par[x]
                return x

            for rr in rows:
                bits = [i for i in range(ny) if (rr >> i) & 1]
                for bb in bits[1:]:
                    ra, rb = f2(bits[0]), f2(bb)
                    if ra != rb:
                        par[ra] = rb
            cB = len({f2(i) for i in range(ny) if (coords >> i) & 1})
            if G - NX < nB - cB:
                viol["thm2"] += 1
    print(f"{count} random circuits (seed {seed}): violations {viol}; circuits attaining d = 2^r - r - 1 > 0: {tight}")


if __name__ == "__main__":
    run(int(sys.argv[1]), int(sys.argv[2]))
