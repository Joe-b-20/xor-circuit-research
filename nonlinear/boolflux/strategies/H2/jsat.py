"""Joint SAT in the relaxed tower model: choose early products (x-only) AND last-layer members
together, with N's coordinates D as extra targets that may use only early products.

Free: affine(L, R, v) + allowed v-quadratics(gamma) (pullback in BMP middle span).
Early candidates (--early): 'rows' = all products of two GF(2)-linear forms inside one umizame
row's 4-bit space (a0, a1, b0, b1)  (3 x 35 = 105);  'umi' = umizame's 9 p's only (forced);
'all' = all 10795 products of x-linear forms.
Late candidates (--late): 'row' (45 row-local members), 'rows+' (lam in a row span, any mu),
'all' (all members).
Cardinality: #early <= E, #late <= K.   Solver: CaDiCaL (pysat), run under a wall-clock limit.
"""
import argparse, itertools, sys, time, json, os
from h2lib import Basis
import tsearch as TS
from tower import m4, tau, W, W2, norm, tab, VAR, ONE
from pysat.formula import CNF, IDPool
from pysat.card import CardEnc, EncType
from pysat.solvers import Solver

ap = argparse.ArgumentParser()
ap.add_argument('--gamma', type=int, default=0)
ap.add_argument('--early', default='rows')
ap.add_argument('--late', default='row')
ap.add_argument('--E', type=int, default=9)
ap.add_argument('--K', type=int, default=13)
ap.add_argument('--solver', default='cadical153')
ap.add_argument('--out', default='')
ap.add_argument('--classes', default='')
ap.add_argument('--freejunk', type=int, default=0)
ap.add_argument('--freev', type=int, default=0)
args = ap.parse_args()
t0 = time.time()
g = args.gamma
free = [ONE] + VAR + TS.allowed_vquads(g)
FB = Basis()
for f in free: FB.add(f)
red = lambda v: FB.full_reduce(v)[0]
Tout = [red(t) for t in TS.targets(g)]
TD = [red(tab(lambda L, R, v, j=j: norm(L, R) >> j & 1)) for j in range(4)]

# early candidates
def xlin(mask):  # mask over the 8 (L,R) bits
    return tab(lambda L, R, v: bin(mask & (L | (R << 4))).count('1') & 1)

early = []
forced = []
if args.early == 'umi+all':
    early = [(red(p), ('p', i)) for i, p in enumerate(TS.early_products())]
    forced = list(range(9))
    seen = set(e[0] for e in early)
    lins = [xlin(m) for m in range(1, 256)]
    for i, j in itertools.combinations(range(255), 2):
        pr = red(lins[i] & lins[j])
        if pr and pr not in seen: seen.add(pr); early.append((pr, ('x', i + 1, j + 1)))
elif args.early.startswith('file:'):
    # level-1 products of a published circuit, ported to (L, R) coordinates
    import tbuild as TB, a28parse as AP
    inv = {}
    for x in range(256): inv[TB.LR(x)] = x
    _, ANDS = AP.load(args.early[5:])
    for A in ANDS:
        if A['stage'] != 'L': continue
        o = A['out']
        early.append((red(tab(lambda L, R, v, o=o: (o >> inv[(L, R)]) & 1)), ('file', A['sig'])))
elif args.early == 'umi':
    early = [(red(p), ('p', i)) for i, p in enumerate(TS.early_products())]
else:
    if args.early == 'rows':
        spaces = []
        for a, b, c in TS.ROWS:
            # the 4 bit-functionals tau(a), tau(Wa), tau(b), tau(Wb) as masks: compute tables
            fs = [tab(lambda L, R, v, a=a, r=r: tau(m4(r, TS.lam_val(a, L, R)))) for r in (1, W)] + \
                 [tab(lambda L, R, v, b=b, r=r: tau(m4(r, TS.lam_val(b, L, R)))) for r in (1, W)]
            lin = []
            for m in range(1, 16):
                t = 0
                for i in range(4):
                    if m >> i & 1: t ^= fs[i]
                lin.append(t)
            spaces.append(lin)
        seen = set()
        for lin in spaces:
            for u, w_ in itertools.combinations(lin, 2):
                pr = red(u & w_)
                if pr and pr not in seen: seen.add(pr); early.append((pr, ('x', len(early))))
    else:
        lins = [xlin(m) for m in range(1, 256)]
        seen = set()
        for i, j in itertools.combinations(range(255), 2):
            pr = red(lins[i] & lins[j])
            if pr and pr not in seen: seen.add(pr); early.append((pr, ('x', i + 1, j + 1)))
late = []
seen = set()
import pickle
_cf = os.path.expanduser('~/xs-campaigns/2026-11-15-study/H2/mtab-%s.pkl' % args.late)
if os.path.exists(_cf):
    _mt = pickle.load(open(_cf, 'rb'))
else:
    _mt = [(lc, mc, TS.member_table(lc, mc)) for lc, mc in TS.candidates(args.late)]
    pickle.dump(_mt, open(_cf, 'wb'))
CL = [(0, 1), (W, 0), (W, 1), (W, W), (W, W2)]
def mclass(mu):
    for i, c in enumerate(CL):
        for k in (1, W, W2):
            if (m4(k, c[0]), m4(k, c[1])) == tuple(mu): return i
allowed_cls = set(map(int, args.classes.split(','))) if args.classes else None
for lc, mc, _tt in _mt:
    if allowed_cls is not None and mclass(mc) not in allowed_cls: continue
    t = red(_tt)
    if t and t not in seen: seen.add(t); late.append((t, (lc, mc)))
print('gamma', g, 'early', len(early), 'late', len(late), 'setup %.1fs' % (time.time() - t0), flush=True)

# quotient coordinates
QB = Basis(track=True); nb = 0
XQ = []
_xl = [xlin(1 << i) for i in range(8)]
for i, j in itertools.combinations(range(8), 2):
    XQ.append(red(_xl[i] & _xl[j]))
for v in XQ:
    if QB.add(v, 1 << nb): nb += 1
nX = nb
for i, j in itertools.combinations(range(4), 2):
    vq = red(tab(lambda L, R, v, i=i, j=j: (v >> i) & (v >> j) & 1))
    if QB.add(vq, 1 << nb): nb += 1
nV = nb
allv = Tout + TD + [e[0] for e in early] + [l[0] for l in late]
for v in allv:
    if QB.add(v, 1 << nb): nb += 1
def coord(v):
    r, tag = QB.full_reduce(v); assert r == 0; return tag
targets = [coord(t) for t in Tout] + [coord(t) for t in TD]
cand = [coord(e[0]) for e in early] + [coord(l[0]) for l in late]
ne = len(early); n = len(cand)
print('quotient dim', nb, 'x-junk dims', nX, flush=True)

pool = IDPool()
s = [pool.id(('s', i)) for i in range(n)]
cnf = CNF()
c = {}
for ti in range(len(targets)):
    for i in range(n):
        if ti >= 8 and i >= ne: continue
        v = pool.id(('c', ti, i)); c[(ti, i)] = v
        cnf.append([-v, s[i]])

def xor_eq(vars_, rhs):
    if not vars_:
        if rhs: cnf.append([])
        return
    acc = vars_[0]
    for x in vars_[1:]:
        y = pool.id(('x', len(cnf.clauses), acc, x))
        cnf.extend([[-y, acc, x], [-y, -acc, -x], [y, -acc, x], [y, acc, -x]])
        acc = y
    cnf.append([acc] if rhs else [-acc])

Y = [[pool.id(('y', l, j)) for j in range(nX)] for l in range(args.freejunk)]
YV = [[pool.id(('yv', l, j)) for j in range(nX, nV)] for l in range(args.freev)]
for ti, tv in enumerate(targets):
    zs = {}
    if ti < 8:
        for l in range(args.freejunk):
            d = pool.id(('d', ti, l))
            for j in range(nX):
                z = pool.id(('z', ti, l, j)); y = Y[l][j]
                cnf.extend([[-z, d], [-z, y], [z, -d, -y]])
                zs.setdefault(j, []).append(z)
        for l in range(args.freev):
            d = pool.id(('dv', ti, l))
            for jj, j in enumerate(range(nX, nV)):
                z = pool.id(('zv', ti, l, j)); y = YV[l][jj]
                cnf.extend([[-z, d], [-z, y], [z, -d, -y]])
                zs.setdefault(j, []).append(z)
    for j in range(nb):
        vs = [c[(ti, i)] for i in range(n) if (ti, i) in c and (cand[i] >> j) & 1] + zs.get(j, [])
        xor_eq(vs, (tv >> j) & 1)
for i in forced: cnf.append([s[i]])
ce = CardEnc.atmost(lits=s[:ne], bound=args.E, vpool=pool, encoding=EncType.seqcounter)
cl = CardEnc.atmost(lits=s[ne:], bound=args.K, vpool=pool, encoding=EncType.seqcounter)
cnf.extend(ce.clauses); cnf.extend(cl.clauses)
print('vars', pool.top, 'clauses', len(cnf.clauses), 'build %.1fs' % (time.time() - t0), flush=True)
with Solver(name=args.solver, bootstrap_with=cnf.clauses) as S:
    r = S.solve()
    print('RESULT', 'SAT' if r else 'UNSAT', 'time %.1fs' % (time.time() - t0), flush=True)
    if r:
        model = set(x for x in S.get_model() if x > 0)
        E = [early[i][1] for i in range(ne) if s[i] in model]
        Lt = [late[i - ne][1] for i in range(ne, n) if s[i] in model]
        print('early', E); print('late', Lt)
        if True:
            for l in range(args.freejunk):
                print('freejunk', l, ''.join('1' if Y[l][j] in model else '0' for j in range(nX)))
        for l in range(args.freev):
            print('freev', l, ''.join('1' if y in model else '0' for y in YV[l]))
        if args.out:
            json.dump({'gamma': g, 'early': E, 'late': Lt, 'args': vars(args)}, open(args.out, 'w'))
