"""Exact eps(T) = L(D_T) - 3m by exhaustive search (exh.c), with the static invariants of geom.py.

usage: python3 run_exh.py all m [emax] [maxnodes]     all reduced classes of size m (perm. + transpose)
       python3 run_exh.py one "1|0|3|02" [emax] [maxnodes]
       python3 run_exh.py file list.txt [emax] [maxnodes]   (one T per line)
Build first: gcc -O2 -o exh exh.c
Output columns: T, rank, delta, forest criterion F (1 = Theorem C circuit exists), eps (or >emax),
number of optimal extra-sets, how many of them are pair-partition sets, histogram by (helpers, blocks).
"""
import subprocess
import sys
import time

import dmap
import geom


def run(T, N, mode=1, maxnodes=0):
    m = len(T)
    T = dmap.zero_diag(T)
    args = ["./exh", str(m), str(N), str(mode)] + [str(r) for r in T] + [str(maxnodes)]
    out = subprocess.run(args, capture_output=True, text=True)
    return out.returncode, out.stdout.strip()


def eps_of(T, emax=2, maxnodes=0, mode=1):
    m = len(T)
    for e in range(0, emax + 1):
        rc, txt = run(T, m + e, mode=mode, maxnodes=maxnodes)
        if rc == 0:
            return e, txt
        if rc == 3:
            return None, txt
    return emax + 1, ""


def classes(m):
    offdiag = [(j, k) for j in range(m) for k in range(m) if j != k]
    seen = {}
    for bits in range(1 << len(offdiag)):
        T = [0] * m
        for idx, (j, k) in enumerate(offdiag):
            if (bits >> idx) & 1:
                T[j] |= 1 << k
        T = tuple(T)
        if not dmap.reduced(T):
            continue
        c = dmap.canon(T)
        seen[c] = seen.get(c, 0) + 1
    return sorted(seen, key=lambda t: (sum(bin(r).count("1") for r in t), t))


def line(T, emax, maxnodes):
    m = len(T)
    t0 = time.time()
    d = geom.delta(T)
    ok, _ = geom.forest_criterion(T) if m <= 9 else (None, None)
    e, txt = eps_of(T, emax, maxnodes)
    tail = ""
    if txt:
        last = txt.splitlines()
        tail = " | ".join(s.strip() for s in last if "solution" not in s or "solution_sets" in s)
    es = "abort" if e is None else (f">{emax}" if e > emax else str(e))
    return f"{dmap.tstr(T):<22} rk={dmap.rank_f2(dmap.zero_diag(T))} delta={d} F={int(bool(ok))} eps={es}  [{tail}] t={time.time() - t0:.1f}s"


def main():
    kind = sys.argv[1]
    emax = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    maxnodes = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    if kind == "all":
        m = int(sys.argv[2])
        cl = classes(m)
        print(f"# m={m}: {len(cl)} reduced classes", flush=True)
        for T in cl:
            print(line(T, emax, maxnodes), flush=True)
    elif kind == "one":
        T = geom.m2_T() if sys.argv[2] == "m2" else dmap.parse_t(sys.argv[2])
        print(line(T, emax, maxnodes), flush=True)
    else:
        for s in open(sys.argv[2]):
            s = s.split("#")[0].strip()
            if s:
                print(line(dmap.parse_t(s), emax, maxnodes), flush=True)


if __name__ == "__main__":
    main()
