"""Gate-cost pricing of class re-basings, and re-basing of product classes at any AND level (idea 06).

Re-basing (gbasis.py): a class of products {Q*R_1..Q*R_d} with a common operand function Q is replaced by
{Q*R'_t}, R'_t = sum_{i in v_t} R_i, {v_t} a basis of GF(2)^d; old product i = sum_t sol_t new_t
(sum_t sol_t v_t = e_i), so every function in the circuit is unchanged and A is unchanged.

1. Any level (find_classes): gbasis only takes top products (feeding no AND).  Here a class may sit at any AND
   level: its members must be an antichain (no member in another member's AND cone, so the new operands R'_t
   do not depend on the class) and the class graph (C1 -> C2 when a member of C2 depends on a member of C1)
   must stay acyclic.  Every consumer form of a replaced product (AND operands below it and outputs) is
   rewritten as the XOR of new products (skeleton(): forms substituted, nodes topologically re-ordered).
   A basis vector v_t = e_i keeps product i itself (the parent's AND, reusable); only the other products are new.
2. Depth (bound): Huffman skeleton bound of the re-based skeleton (every AND at its Huffman-earliest arrival,
   new products at their fastest trivial operand variant); for top classes this equals gbasis's Kraft test.
3. Gate price (price): estimate of the built circuit's G: parent gates that stay live (fan-in of the reused ANDs
   and of the parent signals the new forms start from) + new gates (1 per new or rebuilt AND + xc(F) per
   operand / output form F that has no valid parent signal, xc(F) = min(terms - 1, min over valid parent signals
   s of |F xor form(s)|)).  A parent signal is valid if its structural AND cone avoids the removed products and
   the ANDs that must be rebuilt (operand form changed, or a rebuilt AND in their cone).
4. Build (gbuild): hybrid.py generalised to any re-based skeleton: an AND is reused from the parent where its
   structural cone is reused and the skeleton bound allows the cap, otherwise rebuilt at its latest feasible
   deadline (pair layer, paarb.layer_build); rebuilt top products in one shared layer; outputs in one layer.
"""
import heapq
import itertools
import random
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core, skeleton                     # noqa: E402
from boolflux.hub.common import clean                   # noqa: E402
from skelan import huff, bits                           # noqa: E402
from botbasis import solve, gf2_rank                    # noqa: E402
from rebased_build import Builder, XOR, XNOR, NOT, AND  # noqa: E402
import paarb as PB                                      # noqa: E402

MAX_ENUM = 4            # all bases for d <= 4 (d = 4: 840); larger classes: identity, transvections, samples
SAMPLES = 1500


def popc(x):
    return bin(x).count('1')


class Parent:
    """parent structure shared by skeleton(), price() and gbuild()"""

    def __init__(self, c):
        self.c = c; n = c.n; self.n = n
        self.sk = skeleton.extract(c); K = len(self.sk['ands']); self.K = K
        self.tab, self.ft, _ = skeleton._form_tables(self.sk)
        B = Builder(c); self.form = list(B.form); self.lv = list(B.lv)
        cone = [0] * n; fan = [0] * n; sig_of_and = []
        k = 0
        for j, (op, a, b) in enumerate(c.gates):
            cc = cone[a] | cone[b]
            if op not in (XOR, XNOR, NOT):
                cc |= 1 << k; sig_of_and.append(n + j); k += 1
            cone.append(cc); fan.append(fan[a] | fan[b] | (1 << j))
        self.cone, self.fan, self.sig_of_and = cone, fan, sig_of_and
        dep = []
        for kk, (L, R) in enumerate(self.sk['ands']):
            d = 0
            for p in bits(L | R):
                if p > n: d |= (1 << (p - 1 - n)) | dep[p - 1 - n]
            dep.append(d)
        self.dep = dep
        used = 0
        for L, R in self.sk['ands']: used |= L | R
        outs = 0
        for f in self.sk['outputs']: outs |= f
        self.feeds_and = [bool((used >> (1 + n + k)) & 1) for k in range(K)]
        self.live_and = [bool(((used | outs) >> (1 + n + k)) & 1) for k in range(K)]


def find_classes(P, deep=True, min_size=2):
    """classes [{'Q', 'ands', 'qf', 'rf'}] (gbasis format); deep: any level, else top products only"""
    n, K = P.n, P.K; ands = P.sk['ands']
    cand = {}
    for k in range(K):
        if not P.live_and[k] or (not deep and P.feeds_and[k]): continue
        L, R = ands[k]
        for X, Y in ((L, R), (R, L), (L ^ R ^ 1, R)):
            cand.setdefault(P.ft(X), {}).setdefault(k, (X, Y))
    assigned = set(); cls = []; banned = set()

    def antichain(ks):
        out = []
        for k in sorted(ks):
            if all(not (P.dep[k] >> j) & 1 and not (P.dep[j] >> k) & 1 for j in out): out.append(k)
        return out

    def acyclic(cl):
        mem = [set(x['ands']) for x in cl]; m = len(cl)
        adj = [[j for j in range(m) if j != i and any((P.dep[b] >> a) & 1 for a in mem[i] for b in mem[j])] for i in range(m)]
        col = [0] * m

        def dfs(u):
            col[u] = 1
            for v in adj[u]:
                if col[v] == 1 or (col[v] == 0 and not dfs(v)): return False
            col[u] = 2
            return True
        return all(col[i] or dfs(i) for i in range(m))
    while True:
        best = None
        for Q, mem in cand.items():
            if Q in banned: continue
            ks = antichain([k for k in mem if k not in assigned])
            if best is None or len(ks) > len(best[1]) or (len(ks) == len(best[1]) and min(ks, default=0) < min(best[1], default=0)):
                best = (Q, ks)
        if best is None or len(best[1]) < min_size: break
        Q, ks = best; mem = cand[Q]
        pc = {'Q': Q, 'ands': ks, 'qf': [mem[k][0] for k in ks], 'rf': [mem[k][1] for k in ks],
              'top': not any(P.feeds_and[k] for k in ks)}
        if not acyclic(cls + [pc]): banned.add(Q); continue
        cls.append(pc); assigned.update(ks)
    return cls


def bases(d, rng):
    vecs = list(range(1, 1 << d))
    if d <= MAX_ENUM:
        return [B for B in itertools.combinations(vecs, d) if gf2_rank(B) == d]
    ident = tuple(1 << i for i in range(d)); seen = {frozenset(ident)}; out = [ident]
    for i in range(d):
        for j in range(d):
            if i != j:
                B = list(ident); B[i] |= 1 << j; B = tuple(sorted(B))
                if frozenset(B) not in seen: seen.add(frozenset(B)); out.append(B)
    tries = 0
    while len(out) < SAMPLES and tries < 20 * SAMPLES:
        tries += 1
        B = tuple(sorted(rng.randrange(1, 1 << d) for _ in range(d)))
        if gf2_rank(B) < d or frozenset(B) in seen: continue
        seen.add(frozenset(B)); out.append(B)
    return out


def identity(cls):
    return tuple(tuple(1 << i for i in range(len(pc['ands']))) for pc in cls)


def skeleton_of(P, cls, combo, cap=None):
    """re-based skeleton for combo (one basis per class); returns dict sk (final positions, topological),
    origin (parent AND index or None per AND), removed (set of parent AND indices), changed (parent AND
    indices kept with rewritten operand forms), bound (max output Huffman level); None if cyclic."""
    n, K = P.n, P.K; ands = P.sk['ands']
    rem = {}; newn = []          # rem: parent k -> extended form (XOR of node positions); newn: (ci, v)
    for ci, (pc, Bs) in enumerate(zip(cls, combo)):
        ks = pc['ands']; pos = []
        for v in Bs:
            if popc(v) == 1: pos.append(1 + n + ks[v.bit_length() - 1])
            else: pos.append(1 + n + K + len(newn)); newn.append((ci, v))
        for i, k in enumerate(ks):
            sol = solve(list(Bs), 1 << i)
            if popc(sol) == 1 and Bs[sol.bit_length() - 1] == 1 << i: continue
            f = 0
            for t in range(len(Bs)):
                if (sol >> t) & 1: f ^= 1 << pos[t]
            rem[k] = f
    remmask = sum(1 << (1 + n + k) for k in rem)

    def subst(f):
        g = f & ~remmask
        for p in bits(f & remmask): g ^= rem[p - 1 - n]
        return g
    node = {}                    # ext pos -> (kind, ref, variants)
    changed = set()
    for k in range(K):
        if k in rem: continue
        L, R = ands[k]; L2, R2 = subst(L), subst(R)
        if (L2, R2) != (L, R): changed.add(k)
        node[1 + n + k] = ('old', k, [(L2, R2)])
    for j, (ci, v) in enumerate(newn):
        pc = cls[ci]; R = 0
        for i in range(len(pc['ands'])):
            if (v >> i) & 1: R ^= pc['rf'][i]
        var = []
        for Qf in sorted(set(pc['qf'])):
            for X, Y in ((Qf, R), (Qf, Qf ^ R ^ 1), (Qf ^ R ^ 1, R)):
                var.append((subst(X), subst(Y)))
        node[1 + n + K + j] = ('new', (ci, v), var)
    deps = {p: {q for q in bits(nd[2][0][0] | nd[2][0][1]) if q > n} for p, nd in node.items()}
    for p, nd in node.items():
        for X, Y in nd[2][1:]: deps[p] |= {q for q in bits(X | Y) if q > n}
    key = {p: (nd[1] if nd[0] == 'old' else min(cls[nd[1][0]]['ands'])) for p, nd in node.items()}
    indeg = {p: len(deps[p]) for p in node}
    cons = {p: [] for p in node}
    for p, ds in deps.items():
        for q in ds:
            if q not in node: return None
            cons[q].append(p)
    h = [(key[p], p) for p in node if indeg[p] == 0]; heapq.heapify(h); order = []
    while h:
        _, p = heapq.heappop(h); order.append(p)
        for q in cons[p]:
            indeg[q] -= 1
            if indeg[q] == 0: heapq.heappush(h, (key[q], q))
    if len(order) != len(node): return None
    remap = {p: 1 + n + i for i, p in enumerate(order)}

    def rm(f):
        g = f & ((1 << (1 + n)) - 1)
        for p in bits(f >> (1 + n)): g |= 1 << remap[p + 1 + n]
        return g
    arr = [0] * (1 + n + len(order)); fa = []; origin = []
    for i, p in enumerate(order):
        kind, ref, var = node[p]
        best = None
        for X, Y in var:
            X2, Y2 = rm(X), rm(Y)
            lv = 1 + max(huff([arr[q] for q in bits(X2) if q], X2 & 1), huff([arr[q] for q in bits(Y2) if q], Y2 & 1))
            if best is None or lv < best[0]: best = (lv, X2, Y2)
        arr[1 + n + i] = best[0]; fa.append((best[1], best[2])); origin.append(ref if kind == 'old' else None)
    outs = [rm(subst(f)) for f in P.sk['outputs']]
    bound = max(huff([arr[q] for q in bits(F) if q], F & 1) for F in outs)
    return {'sk': {'n': n, 'm': P.c.m, 'ands': fa, 'outputs': outs}, 'origin': origin, 'removed': set(rem),
            'changed': changed, 'bound': bound, 'arr': arr, 'nnew': len(newn)}


def price(P, st):
    """estimated G of the built circuit (module docstring 3); also returns details"""
    n = P.n; sk = st['sk']; origin = st['origin']
    pos_of_k = {k: 1 + n + i for i, k in enumerate(origin) if k is not None}
    S = 0
    for k in range(P.K):
        if k in st['removed'] or k in st['changed'] or (P.cone[P.sig_of_and[k]] & ~(1 << k)) & S:
            S |= 1 << k
    # valid parent signals by final form (constant dropped)
    by = {}
    for s, f in enumerate(P.form):
        if f is None or P.cone[s] & S: continue
        g = 0
        for p in bits(f & ~1):
            g |= 1 << (p if p <= n else pos_of_k[p - 1 - n])
        if g and (g not in by or P.lv[s] < P.lv[by[g]]): by[g] = s
    items = list(by.items())
    live = 0; new = 0; memo = {}

    def xc(F):
        nonlocal live
        f = F & ~1
        if f in memo: return memo[f]
        s = by.get(f)
        if s is not None or popc(f) <= 1:
            if s is not None: live |= P.fan[s]
            memo[f] = 0; return 0
        best = popc(f) - 1; bs = None
        for g, sg in items:
            cst = popc(f ^ g)
            if cst < best: best, bs = cst, sg
        if bs is not None: live |= P.fan[bs]
        memo[f] = best
        return best
    nre = 0
    for i, (L, R) in enumerate(sk['ands']):
        k = origin[i]
        if k is not None and not (S >> k) & 1:
            live |= P.fan[P.sig_of_and[k]]; continue
        nre += 1; new += 1 + xc(L) + xc(R)
    for F in sk['outputs']: new += xc(F)
    G = popc(live) + new
    return G, {'live': popc(live), 'new': new, 'rebuilt': nre}


def class_options(P, cls, i, cap, rng, maxb=None):
    """per class i: every basis with the bound and price when only class i is re-based (others identity)"""
    base = list(identity(cls)); out = []
    for B in bases(len(cls[i]['ands']), rng)[:maxb]:
        cb = list(base); cb[i] = B
        st = skeleton_of(P, cls, tuple(cb))
        if st is None: continue
        if cap is not None and st['bound'] > cap: continue
        out.append((price(P, st)[0], B))
    out.sort()
    return out


def ranked_combos(P, cls, cap, rng, pool=2000, maxeval=20000, opts=None):
    """combos ranked by price with bound <= cap: per-class options (single-class price) combined best-first by
    the sum of single-class price deltas, each combo evaluated exactly (bound, price); returns
    [(price, bound, combo, st)] (identity excluded), cheapest first."""
    if opts is None:
        opts = [class_options(P, cls, i, cap, rng) for i in range(len(cls))]
    g0 = price(P, skeleton_of(P, cls, identity(cls)))[0]
    dl = [[(g - g0, B) for g, B in o] for o in opts]
    ident = identity(cls)
    if any(not o for o in dl): return []
    # best-first over index vectors (sorted options per class)
    start = tuple(0 for _ in dl)
    h = [(sum(o[0][0] for o in dl), start)]; seen = {start}; res = []; nev = 0
    while h and len(res) < pool and nev < maxeval:
        s, idx = heapq.heappop(h)
        combo = tuple(dl[i][j][1] for i, j in enumerate(idx))
        if combo != ident:
            st = skeleton_of(P, cls, combo); nev += 1
            if st is not None and (cap is None or st['bound'] <= cap):
                res.append((price(P, st)[0], st['bound'], combo, st))
        for i in range(len(idx)):
            if idx[i] + 1 < len(dl[i]):
                nx = idx[:i] + (idx[i] + 1,) + idx[i + 1:]
                if nx not in seen:
                    seen.add(nx); heapq.heappush(h, (s - dl[i][idx[i]][0] + dl[i][idx[i] + 1][0], nx))
    res.sort(key=lambda t: (t[0], t[1]))
    return res


def gbuild(P, st, cap, rng=None, use_paar=True, slack_top=True):
    """build the re-based skeleton st at cap, reusing the parent (module docstring 4); returns (circuit, stats)"""
    c = P.c; n = c.n; sk = st['sk']; origin = st['origin']; removed = st['removed']
    pos_of_k = {k: 1 + n + i for i, k in enumerate(origin) if k is not None}
    B = Builder(c)
    newform = []
    for s, f in enumerate(B.form):
        if f is None: newform.append(None); continue
        g = f & 1; bad = False
        for p in bits(f):
            if p == 0: continue
            if p <= n: g |= 1 << p
            else:
                k = p - 1 - n
                if k in removed: bad = True; break
                g |= 1 << pos_of_k[k]
        newform.append(None if bad else g)
    B.form = newform
    cone = []
    for s in range(len(P.cone)):
        cc = 0
        for k in bits(P.cone[s]):
            cc |= 1 if k in removed else (1 << pos_of_k[k])
        cone.append(cc)
    npar = len(B.form)

    def refresh(mask):
        B.by = {}
        for s, f in enumerate(B.form):
            if f is None: continue
            if s < npar and (cone[s] & ~mask): continue
            key = f & ~1
            if key and (key not in B.by or B.lv[s] < B.lv[B.by[key]]): B.by[key] = s
    pand = {pos_of_k[k]: P.sig_of_and[k] for k in pos_of_k}
    feeds = 0
    for L, R in sk['ands']: feeds |= L | R
    from hybrid import bound_from
    nb = 1 + n + len(sk['ands'])
    arr = [0] * nb; fixed = set(); stats = {'reused': 0, 'rebuilt': 0}; mask = 0; defer = []
    for kk, (L, R) in enumerate(sk['ands']):
        p = 1 + n + kk
        refresh(mask)
        if p in pand and (cone[pand[p]] & ~(mask | (1 << p))) == 0:
            s = pand[p]; arr[p] = B.lv[s]
            bd, _ = bound_from(sk, arr, fixed | {p}, n)
            if bd <= cap:
                fixed.add(p); stats['reused'] += 1; mask |= 1 << p
                continue
        if use_paar and not (feeds >> p) & 1:
            defer.append(kk); continue
        hl = huff([arr[q] for q in bits(L) if q], L & 1); hr = huff([arr[q] for q in bits(R) if q], R & 1)
        d = max(hl, hr)
        for dd in range(d + 3, d, -1):
            arr[p] = dd + 1
            bd, _ = bound_from(sk, arr, fixed | {p}, n)
            if bd <= cap: d = dd; break
        if use_paar: sl, sr = PB.layer_build(B, [(L, d), (R, d)], rng)
        else: sl = B.build(L, d, rng); sr = B.build(R, d, rng)
        s = B.new(AND, sl, sr); B.kind[-1] = 'and'
        B.form[s] = 1 << p; B.by[1 << p] = s; arr[p] = B.lv[s]; fixed.add(p); stats['rebuilt'] += 1
    refresh(mask)
    if defer:
        tg = []
        for kk in defer:
            L, R = sk['ands'][kk]; p = 1 + n + kk
            d = max(huff([arr[q] for q in bits(L) if q], L & 1), huff([arr[q] for q in bits(R) if q], R & 1))
            if slack_top:
                for dd in range(d + 2, d, -1):
                    arr[p] = dd + 1
                    bd, _ = bound_from(sk, arr, fixed | {p}, n)
                    if bd <= cap: d = dd; break
            arr[p] = d + 1; fixed.add(p)
            tg += [(L, d), (R, d)]
        sigs = PB.layer_build(B, tg, rng)
        for i, kk in enumerate(defer):
            p = 1 + n + kk
            s = B.new(AND, sigs[2 * i], sigs[2 * i + 1]); B.kind[-1] = 'and'
            B.form[s] = 1 << p; B.by[1 << p] = s; arr[p] = B.lv[s]; stats['rebuilt'] += 1
    if use_paar: outs = PB.layer_build(B, [(F, cap) for F in sk['outputs']], rng)
    else: outs = [B.build(F, cap, rng) for F in sk['outputs']]
    nc = core.Circuit(n, c.m, B.gates, outs, 'rebase-gprice', c.in_names, c.out_names).live()
    return clean(nc), stats


def gb_classes(res):
    """gbasis analyse result classes -> this module's class list (same members, top products)"""
    return [{'Q': pc['Q'], 'ands': list(pc['ands']), 'qf': list(pc['qf']), 'rf': list(pc['rf']), 'top': True} for pc in res['_pc']]


def priced_feasible(P, res, limit=1.0 + 1e-9, pool=3000, rng=None):
    """Kraft path with gate pricing: gbasis's Kraft-feasible combos (up to pool, randomised DFS) ranked by price.
    Returns [(price, combo)] cheapest first (identity excluded)."""
    import gbasis as GB
    combos = GB.feasible_combos(res, limit=limit, maxn=pool, rng=rng or random.Random(0))
    cls = gb_classes(res); ident = identity(cls); out = []
    for cb in combos:
        if tuple(tuple(B) for B in cb) == ident: continue
        st = skeleton_of(P, cls, cb)
        if st is None: continue
        out.append((price(P, st)[0], cb))
    out.sort(key=lambda t: t[0])
    return out


# ---------------------------------------------------------------------------------------------------------
# 5. Patch build (any level): keep every parent gate; the new products Q*R'_t (operands built from parent
#    signals independent of the class) are added, and each replaced product's gate is redirected to the XOR of
#    the new products that equal it (old_i = sum_t sol_t new_t), so nothing below the class is rebuilt.  Cost:
#    per new product 1 AND + its operand XORs, per replaced product |sol| - 1 XORs (+ NOT for constants), minus
#    the gates that become dead.  Depth: a replaced product arrives one or more levels later (the kernel repairs).

def _topo(n, gates, outs):
    deps = [[x for x in (a, b) if x >= n] for (op, a, b) in gates]
    cons = [[] for _ in gates]; indeg = [0] * len(gates)
    for j, ds in enumerate(deps):
        for x in set(ds): cons[x - n].append(j); indeg[j] += 1
    h = [j for j in range(len(gates)) if indeg[j] == 0]; heapq.heapify(h); order = []
    while h:
        j = heapq.heappop(h); order.append(j)
        for q in cons[j]:
            indeg[q] -= 1
            if indeg[q] == 0: heapq.heappush(h, q)
    if len(order) != len(gates): return None
    new = {j: n + i for i, j in enumerate(order)}
    rs = lambda s: s if s < n else new[s - n]
    return [(gates[j][0], rs(gates[j][1]), rs(gates[j][2])) for j in order], [rs(s) for s in outs]


def patch_one(P, pc, Bs):
    """circuit with class pc re-based to basis Bs by the patch build (section 5), or None"""
    c = P.c; n = c.n
    members = pc['ands']; d = len(members); mmask = sum(1 << k for k in members)
    Bd = Builder(c)
    Bd.by = {}
    for s, f in enumerate(Bd.form):
        if f is None or P.cone[s] & mmask: continue
        key = f & ~1
        if key and (key not in Bd.by or Bd.lv[s] < Bd.lv[Bd.by[key]]): Bd.by[key] = s
    sig = []       # per t: (signal, constant of its function relative to the pure product)
    for t, v in enumerate(Bs):
        if popc(v) == 1:
            k = members[v.bit_length() - 1]; s = P.sig_of_and[k]
            sig.append((s, P.form[s] & 1)); continue
        R = 0
        for i in range(d):
            if (v >> i) & 1: R ^= pc['rf'][i]
        best = None
        for Qf in sorted(set(pc['qf'])):
            for X, Y in ((Qf, R), (Qf, Qf ^ R ^ 1), (Qf ^ R ^ 1, R)):
                if not (X & ~1) or not (Y & ~1): continue
                g0 = len(Bd.gates); snap = (list(Bd.gates), list(Bd.form), list(Bd.lv), list(Bd.kind), dict(Bd.by))
                try:
                    sx = Bd.build(X, 99); sy = Bd.build(Y, 99)
                except (KeyError, ValueError):
                    Bd.gates, Bd.form, Bd.lv, Bd.kind, Bd.by = snap; continue
                key = (len(Bd.gates) - g0, max(Bd.lv[sx], Bd.lv[sy]))
                if best is None or key < best[0]: best = (key, sx, sy, (list(Bd.gates), list(Bd.form), list(Bd.lv), list(Bd.kind), dict(Bd.by)))
                Bd.gates, Bd.form, Bd.lv, Bd.kind, Bd.by = snap
        if best is None: return None
        Bd.gates, Bd.form, Bd.lv, Bd.kind, Bd.by = best[3]
        s = Bd.new(AND, best[1], best[2]); Bd.kind[-1] = 'and'
        Bd.form[s] = 1 << (1 + n + P.K + t)       # fresh basis position (only used for the patch XOR forms)
        sig.append((s, 0))
    redirect = {}
    for i, k in enumerate(members):
        sol = solve(list(Bs), 1 << i)
        if popc(sol) == 1 and Bs[sol.bit_length() - 1] == 1 << i: continue
        terms = [sig[t] for t in range(d) if (sol >> t) & 1]
        s_old = P.sig_of_and[k]
        cst = (P.form[s_old] & 1) ^ (sum(x[1] for x in terms) & 1)
        cur = terms[0][0]
        for j, (s, _) in enumerate(terms[1:]):
            last = j == len(terms) - 2
            cur = Bd.new(XNOR if (last and cst) else XOR, cur, s)
        if len(terms) == 1 and cst: cur = Bd.new(NOT, cur, cur)
        redirect[s_old] = cur
    rd = lambda s: redirect.get(s, s)
    gates = [(op, rd(a), rd(b)) for (op, a, b) in Bd.gates]
    outs = [rd(s) for s in c.outputs]
    t = _topo(n, gates, outs)
    if t is None: return None
    nc = core.Circuit(n, c.m, t[0], t[1], 'rebase-patch', c.in_names, c.out_names).live()
    return clean(nc)


def refind(P1, pc_tables, qt):
    """class in a derived circuit by its member product truth tables and Q's table -> class dict, or None"""
    n = P1.n; idx = {}
    for k in range(P1.K): idx.setdefault(P1.tab[1 + n + k], k)
    ks = [idx.get(tb) for tb in pc_tables]
    if any(k is None for k in ks): return None
    out = {'ands': ks, 'qf': [], 'rf': []}
    for k in ks:
        L, R = P1.sk['ands'][k]; got = None
        for X, Y in ((L, R), (R, L), (L ^ R ^ 1, R)):
            if P1.ft(X) == qt: got = (X, Y); break
        if got is None: return None
        out['qf'].append(got[0]); out['rf'].append(got[1])
    out['Q'] = qt; out['top'] = not any(P1.feeds_and[k] for k in ks)
    return out


def patch_variants(c, deep=True, max_single=40, max_pairs=60, rng=None, verify=None):
    """patch builds: every class x non-identity basis (up to max_single per class, random for d >= 3), then
    sequential pairs of single changes in different classes (up to max_pairs); returns [(circuit, desc)]"""
    rng = rng or random.Random(0)
    P = Parent(c); cls = find_classes(P, deep=deep)
    tabs = [([P.tab[1 + P.n + k] for k in pc['ands']], P.ft(pc['qf'][0])) for pc in cls]
    singles = []
    for ci, pc in enumerate(cls):
        d = len(pc['ands']); ident = tuple(1 << i for i in range(d))
        bs = [B for B in bases(d, rng) if tuple(B) != ident]
        if len(bs) > max_single: bs = rng.sample(bs, max_single)
        for B in bs:
            nc = patch_one(P, pc, B)
            if nc is None: continue
            singles.append((nc, (ci, B)))
    out = [(nc, [desc]) for nc, desc in singles]
    pairs = [(i, j) for i in range(len(singles)) for j in range(len(singles)) if singles[i][1][0] < singles[j][1][0]]
    rng.shuffle(pairs)
    for i, j in pairs[:max_pairs]:
        nc1, (ci, B1) = singles[i]; cj, B2 = singles[j][1]
        P1 = Parent(nc1); pc2 = refind(P1, *tabs[cj])
        if pc2 is None: continue
        # refind may permute nothing: members in the original order, so B2 applies as is
        nc = patch_one(P1, pc2, B2)
        if nc is not None: out.append((nc, [(ci, B1), (cj, B2)]))
    return out, cls
