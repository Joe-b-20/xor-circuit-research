"""A cyclic system that is not a circuit for ANY choice of inputs (REPORT.md, Example 4).

Usage: python3 moore_example.py

Graph: a triangulated disc whose boundary 12-gon is wrapped three times around a 4-cycle
(a flag triangulation of the 2-complex "disc attached to a circle by a map of degree 3").
Vertices: a0..a3 (the circle), r0..r11 (a ring), o (centre): 17 vertices, 52 edges, 36 triangles.
S = the 52 edge vectors e_u + e_v (they span a space of dimension 16).  The script checks
  (1) the only 3-cliques of the graph are the 36 listed triangles, so the collinear triples of S are
      exactly these triangles;
  (2) over F_2 the 36 triangles have rank 36 = |S| - 16: S is a cyclic system of size 36
      (after any spanning tree is taken as the 16 unit vectors);
  (3) over F_3 the 36 oriented triangle equations g(uv) + g(vw) - g(uw) = 0 have rank 35 only.  So for
      every spanning tree T there is a nonzero g: edges -> Z/3 that vanishes on T and satisfies all
      triangle equations; the closure of T under triangles stays inside {g = 0}, hence is not S;
  (4) (sanity) the closure of 200 random spanning trees is a proper subset of S.
Consequence: with any spanning tree as inputs and the other 36 edges as target rows, L_cyc = 36 < L,
and the same holds after every re-encoding (every other choice of inputs among the 52 vectors).
"""
import random
from itertools import combinations


def rank_mod(rows, p):
    rows = [list(r) for r in rows]
    rank = 0
    ncol = len(rows[0])
    for c in range(ncol):
        piv = next((i for i in range(rank, len(rows)) if rows[i][c] % p), None)
        if piv is None:
            continue
        rows[rank], rows[piv] = rows[piv], rows[rank]
        inv = pow(rows[rank][c], -1, p)
        rows[rank] = [(x * inv) % p for x in rows[rank]]
        for i in range(len(rows)):
            if i != rank and rows[i][c] % p:
                f = rows[i][c]
                rows[i] = [(x - f * y) % p for x, y in zip(rows[i], rows[rank])]
        rank += 1
    return rank


def main():
    A = ["a%d" % i for i in range(4)]
    R = ["r%d" % i for i in range(12)]
    verts = A + R + ["o"]
    idx = {v: i for i, v in enumerate(verts)}
    tris = []
    for i in range(12):
        tris.append((A[i % 4], A[(i + 1) % 4], R[i]))
        tris.append((A[(i + 1) % 4], R[i], R[(i + 1) % 12]))
        tris.append((R[i], R[(i + 1) % 12], "o"))
    tris = [tuple(sorted(t, key=idx.get)) for t in tris]
    assert len(set(tris)) == 36 and all(len(set(t)) == 3 for t in tris)
    edges = sorted(set(tuple(sorted(e, key=idx.get)) for t in tris for e in combinations(t, 2)), key=lambda e: (idx[e[0]], idx[e[1]]))
    eidx = {e: i for i, e in enumerate(edges)}
    adj = {v: set() for v in verts}
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    cliques = [t for t in combinations(verts, 3) if t[1] in adj[t[0]] and t[2] in adj[t[0]] and t[2] in adj[t[1]]]
    print("vertices %d, edges %d, triangles %d, 3-cliques of the graph %d" % (len(verts), len(edges), len(tris), len(cliques)))
    assert sorted(cliques) == sorted(tris)
    # rank of the edge vectors
    evec = [[1 if v in e else 0 for v in verts] for e in edges]
    n = rank_mod(evec, 2)
    m2 = [[0] * len(edges) for _ in tris]
    m3 = [[0] * len(edges) for _ in tris]
    for k, (u, v, w) in enumerate(tris):
        for e in ((u, v), (v, w), (u, w)):
            m2[k][eidx[e]] = 1
        m3[k][eidx[(u, v)]] = 1
        m3[k][eidx[(v, w)]] = 1
        m3[k][eidx[(u, w)]] = 2
    r2, r3 = rank_mod(m2, 2), rank_mod(m3, 3)
    print("dimension spanned by S: %d; |S| - dim = %d; rank of the triangles over F_2: %d; "
          "rank of the oriented triangle equations over F_3: %d" % (n, len(edges) - n, r2, r3))
    assert n == 16 and r2 == len(edges) - n == 36 and r3 == 35
    rng = random.Random(1)
    sizes = set()
    for _ in range(200):
        order = edges[:]
        rng.shuffle(order)
        comp = {v: v for v in verts}

        def find(x):
            while comp[x] != x:
                comp[x] = comp[comp[x]]
                x = comp[x]
            return x

        known = set()
        for u, v in order:
            if find(u) != find(v):
                comp[find(u)] = find(v)
                known.add((u, v))
        assert len(known) == 16
        changed = True
        while changed:
            changed = False
            for (u, v, w) in tris:
                es = [(u, v), (v, w), (u, w)]
                miss = [e for e in es if e not in known]
                if len(miss) == 1:
                    known.add(miss[0])
                    changed = True
        sizes.add(len(known))
        assert len(known) < len(edges)
    print("closure of 200 random spanning trees: sizes between %d and %d of %d edges (never all)" % (min(sizes), max(sizes), len(edges)))
    print("=> S is a cyclic system of size 36 (n = 16) that is a circuit for no choice of inputs.")


if __name__ == "__main__":
    main()
