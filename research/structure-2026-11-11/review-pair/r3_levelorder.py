"""Review item 2: is the Q_3 pair mirror level-monotone for SOME order of accumulating readers?

Adjoint values do not depend on the order; only the partial-sum gates do, and the condition
'every nonzero gate has level = min(level of operands)' is per gate.  So for each mirrored signal we test
every ordering of its (few) contributions.  This examines orders for a given circuit; no circuit search."""
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rlib as R  # noqa: E402


def lev(x):
    return R.level_pair(x)


def good_order(ms):
    for perm in itertools.permutations(ms):
        acc, ok = perm[0], True
        for x in perm[1:]:
            y = acc ^ x
            if y and lev(y) != min(lev(acc), lev(x)):
                ok = False
                break
            acc = y
        if ok:
            return perm
    return None


for f, m in (("q3_28.txt", 3), ("q4_40.txt", 4), ("q8_80.txt", 8)):
    qm = R.qm_model(m)
    n, g = R.read_qm(os.path.join(R.QDIR, f))
    for j in range(m):
        lc, tg = R.clean(*R.local_pair(qm, n, g, j))
        M = R.mirror(lc, tg)
        bad = []
        for key, c in M["contribs"].items():
            ms = [M["Tm"][s] for s in c]
            if len(ms) > 1 and good_order(ms) is None:
                bad.append((key, ["%02x" % x for x in ms]))
        print("%s pair (%d,%d): signals whose readers admit no level-monotone order: %d %s"
              % (f, j, (j + 1) % m, len(bad), bad[:3]))
