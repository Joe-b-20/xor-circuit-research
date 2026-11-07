#!/usr/bin/env python3
"""Capture-recapture estimates of the number of 88-gate MixColumns plateaus reachable by the hunt.
Input: landings.json (from landings.py).  Sampling unit = chain (T chains); datum = incidence
y_i = number of chains with at least one sampled state on plateau i.
Only exact-identity (product) plateaus enter the size model; the 18 closure-truncated 'giant'
keys (unknown size, inexact identity) are reported separately.
Pure python (3.12: random.binomialvariate)."""
import json, math, random, collections, sys

L = json.load(open("/home/joebachir20/xs-campaigns/2026-11-07-sprint/estimate/landings.json"))
T = L["T_chains"]
rows = L["rows"]
prod = [r for r in rows if r["kind"] == "product"]
giant = [r for r in rows if r["kind"] != "product"]
random.seed(20261107)


def qcounts(ys):
    return collections.Counter(ys)


def chao2(S, Q1, Q2, T):
    """Chao (1987/2005) incidence estimator, classic and bias-corrected, log-normal 95% CI."""
    k = (T - 1) / T
    if Q2 > 0:
        f0 = k * Q1 * Q1 / (2 * Q2)
        var = Q2 * (k * (Q1 / Q2) ** 2 / 2 + k * k * (Q1 / Q2) ** 3 + k * k * (Q1 / Q2) ** 4 / 4)
    else:
        f0 = k * Q1 * (Q1 - 1) / 2
        var = k * Q1 * (Q1 - 1) / 2 + k * k * Q1 * (2 * Q1 - 1) ** 2 / 4 - k * k * Q1 ** 4 / (4 * max(f0 + S, 1))
    f0bc = k * Q1 * (Q1 - 1) / (2 * (Q2 + 1))
    out = {}
    for name, F0 in (("classic", f0), ("bias-corrected", f0bc)):
        if F0 <= 0:
            out[name] = (S, S, S)
            continue
        C = math.exp(1.96 * math.sqrt(math.log(1 + var / F0 ** 2)))
        out[name] = (S + F0, S + F0 / C, S + F0 * C)
    return out


def coverage(Q1, Q2, U, T):
    """Chao & Jost sample coverage for incidence data (U = total incidences)."""
    if Q2 > 0:
        return 1 - Q1 / U * ((T - 1) * Q1 / ((T - 1) * Q1 + 2 * Q2))
    return 1 - Q1 / U * ((T - 1) * (Q1 - 1) / ((T - 1) * (Q1 - 1) + 2))


def ice(ys, T, k=10):
    """Incidence-based coverage estimator (Chao & Lee / Lee & Chao 1994 form)."""
    freq = [y for y in ys if y > k]
    rare = [y for y in ys if y <= k]
    Q = collections.Counter(rare)
    Nr = sum(rare)
    Q1 = Q[1]
    C = 1 - Q1 / Nr
    Sr = len(rare)
    Tr = T
    g2 = max(Sr / C * Tr / (Tr - 1) * sum(j * (j - 1) * Q[j] for j in Q) / (Nr * Nr - Nr) - 1, 0)  # approx
    return len(freq) + Sr / C + Q1 / C * g2, C, g2


ys = [r["chains"] for r in prod]
ys_all = [r["chains"] for r in rows]
out = []
P = lambda *a: out.append(" ".join(str(x) for x in a))

# ---------------- 1. landing table summary
sizes = [r["size"] for r in prod]
P("== 1. landing table (measured)")
P(f"T = {T} chains with catalogued 88 samples; plateaus touched = {len(rows)} "
  f"(product {len(prod)}, closure-truncated giants {len(giant)} from {len({c for r in giant for c in r['chain_ids']})} chains)")
P("incidence counts Q_j, all keys:", dict(sorted(qcounts(ys_all).items())), "; product only:", dict(sorted(qcounts(ys).items())))
P("first landings: every one of the", T, "chains' first catalogued 88 plateau is distinct (40 singletons, 0 repeats)")


def quant(v, qs=(0, .25, .5, .75, .9, 1)):
    v = sorted(v)
    return [v[min(len(v) - 1, int(q * (len(v) - 1) + 0.5))] for q in qs]


sing = [r["size"] for r in prod if r["chains"] == 1]
dbl = [r["size"] for r in prod if r["chains"] >= 2]
P("singleton sizes quantiles [min,25,50,75,90,max]:", quant(sing))
P("repeated sizes:", sorted(dbl, reverse=True))
order = sorted(sizes, reverse=True)
ranks = [1 + sum(1 for s in sizes if s > d) for d in dbl]
P("ranks of repeated plateaus by size among", len(prod), "(1 = largest, ties -> best rank):", ranks)
P("size classes (product): " + ", ".join(
    f"{lo:g}-{hi:g}: {sum(1 for s in sizes if lo <= s < hi)} plateaus, {sum(1 for r in prod if lo <= r['size'] < hi and r['chains'] > 1)} repeated"
    for lo, hi in ((1, 1e4), (1e4, 1e5), (1e5, 1e6), (1e6, 1e7))))

# ---------------- 2. size dependence
P("\n== 2. does landing probability scale with size?")
# (a) permutation test: under equal probabilities every 3-subset of the 212 is equally likely to be the repeated set
n = len(prod)
obs = sum(math.log(d) for d in dbl)
logs = [math.log(s) for s in sizes]
hits, R = 0, 200000
for _ in range(R):
    if sum(random.sample(logs, len(dbl))) >= obs - 1e-12:
        hits += 1
P(f"(a) permutation test, statistic = sum log size of the {len(dbl)} repeated plateaus: "
  f"P(>= observed | alpha=0) = {hits}/{R} = {hits / R:.2g} (estimated)")
# exact-ish: probability that all repeated sit in top m
m = max(ranks)
P(f"    exact: P(all {len(dbl)} in the top {m} of {n} | alpha=0) = {math.comb(m, len(dbl)) / math.comb(n, len(dbl)):.2g}")


# (b) conditional (zero-truncated Poisson) likelihood, mu_i = exp(b + alpha*log s_i)
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
            # d/db of y*log mu - mu - log(1-e^-mu), dmu/db = mu; q = mu/(e^mu - 1), dq/db = q(1-mu) - q^2
            q = mu / math.expm1(mu) if mu > 1e-300 else 1.0
            g += y - mu - q
            h += -mu - (q * (1 - mu) - q * q)
        step = g / h
        b -= max(min(step, 2), -2)
        if abs(step) < 1e-10:
            break
    return b


data = [(r["chains"], math.log(r["size"])) for r in prod]
grid = [x / 20 for x in range(-40, 81)]  # alpha in [-2, 4]
prof = []
b = -5.0
for a in grid:
    b = fit_b(a, data, b)
    prof.append((a, b, ll_ab(a, b, data)))
amax, bmax, llmax = max(prof, key=lambda t: t[2])
# refine
for a in [amax + d / 200 for d in range(-10, 11)]:
    bb = fit_b(a, data, bmax)
    l = ll_ab(a, bb, data)
    if l > llmax:
        amax, bmax, llmax = a, bb, l
ci = [a for a, bb, l in prof if 2 * (llmax - l) <= 3.841]
ci90 = [a for a, bb, l in prof if 2 * (llmax - l) <= 2.706]
P(f"(b) zero-truncated Poisson, E[#chains on plateau i] = lambda * size_i^alpha, conditional MLE on {len(data)} product plateaus:")
P(f"    alpha_hat = {amax:.2f} (estimated); profile-likelihood 95% CI [{min(ci):.2f}, {max(ci):.2f}]"
  f"{' (upper end hits grid edge 4)' if max(ci) >= 4 else ''}; 90% CI [{min(ci90):.2f}, {max(ci90):.2f}]")
for a0 in (0.0, 0.5, 1.0, 1.5):
    l0 = [l for a, bb, l in prof if abs(a - a0) < 1e-9][0]
    P(f"    LR test alpha={a0}: 2*dlogL = {2 * (llmax - l0):.2f}, p = {math.erfc(math.sqrt(max(2 * (llmax - l0), 0) / 2)):.3g}")


def N_ht(a, bb, data):
    return sum(1 / (-math.expm1(-math.exp(bb + a * ls))) for y, ls in data)


def mu_at(a, bb, s):
    return math.exp(bb + a * math.log(s))


P("    implied mean #chains per plateau (lambda*s^alpha) at alpha_hat: size 2187 -> "
  f"{mu_at(amax, bmax, 2187):.3g}, 6561 -> {mu_at(amax, bmax, 6561):.3g}, 1e5 -> {mu_at(amax, bmax, 1e5):.3g}, "
  f"3.4e6 -> {mu_at(amax, bmax, 3.4e6):.3g}")

# ---------------- 3. N estimates
P("\n== 3. total number of plateaus N (product plateaus, chains as sampling units)")
S = len(prod)
Qc = qcounts(ys)
U = sum(ys)
cc = chao2(S, Qc[1], Qc[2], T)
P(f"S_obs={S} (measured), Q1={Qc[1]}, Q2={Qc[2]}, total incidences U={U}, T={T}")
for k, v in cc.items():
    P(f"Chao2 {k}: N = {v[0]:.0f}, 95% CI [{v[1]:.0f}, {v[2]:.0f}] (estimated; lower bound under heterogeneity)")
C = coverage(Qc[1], Qc[2], U, T)
P(f"sample coverage C_hat = {C:.4f} (estimated): fraction of the landing-probability mass on plateaus already seen;"
  f" the next chain-landing is on a new plateau with probability ~{1 - C:.3f}")
Nice, Cr, g2 = ice(ys, T)
P(f"ICE (coverage-based, CV^2 correction gamma^2={g2:.2f}): N = {Nice:.0f} (estimated)")
# size-stratified Chao2
for cut in (1e5, 3e4):
    big = [r for r in prod if r["size"] >= cut]
    small = [r for r in prod if r["size"] < cut]
    for nm, grp in ((f"size>={cut:g}", big), (f"size<{cut:g}", small)):
        q = qcounts(r["chains"] for r in grp)
        c2 = chao2(len(grp), q[1], q[2], T)
        P(f"  stratum {nm}: S={len(grp)} Q1={q[1]} Q2={q[2]} -> Chao2 bc {c2['bias-corrected'][0]:.0f} "
          f"[{c2['bias-corrected'][1]:.0f}, {c2['bias-corrected'][2]:.0f}]"
          + (f", classic {c2['classic'][0]:.0f} [{c2['classic'][1]:.0f}, {c2['classic'][2]:.0f}]" if q[2] else ""))

# Horvitz-Thompson under the size model
P("Size-model Horvitz-Thompson N = sum_i 1/P(plateau i seen by >=1 of T chains), P = 1-exp(-lambda s_i^alpha):")
for a in sorted({0.0, 0.25, 0.5, round(amax, 2), 0.75, 1.0, 1.25, 1.5}):
    bb = fit_b(a, data, bmax)
    P(f"    alpha={a:5.2f}: lambda refit, logL gap {2 * (llmax - ll_ab(a, bb, data)):.2f}, N_HT = {N_ht(a, bb, data):,.0f}")
NHT = N_ht(amax, bmax, data)
# parametric bootstrap from the HT pseudo-population, grouped by size
bysize = collections.Counter(r["size"] for r in prod)
pseudo = {s: c / (-math.expm1(-mu_at(amax, bmax, s))) for s, c in bysize.items()}
boots = []
nfail = 0
for rep in range(300):
    sim = []
    for s, w in pseudo.items():
        Ns = int(w) + (1 if random.random() < w - int(w) else 0)
        mu = mu_at(amax, bmax, s)
        # counts y ~ Poisson(mu) per plateau: draw how many have y>=1, y>=2 ...
        p1 = -math.expm1(-mu)
        n1 = random.binomialvariate(Ns, p1) if Ns > 0 else 0
        p2c = 1 - mu * math.exp(-mu) / p1  # P(y>=2 | y>=1)
        n2 = random.binomialvariate(n1, p2c) if n1 > 0 else 0
        sim += [(1, math.log(s))] * (n1 - n2) + [(2, math.log(s))] * n2
    if not any(y > 1 for y, _ in sim):
        nfail += 1
        boots.append(float("inf"))
        continue
    best = None
    bb = -5.0
    for a in [x / 10 for x in range(-20, 41)]:
        bb = fit_b(a, sim, bb)
        l = ll_ab(a, bb, sim)
        if best is None or l > best[2]:
            best = (a, bb, l)
    boots.append(N_ht(best[0], best[1], sim))
boots.sort()
q = lambda p: boots[int(p * (len(boots) - 1))]
P(f"    at alpha_hat={amax:.2f}: N_HT = {NHT:,.0f} (estimated); parametric bootstrap (300 reps, alpha refit on grid) "
  f"median {q(.5):,.0f}, 2.5% {q(.025):,.0f}, 97.5% {q(.975):,.0f}; reps with no repeat (N unbounded): {nfail}")
tot_states = sum(r["size"] for r in prod)
P(f"    total states on the 212 seen product plateaus = {tot_states:,} (measured)")

# ---------------- giants
P("\n== giants (closure-truncated, size unknown, identity inexact)")
P(f"{len(giant)} keys from chains {sorted(collections.Counter(c for r in giant for c in r['chain_ids']).items())}")
print("\n".join(out))
open("/home/joebachir20/xs-campaigns/2026-11-07-sprint/estimate/estimate.out", "w").write("\n".join(out) + "\n")
