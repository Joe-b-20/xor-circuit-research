"""Task 4: sub-map minima for unions of k groups (k = 2, 3).

For a set K of groups let A_K be the 4k x n_K matrix (rows = the outputs of the groups in K,
columns = the union of their supports; every row and column nonzero).  Facts used:
  (T)  C(A_K) = C(A_K^T) + n_K - 4k          [transposition identity, proved in REPORT]
  (L0) C(A_K^T) >= |T_K| where T_K = distinct nonbasis columns of A_K (each needs its own gate)
  (U)  C(A_K) <= min over sampled/repo circuits of |union of the cones|, and <= sum of m_g.
SAT instances (value-set encoding, xorsat.py) are run on the TRANSPOSED map (4k inputs, n_K targets)
because it has fewer inputs; m_T = m - n_K + 4k.  UNSAT at m_T proves C(A_K) >= m + 1.

usage: python3 submaps.py "0,1" 900 [forward]     (groups, wall limit seconds per instance)
Appends one json line per instance to submaps.jsonl.
"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from run_sat import solve

HERE = os.path.dirname(os.path.abspath(__file__))


def submatrix(K):
    rows = [t for g in K for t in lib.GROUP_TARGETS[g]]
    m = 0
    for t in rows:
        m |= t
    sup = lib.support(m)
    fwd_targets = [lib.relabel(t, sup) for t in rows]            # over n_K inputs
    cols = []
    for j in sup:
        cols.append(sum(((rows[r] >> j) & 1) << r for r in range(len(rows))))   # over 4k inputs
    return sup, fwd_targets, cols


def sample_upper_bound(K):
    """min over measured circuits of |union of cones of K| (greedy wiring)."""
    d = json.load(open(os.path.join(HERE, "measure.json")))
    best = None
    if len(K) == 2:
        key = f"{K[0]}{K[1]}"
        vals = [r["pair_union"][key] for r in d["samples"]] + [r["pair_union"][key] for r in d["repo"].values()]
        best = min(vals)
    else:
        # recompute unions on the fly for triples
        samples = lib.load_samples(88)
        best = 10 ** 9
        for smp in samples:
            order = lib.wiring_from_values(smp["values"])
            _, cone = lib.cones(order)
            u = set()
            for g in K:
                u |= cone[g]
            best = min(best, len(u))
        for name, path in lib.CIRC.items():
            order = lib.load_repo_circ(path)
            _, cone = lib.cones(order)
            u = set()
            for g in K:
                u |= cone[g]
            best = min(best, len(u))
    return best


if __name__ == "__main__":
    K = [int(x) for x in sys.argv[1].split(",")]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 900
    mode = sys.argv[3] if len(sys.argv) > 3 else "transposed"
    sup, fwd, cols = submatrix(K)
    n = len(sup)
    k4 = 4 * len(K)
    T = set(c for c in cols if bin(c).count("1") >= 2)
    assert all(c != 0 for c in cols) and all(t != 0 for t in fwd)
    lb0 = len(T) + n - k4
    U = min(sample_upper_bound(K), sum(lib.M_GROUP[g] for g in K))
    info = {"K": K, "n": n, "outputs": k4, "distinct_nonbasis_cols": len(T), "distinct_cols": len(set(cols)),
            "lb_transposition_trivial": lb0, "ub_samples_or_sum": U}
    print(json.dumps(info), flush=True)
    out = open(os.path.join(HERE, "submaps.jsonl"), "a")
    m = U - 1
    while m >= lb0:
        if mode == "transposed":
            mT = m - n + k4
            r = solve(k4, sorted(set(cols)), mT, limit=limit, tag=f"K={K} transposed m={m} (mT={mT})",
                      tmpname=f"tmp_sub_{'_'.join(map(str, K))}.json")
            r["forward_m"] = m
        else:
            r = solve(n, sorted(set(fwd)), m, limit=limit, tag=f"K={K} forward m={m}",
                      tmpname=f"tmp_sub_{'_'.join(map(str, K))}.json")
            r["forward_m"] = m
        r.update(info)
        r["mode"] = mode
        print(json.dumps({k: v for k, v in r.items() if k != "gates"}), flush=True)
        out.write(json.dumps(r) + "\n"); out.flush()
        if r["result"] != "SAT":
            break
        m -= 1
