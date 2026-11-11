"""Cross-validate the two lemma deciders (SAT lemma_sat.py --sym, exhaustive lemma_exh) on random
target sets: both must give the same minimum gate count.  Also re-verifies the exhaustive solutions
by an independent closure check."""
import random
import re
import subprocess
import sys

random.seed(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
N = int(sys.argv[2]) if len(sys.argv) > 2 else 12
units = {1 << (4 + i) for i in range(4)}
base = set(range(16)) | units


def closure_ok(helpers, targets):
    V = set(helpers) | set(targets)
    avail = set(base)
    changed = True
    while changed:
        changed = False
        for x in list(V - avail):
            if any((x ^ y) in avail for y in avail):
                avail.add(x)
                changed = True
    return V <= avail


def exh_min(ts, cap=5):
    for h in range(0, cap + 1):
        out = subprocess.run(["./lemma_exh", str(h), "1"] + ["%02x" % t for t in ts],
                             capture_output=True, text=True).stdout
        m = re.search(r"FOUND with (\d+) helpers \((\d+) gates\):(.*)", out)
        if m:
            hs = [int(x, 16) for x in m.group(3).split()]
            assert closure_ok(hs, ts), ("bad exhaustive solution", ts, hs)
            return int(m.group(2))
    return None


def sat_min(ts, cap=9):
    for K in range(1, cap + 1):
        out = subprocess.run(["python3", "lemma_sat.py", str(K), "--sym", "--targets",
                              ",".join("%x" % t for t in ts)], capture_output=True, text=True).stdout
        if "result=SAT" in out:
            assert "strict re-check OK" in out
            return K
    return None


cands = [v for v in range(256) if (v >> 4) and v not in units]
agree = 0
for it in range(N):
    ts = random.sample(cands, 4)
    e = exh_min(ts)
    s = sat_min(ts, 9 if e is None else e)
    print([hex(t) for t in ts], "exh", e, "sat", s, flush=True)
    if e is not None:
        assert s == e, "DISAGREE"
        agree += 1
print("agree on", agree, "of", N)
