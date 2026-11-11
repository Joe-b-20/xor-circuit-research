"""Collect the best record of a heuristic run, verify it and save it in this directory's text format.

usage: python3 collect.py m TAG [j:k,...] [--show]
  reads runs/qM-TAG/workers/quick-00/records/g*.json (search/xorflux), takes a record with the fewest
  gates, verifies it against Q_m (or Q_T with the extra entries), prints the parity profile and writes
  circuits/qM[-TAG]_G.txt.  --show prints the circuit in the sheet language (show.py).
"""
import glob
import json
import os
import re
import subprocess
import sys

import qm

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    m, tag = int(args[0]), args[1]
    extra = args[2] if len(args) > 2 else None
    T = qm.shift_T(m)
    if extra:
        for item in extra.split(","):
            j, k = map(int, item.split(":"))
            T[j] ^= 1 << k
    targets = qm.rows_T(T)
    n = 4 * m
    files = glob.glob(os.path.join(HERE, "runs", f"q{m}-{tag}", "workers", "quick-00", "records", "g*.json"))
    files = [f for f in files if not f.endswith(".verification.json")]
    best = min(files, key=lambda f: (int(re.search(r"g(\d+)-", os.path.basename(f)).group(1)), f))
    gates = [tuple(g) for g in json.load(open(best))["gates"]]
    ok = qm.computes(n, gates, targets)
    pr = qm.profile(n, gates, targets)
    blocks = pr.pop("blocks")
    name = f"q{m}" + (f"-{tag}" if extra else "") + f"_{len(gates)}.txt"
    print(f"m = {m} {('T += ' + extra) if extra else ''}: {len(gates)} gates, verified: {ok}, profile {pr}, "
          f"block sizes {sorted(len(b) for b in blocks)} -> circuits/{name}")
    if ok:
        qm.write_circuit(os.path.join(HERE, "circuits", name), n, gates,
                         f"Q_T, m = {m}, T = shift" + (f" + entries {extra}" if extra else "")
                         + f"; {len(gates)} gates; found by search/xorflux quick (run {tag}); verified by collect.py")
    if "--show" in sys.argv:
        cmd = [sys.executable, os.path.join(HERE, "show.py"), str(m), os.path.join(HERE, "circuits", name)]
        if extra:
            cmd += ["--T", extra]
        print(subprocess.run(cmd, capture_output=True, text=True).stdout)


if __name__ == "__main__":
    main()
