#!/usr/bin/env python3
"""Out-of-sample check of the size model on the signature data.
For all-3 plateaus (radices all 3) the v3 signature is an exact identity (sigcheck.out: 94 of 94
unsplit), so signature coincidences on them are exact plateau coincidences.  Observed: 3 such
cross-chain coincidences (sizes 2187, 2187, 6561; verified by compress in sigcheck.out) among the
146 signature chains.  Under the size model fitted on the 40 catalogued chains, the expected number
of cross-chain coincidences on all-3 plateaus when effort grows by a pair-count factor r is
    E(alpha) = r * sum_{seen all-3 i} (mu_i^2/2) / p_i,   p_i = 1 - exp(-mu_i)
(each seen plateau stands for 1/p_i like it in the HT pseudo-population).  r = cross-chain pairs
ratio, 1.27e6 / 21,968 = 58 raw, ~22 after deflating signature pairs by 1.63^2."""
import json, math
EST = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/estimate"
L = json.load(open(EST + "/landings.json"))
prod = [r for r in L["rows"] if r["kind"] == "product"]
data = [(r["chains"], math.log(r["size"])) for r in prod]


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
            q = (mu / math.expm1(mu) if mu < 700 else 0.0) if mu > 1e-300 else 1.0
            g += y - mu - q
            h += -mu - (q * (1 - mu) - q * q)
        step = g / h
        b -= max(min(step, 2), -2)
        if abs(step) < 1e-10:
            break
    return b


def pois_p_le(k, m):
    s, t = 0.0, math.exp(-m)
    for i in range(k + 1):
        s += t
        t *= m / (i + 1)
    return s


all3 = [r for r in prod if all(x == 3 for x in r["radices"])]
print(f"seen all-3 plateaus: {len(all3)}; observed all-3 cross-chain coincidences in signature data: 3")
lmax = max(ll_ab(a / 20, fit_b(a / 20, data), data) for a in range(-40, 81))
for a in (0.0, 0.25, 0.5, 0.75, 1.0, 1.34, 1.5, 2.0):
    b = fit_b(a, data)
    E = 0.0
    for r in all3:
        mu = math.exp(b + a * math.log(r["size"]))
        E += (mu * mu / 2) / (-math.expm1(-mu))
    gap = 2 * (lmax - ll_ab(a, b, data))
    res = []
    for rr in (22, 58):
        e = rr * E
        res.append(f"r={rr}: E={e:6.2f}, P(>=3)={1 - pois_p_le(2, e):.3f}, P(<=3)={pois_p_le(3, e):.3f}")
    print(f"alpha {a:4.2f} (catalogue logL gap {gap:5.2f}): " + "; ".join(res))
