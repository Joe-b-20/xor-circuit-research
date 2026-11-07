#!/usr/bin/env python3
"""Sensitivity of alpha to the clustering of the 3 exact repeats (two of them are the same chain
pair A/free-05/0 + C/free-00/0 on neighbouring 2101-family plateaus), and the full landing table
written to landing_table.txt."""
import json, math
EST = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/estimate"
L = json.load(open(EST + "/landings.json"))
prod = [r for r in L["rows"] if r["kind"] == "product"]


def ll_ab(a, b, data):
    tot = 0.0
    for y, ls in data:
        mu = max(math.exp(min(b + a * ls, 600)), 1e-300)
        tot += y * math.log(mu) - mu - math.lgamma(y + 1) - math.log(-math.expm1(-mu))
    return tot


def fit_b(a, data, b=-5.0):
    for _ in range(100):
        g = h = 0.0
        for y, ls in data:
            mu = math.exp(min(b + a * ls, 600))
            q = mu / math.expm1(mu) if mu > 1e-300 else 1.0
            g += y - mu - q
            h += -mu - (q * (1 - mu) - q * q)
        step = g / h
        b -= max(min(step, 2), -2)
        if abs(step) < 1e-10:
            break
    return b


def profile(data):
    grid = [x / 20 for x in range(-40, 101)]
    prof, b = [], -5.0
    for a in grid:
        b = fit_b(a, data, b)
        prof.append((a, ll_ab(a, b, data)))
    amax, lmax = max(prof, key=lambda t: t[1])
    ci = [a for a, l in prof if 2 * (lmax - l) <= 3.841]
    l0 = [l for a, l in prof if a == 0][0]
    return amax, min(ci), max(ci), 2 * (lmax - l0)


base = [(r["chains"], math.log(r["size"])) for r in prod]
clus = [((1 if r["size"] == 3119985 and r["chains"] == 2 else r["chains"]), math.log(r["size"])) for r in prod]
for nm, d in (("3 repeats as independent", base), ("2 repeats (2101 pair counted once)", clus)):
    a, lo, hi, lr0 = profile(d)
    print(f"{nm}: alpha_hat {a:.2f}, 95% profile CI [{lo:.2f}, {hi:.2f}]{' (grid edge 5)' if hi >= 5 else ''}, "
          f"LR vs alpha=0: {lr0:.2f} (p={math.erfc(math.sqrt(lr0 / 2)):.2g})")

with open(EST + "/landing_table.txt", "w") as f:
    f.write("# one row per catalogued sprint plateau (measured). chains = # independent chains with a sampled state on it;\n"
            "# first = # chains whose first catalogued 88 state is on it; size None = closure-truncated giant (unknown)\n")
    f.write(f"{'key':24s} {'kind':8s} {'size':>9s} {'chains':>6s} {'first':>5s} {'samples':>7s} arms  radices\n")
    for r in sorted(L["rows"], key=lambda r: (-r["chains"], -(r["size"] or 10 ** 9))):
        f.write(f"{r['key']:24s} {r['kind']:8s} {str(r['size']):>9s} {r['chains']:6d} {r['first_landings']:5d} "
                f"{r['samples']:7d} {r['arms']:5s} {r['radices']}\n")
print("wrote landing_table.txt")
