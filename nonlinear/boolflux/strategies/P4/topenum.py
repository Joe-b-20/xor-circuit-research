"""P4: exhaustive enumeration of top layers in which every gate is a target or one of h chosen helpers.

If a top layer has exactly (#forms + h) gates and computes the forms, every gate's value is a form or a
helper (no repeated values in a minimal circuit), so the set of computed values is forms + helpers.
Feasibility of a value set S (computing exactly S, each element as the XOR of two earlier elements of
S u inputs) does not depend on order choices: the closure from the inputs decides it, and the
earliest possible level of each element is the fixpoint level(t) = 1 + min_{a^b=t} max(level a, level b).
So for given helpers, 'can the forms be computed in #forms + h gates with every form meeting its
deadline' is decided exactly.  [C] for: the top = XOR gates over the 8 inputs, values distinct.

    python3 topenum.py CIRC H GD  -> prints feasible helper sets (with the earliest levels)
"""
import itertools
import json
import sys

import block
import circ


def xmask(sym):
    return sum(1 << int(a[1:]) for a in sym[0])


def closure_levels(S):
    """S: set of non-input vectors. returns dict vector->earliest level, for the reachable ones."""
    lvl = {1 << i: 0 for i in range(8)}
    rest = set(S) - set(lvl)
    changed = True
    while changed:
        changed = False
        for t in list(rest) + [t for t in S if t in lvl and lvl[t] > 0]:
            best = lvl.get(t, 99)
            for a, la in list(lvl.items()):
                b = a ^ t
                if b in lvl and b != a:
                    l = 1 + max(la, lvl[b])
                    if l < best:
                        best = l
            if best < lvl.get(t, 99):
                lvl[t] = best
                rest.discard(t)
                changed = True
    return lvl


def top_spec(path, gd):
    gates = circ.read(path)
    s = circ.symbolic(gates)
    xs = {f'x{i}' for i in range(8)}
    topn = {g[1] for g in gates if g[0] != 'AND' and s[g[1]][0] <= xs}
    req = block.required([g for g in gates if g[1] not in topn], gd)
    forms = {}
    for op, o, ins in gates:
        if op == 'AND':
            for i in ins:
                if s[i][0] <= xs:
                    m = xmask(s[i])
                    forms[m] = min(forms.get(m, 99), req.get(i, 99))
    # x-linear signals read by non-top non-AND gates (middle injections)
    inj = {}
    for op, o, ins in gates:
        if op != 'AND' and o not in topn:
            for i in ins:
                if s[i][0] <= xs:
                    m = xmask(s[i])
                    inj[m] = min(inj.get(m, 99), req.get(i, 99))
    return gates, s, forms, inj


def main():
    path, H, gd = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    gates, s, forms, inj = top_spec(path, gd)
    F = {m: d for m, d in forms.items() if bin(m).count('1') > 1}
    print('forms', len(F), 'injections', {bin(m): d for m, d in inj.items()}, file=sys.stderr)
    allv = [v for v in range(1, 256) if bin(v).count('1') > 1 and v not in F]
    feas = []
    for hs in itertools.combinations(allv, H):
        S = set(F) | set(hs)
        lv = closure_levels(S)
        if all(t in lv for t in S) and all(lv[t] <= d for t, d in F.items()):
            feas.append((hs, {t: lv[t] for t in hs}, max(lv[t] for t in F)))
    print(json.dumps(dict(H=H, feasible=len(feas))))
    for hs, hl, mx in feas[:2000]:
        print(json.dumps(dict(helpers=[circ.fmt((frozenset(f'x{i}' for i in range(8) if h >> i & 1), 0)) for h in hs],
                              masks=list(hs), helper_levels=list(hl.values()), max_form_level=mx)))


if __name__ == '__main__':
    main()
