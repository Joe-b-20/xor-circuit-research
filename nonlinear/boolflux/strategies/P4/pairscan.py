"""P4: scan the 3^9 per-pair operand choices of the 103's level-1 / output ANDs.

Pair i = (g, g') (x-linear forms).  Level-1 AND a_i = g g'; output ANDs f g, f g'.
Choice A: forms {g, g'} (the 103).  B: forms {g, h = g+g'}: level-1 AND g h = a_i + g, output
ANDs f g, f h (bottom columns (c_g + c_g', c_g')).  C: forms {g', h}: g' h = a_i + g', columns
(c_g + c_g', c_g).  The pre-inversion x-parts shift: X'_j = X_j + sum over i in P_j of the shift.
A pre-inversion with 10 + k gates needs k >= rank X' injections (section 2.2 of NOTES), and k =
rank X' needs Avail (top values) to contain a basis of V = span X'.

    python3 pairscan.py CIRC > out.jsonl   (one line per choice: rank, forms, V-coverage by forms)
"""
import itertools
import json
import sys

import circ
import preinj


def xmask(atoms):
    return sum(1 << int(t[1:]) for t in atoms if t[0] == 'x')


def span(vecs):
    sp = {0}
    for v in vecs:
        if v not in sp:
            sp |= {s ^ v for s in sp}
    return sp


def setup(path):
    gates = circ.read(path)
    s = circ.symbolic(gates)
    xs = {f'x{i}' for i in range(8)}
    lvl1 = [(o, ins) for op, o, ins in gates if op == 'AND' and all(s[i][0] <= xs for i in ins)]
    pairs = [(xmask(s[a][0]), xmask(s[b][0])) for o, (a, b) in lvl1]
    names = ['t30', 't31', 't32', 't33']
    X = [xmask(s[n][0]) for n in names]
    P = [[i for i, (o, _) in enumerate(lvl1) if o in s[n][0]] for n in names]
    return gates, s, lvl1, pairs, X, P


def choice(pairs, X, P, c):
    forms = []
    Xp = list(X)
    for i, (g, gp) in enumerate(pairs):
        h = g ^ gp
        if c[i] == 0:
            forms += [g, gp]
            sh = 0
        elif c[i] == 1:
            forms += [g, h]
            sh = g
        else:
            forms += [gp, h]
            sh = gp
        for j in range(len(X)):
            if i in P[j]:
                Xp[j] ^= sh
    return forms, Xp


def main():
    path = sys.argv[1]
    gates, s, lvl1, pairs, X, P = setup(path)
    print(json.dumps(dict(pairs=pairs, X=X, P=P)), flush=True)
    stats = {}
    for c in itertools.product(range(3), repeat=9):
        forms, Xp = choice(pairs, X, P, c)
        rk = preinj.rank(Xp)
        nontriv = {f for f in forms if bin(f).count('1') > 1}
        V = span(Xp)
        av = (nontriv | {1 << i for i in range(8)}) & V
        cov = preinj.rank(list(av))
        key = (rk, len(nontriv), cov)
        stats[key] = stats.get(key, 0) + 1
        if rk <= 3 or (cov >= rk - 1 and len(nontriv) <= 16):
            print(json.dumps(dict(c=c, rank=rk, nforms=len(nontriv), cover=cov, X=Xp)), flush=True)
    print(json.dumps(dict(stats={str(k): v for k, v in sorted(stats.items())})), flush=True)


if __name__ == '__main__':
    main()
