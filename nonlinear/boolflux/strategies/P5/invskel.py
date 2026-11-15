"""Exhaustive AND-skeleton search for a 5-AND GF(2^4) inversion block under an AND-depth cap (P5).

Model (state it with every result):
  * block inputs v0..v3 (4 independent signals, AND level 0 relative), any affine form of
    them may be used; block targets = 4 main outputs + their 5 Karatsuba sums (fixed by the
    bottom of the circuit the block is cut from).
  * exactly NA ANDs (default 5); each AND = L1 & L2 with L1, L2 affine forms over the inputs,
    the constant and earlier ANDs of lower level; every target must be an affine form over
    inputs + ANDs; every target's AND level <= D.
  * linear cost of a skeleton = number of distinct required affine forms (AND operands and
    targets) that are not bare inputs / AND outputs, if every such form is one XOR/XNOR of two
    available signals in some order (checked by greedy closure, which is exact for this test);
    otherwise a greedy upper bound (marked '+').
Pruning used (exact): let r = dim((S + T) / S), S = span of everything chosen, T = target span.
Each AND lowers r by at most 1, so with NA ANDs and r0 = 4 at most NA - 4 ANDs may be
'helpers' (not lowering r).  Component functions of GF(16) inversion all have degree 3, so no
level-1 AND (degree 2) can lower r; the search verifies this rather than assuming it.

usage: python3 invskel.py SPEC.json --depth D [--na 5] [--top 30] [--out FILE]
SPEC as for exsyn.py (targets: first 4 = main outputs, the rest = sums).
"""
import argparse, json, sys, time
from itertools import combinations

ONES = 0xffff
PAIDX = set()


def span_add(S, p):
    if p in S: return S
    return S | {s ^ p for s in S}


def closure_cost(blev, flev, D):
    """Level-aware linear cost.  blev: basis table -> AND level (inputs 0, ANDs their level);
    flev: required form -> highest AND level it may have (operand of a level-l AND: l-1;
    target: D).  Stage l uses signals of level <= l only.  Returns (cost, exact): exact when
    every form is one XOR/XNOR of two signals available at its stage (then cost = #forms,
    a lower bound, so optimal); otherwise a greedy upper bound."""
    avail = {}
    for t, l in blev.items(): avail[t] = l; avail[t ^ ONES] = l
    avail[0] = 0; avail[ONES] = 0
    rem = dict(flev)
    cost = 0; exact = True
    for st in range(0, D + 1):
        changed = True
        while changed:
            changed = False
            al = [g for g, l in avail.items() if l <= st]
            alset = set(al)
            for f in [f for f, l in rem.items() if l >= st]:
                if f in PAIDX or any((f ^ g) in alset for g in al):
                    del rem[f]; avail[f] = st; avail[f ^ ONES] = st; cost += 1; changed = True
                    al.append(f); al.append(f ^ ONES); alset.add(f); alset.add(f ^ ONES)
        # forms due at this stage that are still missing: 2 gates if f = g^h^k, else 3 (crude)
        for f in [f for f, l in rem.items() if l == st]:
            exact = False
            al = [g for g, l in avail.items() if l <= st]
            alset = set(al)
            two = any((f ^ g ^ h) in alset for g, h in combinations(al, 2))
            cost += 2 if two else 3
            del rem[f]; avail[f] = st; avail[f ^ ONES] = st
    return cost, exact


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('spec'); ap.add_argument('--depth', type=int, required=True)
    ap.add_argument('--na', type=int, default=5); ap.add_argument('--top', type=int, default=30)
    ap.add_argument('--out')
    ap.add_argument('--prefix', default='', help='fixed first ANDs: lev:L1:L2,... (hex tables)')
    ap.add_argument('--maxcost', type=int, default=99, help='keep leaves with cost <= this')
    ap.add_argument('--shard', default='0/1', help='i/n: only first-AND choices with index %% n == i')
    a = ap.parse_args()
    spec = json.load(open(a.spec))
    global ONES, PAIDX
    ONES = (1 << (1 << spec["k"])) - 1
    V = [int(i['table'], 16) for i in spec['inputs']]
    VF = [int(i['table'], 16) for i in spec['inputs'] if not i.get('paid')]
    BOUND = [int(bf['table'], 16) for bf in spec.get('boundary', [])]
    for bf in spec.get('boundary', []):
        t = int(bf['table'], 16); PAIDX.add(t); PAIDX.add(t ^ ONES)
    tg = [int(t['table'], 16) for t in spec['targets']]
    names = [t['name'] for t in spec['targets']]
    main4 = tg[:4]
    D, NA = a.depth, a.na
    S0 = {0}
    for v in V + [ONES]: S0 = span_add(S0, v)
    T = {0}
    for t in main4: T = span_add(T, t)

    def r_of(S):
        R = set(S)
        n = 0
        for t in main4:
            if t not in R: R = span_add(R, t); n += 1
        return n

    r0 = r_of(S0)
    print('r0 =', r0, 'helpers allowed', NA - r0, flush=True)
    results = []
    stats = {'leaves': 0, 'nodes': 0}
    t0 = time.time()
    # level spans: lev_span[l] = span of inputs + ANDs of level <= l
    # chosen: list of (level, L1, L2, P)

    def exact_cost(bl, fl):
        """(cost, kind) for basis levels bl and required forms fl (form -> allowed level)."""
        n = len(fl)
        c, e = closure_cost(bl, fl, D)
        if e: return n, 'exact'
        if n + NA + 1 + extra_paid[0] > a.maxcost: return n + 2, 'lb+2'
        sig = list(bl) + list(fl)
        sig += [x ^ ONES for x in sig]
        cand = set()
        for i in range(len(sig)):
            for j in range(i + 1, len(sig)):
                h = sig[i] ^ sig[j]
                if h not in bl and h not in fl and h not in (0, ONES) and (h ^ ONES) not in fl:
                    cand.add(h)
        for h in cand:
            f2 = dict(fl); f2[h] = D
            c, e = closure_cost(bl, f2, D)
            if e: return n + 1, 'exact+1'
        return n + 2, 'lb+2'

    extra_paid = [0]

    def leaf(chosen):
        stats['leaves'] += 1
        blev = {v: 0 for v in VF}
        for c in chosen: blev[c[3]] = c[0]
        flev = {}
        for c in chosen:
            for L in (c[1], c[2]):
                if L not in blev: flev[L] = min(flev.get(L, D), c[0] - 1)
        for t in tg:
            if t not in blev: flev.setdefault(t, D)
        best = None
        masks = range(1 << len(BOUND)) if BOUND else [0]
        for msk in masks:
            U = [BOUND[i] for i in range(len(BOUND)) if msk >> i & 1]
            bl = dict(blev)
            for u in U: bl[u] = 0
            fl = {f: l for f, l in flev.items() if f not in bl}
            extra_paid[0] = len(U)
            c, kind = exact_cost(bl, fl)
            c += len(U)
            if best is None or c < best[0] or (c == best[0] and kind != 'lb+2' and best[1] == 'lb+2'):
                best = (c, kind)
        cost, kind = best
        stats.setdefault(kind, 0); stats[kind] += 1
        if cost + NA > a.maxcost: return
        results.append((cost + NA, kind, [(c[0], c[1], c[2], c[3]) for c in chosen]))

    TG = set(tg)

    def lb_of(chosen):
        B = set(VF) | {c[3] for c in chosen}
        F = set()
        for c in chosen:
            for L in (c[1], c[2]):
                if L not in B: F.add(L)
        need = F | (TG - B)
        rem = NA - len(chosen)
        return len(need) - min(rem, len(TG - B - F)), B, F

    def dfs(chosen, S, levspans, helpers_left, last_key):
        stats["nodes"] += 1
        if len(chosen) == 1 and not a.prefix:
            stats["top"] = stats.get("top", 0) + 1
            si, sn = map(int, a.shard.split('/'))
            if (stats["top"] - 1) % sn != si: return
            print("top", stats["top"], "leaves", stats["leaves"], "kept", len(results), "%.0fs" % (time.time() - t0), flush=True)
        r = r_of(S)
        k = len(chosen)
        if r == 0 and k == NA:
            leaf(chosen); return
        if k == NA: return
        if r > NA - k: return
        lb, B, F = lb_of(chosen)
        slack = a.maxcost - NA - lb
        if slack < 0: return
        curlev = chosen[-1][0] if chosen else 1
        for lev in range(curlev, D + 1):
            src = levspans[lev - 1]
            low = levspans[lev - 2] if lev >= 2 else set()
            forms = sorted(f for f in src if f not in (0, ONES))
            free = [f for f in forms if f in B or f in F or f in TG]
            if slack >= 2:
                pairs = ((forms[i], L2) for i in range(len(forms)) for L2 in forms[i + 1:])
            elif slack == 1:
                seen = set()
                def gen1():
                    for L1 in free:
                        for L2 in forms:
                            if L2 == L1: continue
                            pr = (L1, L2) if L1 < L2 else (L2, L1)
                            if pr in seen: continue
                            seen.add(pr); yield pr
                pairs = gen1()
            else:
                pairs = ((free[i], L2) for i in range(len(free)) for L2 in free[i + 1:])
            for L1, L2 in pairs:
                if lev >= 2 and L1 in low and L2 in low: continue
                key = (lev, L1, L2)
                if lev == curlev and chosen and key <= last_key: continue
                P = L1 & L2
                if P in S: continue          # useless AND (already in span)
                lowers = any((P ^ t) in S for t in T if t)
                h = helpers_left
                if not lowers:
                    if h == 0: continue
                    h -= 1
                ch2 = chosen + [(lev, L1, L2, P)]
                if NA + lb_of(ch2)[0] > a.maxcost: continue
                S2 = span_add(S, P)
                ls2 = list(levspans)
                for l in range(lev, D + 1): ls2[l] = span_add(ls2[l], P)
                dfs(ch2, S2, ls2, h, key)

    levspans = [S0] * (D + 1)
    chosen = []; S = S0; h = NA - r0; key = None
    for item in filter(None, a.prefix.split(',')):
        lev, x, y = item.split(':'); lev = int(lev); L1, L2 = sorted((int(x, 16), int(y, 16)))
        assert L1 in levspans[lev - 1] and L2 in levspans[lev - 1], item
        P = L1 & L2
        if not any((P ^ t) in S for t in T if t): h -= 1
        S = span_add(S, P); levspans = list(levspans)
        for l in range(lev, D + 1): levspans[l] = span_add(levspans[l], P)
        chosen.append((lev, L1, L2, P)); key = (lev, L1, L2)
    print('prefix', len(chosen), 'helpers left', h, flush=True)
    dfs(chosen, S, levspans, h, key)
    results.sort(key=lambda x: (x[0], x[1] == 'lb+2'))
    print('nodes %d leaves %d %.1fs' % (stats['nodes'], stats['leaves'], time.time() - t0), stats)
    if results:
        from collections import Counter
        cnt = Counter((c, e) for c, e, _ in results)
        print('cost distribution (cost incl. ANDs, exact):', sorted(cnt.items())[:12])
    for c, e, ch in results[:a.top]:
        print('cost', c, e, ' '.join('L%d:%04x&%04x' % (l, x, y) for l, x, y, p in ch))
    if a.out:
        json.dump([{'cost': c, 'exact': e == 'exact' or e == 'exact+1', 'kind': e, 'ands': [[l, '%04x' % x, '%04x' % y] for l, x, y, p in ch]}
                   for c, e, ch in results[:20000]], open(a.out, 'w'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
