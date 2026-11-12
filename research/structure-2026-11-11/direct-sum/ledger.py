"""Ledger of a XOR circuit for a direct sum A (+) B.

Standard library only; searches nothing.  A circuit on nX + nY inputs is a list of
gates (i, j): signal indices 0..n-1 are the inputs (X first, then Y), index n + k is gate k.
Masks are Python ints: bit i (i < nX) is x_i, bit nX + j is y_j.

For each gate we record whether its X-part is new (not among {0, X-units, earlier X-parts})
and whether its Y-part is new.  d = new in both, w = new in neither.

Identities checked by the callers:
  G = N_X + N_Y - d + w
  G = N_X + N_Y - (c - 2) + beta     (bipartite graph H of X-parts and Y-parts)
Lemma checked by the callers (proved in the report):
  every mixed signal has its Y-part in the span of the Y-parts of the mixed gates that are
  not X-new, taken up to that time; hence d <= 2^r - r - 1, r = rank of that span.
"""


def basis_add(basis, v):
    """Insert v into a GF(2) basis (dict pivot->vector). Return True if rank grew."""
    while v:
        p = v.bit_length() - 1
        if p in basis:
            v ^= basis[p]
        else:
            basis[p] = v
            return True
    return False


def in_span(basis, v):
    while v:
        p = v.bit_length() - 1
        if p in basis:
            v ^= basis[p]
        else:
            return False
    return True


class UF:
    def __init__(self):
        self.p = {}
        self.ncomp = 0

    def add(self, x):
        if x not in self.p:
            self.p[x] = x
            self.ncomp += 1

    def find(self, x):
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb
            self.ncomp -= 1
            return True
        return False


def masks(n, gates):
    sig = [1 << i for i in range(n)]
    for (i, j) in gates:
        sig.append(sig[i] ^ sig[j])
    return sig


def ledger(nX, nY, gates):
    n = nX + nY
    mX = (1 << nX) - 1
    sig = masks(n, gates)
    seenX = {0} | {1 << i for i in range(nX)}
    seenY = {0} | {1 << j for j in range(nY)}
    uf = UF()
    for v in seenX:
        uf.add(("X", v))
    for v in seenY:
        uf.add(("Y", v))
    E = 0
    for i in range(nX):
        uf.union(("X", 1 << i), ("Y", 0))
        E += 1
    for j in range(nY):
        uf.union(("X", 0), ("Y", 1 << j))
        E += 1
    cls = []          # per gate: 'XY' (d), 'X', 'Y', '-' (w)
    mixed = []
    # Omega-lemma bookkeeping, both orientations
    basY, basX = {}, {}
    lemma_ok = True
    rY = rX = 0
    for k, (i, j) in enumerate(gates):
        v = sig[n + k]
        vx, vy = v & mX, v >> nX
        xn, yn = vx not in seenX, vy not in seenY
        mix = vx != 0 and vy != 0
        mixed.append(mix)
        c = ("X" if xn else "") + ("Y" if yn else "")
        cls.append(c if c else "-")
        if mix and not xn:
            if basis_add(basY, vy):
                rY += 1
        if mix and not yn:
            if basis_add(basX, vx):
                rX += 1
        if mix and not in_span(basY, vy):
            lemma_ok = False
        if mix and not in_span(basX, vx):
            lemma_ok = False
        seenX.add(vx)
        seenY.add(vy)
        uf.add(("X", vx))
        uf.add(("Y", vy))
        uf.union(("X", vx), ("Y", vy))
        E += 1
    V = len(uf.p)
    c = uf.ncomp
    beta = E - V + c
    G = len(gates)
    NX = sum(1 for t in cls if "X" in t)
    NY = sum(1 for t in cls if "Y" in t)
    d = cls.count("XY")
    w = cls.count("-")
    # floating components: containing neither ("X",0) nor ("Y",0)
    roots0 = {uf.find(("X", 0)), uf.find(("Y", 0))}
    comps = {uf.find(x) for x in uf.p}
    floating = len(comps - roots0)
    return dict(G=G, NX=NX, NY=NY, d=d, w=w, c=c, beta=beta, floating=floating,
                merged0=(len(roots0) == 1), rY=rY, rX=rX, lemma_ok=lemma_ok,
                cls=cls, mixed=mixed, sig=sig)


def check_identities(L):
    ok1 = L["G"] == L["NX"] + L["NY"] - L["d"] + L["w"]
    ok2 = L["G"] == L["NX"] + L["NY"] - (L["c"] - 2) + L["beta"]
    r = min(L["rY"], L["rX"])
    ok3 = L["d"] <= (2 ** r - r - 1 if r >= 1 else 0)
    return ok1, ok2, ok3
