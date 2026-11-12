"""Rough size at which the Paul/Strassen counting argument certifies non-additivity.

If L(A (+) B) >= L(A) + L(B) always held, then L(I_n (x) A) >= n L(A) for every n x n A.
Counting gives an A with L(A) >= LB(n); Strassen-Winograd recursion (A fixed, X variable,
naive below a cutoff) gives L(I_n (x) A) <= T(n) for every A.  Non-additivity is certified
as soon as n * LB(n) > T(n).  Pure arithmetic; no circuits are built.

Counting: an optimal circuit has distinct gate values, so it is determined up to the s!
labelings of its gates by choosing two operands per gate among n + s signals and n outputs:
  #{A : L(A) <= s} <= sum_{s' <= s} (n+s')^(2s' + n) / s'!
"""
import math


def log2_count(n, s):
    return (2 * s + n) * math.log2(n + s) - math.lgamma(s + 1) / math.log(2)


def LB(n):
    # smallest s with (s+1) * count(s) >= 2^(n^2); then some A has L(A) >= s
    target = n * n
    lo, hi = 0, n * n
    while lo < hi:
        mid = (lo + hi) // 2
        if math.log2(mid + 1) + log2_count(n, mid) >= target:
            hi = mid
        else:
            lo = mid + 1
    return lo


def T(n, memo={}):
    # upper bound on L(I_n (x) A) valid for every n x n A, n a power of two
    if n in memo:
        return memo[n]
    naive = n * n * (n - 1)
    if n == 1:
        v = 0
    else:
        h = n // 2
        v = min(naive, 7 * T(h) + 11 * h * h)
    memo[n] = v
    return v


def main():
    for t in range(4, 70):
        n = 2 ** t
        lb = LB(n)
        ub = T(n)
        flag = n * lb > ub
        if t % 4 == 0 or flag:
            print("n = 2^%d: LB(n) = %.4g (n^2/(2 log2 n) = %.4g), n*LB = %.4g, T(n) = %.4g, certified: %s"
                  % (t, lb, n * n / (2 * t), n * lb, ub, flag))
        if flag:
            break


if __name__ == "__main__":
    main()
