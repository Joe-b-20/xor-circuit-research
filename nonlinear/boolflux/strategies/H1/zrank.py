"""For GF(4)-norm last layers: dim Z (Z = span of z = A s^4 over members, track C\x27s coordinate)
versus rank pi(S) (members modulo E + T, E = span(1, x, S1, MID)). Track C\x27s exhaustive zdfs runs
cover only rank pi = dim Z (and dim Z = 3, rank 4). (agent H1)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xag, decomp
from xag import gf, AFFX, span
for f in sys.argv[1:]:
    r = decomp.analyse(f)
    if not r["gf4norm_count"]: continue
    zs = []
    for d in r["last"]:
        A = xag.EXP[int(d["L"][1][1:])]; s = xag.EXP[int(d["L"][3][1:])]
        zs.append(gf.mul(A, gf.power(s, 4)))
    c, ands, outs, ot = xag.parse(f)
    roles = [xag.role(A) for A in ands]
    E = [A["tab"] for A, ro in zip(ands, roles) if ro in ("S1", "MID")]
    L = [A["tab"] for A, ro in zip(ands, roles) if ro not in ("S1", "MID")]
    ET = span(AFFX, E, ot); dET = ET.dim()
    S = span(AFFX, E, ot, L)
    print("%-38s k=%d dimZ=%d rank_pi=%d excess=%d" % (r["file"][9:47], len(L), gf.Span(zs).dim(), S.dim() - dET, S.dim() - dET - gf.Span(zs).dim()))
