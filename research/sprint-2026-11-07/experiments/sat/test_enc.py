"""Sanity test of the encoding on the repo 88@5: remove a private cone, ask m=k (SAT expected)
and m=k-1; decode and independently check the reconstructed circuit."""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sat87

order = sat87.load_repo_circ()
print("repo", sat87.check_circuit(order))
vals = sat87.values_of(order)
users = sat87.dependents(order)
# private cone sizes per output
cones = {}
for t in sat87.TARGETS:
    cones[t] = sat87.private_cone(order, [t])
sizes = sorted((len(c), i) for i, (t, c) in enumerate(cones.items()))
print("single-output private cone sizes:", [s for s, _ in sizes])
# pick an output with cone size 3-4
t_idx = sizes[len(sizes)//2][1]
t = sat87.TARGETS[t_idx]
W = cones[t]
K = [v for v in vals if v not in W]
assert sat87.split_closed(K)
k = len(W)
print("test output y%d, k=%d, |K|=%d, targets missing=%d" % (t_idx, k, len(K), sum(1 for x in sat87.TARGETS if x in W)))
for m in (k, k - 1):
    for solver in ("cadical195",):
        r = sat87.solve_instance(K, m, 60, solver=solver, tag="test")
        print(m, solver, {a: b for a, b in r.items() if a != "new_gates"})
        if r.get("result") == "SAT":
            new = [tuple(g) for g in r["new_gates"]]
            full = [(v, a, b) for v, a, b in order if v in set(K)] + new
            print("  reconstructed:", sat87.check_circuit(full))
