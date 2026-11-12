"""Hand-designed circuits of the sharing study, verified (no search).

usage: python3 designs.py

Design A ("t-design", period 1, window-local, no exits): per sheet j
   pure gates on block j:  s0 = e0+e1, s2 = e2+e3, d0 = e0+e2, t = s0+s2                      (4 gates)
   two-block gates, a = block j-1, b = block j:
      u1 = t(b) + s0(a)     u2 = t(b) + s2(a)
      o0 = u1 + e0(b)       o2 = u2 + e2(b)
      v1 = u1 + e1(b)       o1 = v1 + d0(a)
      v3 = u2 + e3(b)       o3 = v3 + d0(a)                                                  (8 gates)
   12 gates per sheet.  The pair u1, u2 of sheet j+1 has equal (j+1)-parts and differs by t on block j: the exit
   u1 + u2 = [j: t] would replace the pure gate t = s0 + s2 of block j, one gate for one gate, and it creates a
   cyclic dependency (t of block j needs t of block j+1).
Prints the gate count, verification, block-monotonicity and charges for m = 4, 5, 8.

Design B (local values only): the sheet with the vector t of its own block given: 8 gates (checked as masks).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "rotation"))
import qm  # noqa: E402


def design_A(m):
    n = 4 * m
    gates = []

    def add(a, b):
        gates.append((a, b))
        return n + len(gates) - 1

    def inp(c, j):
        return 4 * (j % m) + (c % 4)

    pure = {}
    for j in range(m):
        s0 = add(inp(0, j), inp(1, j))
        s2 = add(inp(2, j), inp(3, j))
        d0 = add(inp(0, j), inp(2, j))
        t = add(s0, s2)
        pure[j] = dict(s0=s0, s2=s2, d0=d0, t=t)
    for j in range(m):
        a, b = pure[(j - 1) % m], pure[j]
        u1 = add(b["t"], a["s0"])
        u2 = add(b["t"], a["s2"])
        add(u1, inp(0, j))
        add(u2, inp(2, j))
        v1 = add(u1, inp(1, j))
        add(v1, a["d0"])
        v3 = add(u2, inp(3, j))
        add(v3, a["d0"])
    return n, gates


def charges(m, n, gates):
    targets = qm.rows(m)
    vals = qm.masks(n, gates)
    sup = [frozenset(j for j in range(m) if (v >> (4 * j)) & 15) for v in vals]
    first = {}
    for i in range(n, n + len(gates)):
        first.setdefault(vals[i], i)
    anc = [set() for _ in range(m)]
    viol = set()
    for oi, t in enumerate(targets):
        o = first[t]
        seen, stack = set(), [o]
        while stack:
            s = stack.pop()
            if s < n or s in seen:
                continue
            seen.add(s)
            stack.extend(gates[s - n])
        anc[oi // 4] |= seen
        viol |= {g for g in seen if not sup[g] <= sup[o]}
    mu = [sum(1 for j in range(m) if j in sup[g] and g in anc[j]) for g in range(n, n + len(gates))]
    per = [sum(1 for g in anc[j] if j in sup[g]) for j in range(m)]
    return per, mu.count(0), sum(max(0, x - 1) for x in mu), not viol


def main():
    for m in (4, 5, 8):
        n, gates = design_A(m)
        ok = qm.computes(n, gates, qm.rows(m))
        per, unch, exc, mono = charges(m, n, gates)
        print(f"Design A, m = {m}: {len(gates)} gates ({len(gates) // m} per sheet), computes Q_m: {ok}, block-monotone: {mono}, "
              f"charges {per}, uncharged {unch}, excess {exc}")
    # Design B: masks (b-part, a-part) as 4-bit pairs
    E = [15 ^ (1 << c) for c in range(4)]
    s = [(1 << c) | (1 << ((c + 1) % 4)) for c in range(4)]
    t, d0 = 15, 0b0101
    u1, u2 = (t, s[0]), (t, s[2])
    o0 = (u1[0] ^ 1, u1[1])
    o2 = (u2[0] ^ 4, u2[1])
    v1 = (u1[0] ^ 2, u1[1])
    o1 = (v1[0], v1[1] ^ d0)
    v3 = (u2[0] ^ 8, u2[1])
    o3 = (v3[0], v3[1] ^ d0)
    good = [o0, o1, o2, o3] == [(E[c], s[c]) for c in range(4)]
    print("Design B (t of the own block given, previous block free): 8 gates u1 u2 o0 o2 v1 o1 v3 o3; outputs correct:", good)


if __name__ == "__main__":
    main()
