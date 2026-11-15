"""Experiment 1: the umizame row problem, exactly.

a, b in GF(4) known early, c in GF(4) late (independent variables; 6 bits, 64 points).
Free: affine functions, the three early products p1, p2, p3 of ab (umizame), optionally c0*c1.
Targets: bc and ca (4 coordinates).  Question: least number of further products (any affine
operands in a, b, c), and least number of 'late' (c-dependent) ones among optimal sets.
Normal basis [W^2, W]: x = x0 W^2 + x1 W.
"""
import itertools, sys
from h2lib import Basis, min_cover

def m4(x, y):  # GF(4) poly basis, ints 0..3, bit1 = W
    r = 0
    if y & 1: r ^= x
    if y & 2: r ^= (x << 1)
    if r & 4: r ^= 0b111
    return r

W = 2; W2 = 3
def from_n(x0, x1): return (W2 if x0 else 0) ^ (W if x1 else 0)
def to_n(x):  # returns (x0, x1)
    for x0 in (0, 1):
        for x1 in (0, 1):
            if from_n(x0, x1) == x: return x0, x1
def tau(x): return (x ^ m4(x, x)) & 1  # x + x^2 in {0,1}

NPTS = 64
def pt(p):
    a = from_n(p & 1, (p >> 1) & 1); b = from_n((p >> 2) & 1, (p >> 3) & 1); c = from_n((p >> 4) & 1, (p >> 5) & 1)
    return a, b, c

def tab(f):
    t = 0
    for p in range(NPTS):
        if f(*pt(p)) & 1: t |= 1 << p
    return t

ONE = (1 << NPTS) - 1
lin = [tab(lambda a, b, c, i=i: [to_n(a)[0], to_n(a)[1], to_n(b)[0], to_n(b)[1], to_n(c)[0], to_n(c)[1]][i]) for i in range(6)]
def lform(mask):
    t = 0
    for i in range(6):
        if mask >> i & 1: t ^= lin[i]
    return t

p1 = tab(lambda a, b, c: tau(a) & tau(b))
p2 = tab(lambda a, b, c: tau(m4(W, a)) & tau(m4(W, b)))
p3 = tab(lambda a, b, c: tau(m4(W2, a)) & tau(m4(W2, b)))
c01 = lin[4] & lin[5]
targets = [tab(lambda a, b, c, j=j: to_n(m4(b, c))[j]) for j in (0, 1)] + \
          [tab(lambda a, b, c, j=j: to_n(m4(c, a))[j]) for j in (0, 1)]
ab_t = [tab(lambda a, b, c, j=j: to_n(m4(a, b))[j]) for j in (0, 1)]

def run(free_extra, label, early_free=(p1, p2, p3)):
    E = [ONE] + lin + list(early_free) + free_extra
    B = Basis()
    for v in E: B.add(v)
    red = lambda v: B.full_reduce(v)[0]
    T = [red(t) for t in targets]
    cands = []
    seen = {}
    for l, m in itertools.combinations(range(1, 64), 2):
        pr = lform(l) & lform(m)
        r = red(pr)
        if r == 0 or r in seen: continue
        late = bool((l | m) >> 4)
        # keep an early representative if one exists for this image
        seen[r] = (l, m, late)
    # images may be reached both by early and late products: prefer early label
    best = {}
    for l, m in itertools.combinations(range(1, 64), 2):
        r = red(lform(l) & lform(m))
        if r == 0: continue
        late = bool((l | m) >> 4)
        if r not in best or (best[r][2] and not late): best[r] = (l, m, late)
    cands = [(r, best[r]) for r in best]
    res = min_cover(T, cands, kmax=8, extra_max=4, want_all=True)
    if not res:
        print(label, 'no cover up to 8'); return
    k = res[0][0]
    # min number of late products per optimal span
    early_imgs = [r for r, lab in cands if not lab[2]]
    stats = {}
    for kk, chosen in res:
        S = Basis()
        for (l, m, late) in chosen: S.add(red(lform(l) & lform(m)))
        span = set([0])
        for r in list(S.rows.values()):
            span |= {s ^ r[0] for s in span}
        er = Basis()
        for r in early_imgs:
            if B.full_reduce(r)[0] in span or r in span: er.add(r)
        mlate = kk - er.n
        stats[mlate] = stats.get(mlate, 0) + 1
    print(label, 'min k =', k, ' #optimal spans:', len(res), ' min-late histogram:', stats)
    return res

if __name__ == '__main__':
    print('targets reduced dims check')
    run([], 'free = affine + p1..p3:')
    run([c01], 'free = affine + p1..p3 + c0c1:')
    run([], 'free = affine only (no early ab products):', early_free=())
    run([c01], 'free = affine + c0c1 (no early):', early_free=())
