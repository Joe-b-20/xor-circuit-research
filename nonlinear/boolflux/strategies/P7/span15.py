"""P7: for all 15 non-zero combinations of the four N-coordinates of NIST 59@10 (a conjugation-invariant
span), count Kraft-feasible GL4 decompositions (shapes 4 GL2; 3 GL2 + <= 2 GL1 monomials; 2 GL2 + <= 4 GL1;
1 GL2 + <= 6 GL1 not counted) of the quadratic part (linear part is then solved by s1pol's constants;
here only the quadratic condition, i.e. an upper bound on decomposability)."""
import itertools, sys
sys.path.insert(0, '.')
import s1lib as L, s1search
c = L.load(sys.argv[1]); fs, T, lg, la = s1search.coords(c)
qs = [L.quad(f) for f in fs]
forms = [m for m in range(1, 256) if bin(m).count('1') <= 2]
P2 = [L.wedge(l, m) for l, m in itertools.combinations(forms, 2) if L.wedge(l, m)]
W2 = {}
for i1 in range(len(P2)):
    for i2 in range(i1 + 1, len(P2)):
        W2[P2[i1] ^ P2[i2]] = W2.get(P2[i1] ^ P2[i2], 0) + 1
P1 = [L.wedge(1 << i, 1 << j) for i in range(8) for j in range(i + 1, 8)]
S2 = set(P2)
for mask in range(1, 16):
    q = 0
    for k in range(4):
        if (mask >> k) & 1: q ^= qs[k]
    n4 = sum(W2.get(q ^ P2[i1] ^ P2[i2], 0) for i1 in range(len(P2)) for i2 in range(i1 + 1, len(P2))) // 1
    n32 = 0
    for n1 in (1, 2):
        for g in itertools.combinations(range(28), n1):
            q1 = q
            for i in g: q1 ^= P1[i]
            n32 += sum(W2.get(q1 ^ p, 0) for p in P2)
    n24 = 0
    for n1 in (2, 3, 4):
        for g in itertools.combinations(range(28), n1):
            q1 = q
            for i in g: q1 ^= P1[i]
            n24 += W2.get(q1, 0)
    print('combo %2d: 4-shape %d, 3+<=2 %d, 2+<=4 %d (quadratic condition, ordered pair counts)' % (mask, n4, n32, n24), flush=True)
