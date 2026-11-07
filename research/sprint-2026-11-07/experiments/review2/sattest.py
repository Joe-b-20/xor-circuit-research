#!/usr/bin/env python3
"""Independent check of the F13 encoding on the repo 88@5.
(1) the k=1 test of test_enc.py (m=k SAT, m=k-1 ?);
(2) two finished k=4/5 windows from results.jsonl: m=k-1 with (distinct, symbreak) in all four
    combinations (UNSAT must not depend on the pruning constraints), m=k must be SAT and decode to
    a valid 88 containing K.  Writes tmp request files into this directory only."""
import json, os, sys, time
SAT = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/sat"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SAT)
import sat87

order = sat87.load_repo_circ()
print("repo circuit:", sat87.check_circuit(order))
vals = sat87.values_of(order)
rows = [json.loads(l) for l in open(os.path.join(SAT, "results.jsonl"))]
tests = [r for r in rows if r["circuit"] == "repo" and r["result"] == "UNSAT" and r["k"] in (4, 5)][:3]
tests += [r for r in rows if r["circuit"] == "repo" and r["scope"].startswith("C:") and r["k"] <= 5][:1]
for r in tests:
    W = set(r["W"])
    K = [v for v in vals if v not in W]
    assert sat87.split_closed(K), "K not split-closed"
    k = len(W)
    print(f"\n{r['scope']} k={k} targets in W={r['targets_in_W']} (agent: {r['result']} in {r['solve_secs']} s)")
    for distinct, symbreak in ((True, True), (False, True), (True, False), (False, False)):
        res = sat87.solve_instance(K, k - 1, 300, distinct=distinct, symbreak=symbreak, tag="rev",
                                   tmpname=os.path.join(HERE, "tmp_req_rev.json"))
        print(f"  m=k-1 distinct={distinct} symbreak={symbreak}: {res['result']} solve {res.get('solve_secs')} s vars {res.get('nvars')} cl {res.get('nclauses')}")
    res = sat87.solve_instance(K, k, 300, distinct=True, symbreak=True, tag="rev",
                               tmpname=os.path.join(HERE, "tmp_req_rev.json"))
    out = res["result"]
    if out == "SAT":
        new = [tuple(g) for g in res["new_gates"]]
        full = [(v, a, b) for v, a, b in order if v in set(K)] + new
        chk = sat87.check_circuit(full)
        newvals = {v for v, _, _ in new}
        print(f"  m=k: SAT in {res.get('solve_secs')} s; reconstructed {chk}; new values distinct from K and inputs: "
              f"{newvals.isdisjoint(set(K)) and newvals.isdisjoint(set(sat87.INPUTS))}; contains K: {set(K) <= {v for v, _, _ in full}}")
    else:
        print("  m=k:", out)
