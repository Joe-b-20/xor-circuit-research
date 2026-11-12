"""Path statistics in the mirror: python3 pathstats.py m FILE [ell]

For every run of ell consecutive sheets j+1..j+ell of a circuit for Q_m (default ell = 2), with block j free
and everything else set to zero, build the mirror T of the local family circuit (INDEPENDENT-SHEETS Steps 0-3;
readers of each signal are accumulated in order of decreasing level, the level of a vector being the first
group on which it is nonzero) and print the quantities used in the pair/path argument:

  K, tau, |T|
  f_w    number of distinct non-unit, nonzero first-group parts among the signals of T   (first gates)
  D_tot  number of gates with nonzero first-group part that repeat an earlier first-group part (duplicates)
  N_0    number of gates with zero first-group part
  tau'   number of entry gates of T (one operand with zero first-group part, the other not)
  exits  number of gates whose level is larger than the level of both operands and whose value is nonzero
         (0 means: T is level-monotone)
Checks the identities |T| = f_w + D_tot + N_0, f_w + tau >= 10, D_tot >= tau' >= 3.
Reads existing circuits only.  Standard library only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "rotation"))
import qm  # noqa: E402
import mirror  # noqa: E402


def level(v, r):
    for i in range(r):
        if (v >> (4 * i)) & 15:
            return i
    return r


def build_T(loc, J):
    Jl = list(J)
    r = len(Jl)
    tbit = {(j, c): 1 << (4 * Jl.index(j) + c) for j in Jl for c in range(4)}
    readers = {}
    for g, a, b in loc["circ"]:
        for o in (a, b):
            readers.setdefault(o, []).append(("g", g))
    tg = {}
    for key, g in loc["targets"].items():
        tg.setdefault(("g", g), []).append(tbit[key])
    adj = {}
    T = []           # (mask, opA, opB)
    order = [("g", g) for g, _, _ in loc["circ"]][::-1]
    order += [("z", i) for i in range(len(loc["phi"]))]
    order += [("u", j, c) for j in Jl for c in range(4)]
    for s in order:
        contrib = list(tg.get(s, [])) + [adj[x] for x in readers.get(s, [])]
        contrib.sort(key=lambda v: -level(v, r))
        if not contrib:
            adj[s] = 0
            continue
        acc = contrib[0]
        for x in contrib[1:]:
            T.append((acc ^ x, acc, x))
            acc ^= x
        adj[s] = acc
    return adj, T


def stats(m, gates, J, F):
    loc = mirror.local_family(m, gates, J, F)
    adj, T = build_T(loc, J)
    r = len(J)
    K, tau = len(loc["circ"]), len(loc["phi"])
    seen = {1 << c for c in range(4)}       # first-group parts present (inputs of group 0)
    f_w = D = N0 = entries = exits = 0
    for v, a, b in T:
        w = v & 15
        if w == 0:
            N0 += 1
        elif w in seen:
            D += 1
        else:
            f_w += 1
            seen.add(w)
        if w and ((a & 15 == 0) != (b & 15 == 0)):
            entries += 1
        if v and level(v, r) > min(level(a, r), level(b, r)):
            exits += 1
    assert len(T) == K - tau == f_w + D + N0
    zetas = [adj[("z", i)] for i in range(tau)]
    return dict(K=K, tau=tau, T=len(T), f_w=f_w, D_tot=D, N_0=N0, tau1=entries, exits=exits, zetas=zetas)


def main():
    m = int(sys.argv[1])
    n, gates = qm.read_circuit(sys.argv[2])
    ell = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    print(f"{os.path.basename(sys.argv[2])}: m = {m}, G = {len(gates)}, runs of {ell} sheets")
    for j in range(m):
        J = [(j + 1 + i) % m for i in range(ell)]
        if j in J:
            continue
        st = stats(m, gates, J, [j])
        ok = st["f_w"] + st["tau"] >= 10 and st["D_tot"] >= st["tau1"] >= 3
        print(f"   sheets {J} | free {j}: K = {st['K']} tau = {st['tau']} |T| = {st['T']}  f_w = {st['f_w']} "
              f"D_tot = {st['D_tot']} N_0 = {st['N_0']} tau' = {st['tau1']} exits = {st['exits']}  "
              f"[f_w+tau = {st['f_w'] + st['tau']}; inequalities {'ok' if ok else 'VIOLATED'}]")


if __name__ == "__main__":
    main()
