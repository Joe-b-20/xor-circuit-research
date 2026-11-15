"""P4: pre-inversion lower bounds via the transposition principle, over all inversion-input bases
and a family of top layers.

Facts used (see NOTES 2.2):
  pre >= amin(P') + k, k = number of x-linear injection gates; X' = R S with S in Avail.
  amin(P') = amin(P'^T) + 9 - 4 (transposition principle; P'^T = the 9 product columns as 4-bit
  vectors over the targets).  The reach vector of every node / edge of an a-circuit is a value
  carried by its transposed circuit, so for an a-circuit with amin(P') + e gates the available
  reach vectors are: units, the 9 columns, and at most e helper values of the transposed circuit.
For each top (value set) and each basis M (840) this script computes amin(P'^T) exactly (closure
over GF(2)^4) and the least pre cost amin + k over k in {rank X', ...} for which a k-point
pattern exists inside units + columns (e = 0) with S in Avail; with e = 1 one free helper value.

    python3 prereach.py CIRC MODE GD      MODE = top17 | top18
"""
import itertools
import os
import json
import sys

import circ
import preinj
import topenum


def amin_T(cols):
    """min XOR gates computing the set of non-unit columns from the 4 unit vectors (exhaustive)."""
    need = {c for c in cols if c and c & (c - 1)}
    units = {1, 2, 4, 8}
    base = set(units)
    # BFS over helper counts
    for h in range(0, 4):
        for hs in itertools.combinations([v for v in range(1, 16) if v not in need and v not in units], h):
            S = need | set(hs)
            have = set(units)
            prog = True
            while prog:
                prog = False
                for t in S - have:
                    if any((t ^ a) in have for a in have):
                        have.add(t)
                        prog = True
            if S <= have:
                return len(need) + h, hs
    return None, None


def patterns(X, avail, fixed, k, wild=0, ntg=4):
    av = sorted(avail)
    for B in itertools.combinations_with_replacement(range(1, 1 << ntg), k):
        if len({b for b in B if b not in fixed}) > wild:
            continue
        if preinj.rank(list(B)) < preinj.rank(X):
            continue
        basis = []
        for i in range(k):
            if preinj.rank([B[j] for j in basis] + [B[i]]) > len(basis):
                basis.append(i)
        # (rank B may be below ntg when rank X is; solve_basis checks consistency)
        free = [i for i in range(k) if i not in basis]
        Bb = [B[i] for i in basis]
        s0 = preinj.solve_basis(Bb, list(X), ntg)
        if s0 is None:
            continue
        if not free:
            if all(v in avail for v in s0):
                return B
            continue
        # the solution is affine in the free values: s_basis = s0 + sum_f c_f * v_f
        cs = [preinj.solve_basis(Bb, [(B[f] >> j) & 1 for j in range(ntg)], ntg) for f in free]
        for fv in itertools.product(av, repeat=len(free)):
            ok = True
            for idx in range(len(basis)):
                sv = s0[idx]
                for c, v in zip(cs, fv):
                    if c[idx]:
                        sv ^= v
                if sv not in avail:
                    ok = False
                    break
            if ok:
                return B
    return None


def matmul(M, V):
    out = []
    for r in M:
        acc = 0
        for c in range(4):
            if (r >> c) & 1:
                acc ^= V[c]
        out.append(acc)
    return out


def main():
    path, mode, gd = sys.argv[1], sys.argv[2], int(sys.argv[3])
    ref = circ.read(path)
    s = circ.symbolic(ref)
    xs = {f'x{i}' for i in range(8)}
    xm = lambda at: sum(1 << int(t[1:]) for t in at if t[0] == 'x')
    import anat2
    _an = anat2.anatomy(path)
    prod = _an["lvl1"]
    am = lambda at: sum(1 << prod.index(t) for t in at if t in prod)
    names = _an["targets"]
    X = [xm(s[t][0]) for t in names]
    P = [am(s[t][0]) for t in names]
    gates, s2, forms, inj = topenum.top_spec(path, gd)
    if os.environ.get('P4_RELAX'):
        # relaxed deadlines: a level-1 AND only has to reach every pre target containing it, so
        # its latest level is min over those targets of req(target) - 1 (pre removed, rest fixed);
        # output ANDs keep the reference's required times.
        import block
        topn = {o for op, o, ins in ref if op != 'AND' and s[o][0] <= xs}
        pren = {o for op, o, ins in ref if op != 'AND' and o not in topn and s[o][0] <= xs | set(prod)}
        req = block.required([g for g in ref if g[1] not in topn | pren], gd)
        forms = {}
        for op, o, ins in ref:
            if op != 'AND':
                continue
            if o in prod:
                ra = min(req[t] for t in names if o in s[t][0]) - 1
            else:
                ra = req.get(o, 99)
            for i in ins:
                if s[i][0] <= xs:
                    m = xm(s[i][0])
                    forms[m] = min(forms.get(m, 99), ra - 1)
        print(json.dumps(dict(relaxed_deadlines={str(m): d for m, d in forms.items()})), flush=True)
    F = {m: d for m, d in forms.items() if bin(m).count('1') > 1}
    allv = [v for v in range(1, 256) if bin(v).count('1') > 1 and v not in F]
    tops = []
    if mode == 'top17':
        for hs in itertools.combinations(allv, 2):
            S = set(F) | set(hs)
            lv = topenum.closure_levels(S)
            if all(t in lv for t in S) and (not os.environ.get("P4_DL") or all(lv[t] <= d for t, d in F.items())):
                tops.append(hs)
        target_pre = 15
    else:
        for hs in itertools.combinations(allv, 3):
            S = set(F) | set(hs)
            lv = topenum.closure_levels(S)
            if all(t in lv for t in S) and all(lv[t] <= d for t, d in F.items()):
                tops.append(hs)
        target_pre = 14
    if len(sys.argv) > 4:
        target_pre = int(sys.argv[4])
    print(json.dumps(dict(mode=mode, tops=len(tops), target_pre=target_pre)), flush=True)
    bases = []
    seen = set()
    for M in itertools.permutations(range(1, 16), 4):
        if preinj.rank(list(M)) < 4 or frozenset(M) in seen:
            continue
        seen.add(frozenset(M))
        bases.append(M)
    hits = 0
    for hs in tops:
        avail = set(F) | set(hs) | {1 << i for i in range(8)}
        best = None
        # k = rank X injections need a basis of V = span X (= span MX for every M) inside Avail;
        # when only k = 4, e = 0 can meet target_pre (amin >= 10), a top without full cover is out.
        Vs = {0}
        for v in X:
            if v not in Vs:
                Vs |= {u ^ v for u in Vs}
        cover = preinj.rank([v for v in avail if v in Vs])
        if target_pre - 10 <= preinj.rank(X) and cover < preinj.rank(X):
            print(json.dumps(dict(top=list(hs), best_pre=None, cover=cover, skipped='no V basis in Avail')), flush=True)
            continue
        for M in bases:
            Pp, Xp = matmul(M, P), matmul(M, X)
            # columns of P'^T: for atom i, bit j set iff atom i in P'_j
            cols = [sum(1 << j for j in range(4) if (Pp[j] >> i) & 1) for i in range(9)]
            if len(set(cols)) < 9 or 0 in cols:
                # repeated / zero columns: transposition bound needs distinct non-zero columns;
                # skip (amin computed by the general bound below is still valid but weaker)
                pass
            aT, hh = amin_T(cols)
            if aT is None:
                continue
            amin = aT + 5
            rk = preinj.rank(Xp)
            fixed = set(cols) | {1, 2, 4, 8}
            for e in range(0, target_pre - amin - rk + 1):
                for k in range(rk, target_pre - amin - e + 1):
                    B = patterns(Xp, avail, fixed, k, wild=len(hh) + e)
                    if B:
                        hits += 1
                        print(json.dumps(dict(helpers=list(hs), M=list(M), amin=amin, e=e, k=k,
                                              pre=amin + e + k, reach=list(B), wild=len(hh) + e)), flush=True)
                        if best is None or amin + e + k < best:
                            best = amin + e + k
                        break
        print(json.dumps(dict(top=list(hs), best_pre=best)), flush=True)
    print(json.dumps(dict(done=True, hits=hits)), flush=True)


if __name__ == '__main__':
    main()
