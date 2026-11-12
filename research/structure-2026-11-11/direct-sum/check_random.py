"""Random-sample test of the ledger identities and of the Omega lemma.

Not a search: circuits are drawn at random (biased towards mixing two sides) and the
identities, which are proved in the report for every circuit, are checked on each.
"""
import random
from ledger import ledger, check_identities


def random_circuit(rng, nX, nY, G, pmix):
    n = nX + nY
    gates = []
    for k in range(G):
        m = n + k
        i = rng.randrange(m)
        j = rng.randrange(m)
        while j == i:
            j = rng.randrange(m)
        gates.append((i, j))
    return gates


def main():
    rng = random.Random(20261111)
    trials = 20000
    bad = [0, 0, 0, 0]
    maxd_minus_w = -10**9
    stats = []
    for t in range(trials):
        nX = rng.randint(2, 6)
        nY = rng.randint(2, 6)
        G = rng.randint(3, 30)
        gates = random_circuit(rng, nX, nY, G, 0.5)
        L = ledger(nX, nY, gates)
        o1, o2, o3 = check_identities(L)
        bad[0] += not o1
        bad[1] += not o2
        bad[2] += not o3
        bad[3] += not L["lemma_ok"]
        # savings never exceed floating components minus cycles: d - w = c - 2 - beta
        assert L["d"] - L["w"] == L["c"] - 2 - L["beta"]
        assert L["c"] - 2 <= L["floating"]
        maxd_minus_w = max(maxd_minus_w, L["d"] - L["w"])
        stats.append(L["d"])
    print("trials", trials)
    print("violations: G-identity %d, Euler %d, d-bound %d, span-lemma %d" % tuple(bad))
    print("max (d - w) seen:", maxd_minus_w, " max d seen:", max(stats))


if __name__ == "__main__":
    main()
