"""Explicit vs spanned N^-1 (agent H1): number of circuit wires whose truth table lies in
span(1, n coords) (non-constant), resp. span(1, N coords), versus the rank of n in the span of
all wires (what NOTES section 1 reports)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xag
from xag import gf, NC, nC, span
Sn = span([gf.ONES], nC); SN = span([gf.ONES], NC)
for f in sys.argv[1:]:
    c, ands, outs, ot = xag.parse(f)
    tabs = c.tables()
    nw = sum(1 for t in tabs if t not in (0, gf.ONES) and Sn.contains(t))
    Nw = sum(1 for t in tabs if t not in (0, gf.ONES) and SN.contains(t))
    P = span(gf.affine_x(), [A["tab"] for A in ands])
    print("%-46s wires in span(n): %2d  wires in span(N): %2d  rank of n in circuit span: %d" % (
        Path(f).name[9:55], nw, Nw, xag.cap_dim(P, span(nC))))
