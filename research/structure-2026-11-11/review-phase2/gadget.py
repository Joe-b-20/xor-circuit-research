"""Is 'projecting a derivation onto the blocks of J' a local system (square, invertible)?
Construct a valid (non-minimal) circuit in which it is not: a free vector a + b (two inputs of the
neighbour block) is recomputed through the own block j:  y1 = e + a, y2 = e + b, g = y1 + y2
(e a unit of block j).  The triples of y1, y2, g are live on block j and all lie in T_o whenever g does,
but their incidence on the live unknowns {y1, y2} has rank 2 with 3 rows.
Then check that the repaired construction (row basis, column basis containing the targets, unknowns
outside it set to 0) still yields a valid local system with the right target values and that
|Lam_J| >= 10|J| holds.  Inspection of designed objects only.
"""
from rp_lib import ROOT, all_triples, derivations, values
from review_causal import (ROT, based_from_circuit, lam, lemma23_check, output_index, projection_check,
                           qm_model, mc_model, MC)
from rp_lib import load_txt, load_ncff


def try_gadget(model, n, gates, label):
    S = values(n, gates)
    found = 0
    for gi, (a, b) in enumerate(gates):
        if a >= n or b >= n:
            continue
        v = S[n + gi]
        blocks = model.blocks_of(v)
        if len(blocks) != 1:
            continue
        k = blocks.pop()
        # pick an own block j != k of some sheet whose free part contains block k
        for j in range(model.nsheets):
            if j == k or k not in model.supp[j]:
                continue
            for e in range(n):
                if not (S[e] & model.blockmask[j]):
                    continue
                # new circuit: insert y1 = e + a, y2 = e + b before gate gi, and gate gi := y1 + y2
                new = []
                remap = {}
                for gj, (p, q) in enumerate(gates):
                    if gj == gi:
                        new.append((e, a))
                        new.append((e, b))
                        y1 = n + len(new) - 2
                        y2 = n + len(new) - 1
                        new.append((y1, y2))
                        remap[n + gj] = n + len(new) - 1
                    else:
                        new.append((remap.get(p, p), remap.get(q, q)))
                        remap[n + gj] = n + len(new) - 1
                S2 = values(n, new)
                if len(set(S2)) != len(S2) or 0 in S2:
                    continue
                if not all(r in set(S2) for r in model.rows):
                    continue
                S2, T2 = based_from_circuit(n, new)
                outs = output_index(S2, model.rows)
                deriv = derivations(S2, n, T2)
                J = (j,)
                L, _ = lam(model, S2, T2, n, outs, deriv, J)
                nl, nu, rk, (K, ok) = projection_check(model, S2, T2, n, outs, deriv, J)
                if not (nl == nu == rk):
                    res = lemma23_check(model, S2, T2, n, outs, deriv, J)
                    print(f"{label}: gate {gi} (value on block {k}) rerouted through block {j} via unit {e}: "
                          f"G = {len(new)}; |Lam_J| = {nl}, live unknowns |U'| = {nu}, rank = {rk}; "
                          f"repaired system K = {K}, targets correct = {ok}; Lemma 2.3 checks: "
                          f"cyclic={res.get('cyclic')} c1={res.get('c1')} c2={res.get('c2')} c3={res.get('c3')} "
                          f"K>=10={res.get('ten')}")
                    found += 1
                    if found >= 3:
                        return
                break
    if not found:
        print(f"{label}: no gadget instance found")


def main():
    q4 = qm_model(4)
    n, g = load_txt(ROT + "q4_40.txt")
    try_gadget(q4, n, g, "Q4 40")
    q3 = qm_model(3)
    n, g = load_txt(ROT + "q3_28.txt")
    try_gadget(q3, n, g, "Q3 28")
    mc = mc_model()
    n, g, _ = load_ncff(MC + "aes-mixcolumns-xor88-depth5.circ.txt")
    try_gadget(mc, n, g, "MC 88")


if __name__ == "__main__":
    main()
