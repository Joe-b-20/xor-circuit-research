"""Pure-bilinear question for the GF(4)-norm member family.

Members N_Q(Lambda(x) + G(v)^2) have bilinear part Tr_Q(Lambda(x) G(v)) (rank-1 GF(4) form).
Target: the 4-dim GF(4)-space T of GF(4)-bilinear forms (x, v) -> phi(x v), x in GF(256) = K^2,
v in K = GF(16) (GF(4)-coordinates; equivalent to Tr_{F/Q}(b x^16 v) up to GL changes of x, v,
which preserve rank-1-ness).  Question: least k such that the GF(2)-span of k rank-1 GF(4)
matrices (4 x 2) contains T.  Exhaustive over S = T + W, W <= M/T (M = 16-dim GF(2) space).
Also: same for one copy (GF(16) x GF(16) -> GF(16): 2 x 2 matrices, T_K 2-dim GF(4)).
"""
import itertools
from h2lib import Basis

def m4(x, y):
    r = 0
    if y & 1: r ^= x
    if y & 2: r ^= (x << 1)
    if r & 4: r ^= 0b111
    return r

W = 2

def mat_to_int(entries):
    v = 0
    for i, e in enumerate(entries): v |= e << (2 * i)
    return v

def run(rows, cols, Tgen, label, kmax):
    # rank-1 matrices
    R1 = set()
    for lam in itertools.product(range(4), repeat=rows):
        if not any(lam): continue
        for mu in itertools.product(range(4), repeat=cols):
            if not any(mu): continue
            R1.add(mat_to_int([m4(lam[i], mu[j]) for i in range(rows) for j in range(cols)]))
    R1 = sorted(R1)
    TB = Basis()
    for t in Tgen: TB.add(t)
    t = TB.n
    img = [TB.full_reduce(r)[0] for r in R1]
    print(label, 'rank-1 count', len(R1), 'dim T over GF(2) =', t, ' rank-1 in T:', sum(1 for i in img if i == 0))
    pts = sorted(set(i for i in img if i))
    nM = 2 * rows * cols
    for k in range(t, kmax + 1):
        e = k - t
        cnt = 0; seenW = set()
        for combo in itertools.combinations(pts, e):
            Wsp = {0}
            ok = True
            for r in combo:
                if r in Wsp: ok = False; break
                Wsp |= {s ^ r for s in Wsp}
            if not ok: continue
            key = frozenset(Wsp)
            if key in seenW: continue
            seenW.add(key)
            S = Basis()
            for r, i in zip(R1, img):
                if i in Wsp: S.add(r)
            if S.n == k and all(S.contains(g) for g in Tgen):
                cnt += 1
        print('  k =', k, ': spans S (dim k, >= T, spanned by rank-1):', cnt)
        if cnt: break

# one copy: x, v in K (2 GF(4) coords each); T_K = {phi(x v)}: matrix [[p, q], [q, w p + q]]
def TK(p, q): return [p, q, q, m4(W, p) ^ q]
gensK = []
for (p, q) in [(1, 0), (W, 0), (0, 1), (0, W)]:
    gensK.append(mat_to_int(TK(p, q)))
run(2, 2, gensK, 'GF(16) mult (one copy):', 8)

gens = []
for blk in (0, 1):
    for (p, q) in [(1, 0), (W, 0), (0, 1), (0, W)]:
        top = TK(p, q) if blk == 0 else [0, 0, 0, 0]
        bot = TK(p, q) if blk == 1 else [0, 0, 0, 0]
        gens.append(mat_to_int(top + bot))
run(4, 2, gens, 'GF(256) x GF(16) (two copies, shared v):', 12)
