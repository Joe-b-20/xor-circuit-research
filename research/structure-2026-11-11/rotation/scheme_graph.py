"""Transition graph of sheet schemes between the sixteen bases of the types seen in the 40-gate circuit.

usage: python3 scheme_graph.py [TIMEOUT] [WORKERS]          (writes one line per instance)

Types (rotation c -> c+r acts on indices): alpha_c = {s_c, s_(c+1), t}, beta_c = {s_c, d_c, t},
gamma_c = {s_c, d0, d1}, delta_(c,d) = {s_c, s_(c+2), d}.  For P = the representative of each type
and every O among the sixteen bases of a different type, decides by SAT (scheme_sat.py, 10 gates)
whether the scheme P -> O exists.  By rotation symmetry this gives all transitions between different
types; transitions inside a type are covered by 'scheme_sat.py --period1'.
"""
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import scheme_sat as ss


def states():
    S = {}
    for c in range(4):
        S[f"alpha{c}"] = (f"s{c}", f"s{(c + 1) % 4}", "t")
        S[f"beta{c}"] = (f"s{c}", f"d{c % 2}", "t")
        S[f"gamma{c}"] = (f"s{c}", "d0", "d1")
    for c in range(2):
        for d in range(2):
            S[f"delta{c}{d}"] = (f"s{c}", f"s{c + 2}", f"d{d}")
    return S


def run(job):
    pn, on, P, O, tmo = job
    try:
        res = subprocess.run([sys.executable, ss.__file__, ",".join(P), ",".join(O)], capture_output=True, text=True, timeout=tmo)
        first = res.stdout.splitlines()[0] if res.stdout else "?"
    except subprocess.TimeoutExpired:
        first = "TIMEOUT"
    return f"{pn:<8} -> {on:<8}  ({','.join(P)} -> {','.join(O)}): {first}"


def main():
    tmo = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    S = states()
    reps = ["alpha0", "beta0", "gamma0", "delta00"]
    jobs = []
    for pn in reps:
        for on in S:
            if on.rstrip("0123")[:4] == pn[:4]:
                continue
            jobs.append((pn, on, S[pn], S[on], tmo))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for line in ex.map(run, jobs):
            print(line, flush=True)


if __name__ == "__main__":
    main()
