"""X3b x3b_fixkq.py: H1's fixk.py with stage 1 FREE: the stage-1 products of --S are replaced by all 28
x-quadratics (which contain V_N), so E = span(1, x, Quad, middle of M) + X. A product found here is
necessary for 12 + 1 with ANY stage 1 (then its quadratic junk must still be 9-coverable); none found
excludes 12 + 1 over this middle and these 12 kept products for every stage 1 [C, operand space O/O2/OV].
Same CLI as fixk.py (H1's code unchanged; roles() is wrapped)."""
import sys
from pathlib import Path
S = Path.home() / 'xcr-boolflux/nonlinear/boolflux/strategies'
sys.path.insert(0, str(S / 'C')); sys.path.insert(0, str(S / 'H1'))
import gf, fixk
QUAD = [gf.X[i] & gf.X[j] for i in range(8) for j in range(i + 1, 8)]
_orig = fixk.roles
def roles(f):
    r, T = _orig(f)
    return [(ro, t) for ro, t in r if ro != 'S1'] + [('S1', q) for q in QUAD], T
fixk.roles = roles
fixk.main()
