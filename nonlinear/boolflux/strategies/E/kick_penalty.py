"""Seeded-rebuild penalty of single skeleton moves (max_acc 1) from a start circuit.
python3 kick_penalty.py FILE N [cap_ad] [w.lin]"""
import sys, random, tempfile
from pathlib import Path
from common import load, metrics
from kick import skel_kick

f = sys.argv[1]; n = int(sys.argv[2]); cap_ad = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] != '-' else None
over = {'max_acc': 1}
if len(sys.argv) > 4: over['w.lin'] = float(sys.argv[4])
c = load(f); base = metrics(c)
wd = Path(tempfile.mkdtemp())
rng = random.Random(1); res = []
for i in range(n):
    k, ch = skel_kick(c, wd, rng.randrange(1 << 30), 20000, cap_ad, over)
    if k is None: res.append(None); continue
    m = metrics(k); res.append((ch, m[0], m[2] - base[2], m[3]))
print(base, res)
