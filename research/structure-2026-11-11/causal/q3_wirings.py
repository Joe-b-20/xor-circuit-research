"""Inspection of ONE object: the value set of the recorded 28-gate circuit for Q_3.

usage: python3 q3_wirings.py [m FILE]      (default 3 ../rotation/circuits/q3_28.txt)

Prints
  1. the value set S (inputs and the gate values) in the sheet language;
  2. ALL collinear triples of S (not only the 28 gate triples), and whether they are gate triples;
  3. for every non-input element the triples containing it (the candidate "result" triples);
  4. the window closures: for sheet j the closure of the inputs inside the elements supported on the
     support of sheet j.  A block-monotone wiring needs every output of sheet j inside that closure;
  5. forced precedences: v must be created before w in EVERY wiring iff w is not in the closure of the
     inputs inside S minus {v};
  6. the number of wirings (acyclic choices of one result triple per non-input element), by exact
     counting over closure orders with memoisation on the set of created elements, and the minimum and
     maximum over all wirings of the charge sum and of the excess.

Nothing here searches over circuits or value sets: S is fixed.  Standard library only.
"""
import os
import sys
from functools import lru_cache
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "rotation"))
import qm  # noqa: E402

NAMES = {0b0011: "s0", 0b0110: "s1", 0b1100: "s2", 0b1001: "s3", 0b0101: "d0", 0b1010: "d1", 0b1111: "t",
         0b0001: "e0", 0b0010: "e1", 0b0100: "e2", 0b1000: "e3",
         0b1110: "E0", 0b1101: "E1", 0b1011: "E2", 0b0111: "E3"}


def main():
    m = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "rotation", "circuits", "q3_28.txt")
    n, gates = qm.read_circuit(path)
    targets = qm.rows(m)
    vals = qm.masks(n, gates)
    assert qm.computes(n, gates, targets)
    assert len(set(vals)) == len(vals) and 0 not in vals, "values must be distinct and nonzero"
    G = len(gates)
    S = list(vals)
    idx = {v: i for i, v in enumerate(S)}
    tix = {t: i for i, t in enumerate(targets)}

    def sup(v):
        return frozenset(j for j in range(m) if (v >> (4 * j)) & 15)

    def desc(v):
        return " ".join(f"{j}:{NAMES[(v >> (4 * j)) & 15]}" for j in range(m) if (v >> (4 * j)) & 15)

    def name(i):
        if i < n:
            return f"in({i % 4},{i // 4})"
        if S[i] in tix:
            k = tix[S[i]]
            return f"OUT({k % 4},{k // 4})"
        return f"g{i - n}"

    print(f"== 1. value set: {n} inputs + {G} gate values, all distinct")
    for i in range(n, n + G):
        a, b = gates[i - n]
        print(f"  {name(i):>9} [{desc(S[i]):<14}] blocks {sorted(sup(S[i]))}  recorded as {name(a)} + {name(b)}")

    # all triples
    triples = []
    for i, j in combinations(range(len(S)), 2):
        w = S[i] ^ S[j]
        k = idx.get(w)
        if k is not None and k > j:
            triples.append((i, j, k))
    gate_tr = set(tuple(sorted((n + gi, a, b))) for gi, (a, b) in enumerate(gates))
    print(f"\n== 2. collinear triples of S: {len(triples)} (gate triples: {len(gate_tr)})")
    for t in triples:
        tag = "gate" if t in gate_tr else "EXTRA"
        print(f"  {{{name(t[0])}, {name(t[1])}, {name(t[2])}}}  {tag}   "
              f"[{desc(S[t[0]])}] + [{desc(S[t[1]])}] = [{desc(S[t[2]])}]")
    # rank of all triples on the non-input coordinates
    rows = []
    for t in triples:
        r = 0
        for i in t:
            if i >= n:
                r |= 1 << (i - n)
        rows.append(r)
    print(f"  rank of all triples on the non-input coordinates: {qm.rank(rows)} (= G = {G} means cyclic)")

    by_elem = {i: [t for t in triples if i in t] for i in range(n, n + G)}
    print("\n== 3. candidate result triples per non-input element")
    for i in range(n, n + G):
        opts = []
        for t in by_elem[i]:
            o = [x for x in t if x != i]
            opts.append(f"{name(o[0])}+{name(o[1])}")
        print(f"  {name(i):>9}: {len(opts)}  " + " | ".join(opts))

    def closure(allowed):
        """closure of the inputs under triples, inside the index set `allowed` (inputs always allowed)."""
        have = set(range(n))
        changed = True
        while changed:
            changed = False
            for t in triples:
                inn = [x for x in t if x in have]
                if len(inn) == 2:
                    z = [x for x in t if x not in have][0]
                    if z in allowed:
                        have.add(z)
                        changed = True
        return have

    full = closure(set(range(n + G)))
    assert len(full) == n + G
    print("\n== 4. window closures (necessary condition for a block-monotone wiring)")
    for j in range(m):
        win = frozenset(sup(targets[4 * j]))
        allowed = {i for i in range(n + G) if sup(S[i]) <= win}
        cl = closure(allowed)
        outs = [idx[targets[4 * j + c]] for c in range(4)]
        miss = [name(o) for o in outs if o not in cl]
        print(f"  sheet {j}: window {sorted(win)}; elements supported in the window: {len(allowed) - sum(1 for i in allowed if i < n)} "
              f"non-inputs; closure reaches {len(cl) - n} of them; outputs NOT reachable inside the window: {miss}")
        print(f"     reachable: {[name(i) for i in sorted(cl) if i >= n]}")

    print("\n== 5. forced precedences (v before w in every wiring)")
    forced = {}
    for v in range(n, n + G):
        cl = closure(set(range(n + G)) - {v})
        after = [w for w in range(n, n + G) if w != v and w not in cl]
        forced[v] = after
        if after:
            print(f"  {name(v):>9} [{desc(S[v])}] precedes: {', '.join(name(w) for w in after)}")
    outs_all = [idx[t] for t in targets]
    print("  output -> output forced precedences across sheets:")
    for v in outs_all:
        for w in forced[v]:
            if w in outs_all and tix[S[v]] // 4 != tix[S[w]] // 4:
                print(f"     {name(v)} before {name(w)}")

    # 6. exact count of wirings.  A wiring = choice of result triple per non-input, acyclic.
    # Count pairs (wiring) by counting, for each wiring, exactly once: sum over wirings = number of
    # choice functions whose dependency graph is acyclic.  Use inclusion by "sources": dynamic programme
    # over the set C of created elements: f(C) = number of ways to wire the elements outside C given that
    # exactly C is available first is not well defined for DAG counting; instead enumerate choice
    # functions by depth-first search with incremental cycle check (the set is small).
    sys.setrecursionlimit(10000)
    order = sorted(range(n, n + G), key=lambda i: len(by_elem[i]))
    choice = {}
    stats = {"count": 0, "min_sum": 10 ** 9, "max_sum": -1, "min_exc": 10 ** 9, "max_exc": -1, "mono": 0}
    best = {}
    supp = [sup(v) for v in S]
    sheet_of_out = {idx[t]: k // 4 for t, k in tix.items()}

    def reaches(src, dst):
        """is dst an ancestor-or-equal of src under the partial choice (follow chosen operands)."""
        stack, seen = [src], set()
        while stack:
            x = stack.pop()
            if x == dst:
                return True
            if x in seen or x < n or x not in choice:
                continue
            seen.add(x)
            stack.extend(choice[x])
        return False

    def evaluate():
        anc = [set() for _ in range(m)]
        mono = True
        for o, j in sheet_of_out.items():
            stack, seen = [o], set()
            while stack:
                x = stack.pop()
                if x < n or x in seen:
                    continue
                seen.add(x)
                stack.extend(choice[x])
            anc[j] |= seen
            for g in seen:
                if not supp[g] <= supp[o]:
                    mono = False
        mu = [sum(1 for j in range(m) if j in supp[g] and g in anc[j]) for g in range(n, n + G)]
        return sum(mu), sum(max(0, x - 1) for x in mu), mono, [sum(1 for g in anc[j] if j in supp[g]) for j in range(m)]

    limit = int(os.environ.get("WIRING_LIMIT", "5000000"))

    def rec(k):
        if stats["count"] >= limit:
            return
        if k == len(order):
            stats["count"] += 1
            sm, ex, mono, per = evaluate()
            if mono:
                stats["mono"] += 1
            if sm < stats["min_sum"]:
                stats["min_sum"] = sm
                best["min_sum"] = (dict(choice), per)
            stats["max_sum"] = max(stats["max_sum"], sm)
            if ex < stats["min_exc"]:
                stats["min_exc"] = ex
                best["min_exc"] = (dict(choice), per, sm)
            stats["max_exc"] = max(stats["max_exc"], ex)
            return
        v = order[k]
        for t in by_elem[v]:
            a, b = [x for x in t if x != v]
            # adding v <- (a, b) must not close a cycle: v must not be an ancestor-or-equal of a or b
            if reaches(a, v) or reaches(b, v):
                continue
            choice[v] = (a, b)
            rec(k + 1)
            del choice[v]

    rec(0)
    print(f"\n== 6. wirings of S: {stats['count']}{' (limit reached)' if stats['count'] >= limit else ''}")
    print(f"  block-monotone wirings: {stats['mono']}")
    print(f"  charge sum over wirings: min {stats['min_sum']}, max {stats['max_sum']} (theorem: >= {10 * m})")
    print(f"  excess over wirings:     min {stats['min_exc']}, max {stats['max_exc']} (theorem: >= {10 * m - G})")
    if "min_exc" in best:
        ch, per, sm = best["min_exc"]
        print(f"  a wiring of minimum excess (charges per sheet {per}, sum {sm}):")
        for v in range(n, n + G):
            a, b = ch[v]
            rec_a, rec_b = gates[v - n]
            mark = "" if {a, b} == {rec_a, rec_b} else "   (differs from the recorded circuit)"
            print(f"     {name(v):>9} = {name(a)} + {name(b)}{mark}")


if __name__ == "__main__":
    main()
