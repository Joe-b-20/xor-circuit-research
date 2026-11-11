"""Why 246 kste lines are not counted: file, gate count, how many targets they compute."""
import glob, os, re
from collections import Counter
import families as F

c = Counter()
for fn in sorted(glob.glob(os.path.join(F.KSTE, "circuits_*.txt"))):
    for line in open(fn):
        if not line.strip():
            continue
        gates = [(int(a), int(b)) for a, b in re.findall(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", line)]
        if F.analyse(gates) is not None:
            continue
        vals = [1 << i for i in range(32)]
        okw = True
        for a, b in gates:
            if a >= len(vals) or b >= len(vals):
                okw = False
                break
            vals.append(vals[a] ^ vals[b])
        hit = sum(1 for t in F.TARGET if t in set(vals[32:]))
        c[(os.path.basename(fn), len(gates), okw, hit)] += 1
print(dict(c))
