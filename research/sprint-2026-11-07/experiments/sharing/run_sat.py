"""Run one xorsat instance in a child under nice, with a wall limit.  Importable helper."""
import json
import os
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def solve(n, targets, m, limit=600, tag="", nice=8, tmpname="tmp_req.json", solver="cadical195"):
    req = {"n": n, "targets": sorted(set(targets)), "m": m, "solver": solver}
    tmp = os.path.join(HERE, tmpname)
    json.dump(req, open(tmp, "w"))
    t0 = time.time()
    try:
        p = subprocess.run(["nice", "-n", str(nice), "python3", os.path.join(HERE, "xorsat.py"), tmp],
                           capture_output=True, text=True, timeout=limit)
        out = p.stdout.strip().splitlines()
        res = json.loads(out[-1]) if out else {"result": "ERROR", "err": p.stderr[-800:]}
    except subprocess.TimeoutExpired:
        res = {"result": "TIMEOUT"}
    res["secs"] = round(time.time() - t0, 1)
    res["limit"] = limit
    res["tag"] = tag
    res["n"] = n
    res["m"] = m
    res["ntargets"] = len(set(targets))
    return res
