"""Does a real circuit realise each group minimally inside its cone?  For each group g and circuit,
V_g = value set of the cone C_g.  c_g = size of the smallest split-closed subset of V_g that contains
the 4 targets (a sub-circuit of the cone computing the group, any wiring within V_g).  Exact by
brute force over subsets (|V_g| <= ~25).  c_g >= m_g always; c_g = m_g means the cone contains a
minimum circuit of the group and the remaining |C_g| - c_g gates are 'paid for sharing / for the
rest of the map'; c_g > m_g means the cone's own values cannot realise the group with m_g gates.
Also reports whether the cone's values are closed in a way that needs values outside V_g (never:
V_g is split-closed by construction)."""
import itertools
import json
import os
import random
import statistics as st
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib

HERE = os.path.dirname(os.path.abspath(__file__))


def closed(sub):
    """Is INPUTS u sub split-closed (sub a set of values)?  Greedy closure works since availability
    only grows."""
    avail = set(lib.INPUTS)
    todo = set(sub)
    changed = True
    while todo and changed:
        changed = False
        for v in list(todo):
            for a in avail:
                if (a ^ v) in avail and (a ^ v) != a:
                    avail.add(v); todo.discard(v); changed = True
                    break
    return not todo


def min_closed_subset(vals, targets, lower):
    vals = sorted(set(vals))
    tg = set(targets)
    rest = [v for v in vals if v not in tg]
    for extra in range(max(0, lower - len(tg)), len(rest) + 1):
        for comb in itertools.combinations(rest, extra):
            if closed(tg | set(comb)):
                return len(tg) + extra
    return None


def analyse(order, label, verbose=True):
    par, cone = lib.cones(order)
    out = []
    for g in range(8):
        vals = cone[g]
        c = min_closed_subset(vals, lib.GROUP_TARGETS[g], lib.M_GROUP[g])
        out.append((len(vals), c, lib.M_GROUP[g]))
    if verbose:
        print(f"{label}: per group (|C_g|, c_g, m_g): {out}")
    return out


res = {}
for name, path in lib.CIRC.items():
    res[name] = analyse(lib.load_repo_circ(path), f"repo {name}")

samples = lib.load_samples(88)
rng = random.Random(3)
rng.shuffle(samples)
sub = samples[:25]
rows = []
for smp in sub:
    o = lib.wiring_from_values(smp["values"])
    rows.append(analyse(o, smp["hash"], verbose=False))
print(f"\n25 random sampled 88s: distribution of c_g - m_g (does the cone contain a minimum group circuit?)")
for g in range(8):
    xs = [r[g][1] - r[g][2] for r in rows]
    c = {}
    for x in xs:
        c[x] = c.get(x, 0) + 1
    ys = [r[g][0] - r[g][1] for r in rows]
    cy = {}
    for y in ys:
        cy[y] = cy.get(y, 0) + 1
    print(f"  group {g}: c_g - m_g hist {dict(sorted(c.items()))};  |C_g| - c_g (gates beyond the smallest sub-circuit) hist {dict(sorted(cy.items()))}")
res["samples"] = rows
json.dump(res, open(os.path.join(HERE, "cone_core.json"), "w"))
