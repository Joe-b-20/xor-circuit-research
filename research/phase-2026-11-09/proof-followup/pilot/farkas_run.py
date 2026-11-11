#!/usr/bin/env python3
"""farkas_run.py -- parallel driver for farkas_q3.certify over the leaf files of a results directory (default
results_final/): one exact integer Farkas certificate per LP decision 'infeasible' of step S (monotone and exact count
vectors).  Each certificate is checked in exact integer arithmetic inside certify (lambda >= 0, lambda^T A >= 0 on every
column, lambda^T b < 0) and stored sparsely (row index -> weight; rows = the case system S(K,a,d) of
check_combined75.matrix followed by the count rows in the order built by certify) in farkas_final/<leaf>.json.
A leaf's step-S decisions are [certified] only if EVERY pruned vector of the leaf has a certificate.
usage: python3 farkas_run.py [results_dir] [workers]
"""
import sys, json, glob, time
from pathlib import Path
from collections import Counter
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import enum_q3 as E, farkas_q3 as F
OUT = HERE / "farkas_final"


def one(fn):
    c0 = time.process_time()
    r = json.load(open(fn)); key = tuple(r["key"]); a = r["A"]; d = r["qD"]
    lp = E.LeafLP(key, a, d)
    res = []; ok = 0
    for cv, ex in r.get("lp_pruned_vectors", []):
        counts = {tuple(c): n for c, n in cv}
        c = F.certify(lp, counts, ex); ok += c["ok"]
        res.append(dict(counts=[[list(k), n] for k, n in counts.items()], exact=ex, ok=c["ok"], reason=c["reason"], wrhs=c.get("wrhs"),
                        cert={str(i): w for i, w in enumerate(c["cert"]) if w} if c.get("cert") else None))
    name = Path(fn).name
    json.dump(dict(key=list(key), A=a, qD=d, vectors=len(res), certified=ok, detail=res), open(OUT / name, "w"))
    return dict(leaf=name, key=list(key), A=a, qD=d, result=r.get("result"), excluded_by=r.get("excluded_by"), vectors=len(res), certified=ok,
                reasons=dict(Counter(x["reason"] for x in res if not x["ok"])), cpu=round(time.process_time() - c0, 1))


if __name__ == "__main__":
    rd = sys.argv[1] if len(sys.argv) > 1 else str(HERE / "results_final")
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    OUT.mkdir(exist_ok=True); t0 = time.time()
    import multiprocessing as mp
    files = sorted(glob.glob(str(Path(rd) / "leaf_*.json")))
    with mp.get_context("fork").Pool(workers) as pool:
        rows = []
        for n, r in enumerate(pool.imap_unordered(one, files, chunksize=1)):
            rows.append(r)
            if (n + 1) % 20 == 0: print(n + 1, "/", len(files), "leaves", round(time.time() - t0), "s", flush=True)
    tot = sum(r["vectors"] for r in rows); okc = sum(r["certified"] for r in rows)
    summ = dict(leaves=len(rows), pruned_vectors=tot, certified=okc, not_certified=tot - okc,
                leaves_fully_certified=sum(1 for r in rows if r["vectors"] == r["certified"]),
                leaves_with_uncertified=[[r["key"], r["A"], r["qD"], r["vectors"] - r["certified"], r["reasons"]] for r in rows if r["vectors"] != r["certified"]],
                failure_reasons=dict(sum((Counter(r["reasons"]) for r in rows), Counter())),
                cpu_seconds=round(sum(r["cpu"] for r in rows)), wall=round(time.time() - t0), rows=rows)
    json.dump(summ, open(HERE / "farkas_final.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in summ.items() if k != "rows"}, indent=1))
