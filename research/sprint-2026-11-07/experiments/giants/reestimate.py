#!/usr/bin/env python3
"""Step 3: merge the resolved giant/closure entries (resolve.jsonl) into the landing table and
re-run the estimators exactly as estimate/estimate.py (Chao2, coverage, alpha profile, HT) and
review2/recount.py (D2, chain-pair N_eff).  Unresolved entries: excluded (main), plus a
sensitivity with them as singletons of hypothetical size.
Writes landing_table_corrected.txt and reestimate.out."""
import json, math, collections, sys
EST = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/estimate"
G = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/giants"
sys.path.insert(0, EST)
from estimate_lib import chao2, coverage, d2, pois_ci  # noqa: E402

L = json.load(open(EST + "/landings.json"))
T = L["T_chains"]
res = {}
for line in open(G + "/resolve.jsonl"):
    r = json.loads(line)
    res[r["entry"]] = r
rows = {}
unres = []
for r in L["rows"]:
    k, size, kind = r["key"], r["size"], r["kind"]
    if kind != "product":
        x = res.get(k)
        if not x or not x.get("resolved"):
            unres.append(r)
            continue
        k, size = x["canon"], x["size"]
        rad = x["radices"]
    else:
        rad = r["radices"]
    if k not in rows:
        rows[k] = {"key": k, "size": size, "chains": set(), "arms": set(), "first": 0, "samples": 0,
                   "radices": rad, "from": []}
    R = rows[k]
    assert R["size"] == size, (k, R["size"], size)
    R["chains"] |= set(r["chain_ids"])
    R["arms"] |= set(r["arms"])
    R["samples"] += r["samples"]
    R["from"].append(r["key"])
kmap = {e: x["canon"] for e, x in res.items() if x.get("resolved")}
first = collections.Counter()
for c, seq in L["chains"].items():
    first[kmap.get(seq[0], seq[0])] += 1
for k, R in rows.items():
    R["first"] = first[k]
prod = sorted(rows.values(), key=lambda r: (-len(r["chains"]), -r["size"]))
out = []


def P(*a):
    out.append(" ".join(str(x) for x in a))


with open(G + "/landing_table_corrected.txt", "w") as f:
    f.write("# corrected landing table (measured): estimate/landing_table.txt with the resolved giant/closure keys replaced\n"
            "# by their exact canonical plateau key (merged with any coinciding key; [merged from] lists the old keys);\n"
            "# unresolved entries listed at the end and excluded from the estimates\n")
    f.write(f"{'key':24s} {'kind':8s} {'size':>9s} {'chains':>6s} {'first':>5s} {'samples':>7s} arms  radices  [merged from]\n")
    for r in prod:
        extra = "" if r["from"] == [r["key"]] else f"  {r['from']}"
        f.write(f"{r['key']:24s} {'product':8s} {r['size']:>9d} {len(r['chains']):6d} {r['first']:5d} {r['samples']:7d} "
                f"{''.join(sorted(r['arms'])):5s} {r['radices']}{extra}\n")
    for r in unres:
        f.write(f"{r['key']:24s} {'UNRESOLV':8s} {'None':>9s} {r['chains']:6d} {r['first_landings']:5d} {r['samples']:7d} "
                f"{r['arms']:5s} []\n")

ys = [len(r["chains"]) for r in prod]
Q = collections.Counter(ys)
S, U = len(prod), sum(ys)
P("== corrected landing table (measured)")
P(f"T = {T} chains; product plateaus = {S} (was 212); unresolved non-product keys = {len(unres)}; "
  f"Q_j = {dict(sorted(Q.items()))}; incidences U = {U}")
P("repeated (>=2 chains):")
for r in prod:
    if len(r["chains"]) > 1:
        P(f"   {r['key']} size {r['size']} chains {sorted(r['chains'])} from {r['from']}")
cc = chao2(S, Q[1], Q[2], T)
P("\n== Chao2 (estimated; lower bound under heterogeneity)")
for k, v in cc.items():
    P(f"Chao2 {k}: N = {v[0]:.0f}, 95% CI [{v[1]:.0f}, {v[2]:.0f}]")
P(f"coverage C_hat = {coverage(Q[1], Q[2], U, T):.4f}")
for cut in (1e5, 3e4):
    for nm, grp in ((f"size>={cut:g}", [r for r in prod if r["size"] >= cut]),
                    (f"size<{cut:g}", [r for r in prod if r["size"] < cut])):
        q = collections.Counter(len(r["chains"]) for r in grp)
        c2 = chao2(len(grp), q[1], q[2], T)
        P(f"  stratum {nm}: S={len(grp)} Q1={q[1]} Q2={q[2]} -> Chao2 bc {c2['bias-corrected'][0]:.0f} "
          f"[{c2['bias-corrected'][1]:.0f}, {c2['bias-corrected'][2]:.0f}]"
          + (f", classic {c2['classic'][0]:.0f} [{c2['classic'][1]:.0f}, {c2['classic'][2]:.0f}]" if q[2] else ""))
inc = {r["key"]: r["chains"] for r in prod}
pc = collections.Counter(c for v in inc.values() for c in v)
D, lo, hi, pairs, coin = d2(inc, pc)
P(f"D2: incidence pairs in different chains {pairs:,.0f}, coincidences {coin}, D2 = {D:,.0f}, 95% [{lo:,.0f}, {hi:,.0f}] (estimated)")
met = collections.Counter()
for k, cs in inc.items():
    cs = sorted(cs)
    for i in range(len(cs)):
        for j in range(i + 1, len(cs)):
            met[(cs[i], cs[j])] += 1
lo2, hi2 = pois_ci(len(met))
P(f"chain-pair meetings {len(met)}: N_eff = {pairs / len(met):,.0f}, 95% [{pairs / hi2:,.0f}, {pairs / lo2:,.0f}]; {dict(met)}")


def ll_ab(a, b, data):
    tot = 0.0
    for y, ls in data:
        mu = max(math.exp(min(b + a * ls, 600)), 1e-300)
        tot += y * math.log(mu) - mu - math.lgamma(y + 1) - math.log(-math.expm1(-mu))
    return tot


def fit_b(a, data, b0=-5.0):
    b = b0
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


def N_ht(a, bb, data):
    return sum(1 / (-math.expm1(-math.exp(bb + a * ls))) for y, ls in data)


def fit(data, hi_grid=100):
    grid = [x / 20 for x in range(-40, hi_grid + 1)]   # alpha in [-2, 5] (sens.py grid; estimate.py used [-2, 4])
    prof, b = [], -5.0
    for a in grid:
        b = fit_b(a, data, b)
        prof.append((a, b, ll_ab(a, b, data)))
    amax, bmax, llmax = max(prof, key=lambda t: t[2])
    for a in [amax + d / 200 for d in range(-10, 11)]:
        bb = fit_b(a, data, bmax)
        l = ll_ab(a, bb, data)
        if l > llmax:
            amax, bmax, llmax = a, bb, l
    ci = [a for a, bb, l in prof if 2 * (llmax - l) <= 3.841]
    l0 = [l for a, bb, l in prof if a == 0][0]
    return amax, bmax, llmax, min(ci), max(ci), 2 * (llmax - l0), grid[-1]


def report(data, label):
    amax, bmax, llmax, lo, hi, lr0, edge = fit(data)
    edge_s = " (grid edge)" if hi >= edge else ""
    P(f"{label}: alpha_hat = {amax:.2f}, profile 95% CI [{lo:.2f}, {hi:.2f}]{edge_s}, "
      f"LR vs alpha=0: {lr0:.2f} (p={math.erfc(math.sqrt(max(lr0, 0) / 2)):.2g})")
    for a in (0.0, 0.5, 0.75, 1.0, round(amax, 2)):
        bb = fit_b(a, data, bmax)
        P(f"    alpha={a:5.2f}: logL gap {2 * (llmax - ll_ab(a, bb, data)):.2f}, N_HT = {N_ht(a, bb, data):,.0f}")
    return amax


P("\n== size model, E[#chains] = lambda*size^alpha, zero-truncated Poisson (estimated)")
data = [(len(r["chains"]), math.log(r["size"])) for r in prod]
report(data, f"corrected, {len(data)} product plateaus")
clus = [((1 if r["size"] == 3119985 and len(r["chains"]) == 2 else len(r["chains"])), math.log(r["size"])) for r in prod]
report(clus, "corrected, 2101 pair counted once (sens.py clustering variant)")
if unres:
    for gs in (3e4, 3e5, 3e6, 1e7):
        report(data + [(r["chains"], math.log(gs)) for r in unres], f"+ {len(unres)} unresolved as singletons of size {gs:g}")
P(f"total states on the {S} product plateaus = {sum(r['size'] for r in prod):,} (measured)")
print("\n".join(out))
open(G + "/reestimate.out", "w").write("\n".join(out) + "\n")
