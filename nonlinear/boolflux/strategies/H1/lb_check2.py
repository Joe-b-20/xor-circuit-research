"""Independent check for the MC >= 13 proof: degrees of all 255 nonzero output combinations of a
NIST AES S-box circuit file (agent H1)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xag
c, ands, outs, ot = xag.parse(sys.argv[1])
h = {}
for m in range(1, 256):
    t = 0
    for k in range(8):
        if m >> k & 1: t ^= ot[k]
    d = xag.anf_degree(t); h[d] = h.get(d, 0) + 1
print(Path(sys.argv[1]).name, "degree histogram over 255 combinations:", h)
