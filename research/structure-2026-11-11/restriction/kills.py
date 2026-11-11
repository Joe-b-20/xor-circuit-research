"""Dead-gate counts of single restrictions and of full merge sequences on the recorded MixColumns circuits.

Usage: python3 research/structure-2026-11-11/restriction/kills.py
Observed facts about specific circuits only (88, 89, 97 gates); not statements about all circuits.
"""
from collections import Counter

from common import N, circuit_masks, mc_circuits, read_circuit, read_matrix, wt

M = read_matrix()


def single_restrictions(masks):
    """D(lam) = #{gates g : w_g + lam in {0} U {masks of earlier signals}} for every lam with D > 0."""
    cnt = Counter()
    for g in range(N, len(masks)):
        cnt[masks[g]] += 1
        for s in range(g):
            cnt[masks[g] ^ masks[s]] += 1
    return cnt


def block_value(w, blocks):
    v = 0
    for k, b in enumerate(blocks):
        if wt(w & b) & 1:
            v |= 1 << k
    return v


def live_set(masks, blocks):
    seen = {0} | {1 << k for k in range(len(blocks))}
    live, val = [], {}
    for g in range(N, len(masks)):
        v = block_value(masks[g], blocks)
        val[g] = v
        if v not in seen:
            seen.add(v)
            live.append(g)
    return live, val


def nonunit_rows(blocks):
    vals = {block_value(r, blocks) for r in M}
    return {v for v in vals if wt(v) >= 2}


def merge_sequence(masks, ops, policy):
    """Follow the circuit itself (no re-minimisation); merge two blocks per step until no gate is live."""
    blocks = [1 << j for j in range(N)]
    live, val = live_set(masks, blocks)
    rows = nonunit_rows(blocks)
    steps = []
    while live:
        cands = [g for g in live if wt(val[g]) == 2]          # gates whose restricted value is e_A + e_B
        if policy == "first":
            choice = [live[0]]                                   # first live gate: always a 2-block value
            assert wt(val[live[0]]) == 2
        else:
            choice = cands
        best = None
        for g in choice:
            a, b = [k for k in range(len(blocks)) if val[g] >> k & 1]
            nb = [blk for k, blk in enumerate(blocks) if k not in (a, b)] + [blocks[a] | blocks[b]]
            nlive, nval = live_set(masks, nb)
            nrows = nonunit_rows(nb)
            D = len(live) - len(nlive)
            ell = len(rows) - len(nrows)
            key = (D - 1 - ell, D)
            if best is None or key > best[0]:
                best = (key, g, nb, nlive, nval, nrows, D, ell)
        _, g, blocks, live, val, rows, D, ell = best
        steps.append((D, ell))
    return steps, len(blocks)


def main():
    for path in mc_circuits():
        gates = read_circuit(path)
        names, masks, ops, idx = circuit_masks(gates)
        G = len(gates)
        assert all(r in set(masks) for r in M), "circuit does not compute M"
        fo = Counter()
        for o in ops[N:]:
            fo[o[0]] += 1
            fo[o[1]] += 1
        in_fo = Counter(fo[j] for j in range(N))
        first_layer = [g for g in range(N, len(masks)) if ops[g][0] < N and ops[g][1] < N]
        fl_fo = Counter(fo[g] for g in first_layer)
        cnt = single_restrictions(masks)
        by = lambda pred: max((d, lam) for lam, d in cnt.items() if pred(lam))
        print(f"== {path.name}: G={G}")
        print(f"  input gate-fan-out histogram {dict(sorted(in_fo.items()))};"
              f" first-layer gates {len(first_layer)}, their fan-out histogram {dict(sorted(fl_fo.items()))}")
        print(f"  max dead gates of one hyperplane restriction: any lam {by(lambda l: True)[0]},"
              f" wt1 (x_i:=0) {by(lambda l: wt(l) == 1)[0]}, wt2 (x_i:=x_j) {by(lambda l: wt(l) == 2)[0]},"
              f" even lam (keeps point 1) {by(lambda l: wt(l) % 2 == 0)[0]}")
        hist = Counter(cnt[1 << j] for j in range(N))
        print(f"  x_i:=0 dead-count histogram over the 32 inputs {dict(sorted(hist.items()))}")
        for policy in ("first", "greedy"):
            steps, c_f = merge_sequence(masks, ops, policy)
            excess = [D - 1 - ell for D, ell in steps]
            assert sum(D for D, _ in steps) == G
            assert G == 64 - c_f + sum(excess)
            print(f"  merge sequence ({policy:6s}): {len(steps)} steps, final blocks c_f={c_f},"
                  f" sum D = G, excess total {sum(excess)} = G-64+c_f;"
                  f" excess on step 1..5: {excess[:5]}; steps with ell=0: {sum(1 for _, l in steps if l == 0)}")


if __name__ == "__main__":
    main()
