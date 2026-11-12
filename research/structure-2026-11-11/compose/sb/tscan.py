"""Check of ONE hand-chosen tight mirror T* for the first sheet (o = 2 type): lists the primal signals
of its transposes over all summation orders and every pair of them with equal w^1-part, with the
formal label difference delta.  A check of a given T*, not a search over circuits.

T* spec (python literal in a file): {"gates": [(name, op1, op2), ...], "des": {node: [designations]}}
nodes W0..W3 are the T* inputs (the four targets); designations "w0".."w3" (sheet inputs, on the E
nodes) and "z1".."z4" (formal labels, on the zeta nodes).
"""
import ast
import itertools
import sys

spec = ast.literal_eval(open(sys.argv[1]).read())
nodes = ["W0", "W1", "W2", "W3"] + [g[0] for g in spec["gates"]]
val = {"W%d" % c: 1 << c for c in range(4)}
readers = {n: [] for n in nodes}
for name, a, b in spec["gates"]:
    val[name] = val[a] ^ val[b]
    readers[a].append(name)
    readers[b].append(name)
DES = {"w%d" % c: 1 << c for c in range(4)}
DES.update({"z%d" % j: 1 << (3 + j) for j in range(1, 5)})
reach = {}
for n in reversed(nodes):
    r = 0
    for d in spec["des"].get(n, []):
        r ^= DES[d]
    for u in readers[n]:
        r ^= reach[u]
    reach[n] = r
for c in range(4):
    assert reach["W%d" % c] & 15 == 15 ^ (1 << c), "target %d wrong" % c
print("gate values:", {n: format(val[n], "04b")[::-1] for n in nodes[4:]})
print("targets l_c:", [format(reach["W%d" % c] >> 4, "04b")[::-1] for c in range(4)])
gates = sum(len(readers[n]) + len(spec["des"].get(n, [])) - 1 for n in nodes)
print("primal gates (all orders):", gates)
sig = []  # (mask, node, frozenset of contributions)
for n in nodes:
    contrib = [("r", u, reach[u]) for u in readers[n]] + [("d", d, DES[d]) for d in spec["des"].get(n, [])]
    k = len(contrib)
    for s in range(1, k + 1):
        for sub in itertools.combinations(range(k), s):
            items = [contrib[i] for i in sub]
            nonfree = [x for x in items if not (x[0] == "d" and x[1][0] == "z")]
            if s == 1:
                continue
            if not nonfree:
                continue
            m = 0
            for x in items:
                m ^= x[2]
            sig.append((m, n, frozenset(sub)))
# plus input signals and single-contribution nodes (wires): the primal inputs w_c
for c in range(4):
    sig.append((1 << c, "in", frozenset()))
best = []
for (m1, n1, s1), (m2, n2, s2) in itertools.combinations(sig, 2):
    if m1 & 15 != m2 & 15 or m1 & 15 == 0:
        continue
    if n1 == n2 and not (s1 < s2 or s2 < s1):
        continue
    d = (m1 ^ m2) >> 4
    if d:
        best.append((bin(d).count("1"), format(m1 & 15, "04b")[::-1], format(d, "04b")[::-1], n1, sorted(s1), n2, sorted(s2)))
best.sort(reverse=True)
for b in best[:12]:
    print(" |delta| %d  omega %s  delta(z1..z4) %s   %s%s ~ %s%s" % b)
print("max |delta|:", best[0][0] if best else None)
