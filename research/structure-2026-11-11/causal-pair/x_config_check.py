"""CHECK (not a proof): configuration (X) of pair/PROOF.md, order-free.

For every label pattern that the hand derivation leaves in the path case and in the
spider case (all index choices, i.e. all instantiations of the parametrised cases),
build the five entry relations and four exit relations of the mirror T, and report:
  - that every relation holds as a vector identity (values consistent),
  - whether two fibre vertices coincide in value (distinctness),
  - the F_2 rank of the nine relations as formal vectors, and one explicit dependency,
  - the borrowing matrix N (E-labelled edge e -> E-labelled edges of the path of B_l(e)),
    det(I + N) over F_2, and whether N is acyclic (necessary for an executable order).
Signals are (omega | s) in F_2^4 x F_2^4, written as two 4-bit strings.
"""
import itertools

def u(k):
    return tuple(1 if i == k else 0 for i in range(4))

def E(k):
    return tuple(0 if i == k else 1 for i in range(4))

def add(x, y):
    return tuple(a ^ b for a, b in zip(x, y))

ZERO = (0, 0, 0, 0)
ONES = (1, 1, 1, 1)

def name(v):
    if sum(v) == 1:
        return "u%d" % v.index(1)
    if sum(v) == 3:
        return "E%d" % v.index(0)
    return "".join(map(str, v))

def rank_and_dep(rows):
    """rows: list of 0/1 lists. Return rank and one nonempty dependency (index set) if any."""
    n = len(rows)
    work = [(list(r), {i}) for i, r in enumerate(rows)]
    basis = []  # (pivot, row, combo)
    dep = None
    for r, combo in work:
        r = r[:]
        combo = set(combo)
        for piv, br, bc in basis:
            if r[piv]:
                r = [a ^ b for a, b in zip(r, br)]
                combo ^= bc
        if any(r):
            basis.append((r.index(1), r, combo))
        elif dep is None:
            dep = sorted(combo)
    return len(basis), dep, dep is None

def f2_det(M):
    M = [row[:] for row in M]
    n = len(M)
    for c in range(n):
        p = next((r for r in range(c, n) if M[r][c]), None)
        if p is None:
            return 0
        M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r != c and M[r][c]:
                M[r] = [a ^ b for a, b in zip(M[r], M[c])]
    return 1

def acyclic(nodes, succ):
    state = {}
    def dfs(x):
        state[x] = 1
        for y in succ[x]:
            if state.get(y) == 1:
                return False
            if y not in state and not dfs(y):
                return False
        state[x] = 2
        return True
    return all(dfs(x) for x in nodes if x not in state)

def analyse(tag, edges, labels, paths):
    """edges: list of (parent, child) vertex names, edge i = edges[i-1]; root = 'r'.
    labels: dict edge index -> label vector (u_k or E_l).
    paths: list of 4 edge-index sets (the exit paths P_i)."""
    omega = (1, 0, 0, 0)
    val = {"r": (omega, ZERO)}
    # tree: edges listed so that parent is known before child
    for i, (p, c) in enumerate(edges, 1):
        val[c] = (omega, add(val[p][1], labels[i]))
    # adjacency to compute path endpoints
    def endpoints(P):
        deg = {}
        for i in P:
            for x in edges[i - 1]:
                deg[x] = deg.get(x, 0) + 1
        ends = [x for x, d in deg.items() if d == 1]
        assert len(ends) == 2, (tag, P)
        return ends
    out = ["== %s: labels %s" % (tag, " ".join("%d:%s" % (i, name(labels[i])) for i in sorted(labels)))]
    # distinctness of fibre vertices
    verts = list(val)
    dup = [(a, b) for a, b in itertools.combinations(verts, 2) if val[a] == val[b]]
    # exits
    Bval = {}
    exits = []
    for P in paths:
        s = ZERO
        for i in P:
            s = add(s, labels[i])
        x, y = endpoints(P)
        assert add(val[x][1], val[y][1]) == s
        assert sum(s) == 3, (tag, P, s)
        l = s.index(0)
        assert l not in Bval, (tag, "two exits with the same value")
        Bval[l] = sorted(P)
        exits.append((x, y, "B%d" % l, sorted(P)))
    assert sorted(Bval) == [0, 1, 2, 3]
    out.append("   exits: " + ", ".join("B%d=path%s" % (l, Bval[l]) for l in sorted(Bval)))
    out.append("   duplicate fibre vertices: %s" % (dup if dup else "none"))
    # element list and formal relations
    elems = ["r"] + [c for _, c in edges] + ["w'%d" % k for k in range(4)] + ["B%d" % l for l in range(4)]
    idx = {e: i for i, e in enumerate(elems)}
    def value(e):
        if e in val:
            return val[e]
        if e.startswith("w'"):
            return (ZERO, u(int(e[2])))
        return (ZERO, E(int(e[1])))
    rels, rnames = [], []
    for i, (p, c) in enumerate(edges, 1):
        lab = labels[i]
        le = ("w'%d" % lab.index(1)) if sum(lab) == 1 else ("B%d" % lab.index(0))
        trip = [p, le, c]
        rels.append(trip); rnames.append("entry%d{%s}" % (i, ",".join(trip)))
    for x, y, b, P in exits:
        trip = [x, y, b]
        rels.append(trip); rnames.append("exit_%s{%s}" % (b, ",".join(trip)))
    for trip in rels:  # vector identities
        s = (ZERO, ZERO)
        for e in trip:
            v = value(e)
            s = (add(s[0], v[0]), add(s[1], v[1]))
        assert s == (ZERO, ZERO), (tag, trip)
    rows = []
    for trip in rels:
        row = [0] * len(elems)
        for e in trip:
            row[idx[e]] ^= 1
        rows.append(row)
    rk, dep, indep = rank_and_dep(rows)
    out.append("   all 9 relations hold as vector identities; F_2 rank of the 9 formal relations: %d" % rk)
    if dep:
        out.append("   dependency (formal sum zero): " + " + ".join(rnames[j] for j in dep))
    # borrowing matrix
    Eedges = [i for i in sorted(labels) if sum(labels[i]) == 3]
    N = [[1 if f in Bval[labels[e].index(0)] else 0 for f in Eedges] for e in Eedges]
    IN = [[(1 if a == b else 0) ^ N[a][b] for b in range(len(Eedges))] for a in range(len(Eedges))]
    succ = {e: [f for j, f in enumerate(Eedges) if N[Eedges.index(e)][j]] for e in Eedges}
    out.append("   E-labelled edges %s, N rows %s, det(I+N) over F_2 = %d, N acyclic: %s"
               % (Eedges, N, f2_det(IN), acyclic(Eedges, succ)))
    return out, (rk, bool(dup), f2_det(IN), acyclic(Eedges, succ))

PATH = [("r", "v1"), ("v1", "v2"), ("v2", "v3"), ("v3", "v4"), ("v4", "v5")]
PATH_P = [{1, 2, 3, 4, 5}, {1, 2, 3}, {2, 3, 4}, {3, 4, 5}]
# spider legs 2,2,1 at centre c = root: 1=c-a, 2=a-a', 3=c-b, 4=b-b', 5=c-d
SPIDER = [("r", "a"), ("a", "a2"), ("r", "b"), ("b", "b2"), ("r", "d")]
SPIDER_P = [{1, 2, 3}, {1, 2, 5}, {1, 3, 4}, {3, 4, 5}]

def main():
    summary = {}
    for perm in itertools.permutations(range(4)):
        a, m, x, y = perm
        cases = {
            "path-1a": {1: u(x), 2: u(m), 3: u(a), 4: E(m), 5: u(a)},
            "path-1b": {1: u(x), 2: u(m), 3: u(a), 4: E(m), 5: E(y)},
            "path-3":  {1: E(a), 2: u(m), 3: u(a), 4: E(m), 5: E(x)},
        }
        for tag, lab in cases.items():
            for rev in (False, True):
                L = {i: lab[6 - i] for i in lab} if rev else lab
                t = tag + ("-reversed" if rev else "")
                o, res = analyse(t + " (a,m,x,y)=%s" % (perm,), PATH, L, PATH_P)
                summary.setdefault(t, set()).add(res)
                if perm == (0, 1, 2, 3):
                    print("\n".join(o))
        m, p, r, z = perm  # spider indices
        scases = {
            "spider-S1 (p=m, l5=u_z)": {1: E(m), 2: u(m), 3: u(m), 4: u(r), 5: u(z)},
            "spider-S2 (p!=m, l5=u_p)": {1: E(m), 2: u(p), 3: u(m), 4: u(r), 5: u(p)},
            "spider-S3 (p!=m, l5=E_r)": {1: E(m), 2: u(p), 3: u(m), 4: u(r), 5: E(r)},
        }
        for tag, lab in scases.items():
            o, res = analyse(tag + " (m,p,r,z)=%s" % (perm,), SPIDER, lab, SPIDER_P)
            summary.setdefault(tag, set()).add(res)
            if perm == (0, 1, 2, 3):
                print("\n".join(o))
    print("\nSummary over all 24 index choices per case: (rank of 9 relations, duplicate vertex, det(I+N), N acyclic)")
    for t, s in summary.items():
        print("  %-28s %s" % (t, sorted(s)))

if __name__ == "__main__":
    main()
