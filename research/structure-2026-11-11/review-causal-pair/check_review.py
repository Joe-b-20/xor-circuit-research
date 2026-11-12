"""Review CHECKS (not proofs) for causal-pair/REPORT.md.
1. Lemma 2 completeness on the forest premise: every 5-edge tree, every odd labelling
   (u_k or E_l), every assignment of B_0..B_3 to distinct paths of length 3 or 5 with the right sum;
   count cases with 9 independent formal relations AND all six fibre vertices distinct.
2. Examples (a), (b): does the VALUE SET admit an executable basis of the same size?
   (greedy closure: add any value that is a sum of two available values; closure is monotone,
   so greedy decides existence of an ordering in which each value is one XOR of earlier ones).
"""
import itertools, os, sys

def u(k): return 1 << k
def E(k): return 0b1111 ^ (1 << k)
ODD = [u(k) for k in range(4)] + [E(k) for k in range(4)]

TREES = {
    "path": [(0,1),(1,2),(2,3),(3,4),(4,5)],
    "spider221": [(2,1),(1,0),(2,3),(3,4),(2,5)],
    "spider311": [(3,2),(2,1),(1,0),(3,4),(3,5)],
    "doublestar": [(1,2),(1,0),(1,4),(2,3),(2,5)],
    "spider2111": [(2,1),(1,0),(2,3),(2,4),(2,5)],
    "star": [(0,1),(0,2),(0,3),(0,4),(0,5)],
}

def rank(rows):
    basis = {}
    for r in rows:
        while r:
            low = r & -r
            if low in basis: r ^= basis[low]
            else: basis[low] = r; break
    return len(basis)

def tree_paths(edges):
    adj = {}
    for i,(a,b) in enumerate(edges):
        adj.setdefault(a, []).append((b,i)); adj.setdefault(b, []).append((a,i))
    out = []
    for x, y in itertools.combinations(sorted(adj), 2):
        # BFS path
        prev = {x: None}; st = [x]
        while st:
            v = st.pop()
            for w, i in adj[v]:
                if w not in prev: prev[w] = (v, i); st.append(w)
        P = []; v = y
        while prev[v]: v, i = prev[v]; P.append(i)
        if len(P) in (3, 5): out.append((x, y, frozenset(P)))
    return out

def part1():
    total = bad = 0
    per = {}
    for tname, edges in TREES.items():
        paths = tree_paths(edges)
        for labs in itertools.product(range(8), repeat=5):
            L = [ODD[i] for i in labs]
            cand = {l: [] for l in range(4)}
            for x, y, P in paths:
                s = 0
                for i in P: s ^= L[i]
                for l in range(4):
                    if s == E(l): cand[l].append((x, y))
            if any(not cand[l] for l in range(4)): continue
            # vertex values (root 0 value 0 in s-part; same omega)
            val = {edges[0][0]: 0}
            changed = True
            while changed:
                changed = False
                for i,(a,b) in enumerate(edges):
                    if a in val and b not in val: val[b] = val[a] ^ L[i]; changed = True
                    elif b in val and a not in val: val[a] = val[b] ^ L[i]; changed = True
            dup = len(set(val.values())) < 6
            # element bits: vertices 0..5, w'k 6..9, B_l 10..13
            def lab_el(v):
                return 6 + v.bit_length() - 1 if bin(v).count("1") == 1 else 10 + (0b1111 ^ v).bit_length() - 1
            ent = [(1 << a) | (1 << b) | (1 << lab_el(L[i])) for i,(a,b) in enumerate(edges)]
            for choice in itertools.product(*[cand[l] for l in range(4)]):
                rows = ent + [(1 << x) | (1 << y) | (1 << (10 + l)) for l,(x,y) in enumerate(choice)]
                rk = rank(rows)
                total += 1
                key = tname
                per.setdefault(key, [0, 0])[0] += 1
                if rk == 9 and not dup:
                    bad += 1; per[key][1] += 1
                    if bad <= 5: print("  COUNTEREXAMPLE?", tname, [bin(x) for x in L], choice)
    print("part1: configurations (tree, labelling, exit choice) =", total, "; with rank 9 and distinct vertices =", bad)
    for k, v in per.items(): print("   %-11s configs %d, rank-9-and-distinct %d" % (k, v[0], v[1]))

def closure_ok(known, V):
    have = set(known); rest = set(V) - have; steps = 0
    progress = True
    while rest and progress:
        progress = False
        for v in list(rest):
            if any((v ^ a) in have and (v ^ a) != a for a in have):
                have.add(v); rest.discard(v); steps += 1; progress = True
    return not rest, steps

def part2():
    om = 1 << 4
    # (a): values from loop_examples_check.example_a
    x = {"x0": om}
    x["x1"] = om ^ u(1); x["x2"] = x["x1"] ^ E(0); x["x3"] = x["x2"] ^ E(1)
    x["x4"] = x["x3"] ^ u(2); x["x5"] = x["x4"] ^ u(3); x["y1"] = x["x2"] ^ u(1); x["y2"] = x["y1"] ^ u(0)
    V = [x[k] for k in ["x1","x2","x3","x4","x5","y1","y2"]] + [E(0), E(1)]
    known = [om] + [u(k) for k in range(4)]
    ok, n = closure_ok(known, V)
    print("part2 (a): value set of 9 admits an executable basis with 9 gates:", ok, "(gates", n, ")")
    HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(HERE, "..", "causal-pair"))
    import loop_examples_check as L
    import io, contextlib
    for m in (3, 4, 5):
        # rebuild values of (b) by running example_b silently and capturing via monkeypatch of check
        cap = {}
        def fake(rels, known, values, label, cap=cap):
            cap["rels"], cap["known"], cap["values"] = rels, known, values
            return True, False
        orig = L.check; L.check = fake
        with contextlib.redirect_stdout(io.StringIO()): L.example_b(m)
        L.check = orig
        kn = [cap["values"][k] for k in cap["known"]]
        unk = sorted({e for t in cap["rels"] for e in t} - set(cap["known"]))
        Vb = [cap["values"][e] for e in unk]
        ok, n = closure_ok(kn, Vb)
        # executable original: t_j = s0_j + s2_j
        rels2 = [t for t in cap["rels"] if not (t[2].startswith("t_"))] + \
                [("s0_%d" % j, "s2_%d" % j, "t_%d" % j) for j in range(m)]
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            det, exe = orig(rels2, cap["known"], cap["values"], "orig")
        print("part2 (b) m=%d: |V| = %d, greedy executable basis of size |V|: %s; Design A wiring determined %s executable %s"
              % (m, len(Vb), ok and n == len(Vb), det, exe))

if __name__ == "__main__":
    part2()
    part1()
