"""Reviewer (machine review): how often the J6 edge case occurs -- pure-b gates with a non-pure operand
(omega differs from the value), and gates that are outputs and also read by later gates.
usage: python3 rv_edge.py STRIDE"""
import itertools, os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rvlib import ROWS, COMPAT, JOINT, check, load_json, pure_block, values
from rv_checks import get, specs
from rv_caps import carrier_build
c = Counter()
circs = [get(sp) for sp in specs(int(sys.argv[1]))]
circs += [("lw%d" % k, load_json(os.path.join(COMPAT, "lw%d.json" % k))) for k in range(8)]
circs += [("W*", load_json(os.path.join(JOINT, "wstar.json")))]
circs += [("cB", carrier_build(B)) for s in (1, 2) for B in itertools.combinations(range(8), s)]
for name, g in circs:
    if not all(check(g)):
        continue
    v = values(g)
    rows = {v.index(r, 32) for r in ROWS.values()}
    rd = set(a for a, b in g) | set(b for a, b in g)
    e = sum(1 for k, (a, b) in enumerate(g) if pure_block(v[32 + k]) is not None and
            (pure_block(v[a]) is None or pure_block(v[b]) is None))
    c[("pure gate with non-pure operand > 0", name[:2] if name[:2] in ("lw", "W*", "cB") else "corpus", e > 0)] += 1
    c[("output read by a later gate > 0", name[:2] if name[:2] in ("lw", "W*", "cB") else "corpus", len(rows & rd) > 0)] += 1
for k, n in sorted(c.items()):
    print(k, n)
