#!/usr/bin/env python3
"""verify_q3.py -- independent re-check of a label configuration against the rules R1-R8 of PILOT_SPEC.md section 3.

Written separately from the search of enum_q3.py: it rebuilds every rule from the object alone (no incremental state), uses
the second GF(2) rank routine (geo_q3.rank_hi, highest-bit pivots) and compares it with jc_geo.rank, builds the joint
family F(O) of Lemma J* with the STAR tree at the first carrier of every label, and re-solves the LP of R8 from a freshly
built case matrix.  Also provides the MILP of PILOT_SPEC.md section 9 (integer extension of the configuration's counts).

Object format (JSON-able):
  {"ori": "Mt", "labels": [{"value": int, "status": "F"|"B"|"D"}, ...],
   "helpers": [{"mask": int, "r": int, "triples": [64-bit boundary-subset masks], "labels": [label indices]}, ...]}
The ends b_{i,l} are not stored: b = mask ^ value, and the verifier checks that it lies in B.
"""
import sys, itertools
from pathlib import Path
from collections import Counter
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import geo_q3  # noqa: E402
REPO = Path.home() / "xor-circuit-research"
CHK = REPO / "lower-bound-proofs/mixcolumns-lb75-open-cases/checkers"
sys.path.insert(0, str(CHK))
import check_combined75 as CC  # noqa: E402


def counts_of(obj):
    c = Counter()
    for hp in obj["helpers"]:
        c[(hp["r"], len(hp["labels"]))] += 1
    return c


def family(obj, geo):
    """F(O): triple vectors and, per label, the star at its first carrier (PILOT_SPEC.md 3.7).  Helper i uses bit 64 + i."""
    vecs = []
    for i, hp in enumerate(obj["helpers"]):
        for T in hp["triples"]:
            vecs.append(T | (1 << (64 + i)))
    for j, lab in enumerate(obj["labels"]):
        carriers = [i for i, hp in enumerate(obj["helpers"]) if j in hp["labels"]]
        if len(carriers) >= 2:
            c0 = carriers[0]; b0 = obj["helpers"][c0]["mask"] ^ lab["value"]
            for c in carriers[1:]:
                b = obj["helpers"][c]["mask"] ^ lab["value"]
                vecs.append((1 << (64 + c0)) | (1 << (64 + c)) | (1 << geo.Bidx[b0]) | (1 << geo.Bidx[b]))
    return vecs


def verify(obj, geo, key=None, a=None, d=None, lp_check=True):
    """returns dict rule -> (ok, detail); 'all' is the conjunction of the rules checked."""
    B = geo.B; Bset = geo.Bset; Bidx = geo.Bidx
    res = {}
    H = obj["helpers"]; L = obj["labels"]
    masks = [hp["mask"] for hp in H]; vals = [lab["value"] for lab in L]
    # R1
    ok = (len(set(masks)) == len(masks) and all(m & 1 or bin(m).count("1") % 2 for m in masks) and all(bin(m).count("1") % 2 == 1 for m in masks)
          and all(m not in Bset for m in masks) and len(set(vals)) == len(vals) and all(v and bin(v).count("1") % 2 == 0 for v in vals))
    res["R1"] = (ok, "masks distinct odd not in B; labels distinct even nonzero")
    # R2 (and the ends in B)
    ok = True
    for hp in H:
        if len(set(hp["labels"])) != len(hp["labels"]): ok = False
        for j in hp["labels"]:
            if (hp["mask"] ^ vals[j]) not in Bset: ok = False
    res["R2"] = (ok, "label sets; ends in B")
    # R3
    ok = True
    for hp in H:
        T = hp["triples"]; r = hp["r"]
        if len(T) != r or len(set(T)) != r or r > 3: ok = False; continue
        for t in T:
            bits = [k for k in range(64) if t >> k & 1]
            if len(bits) != 3 or bin(t).count("1") != 3: ok = False; continue
            if B[bits[0]] ^ B[bits[1]] ^ B[bits[2]] != hp["mask"]: ok = False
        if r == 3 and set(T) != set(geo.trip.get(hp["mask"], [])): ok = False
    res["R3"] = (ok, "r distinct boundary triples with XOR = mask; full = all three")
    # R4
    ok = True
    full = [i for i, hp in enumerate(H) if hp["r"] == 3]
    at_full = Counter(j for i in full for j in H[i]["labels"])
    if any(c > 1 for c in at_full.values()): ok = False
    for j, lab in enumerate(L):
        if (lab["status"] == "F") != (at_full.get(j, 0) == 1): ok = False
    if a is not None and sum(1 for lab in L if lab["status"] == "F") != a: ok = False
    for i, i2 in itertools.combinations(full, 2):
        if (H[i]["mask"] ^ H[i2]["mask"]) in geo.PM: ok = False
    res["R4"] = (ok, "one full helper per full-met label; a full-met labels; full pairs not pair values")
    # R5
    ok = all(len(set(H[i]["labels"]) & set(H[i2]["labels"])) <= 1 for i, i2 in itertools.combinations(range(len(H)), 2))
    res["R5"] = (ok, "two helpers share at most one label")
    # R6
    ok = True
    for j, lab in enumerate(L):
        anch = [i for i, hp in enumerate(H) if j in hp["labels"] and hp["r"] >= 1]
        if (lab["status"] == "D") != (len(anch) == 0): ok = False
        if lab["status"] == "B" and (not anch or at_full.get(j, 0)): ok = False
    if d is not None and sum(1 for lab in L if lab["status"] == "D") != d: ok = False
    res["R6"] = (ok, "dark = no anchored carrier; d dark labels")
    # R7
    vecs = family(obj, geo)
    r_hi = geo_q3.rank_hi(vecs); r_lo = geo_q3.rank(vecs)
    res["R7"] = (r_hi == len(vecs) and r_lo == len(vecs), f"family size {len(vecs)}, rank_hi {r_hi}, rank_lo {r_lo}")
    # R8
    if lp_check and key is not None:
        from enum_q3 import LeafLP
        lp = LeafLP(key, a, d)
        res["R8"] = (lp.feasible(dict(counts_of(obj)), True), f"counts {dict(counts_of(obj))}, LP statuses {dict(lp.status)}")
    res["all"] = (all(v[0] for k, v in res.items() if k != "all"), "")
    return res


def milp_status(key, a, d, counts, time_limit=60.0):
    """integer extension of the leaf's case system with the configuration's (r,u) counts imposed (scipy HiGHS MILP).
    Returns dict(status=..., message=..., solution=..., violations=...); 'feasible' only on status 0 with 0 violations."""
    import numpy as np
    from scipy.optimize import milp, LinearConstraint, Bounds
    h = key[0]; G = 75
    b, cols, *_ = CC.matrix(key, ("eq", a), d)
    labels = [lab for lab, _ in cols]
    A = np.array([col for _, col in cols], float).T
    rows = []; lo = []; hi = []
    for (r, u), n in counts.items():
        ind = np.array([1.0 if isinstance(lab, tuple) and lab[0] == r and lab[1] == u else 0.0 for lab in labels])
        if not ind.any():
            if n: return dict(status=2, message="count on a deleted type", solution=None, violations=None, cls="infeasible")
            continue
        rows.append(ind); lo.append(n); hi.append(n)
    for r in range(4):
        for u in range(1, 4):
            if (r, u) in counts: continue
            ind = np.array([1.0 if isinstance(lab, tuple) and lab[0] == r and lab[1] == u else 0.0 for lab in labels])
            if ind.any(): rows.append(ind); lo.append(0); hi.append(0)
    Afull = np.vstack([A] + rows); lofull = np.concatenate([-np.inf * np.ones(len(b)), lo]); hifull = np.concatenate([np.array(b, float), hi])
    ub = np.array([h if isinstance(lab, tuple) else 2 * G for lab in labels], float)
    res = milp(np.zeros(len(labels)), constraints=[LinearConstraint(Afull, lofull, hifull)], integrality=np.ones(len(labels)),
               bounds=Bounds(np.zeros(len(labels)), ub), options=dict(time_limit=time_limit))
    out = dict(status=int(res.status), message=res.message, solution=None, violations=None)
    if res.x is not None:
        x = np.round(res.x).astype(int)
        viol = int(np.sum(A @ x > np.array(b) + 1e-9)) + int(np.sum(np.abs(np.vstack(rows) @ x - np.array(lo)) > 1e-9))
        out["solution"] = {str(lab): int(v) for lab, v in zip(labels, x) if v}
        out["violations"] = viol
    out["cls"] = "feasible" if (out["status"] == 0 and out["violations"] == 0) else ("infeasible" if out["status"] == 2 else "unresolved")
    return out


if __name__ == "__main__":
    import json
    geo = geo_q3.GeoQ("Mt")
    for fn in sys.argv[1:]:
        for obj in json.load(open(fn)):
            print(fn, verify(obj, geo))
