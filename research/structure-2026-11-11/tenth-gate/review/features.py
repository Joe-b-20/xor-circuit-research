"""Which edge cases of Step 0 occur in the random sheet circuits of test_lemma.py (same generator and
seed), after cleaning; each such circuit also passed ml.full_check there.  usage: python3 features.py [N]"""
import random
import sys
from collections import Counter

import mirror_lib as ml
import test_lemma as tl


def features(g):
    tg = tl.sheet_targets()
    cg, gc = ml.clean(g, 4, tg)
    vals = ml.evaluate(cg, 4)
    f = Counter()
    phis = []
    for i, (a, b) in enumerate(cg):
        fr = [op for op in (a, b) if op[0] == 'F']
        if a == b:
            f["gate x+x survives"] += 1
        if len(fr) == 1:
            phis.append(fr[0][1])
            other = b if fr[0] is a else a
            if other[0] == 'U':
                f["entry with unit operand"] += 1
            if fr[0][1] == 0:
                f["entry with phi = 0"] += 1
            if i in gc:
                f["target gate is an entry gate"] += 1
    nz = [p for p in phis if p]
    if len(nz) != len(set(nz)):
        f["repeated nonzero phi"] += 1
    if 0 in vals:
        f["zero-valued gate"] += 1
    if len(set(vals)) < len(vals):
        f["two gates with equal value"] += 1
    anc = set()
    for c, g0 in enumerate(gc):
        stack, seen = [g0], set()
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            for op in cg[x]:
                if op[0] == 'G':
                    stack.append(op[1])
        if any(g1 in seen and g1 != g0 for g1 in gc):
            f["target gate is ancestor of another"] += 1
    C, zphi, N = ml.build_C(cg, 4)
    fm = ml.formal_masks(C, N)
    l = [fm[N + x] >> 4 for x in gc]
    zeta = [sum(((l[c] >> i) & 1) << c for c in range(4)) for i in range(len(zphi))]
    if 0 in zeta:
        f["some zeta = 0"] += 1
    if len(set(zeta)) < len(zeta):
        f["repeated zeta"] += 1
    return {k: 1 for k in f}


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 600
    rng = random.Random(99)
    pool = [rng.randrange(16) for _ in range(3)]

    def fs():
        r = rng.random()
        if r < 0.2:
            return 0
        if r < 0.5:
            return rng.choice(pool)
        return rng.randrange(16)

    tot = Counter()
    for _ in range(n):
        g = tl.random_local(tl.sheet_targets(), 4, rng, fs, rng.randrange(0, 14))
        ml.full_check(g, 4, tl.sheet_targets(), [[0, 1, 2, 3]], rng)
        tot.update(features(g))
    print(f"{n} random sheet circuits (all passed full_check); circuits showing each edge case after cleaning:")
    for k, v in sorted(tot.items()):
        print(f"   {k}: {v}")


if __name__ == "__main__":
    main()
