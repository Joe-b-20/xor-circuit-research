"""Rank-connectivity experiments: does a fan-in-2 graph with fewer gates satisfy kappa(S,T) >= rank M[T,S]?

Usage: python3 research/structure-2026-11-11/restriction/connectivity.py [seed]
Starts from the graph of the recorded 88-gate circuit, greedily deletes non-output gates (redirecting
their out-edges to one operand) while a test panel of (S,T) pairs stays satisfied, then re-validates
the pruned graph on a larger independent panel. OBSERVED evidence only: no panel covers all 2^64 pairs.
"""
import random
import sys
from itertools import combinations

from common import MC_DIR, N, circuit_masks, rank, read_circuit, read_matrix, wt

M = read_matrix()
BYTE = [sum(1 << (8 * b + k) for k in range(8)) for b in range(4)]


def sub_rank(S, T):
    """rank of M[T,S]; S, T int masks over inputs / outputs."""
    return rank([M[o] & S for o in range(N) if T >> o & 1])


class Graph:
    """Vertices 0..N-1 inputs; gates have exactly two in-neighbours; out_of[o] = vertex carrying output o."""

    def __init__(self, preds, out_of):
        self.preds = dict(preds)          # gate vertex -> (a, b)
        self.out_of = list(out_of)

    def gates(self):
        return len(self.preds)

    def topo(self):
        order, seen = list(range(N)), set(range(N))
        rest = dict(self.preds)
        while rest:
            ready = [v for v, (a, b) in rest.items() if a in seen and b in seen]
            if not ready:
                return None
            for v in ready:
                order.append(v)
                seen.add(v)
                del rest[v]
        return order

    def reach_inputs(self):
        order = self.topo()
        r = {}
        for v in order:
            r[v] = (1 << v) if v < N else r[self.preds[v][0]] | r[self.preds[v][1]]
        return r

    def kappa(self, S, T, need):
        """Max number of vertex-disjoint S->T paths (Edmonds-Karp on the node-split network;
        stops once `need` is reached)."""
        verts = list(range(N)) + sorted(self.preds)
        ix = {v: k for k, v in enumerate(verts)}
        V = len(verts)
        src, snk = 2 * V, 2 * V + 1
        head, cap, adj = [], [], [[] for _ in range(2 * V + 2)]

        def arc(u, w):
            adj[u].append(len(head)); head.append(w); cap.append(1)
            adj[w].append(len(head)); head.append(u); cap.append(0)

        for v in verts:
            arc(2 * ix[v], 2 * ix[v] + 1)
        for v, (a, b) in self.preds.items():
            arc(2 * ix[a] + 1, 2 * ix[v])
            arc(2 * ix[b] + 1, 2 * ix[v])
        for i in range(N):
            if S >> i & 1:
                arc(src, 2 * ix[i])
        for o in range(N):
            if T >> o & 1:
                arc(2 * ix[self.out_of[o]] + 1, snk)
        flow = 0
        while flow < need:
            par = [-1] * (2 * V + 2)
            par[src] = -2
            q = [src]
            for u in q:
                if u == snk:
                    break
                for e in adj[u]:
                    w = head[e]
                    if cap[e] and par[w] == -1:
                        par[w] = e
                        q.append(w)
            if par[snk] == -1:
                break
            w = snk
            while w != src:
                e = par[w]
                cap[e] -= 1
                cap[e ^ 1] += 1
                w = head[e ^ 1]
            flow += 1
        return flow


def from_circuit(path):
    gates = read_circuit(path)
    names, masks, ops, idx = circuit_masks(gates)
    preds = {g: ops[g] for g in range(N, len(masks))}
    pos = {m: i for i, m in enumerate(masks)}
    return Graph(preds, [pos[r] for r in M])


def check(g, panel, reach_only=False):
    r = g.reach_inputs()
    if r is None:
        return False, None
    for o in range(N):
        if M[o] & ~r[g.out_of[o]]:
            return False, ("reach", o)
    if reach_only:
        return True, None
    for k, (S, T, need) in enumerate(panel):
        if g.kappa(S, T, need) < need:
            return False, k
    return True, None


def make_panel(rng, n_random):
    panel = []
    bytesets = [sum(BYTE[b] for b in A) for k in range(1, 5) for A in combinations(range(4), k)]
    for S in bytesets:
        for T in bytesets:
            panel.append((S, T, sub_rank(S, T)))
    for _ in range(n_random):
        k = rng.randint(2, 20)
        S = sum(1 << i for i in rng.sample(range(N), k))
        T = sum(1 << i for i in rng.sample(range(N), rng.randint(2, 20)))
        panel.append((S, T, sub_rank(S, T)))
    for _ in range(n_random // 2):          # one input byte subset vs one output byte subset unions
        S = sum(1 << i for i in range(N) if rng.random() < 0.5)
        T = BYTE[rng.randrange(4)] | BYTE[rng.randrange(4)]
        panel.append((S, T, sub_rank(S, T)))
    return [p for p in panel if p[2] > 0]


def prune(g, panel, rng):
    order = list(g.preds)
    outs = set(g.out_of)
    rng.shuffle(order)
    hard = []                      # panel indices that rejected something, tested first
    changed = True
    while changed:
        changed = False
        for v in list(order):
            if v not in g.preds or v in outs:
                continue
            a, b = g.preds[v]
            users = [w for w, p in g.preds.items() if v in p]
            for keep in (a, b):
                if any(keep in g.preds[w] for w in users):
                    continue
                new = {w: p for w, p in g.preds.items() if w != v}
                for w in users:
                    p = new[w]
                    new[w] = (keep if p[0] == v else p[0], keep if p[1] == v else p[1])
                cand = Graph(new, g.out_of)
                ok, why = check(cand, [panel[k] for k in hard], reach_only=False)
                if ok:
                    ok, why = check(cand, panel)
                    if not ok and isinstance(why, int) and why not in hard:
                        hard.append(why)
                if ok:
                    g = cand
                    changed = True
                    break
    return g


def descendants(g, v):
    succ = {}
    for w, (a, b) in g.preds.items():
        succ.setdefault(a, []).append(w)
        succ.setdefault(b, []).append(w)
    out, stack = {v}, [v]
    while stack:
        u = stack.pop()
        for w in succ.get(u, ()):
            if w not in out:
                out.add(w)
                stack.append(w)
    return out


def prune_dominate(g, panel, rng):
    """Delete a non-output gate v; every user of v gets instead a vertex w whose input-reach contains
    that of v (w not a descendant of v): reachability can only grow, connectivity is re-tested."""
    outs = set(g.out_of)
    hard = []
    changed = True
    stats = {"tried": 0, "no_cand": 0, "reject": 0}
    while changed:
        changed = False
        order = [v for v in g.preds if v not in outs]
        rng.shuffle(order)
        for v in order:
            reach = g.reach_inputs()
            desc = descendants(g, v)
            users = [w for w, p in g.preds.items() if v in p]
            cands = [w for w in reach if w not in desc and reach[w] & reach[v] == reach[v]]
            stats["no_cand"] += not cands
            rng.shuffle(cands)
            for w in cands[:12]:
                stats["tried"] += 1
                if any(w in g.preds[u] for u in users):
                    continue
                new = {u: p for u, p in g.preds.items() if u != v}
                for u in users:
                    p = new[u]
                    new[u] = (w if p[0] == v else p[0], w if p[1] == v else p[1])
                cand = Graph(new, g.out_of)
                if cand.topo() is None:
                    continue
                ok, why = check(cand, [panel[k] for k in hard])
                if ok:
                    ok, why = check(cand, panel)
                    if not ok and isinstance(why, int) and why not in hard:
                        hard.append(why)
                if ok:
                    g = cand
                    changed = True
                    break
                stats["reject"] += 1
            if changed:
                break
    print("dominating-vertex moves:", stats, "hard panel size", len(hard))
    return g


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    rng = random.Random(seed)
    g0 = from_circuit(MC_DIR / "aes-mixcolumns-xor88-depth5.circ.txt")
    panel = make_panel(rng, 300)
    ok, _ = check(g0, panel)
    print(f"88-gate circuit graph satisfies the {len(panel)}-pair panel: {ok}")
    g = prune(g0, panel, rng)
    g = prune_dominate(g, panel, rng)
    print(f"pruned graph: {g.gates()} gates (non-output gates {g.gates() - N})")
    val = make_panel(random.Random(10 ** 6 + seed), 2000)
    ok, why = check(g, val)
    print(f"validation on an independent {len(val)}-pair panel: {ok} {why if not ok else ''}")
    # all |S| = |T| = 2 pairs with rank 2 (exhaustive for this size)
    bad = 0
    tested = 0
    pairs = list(combinations(range(N), 2))
    for i1, i2 in pairs:
        S = (1 << i1) | (1 << i2)
        for o1, o2 in pairs:
            T = (1 << o1) | (1 << o2)
            need = sub_rank(S, T)
            if need == 2:
                tested += 1
                if g.kappa(S, T, 2) < 2:
                    bad += 1
    print(f"all 2x2 requirements of rank 2: {tested} tested, {bad} violated")
    print("pruned graph predecessors:", sorted(g.preds.items()))
    print("outputs carried by:", g.out_of)


if __name__ == "__main__":
    main()
