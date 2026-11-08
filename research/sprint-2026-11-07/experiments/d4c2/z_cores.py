"""z_cores.py TAG... -- per run: which subsolver produced each bound improvement, and the core sizes."""
import re, sys, os, collections
HERE = os.path.dirname(os.path.abspath(__file__))
for t in sys.argv[1:]:
    p = os.path.join(HERE, f"e3_{t}.log")
    if not os.path.exists(p): continue
    who = collections.Counter(); sizes = []
    for line in open(p):
        if not line.startswith("#Bound"): continue
        f = line.split()
        who[f[4]] += 1
        m = re.search(r"\[size:(\d+)", line)
        if m: sizes.append(int(m.group(1)))
    print(t, dict(who), "core sizes", (min(sizes), max(sizes)) if sizes else None, sizes)
