"""Pair-proof review, items 3 and 7: finite checks of Lemma B and of the forest classification.
Lemma B: over every ordered basis (labels) of F_2^4, compute zeta_j directly as columns of l_i = Phi^-1 p_i
(no dual-basis argument) and check every statement.  Forests: all labelled forests with five edges on
up to 10 vertices, counted up to isomorphism by brute force over edge sets; count 3-edge paths directly.
A finite check, standard library only."""
import itertools
from collections import Counter

def pc(v): return bin(v).count("1")
U = [1 << k for k in range(4)]
P = [U[(i - 1) % 4] ^ U[i] for i in range(4)]
E = [15 ^ U[i] for i in range(4)]

def solve(labels, x):
    # coefficients c with sum c_j labels_j = x
    for c in range(16):
        s = 0
        for j in range(4):
            if c >> j & 1: s ^= labels[j]
        if s == x: return c
    return None

nb = 0; bad = []
for labels in itertools.permutations(range(1, 16), 4):
    # basis?
    span = {0}
    for l in labels: span |= {s ^ l for s in span}
    if len(span) != 16: continue
    nb += 1
    l = [solve(labels, P[i]) for i in range(4)]
    zeta = [sum(((l[i] >> j) & 1) << i for i in range(4)) for j in range(4)]
    o = sum(pc(x) % 2 for x in labels)
    if any(pc(z) % 2 for z in zeta): bad.append(("odd zeta", labels))
    cnt = len({z for z in zeta if z})
    if cnt != (3 if o <= 2 else 4): bad.append(("count", labels, o, zeta))
    if o == 4:
        if zeta[0] ^ zeta[1] ^ zeta[2] ^ zeta[3]: bad.append(("sum", labels))
        for tri in itertools.combinations(zeta, 3):
            sp = {0}
            for z in tri: sp |= {s ^ z for s in sp}
            if len(sp) != 8: bad.append(("dep", labels))
        forb = {0} | set(U) | set(E) | set(zeta)
        for j, k in itertools.combinations(range(4), 2):
            if zeta[j] ^ zeta[k] in forb: bad.append(("pair", labels, j, k))
print("Lemma B: ordered bases checked:", nb, " failures:", len(bad), bad[:3])
o4 = set()
for labels in itertools.permutations(range(1, 16), 4):
    if all(pc(x) % 2 for x in labels):
        span = {0}
        for l in labels: span |= {s ^ l for s in span}
        if len(span) == 16:
            l = [solve(labels, P[i]) for i in range(4)]
            o4.add(frozenset(sum(((l[i] >> j) & 1) << i for i in range(4)) for j in range(4)))
print("o=4: distinct zeta sets:", sorted(sorted(format(z, "04b")[::-1] for z in s) for s in o4))

# forests with 5 edges
def paths3(edges):
    adj = Counter()
    for a, b in edges: adj[a] += 1; adj[b] += 1
    return sum((adj[a] - 1) * (adj[b] - 1) for a, b in edges)

def canon(edges):
    vs = sorted({v for e in edges for v in e})
    best = None
    for perm in itertools.permutations(range(len(vs))):
        mp = dict(zip(vs, perm))
        key = tuple(sorted(tuple(sorted((mp[a], mp[b]))) for a, b in edges))
        if best is None or key < best: best = key
    return best

def is_forest(edges, n):
    par = list(range(n))
    def f(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    for a, b in edges:
        ra, rb = f(a), f(b)
        if ra == rb: return False
        par[ra] = rb
    return True

# direct path count by enumeration of simple paths with 3 edges (as edge sets)
def paths3_direct(edges):
    adj = {}
    for idx, (a, b) in enumerate(edges):
        adj.setdefault(a, []).append((b, idx)); adj.setdefault(b, []).append((a, idx))
    S = set()
    def dfs(v, used, seen):
        if len(used) == 3: S.add(frozenset(used)); return
        for w, i in adj.get(v, []):
            if w not in seen: dfs(w, used + [i], seen | {w})
    for v in adj: dfs(v, [], {v})
    return len(S)

trees, forests = {}, {}
# trees on 6 vertices: Pruefer sequences
for seq in itertools.product(range(6), repeat=4):
    deg = [1] * 6
    for x in seq: deg[x] += 1
    s = list(seq); edges = []
    for x in s:
        leaf = min(i for i in range(6) if deg[i] == 1)
        edges.append((leaf, x)); deg[leaf] -= 1; deg[x] -= 1
    u, v = [i for i in range(6) if deg[i] == 1]
    edges.append((u, v))
    trees.setdefault(canon(edges), edges)
print("trees with 5 edges:", len(trees))
for k, e in trees.items():
    assert paths3(e) == paths3_direct(e)
    print("   degrees", sorted(Counter(v for ed in e for v in ed).values(), reverse=True), "3-edge paths", paths3(e))
# disconnected forests: union of trees with edge counts summing to 5, at least two nontrivial parts
mx = 0
for n in range(7, 11):
    allE = list(itertools.combinations(range(n), 2))
for parts in [(4, 1), (3, 2), (3, 1, 1), (2, 2, 1), (2, 1, 1, 1), (1, 1, 1, 1, 1)]:
    pass
# brute force: all 5-edge forests on 8 vertices with >= 2 components having edges (8 vertices suffice for 2 comps with 5 edges: 7)
n = 8
allE = list(itertools.combinations(range(n), 2))
seen = set()
for es in itertools.combinations(allE, 5):
    if not is_forest(es, n): continue
    vs = {v for e in es for v in e}
    if len(vs) == 6: continue  # connected (tree)
    c = paths3_direct(es)
    mx = max(mx, c)
print("max 3-edge paths in a disconnected 5-edge forest:", mx)
