"""CHECK (explicit objects, no search): two borrowing loops that are F_2-determined but not executable.

(a) A fibre forest with odd labels and two exits whose path-edge borrowing matrix N has a cycle and
    det(I + N) = 1 over F_2 (so the order-free argument used for configuration (X) does not extend
    to arbitrary forests). Not a pair-problem system: a sub-configuration only.
(b) Design A of sharing/designs.py made cyclic: the pure gate t_j = s0_j + s2_j is replaced by the exit
    t_j = u1_(j+1) + u2_(j+1). Checked for m = 3, 4, 5: F_2-determined, contains all targets of Q_m,
    12m relations, not executable (peeling stalls). Here N = 0 on path edges: the loop runs through
    the fibre roots, which cancel in the exit.
Determined = the incidence matrix of the relations on the unknowns is invertible over F_2.
Executable = the based leaf property: peeling unknowns that lie in exactly one remaining relation
removes every relation (cyclic/REPORT.md Theorem W, based version).
"""
import os
import sys

def rank(rows):
    rows = [r for r in rows]
    rk = 0
    piv_rows = []
    for r in rows:
        for p in piv_rows:
            if r & (p & -p):
                r ^= p
        if r:
            piv_rows.append(r)
            rk += 1
    return rk

def check(rels, known, values, label):
    """rels: list of tuples of element names; known: set of input names; values: name -> int (bit vector)."""
    for t in rels:
        acc = 0
        for e in t:
            acc ^= values[e]
        assert acc == 0, (label, t)
    unknowns = sorted({e for t in rels for e in t} - set(known))
    idx = {e: i for i, e in enumerate(unknowns)}
    rows = []
    for t in rels:
        r = 0
        for e in t:
            if e in idx:
                r ^= 1 << idx[e]
        rows.append(r)
    # reduced-row rank (pivot on lowest set bit, keep rows reduced)
    basis = {}
    for r in rows:
        while r:
            low = r & -r
            if low in basis:
                r ^= basis[low]
            else:
                basis[low] = r
                break
    rk = len(basis)
    # peeling
    remaining = list(range(len(rels)))
    progress = True
    while progress and remaining:
        progress = False
        count = {}
        for i in remaining:
            for e in rels[i]:
                if e in idx:
                    count[e] = count.get(e, 0) + 1
        for i in remaining:
            if any(count.get(e, 0) == 1 for e in rels[i] if e in idx):
                remaining.remove(i)
                progress = True
                break
    vals = [values[e] for e in unknowns]
    distinct = len(set(vals)) == len(vals) and 0 not in vals and not (set(vals) & {values[k] for k in known})
    print("%s: %d relations, %d unknowns, F_2 rank on unknowns %d (%s), values distinct and new: %s, "
          "peeling leaves %d relations (%s)"
          % (label, len(rels), len(unknowns), rk, "determined" if rk == len(unknowns) == len(rels) else "NOT determined",
             distinct, len(remaining), "executable" if not remaining else "not executable"))
    return rk == len(unknowns) == len(rels), not remaining

def example_a():
    # vectors (omega | s) as 8-bit ints: omega in bits 4..7, s in bits 0..3
    u = lambda k: 1 << k
    E = lambda k: 0b1111 ^ (1 << k)
    om = 1 << 4
    lab = {  # edge: (parent, child, label element, label vector)
        "a1": ("x0", "x1", "w'1", u(1)),
        "e":  ("x1", "x2", "B0", E(0)),
        "f":  ("x2", "x3", "B1", E(1)),
        "c1": ("x3", "x4", "w'2", u(2)),
        "c2": ("x4", "x5", "w'3", u(3)),
        "d1": ("x2", "y1", "w'1", u(1)),
        "d2": ("y1", "y2", "w'0", u(0)),
    }
    values = {"x0": om}
    for k in range(4):
        values["w'%d" % k] = u(k)
        values["B%d" % k] = E(k)
    rels = []
    for name in ["a1", "e", "f", "c1", "c2", "d1", "d2"]:
        p, c, le, lv = lab[name]
        values[c] = values[p] ^ lv
        rels.append((p, le, c))
    rels.append(("x0", "x5", "B1"))   # exit B1 = path a1,e,f,c1,c2
    rels.append(("y2", "x3", "B0"))   # exit B0 = path d2,d1,f
    known = {"x0", "w'0", "w'1", "w'2", "w'3"}
    print("(a) forest: x0-a1(u1)-x1-e(E0)-x2-f(E1)-x3-c1(u2)-x4-c2(u3)-x5, x2-d1(u1)-y1-d2(u0)-y2;"
          " exits B1 = x0+x5, B0 = y2+x3")
    print("    borrowed edges e (label B0, path {d2,d1,f}) and f (label B1, path {a1,e,f,c1,c2}):"
          " N = [[0,1],[1,1]], det(I+N) = 1")
    # B2, B3 are not used here; they are not part of this sub-configuration
    return check(rels, known, values, "(a)")

def example_b(m):
    HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(HERE, "..", "rotation"))
    import qm
    n = 4 * m
    values = {}
    rels = []
    def inp(c, j):
        return "e%d_%d" % (j % m, c)
    for j in range(m):
        for c in range(4):
            values[inp(c, j)] = 1 << (4 * j + c)
    def put(name, a, b):
        values[name] = values[a] ^ values[b]
        rels.append((a, b, name))
    # pure gates except t
    for j in range(m):
        put("s0_%d" % j, inp(0, j), inp(1, j))
        put("s2_%d" % j, inp(2, j), inp(3, j))
        put("d0_%d" % j, inp(0, j), inp(2, j))
        values["t_%d" % j] = values["s0_%d" % j] ^ values["s2_%d" % j]
    for j in range(m):
        a = (j - 1) % m
        put("u1_%d" % j, "t_%d" % j, "s0_%d" % a)
        put("u2_%d" % j, "t_%d" % j, "s2_%d" % a)
        put("o0_%d" % j, "u1_%d" % j, inp(0, j))
        put("o2_%d" % j, "u2_%d" % j, inp(2, j))
        put("v1_%d" % j, "u1_%d" % j, inp(1, j))
        put("o1_%d" % j, "v1_%d" % j, "d0_%d" % a)
        put("v3_%d" % j, "u2_%d" % j, inp(3, j))
        put("o3_%d" % j, "v3_%d" % j, "d0_%d" % a)
    # the exits replacing t_j = s0_j + s2_j: t_j = u1_(j+1) + u2_(j+1)
    for j in range(m):
        b = (j + 1) % m
        rels.append(("u1_%d" % b, "u2_%d" % b, "t_%d" % j))
    known = {inp(c, j) for j in range(m) for c in range(4)}
    tg = set(qm.rows(m))
    have = set(values.values())
    print("(b) cyclic Design A, m = %d: all %d targets of Q_m among the values: %s"
          % (m, len(tg), tg <= have))
    return check(rels, known, values, "(b) m=%d" % m)

if __name__ == "__main__":
    example_a()
    for m in (3, 4, 5):
        example_b(m)
