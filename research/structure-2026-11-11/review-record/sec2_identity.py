"""Section 2 test: identity (2.1) G = 2n + x - S on every recorded circuit of a map meeting the hypotheses.

Per map: square, all rows odd, all columns odd, and no nonzero relation of weight <= 4 among the 2n
boundary vectors (units and rows): checked as distinct nonzero, no sum of two in the set, all pairwise
sums distinct. Per circuit: normalisation (distinct nonzero masks over inputs+gates, every gate used or
an output, each row carried by exactly one signal, a gate). Then, from the definitions only:
  points = odd signals, vectors = even signals (labels: all even gate signals);
  edges: producer a+b (odd+odd): edge a-b labelled by the result; translate (odd+even): edge
         odd operand - result labelled by the even operand;
  represented label: has an edge with both ends boundary; missing: every other even signal
         (including even signals that label no edge), q = #missing;
  e_l = #edges with label l; r_p = #edges helper p - boundary with represented label;
  z_r = #helper-helper edges with represented label;
  S = sum_p (r_p - 2) + z_r + sum_missing (e_l - 1).
Compare with G - 2n - x. Also report x, y, h, h+y, S, the split of S, q0 = even signals labelling
no edge, max r_p, and check: simple graph, each label a matching, <= 1 B-B edge per label.
"""
import sys
from collections import Counter, defaultdict

from lib import all_circuits, load, par, wt


def hypotheses(rows, n):
    if len(rows) != n:
        return False, "not square"
    if not all(par(r) for r in rows):
        return False, "even row"
    for i in range(n):
        if not sum((r >> i) & 1 for r in rows) & 1:
            return False, "even column"
    B = [1 << i for i in range(n)] + rows
    if len(set(B)) != len(B) or 0 in B:
        return False, "relation of weight <= 2"
    s = set(B)
    pairs = set()
    for i in range(len(B)):
        for j in range(i + 1, len(B)):
            v = B[i] ^ B[j]
            if v in s:
                return False, "relation of weight 3"
            if v in pairs:
                return False, "relation of weight 4"
            pairs.add(v)
    return True, "ok"


def normalised(n, gates, outs, vals, rows):
    names = [k for k in vals if k not in {g[0] for g in gates}] + [g[0] for g in gates]
    masks = [vals[k] for k in names]
    if len(set(masks)) != len(masks) or 0 in masks:
        return False, "duplicate or zero mask"
    used = Counter()
    for o, a, b in gates:
        used[a] += 1
        used[b] += 1
    outset = set(outs)
    for o, _, _ in gates:
        if not used[o] and o not in outset:
            return False, f"unused gate {o}"
    gate_names = {g[0] for g in gates}
    if not all(o in gate_names for o in outs):
        return False, "output not a gate"
    return True, "ok"


def analyse(n, gates, outs, vals):
    outset = set(outs)
    gate_names = {g[0] for g in gates}
    inputs = [k for k in vals if k not in gate_names]
    boundary = set(inputs) | outset
    odd = {k for k in vals if par(vals[k])}
    helpers = {g for g in gate_names if g in odd and g not in outset}
    x = y = 0
    edges = []  # (u, v, label)
    for o, a, b in gates:
        pa, pb = a in odd, b in odd
        if pa and pb:
            x += 1
            edges.append((a, b, o))
        elif not pa and not pb:
            y += 1
        else:
            od, ev = (a, b) if pa else (b, a)
            edges.append((od, o, ev))
    h = len(helpers)
    G = len(gates)
    assert G == n + x + y + h
    labels = [g for g in gate_names if g not in odd]
    # checks of Lemma 4.1
    pairset = Counter(frozenset((u, v)) for u, v, _ in edges)
    simple = all(c == 1 for c in pairset.values()) and all(u != v for u, v, _ in edges)
    at = defaultdict(Counter)
    for u, v, l in edges:
        at[l][u] += 1
        at[l][v] += 1
    matching = all(c == 1 for l in at for c in at[l].values())
    bb = Counter(l for u, v, l in edges if u in boundary and v in boundary)
    one_bb = all(c <= 1 for c in bb.values())
    represented = {l for l in labels if bb[l] >= 1}
    missing = [l for l in labels if l not in represented]
    e = Counter(l for _, _, l in edges)
    r = Counter()
    z_r = 0
    for u, v, l in edges:
        inb = (u in boundary) + (v in boundary)
        if inb == 1 and l in represented:
            r[u if u in helpers else v] += 1
        if inb == 0 and l in represented:
            z_r += 1
    s_help = sum(r[p] - 2 for p in helpers)
    s_miss = sum(e[l] - 1 for l in missing)
    S = s_help + z_r + s_miss
    q0 = sum(1 for l in labels if e[l] == 0)
    return dict(G=G, n=n, x=x, y=y, h=h, hy=h + y, S=S, s_help=s_help, z_r=z_r, s_miss=s_miss,
                q=len(missing), q0=q0, rmax=max([r[p] for p in helpers], default=0),
                full=sum(1 for p in helpers if r[p] == 3), simple=simple, matching=matching,
                one_bb=one_bb, identity=(G == 2 * n + x - S))


def main():
    total = good = 0
    for mapname, mat, circs in all_circuits():
        n0, gates0, outs0, vals0, rows = load(circs[0], mat)
        ok, why = hypotheses(rows, n0)
        if not ok:
            print(f"{mapname}: hypotheses fail ({why})")
            continue
        for circ in circs:
            n, gates, outs, vals, rows = load(circ, mat)
            nok, nwhy = normalised(n, gates, outs, vals, rows)
            a = analyse(n, gates, outs, vals)
            total += 1
            good += a["identity"]
            print(f"{circ.name}: norm={nok}({nwhy}) G={a['G']} n={n} x={a['x']} y={a['y']} h={a['h']} h+y={a['hy']} "
                  f"S={a['S']} [helpers {a['s_help']}, z_r {a['z_r']}, missing {a['s_miss']}] q={a['q']} q0={a['q0']} "
                  f"rmax={a['rmax']} full={a['full']} simple={a['simple']} matching={a['matching']} "
                  f"bb<=1={a['one_bb']} IDENTITY={'OK' if a['identity'] else 'FAIL'}")
    print(f"identity holds on {good} of {total} circuits of maps meeting the hypotheses")


if __name__ == "__main__":
    main()
