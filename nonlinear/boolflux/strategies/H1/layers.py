"""Distinct GF(4)-norm last layers of the analysed files as (gamma, sorted members (z, zeta)),
computed from decomp_all.json operand splits: z = A s^4, zeta = s^3 (invariant under the
member\x27s cube-root / operand-swap ambiguity), gamma = t/s exponent (agent H1)."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xag
from xag import gf, EXP
R = json.load(open("/home/joebachir20/xs-campaigns/2026-11-15-study/H1/decomp_all.json"))
out = {}
for r in R:
    if r["gf4norm_count"] != len(r["last"]) or not r["last"]: continue
    mem = []; gam = set()
    for d in r["last"]:
        A = EXP[int(d["L"][1][1:])]; s = EXP[int(d["L"][3][1:])]
        mem.append((gf.mul(A, gf.power(s, 4)), gf.power(s, 3)))
        g = d.get("gammaL"); gam.add(str(int(g[1:]) % 255) if g else "none")
    assert len(gam) == 1, gam
    key = (gam.pop(), tuple(sorted(mem)))
    out.setdefault(key, []).append(r["file"])
L = [{"gamma": k[0], "members": k[1], "files": v} for k, v in out.items()]
json.dump(L, open("/home/joebachir20/xs-campaigns/2026-11-15-study/H1/layers.json", "w"), indent=1)
for l in L: print(l["gamma"], len(l["members"]), len(l["files"]), l["files"][0][:40])
