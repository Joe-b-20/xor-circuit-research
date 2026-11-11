"""Probe: enumerate sheet-0 circuits Z satisfying the lending condition of qa_sat.py and, for each, decide by SAT
whether sheet 1 can be completed with KB gates that have no operand supported on block 0 alone or block 7 alone.

usage: python3 qa_probe.py KZ MAXU KB NMAX [TIMEOUT_PER_Z]
  Z: KZ gates over blocks 7 (free, bits 0..3) and 0 (bits 4..7), with a set U of <= MAXU two-block gates whose span
  contains the diagonal space; distinct Z are enumerated by blocking the set of two-block gate masks of U.
  For each Z: SAT for KB gates on block 1 (bits 8..11) with operands among the block-1 inputs, the gates of Z that
  are nonzero on both blocks, and earlier such gates.
Prints one line per Z; a SAT answer is a joint circuit for sheets 0 and 1 with KZ + KB gates.
"""
import sys
import time

from pysat.card import CardEnc, EncType
from pysat.solvers import Solver

import qa_sat

S_VEC = qa_sat.S_VEC


def second_layer(zmasks, kb):
    """SAT: kb gates, nonzero on block 1, operands: block-1 inputs, the given two-block Z masks, earlier gates."""
    base = [1 << i for i in range(8, 12)] + list(zmasks)
    targets = []
    for c in range(4):
        Ec = 15 ^ (1 << c)
        targets.append((Ec << 8) | (S_VEC[c] << 4) | S_VEC[c])
    cl, val, nv = qa_sat.encode(base, targets, kb, nbits=12)
    nb = len(base)
    for g in range(nb, nb + kb):
        cl.append(val[g][8:12])
    with Solver(name="cadical153", bootstrap_with=cl) as sol:
        if not sol.solve():
            return None
        model = set(x for x in sol.get_model() if x > 0)
        return [sum(1 << i for i in range(12) if val[g][i] in model) for g in range(nb, nb + kb)]


def main():
    kz, maxu, kb, nmax = (int(x) for x in sys.argv[1:5])
    base = [1 << i for i in range(8)] + [v for v in range(1, 16) if bin(v).count("1") >= 2]
    targets = []
    for c in range(4):
        Ec = 15 ^ (1 << c)
        targets.append((Ec << 4) | S_VEC[c])
    cl, val, nv = qa_sat.encode(base, targets, kz)
    nb = len(base)

    def new():
        nv[0] += 1
        return nv[0]

    gates = list(range(nb, nb + kz))
    u = {g: new() for g in gates}
    for g in gates:
        cl.append([-u[g]] + val[g][0:4])
        cl.append([-u[g]] + val[g][4:8])
    card = CardEnc.atmost(lits=list(u.values()), bound=maxu, top_id=nv[0], encoding=EncType.seqcounter)
    cl += card.clauses
    nv[0] = max(nv[0], card.nv)
    diag = lambda s: s | (s << 4)
    for d in (diag(S_VEC[0]), diag(S_VEC[1]), diag(S_VEC[2])):
        lam = {g: new() for g in gates}
        for g in gates:
            cl.append([-lam[g], u[g]])
        for i in range(8):
            terms = []
            for g in gates:
                t = new()
                cl += [[-t, lam[g]], [-t, val[g][i]], [t, -lam[g], -val[g][i]]]
                terms.append(t)
            acc = terms[0]
            for t in terms[1:]:
                x = new()
                cl += [[-x, acc, t], [-x, -acc, -t], [x, -acc, t], [x, acc, -t]]
                acc = x
            cl.append([acc] if (d >> i) & 1 else [-acc])
    # presence variables for blocking on the set of gate masks
    found = 0
    t_all = time.time()
    with Solver(name="cadical153", bootstrap_with=cl) as sol:
        while found < nmax and sol.solve():
            model = set(x for x in sol.get_model() if x > 0)
            masks = [sum(1 << i for i in range(8) if val[g][i] in model) for g in gates]
            mixed = [m for m in masks if (m & 15) and (m >> 4)]
            found += 1
            t0 = time.time()
            res = second_layer(mixed, kb)
            print(f"Z #{found}: masks {[format(m, '08b') for m in masks]}: sheet 1 with {kb} gates: "
                  f"{'SAT ' + str([format(x, '012b') for x in res]) if res else 'UNSAT'}  ({time.time() - t0:.1f} s)", flush=True)
            if res:
                break
            # block this exact mask set (as an ordered assignment is not canonical, block the set of masks)
            blk = []
            for m in set(masks):
                # some gate differs from every mask in the set: approximate by blocking the ordered model
                pass
            blk = []
            for g, m in zip(gates, masks):
                for i in range(8):
                    blk.append(-val[g][i] if (m >> i) & 1 else val[g][i])
            sol.add_clause(blk)
    print(f"done: {found} circuits examined in {time.time() - t_all:.1f} s")


if __name__ == "__main__":
    main()
