"""Independent review code for cancel/CANCEL.md (does not import the authors' scripts).

Read-only evaluation of given circuits: values, block supports, charge families F_j,
E, R, U, Lemma-W slack c, exits, and the off-path operands of exits lying on paths from
double-charged gates to the sheets whose window misses a block of the gate.
"""
import ast, sys, os

# ---------------- MixColumns (own derivation) ----------------
def xt(b):
    b <<= 1
    return b ^ 0x11b if b & 0x100 else b

def gmul(a, x):
    return a if x == 1 else (xt(a) if x == 2 else xt(a) ^ a)

E = [15 ^ (1 << c) for c in range(4)]
S = [(1 << c) | (1 << ((c + 1) % 4)) for c in range(4)]

class MC:
    name = 'MixColumns'
    nb = 8
    n = 32
    def __init__(self):
        coef = [2, 3, 1, 1]          # out_i = 2a_i + 3a_{i+1} + a_{i+2} + a_{i+3}
        self.out = {}
        for i in range(4):
            for j in range(8):
                mask = 0
                for c in range(4):
                    for jj in range(8):
                        if gmul(1 << jj, coef[(c - i) % 4]) >> j & 1:
                            mask |= 1 << (8 * c + jj)
                self.out[8 * i + j] = mask
        self.bmask = [sum(1 << (8 * c + b) for c in range(4)) for b in range(8)]
        # sheet j = output wires 8c + j (bit j of every output byte)
        self.rows = {j: [self.out[8 * c + j] for c in range(4)] for j in range(8)}
        self.proj = {j: {(j - 1) % 8, j} for j in range(8)}
    def part(self, v, b):
        return sum(((v >> (8 * c + b)) & 1) << c for c in range(4))

class Q:
    def __init__(self, m):
        self.m = m; self.nb = m; self.n = 4 * m; self.name = 'Q_%d' % m
        self.bmask = [15 << (4 * b) for b in range(m)]
        self.rows = {j: [(E[c] << (4 * j)) | (S[c] << (4 * ((j - 1) % m))) for c in range(4)]
                     for j in range(m)}
        self.proj = {j: {(j - 1) % m, j} for j in range(m)}
    def part(self, v, b):
        return (v >> (4 * b)) & 15

def sup(M, v):
    return sum(1 << b for b in range(M.nb) if v & M.bmask[b])

def blocks(x):
    return [b for b in range(16) if x >> b & 1]

# ---------------- analysis ----------------
def analyse(M, gates, detail=False):
    n = M.n
    val = [1 << i for i in range(n)]
    for a, b in gates:
        val.append(val[a] ^ val[b])
    N = len(val)
    sp = [sup(M, v) for v in val]
    W = {j: sup(M, M.rows[j][0]) for j in M.rows}
    for j in M.rows:
        assert all(sup(M, r) == W[j] for r in M.rows[j]), 'rows of a sheet differ in support'
        assert W[j] >> j & 1
    rowsheet = {}
    for j in M.rows:
        for r in M.rows[j]:
            rowsheet[r] = j
    vset = set(val[n:])
    ok = all(r in vset for r in rowsheet)
    anc = [1 << s for s in range(N)]
    for t, (a, b) in enumerate(gates):
        anc[n + t] |= anc[a] | anc[b]
    A = {}
    nrowgates = 0
    for j in M.rows:
        x = 0
        for s in range(n, N):
            if rowsheet.get(val[s]) == j:
                x |= anc[s]; nrowgates += 1
        A[j] = x
    F = {j: [s for s in range(n, N) if A[j] >> s & 1 and sp[s] >> j & 1] for j in M.rows}
    mult = [0] * N
    for j in F:
        for s in F[j]:
            mult[s] += 1
    s_ = len(M.rows)
    Eex = sum(len(F[j]) - 10 for j in F)
    R = sum(max(mult[s] - 1, 0) for s in range(n, N))
    U = sum(1 for s in range(n, N) if mult[s] == 0)
    G = len(gates)
    union = sum(1 for s in range(n, N) if mult[s] >= 1)
    assert union == 10 * s_ + Eex - R and G == union + U
    # Lemma W
    units = set(1 << i for i in range(n))
    cj = {}
    for j in F:
        pm = sum(M.bmask[b] for b in M.proj[j])
        d = set(val[s] & pm for s in F[j]) - units
        assert all(v & M.bmask[j] for v in d)
        cj[j] = len(F[j]) - len(d)
        assert len(d) >= 10 or not ok, ('Lemma W violated', j, len(d))
    c = sum(cj.values())
    # exits
    isexit = {}
    for t, (a, b) in enumerate(gates):
        e = n + t
        lost = (sp[a] | sp[b]) & ~sp[e]
        if lost:
            isexit[e] = lost
    # double charges and their exits
    stats = dict(dc_gates=0, inst=0, inst_cancel=0, conf_nonesc=0, conf_nonesc_cancel=0,
                 conf_esc=0, notconf=0, off_uncharged=0, off_input=0, exits_used=set(),
                 conf_ok_cases=[])
    for g in range(n, N):
        if mult[g] < 2:
            continue
        stats['dc_gates'] += 1
        for j in F:
            if not (A[j] >> g & 1 and sp[g] >> j & 1):
                continue
            need = sp[g] & ~W[j]
            if not need:
                continue
            for e, lost in isexit.items():
                if not (A[j] >> e & 1):
                    continue
                a, b = gates[e - n]
                for o, off in ((a, b), (b, a)):
                    if not (anc[o] >> g & 1):
                        continue           # o must be g or a descendant of g
                    stats['inst'] += 1
                    cancels_needed = bool(lost & need & sp[o])
                    if cancels_needed:
                        stats['inst_cancel'] += 1
                        stats['exits_used'].add(e)
                    L = [l for l in blocks(sp[off]) if sp[off] & ~W[l] == 0]
                    nonesc = [l for l in L if sp[e] >> l & 1]
                    if L and nonesc:
                        stats['conf_nonesc'] += 1
                        if cancels_needed:
                            stats['conf_nonesc_cancel'] += 1
                            stats['conf_ok_cases'].append((g, j, e, off, nonesc,
                                                           [k for k in F if off in F[k]]))
                    elif L:
                        stats['conf_esc'] += 1
                    else:
                        stats['notconf'] += 1
                    if cancels_needed:
                        if off < n:
                            stats['off_input'] += 1
                        elif mult[off] == 0:
                            stats['off_uncharged'] += 1
    return dict(ok=ok, G=G, E=Eex, R=R, U=U, c=c, cj=cj, union=union, F=F, mult=mult,
                sp=sp, val=val, nexits=len(isexit), isexit=isexit, W=W, stats=stats,
                nrowgates=nrowgates, A=A, anc=anc)

# ---------------- readers ----------------
def read_rot(path):
    lines = [l for l in open(path) if l.strip() and not l.startswith('#')]
    n, k = map(int, lines[0].split())
    gates = [tuple(map(int, l.split())) for l in lines[1:1 + k]]
    assert len(gates) == k
    return n, gates

def read_ncff(path):
    names = {'x%d' % i: i for i in range(32)}
    gates = []
    for l in open(path):
        p = l.split()
        if len(p) == 4 and p[0] == 'XOR':
            gates.append((names[p[2]], names[p[3]]))
            names[p[1]] = 32 + len(gates) - 1
    return gates

def read_kste_line(line):
    return [tuple(p) for p in ast.literal_eval(line.strip())]
