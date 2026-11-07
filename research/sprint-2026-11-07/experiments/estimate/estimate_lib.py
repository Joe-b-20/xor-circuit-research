"""Shared estimators (same formulas as estimate.py)."""
import math


def chao2(S, Q1, Q2, T):
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
        C = math.exp(1.96 * math.sqrt(math.log(1 + var / F0 ** 2)))
        out[name] = (S + F0, S + F0 / C, S + F0 * C)
    return out


def coverage(Q1, Q2, U, T):
    if Q2 > 0:
        return 1 - Q1 / U * ((T - 1) * Q1 / ((T - 1) * Q1 + 2 * Q2))
    return 1 - Q1 / U * ((T - 1) * (Q1 - 1) / ((T - 1) * (Q1 - 1) + 2))


def pois_ci(k):
    """Exact (Garwood) 95% CI for a Poisson count, by bisection on the cdf."""
    def cdf(m, k):
        s, t = 0.0, math.exp(-m)
        for i in range(k + 1):
            s += t
            t *= m / (i + 1)
        return s

    def solve(f, lo, hi):
        for _ in range(200):
            mid = (lo + hi) / 2
            if f(mid):
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2
    lower = 0.0 if k == 0 else solve(lambda m: 1 - cdf(m, k - 1) < 0.025, 0, 10 * k + 10)
    upper = solve(lambda m: cdf(m, k) > 0.025, 0, 10 * k + 20)
    return lower, upper


def d2(inc, per_chain):
    """Inverse Simpson effective number: (# incidence pairs in different chains) / (# such pairs on
    the same plateau).  inc: key -> set of chains; per_chain: chain -> # incidences."""
    n = list(per_chain.values())
    pairs = (sum(n) ** 2 - sum(x * x for x in n)) / 2
    coin = sum(len(v) * (len(v) - 1) / 2 for v in inc.values())
    lo, hi = pois_ci(int(coin))
    return pairs / coin if coin else float("inf"), pairs / hi, (pairs / lo if lo else float("inf")), pairs, int(coin)
