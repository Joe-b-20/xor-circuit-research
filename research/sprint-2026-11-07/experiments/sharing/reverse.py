"""Constructive transposition: build a minimum circuit for each group by (i) a greedy closure
circuit for the transposed map (4 inputs -> the 8 distinct nonbasis columns, one gate each) and
(ii) mechanical reversal (Lemma 2.2 of REPORT.md).  Verifies the result by evaluation and prints the
forward circuits (gate count must be |T| + n - 4 = 12 or 16).  Appends to minima.jsonl."""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from submaps import submatrix

HERE = os.path.dirname(os.path.abspath(__file__))


def closure_circuit(k, targets):
    """Greedy: gates computing targets from the k unit vectors, each gate = XOR of two available."""
    avail = {1 << i: ("in", i) for i in range(k)}
    gates = []   # (value, a, b)
    todo = set(targets) - set(avail)
    while todo:
        found = None
        for t in sorted(todo):
            for a in list(avail):
                b = a ^ t
                if b in avail and b != a:
                    found = (t, a, b)
                    break
            if found:
                break
        assert found, "targets not closable without extras"
        gates.append(found)
        avail[found[0]] = ("gate", len(gates) - 1)
        todo.discard(found[0])
    return gates


def reverse(k, gates, outputs):
    """gates: transposed circuit over k inputs (values are k-bit masks); outputs: list of values
    (one per forward input j, i.e. column j), possibly repeated.  Returns the forward circuit as a
    list of (value, a, b) over len(outputs) inputs, with forward outputs = the k unit vectors' r()."""
    n = len(outputs)
    # nodes: inputs 'i<idx>' and gates 'g<idx>'; users: operand edges; designations: output markers
    val_to_node = {}
    for i in range(k):
        val_to_node[1 << i] = ("in", i)
    for gi, (v, a, b) in enumerate(gates):
        val_to_node[v] = ("gate", gi)
    users = {}
    for gi, (v, a, b) in enumerate(gates):
        for o in (a, b):
            users.setdefault(val_to_node[o], []).append(("gate", gi))
    desig = {}
    for j, cv in enumerate(outputs):
        desig.setdefault(val_to_node[cv], []).append(j)
    # reverse values r(node) in GF(2)^n, computed from sinks backwards; forward gates created on the way
    fwd = []            # (value, a, b) over n forward inputs
    fwd_avail = {1 << j for j in range(n)}
    r = {}

    def term_values(node):
        terms = [1 << j for j in desig.get(node, [])]
        terms += [r[u] for u in users.get(node, [])]
        return terms

    order = [("gate", gi) for gi in range(len(gates) - 1, -1, -1)] + [("in", i) for i in range(k)]
    for node in order:
        terms = term_values(node)
        assert terms, "dead node"
        acc = terms[0]
        for t in terms[1:]:
            nv = acc ^ t
            assert acc != t
            fwd.append((nv, acc, t))
            fwd_avail.add(nv)
            acc = nv
        r[node] = acc
    fwd_outputs = [r[("in", i)] for i in range(k)]
    return fwd, fwd_outputs


def verify_forward(n, fwd, targets):
    avail = set(1 << j for j in range(n))
    for v, a, b in fwd:
        assert a in avail and b in avail and a != b and a ^ b == v
        avail.add(v)
    for t in targets:
        assert t in avail, "target missing"
    return True


if __name__ == "__main__":
    out = open(os.path.join(HERE, "minima.jsonl"), "a")
    for g in range(8):
        sup, fwd_targets, cols = submatrix([g])
        n = len(sup)
        T = sorted(set(c for c in cols if bin(c).count("1") >= 2))
        tg = closure_circuit(4, T)
        fwd, fouts = reverse(4, tg, cols)
        verify_forward(n, fwd, fwd_targets)
        assert sorted(fouts) == sorted(fwd_targets), (fouts, fwd_targets)
        # express in x-names
        names = {1 << i: f"x{sup[i]}" for i in range(n)}
        lines = []
        for idx, (v, a, b) in enumerate(fwd):
            names.setdefault(v, f"t{idx+1}")
            lines.append(f"{names[v]} = {names[a]} ^ {names[b]}")
        outs = {names[fouts[i]]: f"y{lib.GROUPS[g][i]}" for i in range(4)}
        print(f"group {g}: transposed closure gates {len(tg)}, forward gates {len(fwd)} (claimed minimum {lib.M_GROUP[g]}), verified")
        for l in lines:
            print("   " + l)
        print("   outputs: " + ", ".join(f"{yo} = {nm}" for nm, yo in outs.items()))
        out.write(json.dumps({"group": g, "mode": "reversal", "forward_gates": len(fwd), "gates": fwd,
                              "support": sup, "verified": True}) + "\n")
