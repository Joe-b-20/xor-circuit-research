"""Class re-basing of last-level AND products for any circuit (botbasis.py generalised).

Case.  A "top" product is an AND whose output feeds no other AND (only output XOR trees).  Two top
products Q*R1 and Q*R2 with a common operand function Q (any of the three trivial operand variants
(L, R), (R, L), (L+R+1, R) of each AND) form a class; a class {Q*R_1..Q*R_d} can be replaced by
{Q*R'_1..Q*R'_d}, R'_t = sum_{i in v_t} R_i, for any basis {v_t} of GF(2)^d: Q*R'_t is the XOR of the
old products in v_t, so every output stays expressible (old product i = sum of new ones) and A is
unchanged.  Classes are chosen greedily (largest common-Q group first, size >= 2).
Depth bound [C for the stated case: non-class ANDs fixed at their Huffman-earliest arrivals, products
restricted to re-bases of the classes, outputs = XOR trees]: Kraft sum per output at the cap D,
sum 2^(arr - D) over the output's terms (class products after re-basing + fixed other terms) <= 1.
Bases: all unordered bases for d <= MAX_ENUM (d = 4: 840, d = 5: 83,328), otherwise the identity, all
transvections of it and random bases (sampled, heuristic).
Class merge (analyse): Pareto merge of the partial Kraft sums over the classes.  With ub (callers pass their
decision limit: 1.0, or a move scan's limit; a beam pass first lowers it to the max of an achievable combo)
partial states whose max Kraft already exceeds ub are dropped.
Exact for every best <= ub: Kraft sums only grow, and a state with max <= ub is only dominated by states
with max <= ub, so best, best_kraft and best_combo equal the unpruned merge's; when no state reaches ub one
state above it is kept, 'exact' is False and best is that combo's max (> ub).  No silent cut: a merge
above MAX_STATES Pareto states is cut and reported ('exact' False, diag 'truncated').
"""
import itertools
import random
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core, skeleton          # noqa: E402
from skelan import huff, bits, anatomy       # noqa: E402
from botbasis import solve, gf2_rank, load   # noqa: E402

MAX_ENUM = 5
SAMPLES = 3000
EPS = 1e-9
BEAM = 64                   # beam width of the upper-bound pass (analyse with ub)
MAX_STATES = 200000         # safety cut of the class merge, reported ('exact', diag 'truncated'); was a silent 20000


def top_products(sk, n):
    used = 0
    for L, R in sk['ands']: used |= L | R
    outs = 0
    for f in sk['outputs']: outs |= f
    return [k for k in range(len(sk['ands'])) if not (used >> (1 + n + k)) & 1 and (outs >> (1 + n + k)) & 1]


def find_classes(sk, ft, n, min_size=2):
    top = top_products(sk, n)
    cand = {}
    for k in top:
        L, R = sk['ands'][k]
        for X, Y in ((L, R), (R, L), (L ^ R ^ 1, R)):
            Q = ft(X)
            cand.setdefault(Q, {}).setdefault(k, (X, Y))
    assigned = set(); cls = []
    while True:
        best = None
        for Q, mem in cand.items():
            ks = [k for k in mem if k not in assigned]
            if best is None or len(ks) > len(best[1]): best = (Q, ks)
        if best is None or len(best[1]) < min_size: break
        Q, ks = best
        mem = cand[Q]
        cls.append({'Q': Q, 'ands': ks, 'qf': [mem[k][0] for k in ks], 'rf': [mem[k][1] for k in ks]})
        assigned.update(ks)
    return top, cls


def _bases(d, rng):
    vecs = list(range(1, 1 << d))
    if d <= MAX_ENUM:
        for B in itertools.combinations(vecs, d):
            if gf2_rank(B) == d: yield B
        return
    ident = tuple(1 << i for i in range(d))
    seen = {frozenset(ident)}; yield ident
    for i in range(d):          # transvections e_i -> e_i + e_j
        for j in range(d):
            if i != j:
                B = list(ident); B[i] |= 1 << j
                k = frozenset(B)
                if k not in seen: seen.add(k); yield tuple(B)
    tries = 0
    while len(seen) < SAMPLES and tries < 20 * SAMPLES:
        tries += 1
        B = tuple(rng.randrange(1, 1 << d) for _ in range(d))
        if gf2_rank(B) < d: continue
        k = frozenset(B)
        if k in seen: continue
        seen.add(k); yield tuple(sorted(B))


def pareto(items):
    """items: list of (vec, payload); keep the non-dominated (min) vectors, first payload per vector"""
    items = sorted(items, key=lambda t: (sum(t[0]), max(t[0])))
    P = []
    for v, pl in items:
        if any(all(a <= b + EPS for a, b in zip(p, v)) for p, _ in P): continue
        P.append((v, pl))
    return P


def _merge(base, cls, ub, beam):
    """Pareto merge of partial Kraft sums over the classes (exact min-max: dominance is preserved under
    addition).  ub: drop states with max > ub (exact for results <= ub; when nothing reaches ub one state
    above it is carried); beam: keep only the beam lowest (max, sum) states per step (heuristic upper bound).
    Returns (states, per-step diag (in, distinct sums, Pareto out, cut, pruned), exact, above_ub)."""
    states = [(tuple(base), ())]
    merge = []; exact = True; above = False
    for pc in cls:
        nxt = {}
        for v, ch in states:
            for kv, B in pc['pareto']:
                s = tuple(round(a + b, 9) for a, b in zip(v, kv))
                if s not in nxt: nxt[s] = ch + (B,)
        items = list(nxt.items()); npr = 0
        if ub is not None:
            kept = [t for t in items if max(t[0]) <= ub + EPS]
            npr = len(items) - len(kept)
            if not kept and items:          # nothing reaches ub: carry one state above it (best > ub, not exact)
                kept = [min(items, key=lambda t: (max(t[0]), sum(t[0])))]
                above = True; exact = False
            items = kept
        if beam is not None:
            items = sorted(items, key=lambda t: (max(t[0]), sum(t[0])))[:beam]
        par = pareto(items)
        cut = len(par) > MAX_STATES
        if cut: exact = False
        merge.append((len(states), len(nxt), len(par), cut, npr))
        states = par[:MAX_STATES]
    return states, merge, exact, above


def analyse(c, cap, rng=None, min_size=2, ub=None, value_only=False):
    """returns res dict: classes (_pc), base Kraft per output, best (min max Kraft), best combo, exact, or
    None if no class exists (structure not applicable).  ub: upper-bound prune of the class merge (exact
    for every best <= ub, module docstring); None: no prune.  value_only (with ub): best exact, but
    best_combo / best_kraft may be another combo of the same max (callers that only rank by the bound)."""
    rng = rng or random.Random(0)
    import time as _t
    t_a0 = _t.time()
    sk, arr, alv = anatomy(c)
    n = c.n
    tab, ft, ones = skeleton._form_tables(sk)
    top, cls = find_classes(sk, ft, n, min_size)
    if not cls: return None

    def farr(f):
        return huff([arr[p] for p in bits(f) if p], f & 1)
    outs = sk['outputs']; m = len(outs)
    clsbits = 0
    for pc in cls:
        for k in pc['ands']: clsbits |= 1 << (1 + n + k)
    base = []
    for f in outs:
        base.append(sum(2.0 ** (arr[p] - cap) for p in bits(f & ~clsbits) if p))
    for pc in cls:
        ks = pc['ands']; d = len(ks); rf = pc['rf']
        qforms = sorted(set(pc['qf']), key=farr)
        blk = []
        for f in outs:
            mm = 0
            for i, k in enumerate(ks):
                if (f >> (1 + n + k)) & 1: mm |= 1 << i
            blk.append(mm)
        va = {}

        def varr(v):
            if v in va: return va[v]
            R = 0
            for i in range(d):
                if (v >> i) & 1: R ^= rf[i]
            best = 99
            for Qf in qforms:
                best = min(best, 1 + max(farr(Qf), farr(R)), 1 + max(farr(Qf), farr(Qf ^ R ^ 1)),
                           1 + max(farr(Qf ^ R ^ 1), farr(R)))
            va[v] = best
            return best
        opts = {}
        for B in _bases(d, rng):
            kr = []
            for mm in blk:
                s = solve(list(B), mm)
                kr.append(sum(2.0 ** (varr(B[t]) - cap) for t in range(d) if (s >> t) & 1))
            key = tuple(kr)
            if key not in opts: opts[key] = B
        pc['pareto'] = pareto(list(opts.items()))
        pc['current'] = [sum(2.0 ** (varr(1 << i) - cap) for i in range(d) if (mm >> i) & 1) for mm in blk]
        pc['blk'] = blk; pc['nbases'] = len(opts); pc['d'] = d
    cur = [base[j] + sum(pc['current'][j] for pc in cls) for j in range(m)]
    # exact min-max over combos: Pareto merge of partial sums (dominance is preserved under addition)
    t_m0 = _t.time()
    U = ub; u0 = None
    if ub is not None:
        # a beam pass (BEAM lowest (max, sum) states per step) gives an achievable combo; its max u0 >= the true
        # min-max, so the exact pass may prune at min(ub, u0) (same rounded sums per combo in both passes)
        bs, _m, _e, _a = _merge(base, cls, None, BEAM)
        bstate = min(bs, key=lambda t: (max(t[0]), sum(t[0])))
        u0 = max(bstate[0])
        U = min(ub, u0)
    probe = value_only and ub is not None and u0 <= ub
    if probe:
        # only the min-max value is needed: prune just below u0; if no state gets there, the min is u0 itself
        # (Kraft sums are dyadic, far coarser than 1e-6), and the beam's combo attains it
        U = u0 - 1e-6
    states, merge, exact, above = _merge(base, cls, U, None)
    if probe and above:
        states, exact, above = [bstate], True, False
    bv, bch = min(states, key=lambda t: (max(t[0]), sum(t[0])))
    return {'sk': sk, 'arr': arr, 'farr': farr, '_pc': cls, 'base': base, 'current_kraft': cur,
            'current_max': max(cur), 'best': max(bv), 'best_kraft': list(bv), 'best_combo': bch,
            'exact': exact, 'n_top': len(top), 'class_sizes': [len(pc['ands']) for pc in cls],
            'diag': {'classes': [{'d': pc['d'], 'nbases': pc['nbases'], 'pareto': len(pc['pareto'])} for pc in cls],
                     'merge': merge, 'truncated': any(x[3] for x in merge), 'ub': ub, 'beam_ub': u0, 'above_ub': above, 'secs': round(_t.time() - t_a0, 3),
                     'merge_s': round(_t.time() - t_m0, 3)}}


def feasible_combos(res, limit=1.0 + EPS, maxn=500, rng=None):
    """DFS over the classes' Pareto reps, all combos with every output Kraft <= limit (up to maxn);
    the best combo first, the rest in DFS order (randomised child order if rng)."""
    cls = res['_pc']; out = [tuple(res['best_combo'])] if res['best'] <= limit else []
    seen = set(out)
    order = sorted(range(len(cls)), key=lambda i: len(cls[i]['pareto']))

    def dfs(i, vec, ch):
        if len(out) >= maxn: return
        if i == len(order):
            full = [None] * len(cls)
            for ci, B in zip(order, ch): full[ci] = B
            t = tuple(full)
            if t not in seen: seen.add(t); out.append(t)
            return
        opts = list(cls[order[i]]['pareto'])
        if rng: rng.shuffle(opts)
        for kv, B in opts:
            s = [a + b for a, b in zip(vec, kv)]
            if max(s) <= limit: dfs(i + 1, s, ch + [B])
    dfs(0, list(res['base']), [])
    return out


def new_skeleton(c, res, combo):
    """skeleton with the classes re-based per combo (one basis per class, in res['_pc'] order)"""
    sk = res['sk']; farr = res['farr']; n = c.n; cls = res['_pc']
    pos = {1 + n + k for pc in cls for k in pc['ands']}
    keep = [k for k in range(len(sk['ands'])) if 1 + n + k not in pos]
    remap = {1 + n + k: 1 + n + i for i, k in enumerate(keep)}

    def rm(f):
        g = f & 1
        for p in bits(f):
            if p == 0: continue
            assert p not in pos
            g |= 1 << remap.get(p, p)
        return g
    ands = [(rm(sk['ands'][k][0]), rm(sk['ands'][k][1])) for k in keep]
    clsmask = sum(1 << p for p in pos)
    outs = [rm(f & ~clsmask) for f in sk['outputs']]
    for pc, Bs in zip(cls, combo):
        ks = pc['ands']; d = len(ks); rf = pc['rf']
        qforms = sorted(set(pc['qf']), key=farr)
        newpos = []
        for v in Bs:
            R = 0
            for i in range(d):
                if (v >> i) & 1: R ^= rf[i]
            best = None
            for Qf in qforms:
                for X, Y in ((Qf, R), (Qf, Qf ^ R ^ 1), (Qf ^ R ^ 1, R)):
                    lvl = 1 + max(farr(X), farr(Y))
                    if best is None or lvl < best[0]: best = (lvl, X, Y)
            ands.append((rm(best[1]), rm(best[2]))); newpos.append(1 + n + len(ands) - 1)
        for j, mm in enumerate(pc['blk']):
            sol = solve(list(Bs), mm)
            for t in range(d):
                if (sol >> t) & 1: outs[j] ^= 1 << newpos[t]
    return {'n': n, 'm': c.m, 'ands': ands, 'outputs': outs}
