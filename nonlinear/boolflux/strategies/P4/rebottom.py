"""P4: replace the bottom of a 103-family circuit by the best-timed minimum bottom.

Every minimum bottom is the transpose of a minimum circuit T for the product columns (see
bottomT.py).  For each T realisation the original is rebuilt with every multi-input XOR node
arranged optimally for the actual product arrival times (join the two earliest signals first);
the realisation with the smallest latest output (then smallest sum of output levels) is spliced
in, the whole circuit is checked on all 256 inputs and written.

    python3 rebottom.py IN.circ.txt OUT.circ.txt
"""
import heapq
import itertools
import json
import sys

import block
import circ


def min_helper_sets(values, units, hmax=2):
    def closed(S):
        have = set(units)
        prog = True
        while prog:
            prog = False
            for t in S:
                if t not in have and any((t ^ x) in have for x in have):
                    have.add(t)
                    prog = True
        return set(S) <= have
    cand = [h for h in range(1, 256) if h & (h - 1) and h not in values]
    for H in range(hmax + 1):
        sets = [hs for hs in itertools.combinations(cand, H) if closed(values + list(hs))]
        if sets:
            return H, sets
    return None, []


def realisations(V, units):
    allv = units + V
    rec = {v: [(x, v ^ x) for x in allv if x < (v ^ x) and (v ^ x) in allv] for v in V}
    for choice in itertools.product(*[rec[v] for v in V]):
        dep = {v: p for v, p in zip(V, choice)}
        st = {}

        def ok(v):
            if v in units:
                return True
            if st.get(v) == 1:
                return False
            if st.get(v) == 2:
                return True
            st[v] = 1
            r = all(ok(u) for u in dep[v])
            st[v] = 2
            return r
        if all(ok(v) for v in V):
            yield dep


def build(dep, V, units, prods_at, arr, outnames, consts):
    """returns (gates, output levels)."""
    allv = units + V
    readers = {x: [] for x in allv}
    for v, (x1, x2) in dep.items():
        readers[x1].append(v)
        readers[x2].append(v)
    order = []
    seen = set()

    def visit(v):
        if v in seen:
            return
        seen.add(v)
        if v in dep:
            for u in dep[v]:
                visit(u)
        order.append(v)
    for v in allv:
        visit(v)
    sig = {}
    gates = []
    cnt = [0]
    lev = dict(arr)
    for w in reversed(order):
        inc = [(arr[p], p) for p in prods_at.get(w, [])] + [(lev[sig[r]], sig[r]) for r in readers[w]]
        if not inc:
            sig[w] = None
            continue
        hq = list(inc)
        heapq.heapify(hq)
        while len(hq) > 1:
            l1, s1 = heapq.heappop(hq)
            l2, s2 = heapq.heappop(hq)
            cnt[0] += 1
            o = f"p4b{cnt[0]}"
            gates.append(['XOR', o, (s1, s2)])
            lev[o] = max(l1, l2) + 1
            heapq.heappush(hq, (lev[o], o))
        sig[w] = hq[0][1]
    outl = []
    ren = {}
    for j, u in enumerate(units):
        sname = sig[u]
        ren[sname] = outnames[j]
        outl.append(lev[sname])
    gates = [[op, ren.get(o, o), tuple(ren.get(i, i) for i in ins)] for op, o, ins in gates]
    # constants: flip the final gate of each output when needed
    s = {}
    for op, o, ins in gates:
        pass
    return gates, outl


def main():
    inp, outp = sys.argv[1], sys.argv[2]
    ref = circ.read(inp)
    s = circ.symbolic(ref)
    used = set()
    for op, o, ins in ref:
        if op == 'AND':
            for i in ins:
                used |= s[i][0]
    outprod = [o for op, o, ins in ref if op == 'AND' and o not in used]
    ys = [f'y{j}' for j in range(8)]
    col = {p: sum(1 << j for j, y in enumerate(ys) if p in s[y][0]) for p in outprod}
    L = block.levels_of(ref)
    arr = {p: L[p] for p in outprod}
    values = sorted({c for c in col.values() if c & (c - 1)})
    units = [1 << j for j in range(8)]
    H, hsets = min_helper_sets(values, units)
    prods_at = {}
    for p, c in col.items():
        prods_at.setdefault(c, []).append(p)
    bot = [o for op, o, ins in ref if op != 'AND' and s[o][0] and s[o][0] <= set(outprod)]
    best = None
    for hs in hsets:
        V = values + list(hs)
        for dep in realisations(V, units):
            g, outl = build(dep, V, units, prods_at, arr, ys, None)
            key = (max(outl), sum(outl))
            if best is None or key < best[0]:
                best = (key, g, outl)
    keep = [g for g in ref if g[1] not in set(bot)]
    new = keep + [tuple(x) for x in best[1]]
    # order topologically
    have = {f'x{i}' for i in range(8)}
    out = []
    pend = list(new)
    while pend:
        rest = []
        for g in pend:
            if all(i in have for i in g[2]):
                out.append(g)
                have.add(g[1])
            else:
                rest.append(g)
        if len(rest) == len(pend):
            raise RuntimeError('order')
        pend = rest
    # fix output constants: choose XNOR flags c_g on the new bottom gates so that
    # const(y_j) = sum_g c_g * paths(g -> y_j) (mod 2) + const from the rest = wanted constant
    sym = circ.symbolic(out)
    want = circ.symbolic(ref)
    newn = [x[1] for x in best[1]]
    gi = {n: i for i, n in enumerate(newn)}
    rd = {}
    for op, o, ins in out:
        for i in ins:
            rd.setdefault(i, []).append(o)
    reach = {}
    for n in reversed(newn):
        r = 0
        if n in ys:
            r |= 1 << ys.index(n)
        for w in rd.get(n, []):
            r ^= reach.get(w, 0)
        reach[n] = r
    need = sum(((sym[y][1] ^ want[y][1]) & 1) << j for j, y in enumerate(ys))
    # solve sum c_g reach[g] = need over GF(2)
    rows = []   # (vector, combination bitmask over gates)
    for i, n in enumerate(newn):
        v, comb = reach[n], 1 << i
        for pv, pc in rows:
            if v ^ pv < v:
                v ^= pv
                comb ^= pc
        if v:
            rows.append((v, comb))
            rows.sort(key=lambda t: -t[0])
    v, comb = need, 0
    for pv, pc in rows:
        if v ^ pv < v:
            v ^= pv
            comb ^= pc
    if v:
        raise RuntimeError('constants not solvable')
    flip = {newn[i] for i in range(len(newn)) if (comb >> i) & 1}
    out2 = []
    for op, o, ins in out:
        if o in flip:
            op = 'XNOR' if op == 'XOR' else 'XOR'
        out2.append((op, o, ins))
    ok = circ.correct(out2)
    if not ok:
        vv = circ.simulate(out2); tt = circ.output_targets(); sy = circ.symbolic(out2)
        print("DEBUG", [(y, vv[y] == tt[y], vv[y] == tt[y] ^ circ.MASK, sorted(sy[y][0]) == sorted(want[y][0])) for y in ys], file=sys.stderr)
    m = circ.metrics(out2)
    if ok:
        circ.write(outp, out2, 'p4-rebottom', comment=[f'P4 rebottom of {inp}'])
    print(json.dumps(dict(input=inp, helpers=H, ok=ok, metrics=m, out_levels=best[2], old=circ.metrics(ref))))


if __name__ == '__main__':
    main()
