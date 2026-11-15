"""Check the member spectral formulas used in the n-block argument (agent H1): for every member
(z, zeta) and gamma, the univariate coefficient at x^239 (class of x^-1) equals Y = z / zeta, and
the coefficient at the class-47 representative x^47 is a fixed multiple of z (ratio printed);
also lists every coset class (wt >= 4) the members ever hit."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import cond27, xag
from cond27 import gf, MU5
ok239 = True; ratios = set(); classes = set()
for g in sys.argv[1:]:
    for z in range(1, 256):
        for zt in MU5:
            t = cond27.member_table(z, zt, g)
            Y = gf.mul(z, gf.INV[zt])
            if xag.coeff(t, 239) != Y: ok239 = False
            c47 = xag.coeff(t, 47)
            ratios.add(gf.mul(c47, gf.INV[z]))
            if z < 4:
                classes |= {e for e in xag.coset_support(t) if xag.WT.get(e, 8) >= 4}
print("coeff239 == Y for all:", ok239, "| c47/z values:", sorted(ratios), "| high classes seen:", sorted(classes))
