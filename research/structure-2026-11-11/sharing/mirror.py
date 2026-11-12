"""Mirror (transpose) of the local family circuit cut out of a circuit for Q_m.

usage: python3 mirror.py m FILE j1,j2,...  f1,f2,...   [--quiet]
   sheets J = {j1, j2, ..} (own blocks), free blocks F = {f1, ..}; every other block is set to zero.

Follows sharing/INDEPENDENT-SHEETS.md Steps 0-3 literally on an existing circuit (no search):
  D      = gates that are ancestors-or-equal of an output gate of J and nonzero on an own block (after restriction)
  entry  = gate of D with exactly one operand whose restricted value is supported on F (zero included)
  formal = each entry's free operand is replaced by a new input z_i
  T      = transposed circuit on the inputs w_(j,c); |T| = sum over read signals of (reads - 1) = K - tau
Prints K = |D|, tau, |T|, the adjoints of the own units and of the z_i, and every signal of T with its
class (parity on each group).  Standard library only.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "rotation"))
import qm  # noqa: E402

NAMES = {0: "-", 0b0011: "s0", 0b0110: "s1", 0b1100: "s2", 0b1001: "s3", 0b0101: "d0", 0b1010: "d1", 0b1111: "t",
         0b0001: "e0", 0b0010: "e1", 0b0100: "e2", 0b1000: "e3",
         0b1110: "E0", 0b1101: "E1", 0b1011: "E2", 0b0111: "E3"}


def local_family(m, gates, J, F):
    """Returns dict with the cleaned local circuit: list of (gate id, opA, opB) where an operand is
    ('u', j, c) own unit, ('g', id) earlier D gate, ('z', i) formal entry input; plus phi values, targets."""
    n = 4 * m
    keep = set(J) | set(F)
    vals = []
    for i in range(n):
        vals.append((1 << i) if (i // 4) in keep else 0)
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    full = qm.masks(n, gates)
    targets = qm.rows(m)
    first = {}
    for i in range(n, n + len(gates)):
        first.setdefault(full[i], i)
    ownmask = sum(15 << (4 * j) for j in J)
    freemask = sum(15 << (4 * f) for f in F)
    tgt_gate = {}
    for j in J:
        for c in range(4):
            tgt_gate[(j, c)] = first[targets[4 * j + c]]
    anc = set()
    stack = list(tgt_gate.values())
    while stack:
        s = stack.pop()
        if s < n or s in anc:
            continue
        anc.add(s)
        stack.extend(gates[s - n])
    D = sorted(g for g in anc if vals[g] & ownmask)
    Dset = set(D)
    circ, phi = [], []
    for g in D:
        ops = []
        nfree = 0
        for o in gates[g - n]:
            if o in Dset:
                ops.append(("g", o))
            elif o < n and (o // 4) in J:
                ops.append(("u", o // 4, o % 4))
            else:
                assert vals[o] & ~freemask == 0, (g, o)
                ops.append(("free", vals[o]))
                nfree += 1
        assert nfree <= 1, "gate of D with two free operands"
        if nfree == 1:
            k = 0 if ops[0][0] == "free" else 1
            phi.append(ops[k][1])
            ops[k] = ("z", len(phi) - 1)
        circ.append((g, ops[0], ops[1]))
    return dict(circ=circ, phi=phi, targets=tgt_gate, vals=vals, n=n)


def mirror(loc, J):
    """Adjoints: for every signal the set of targets (as a bit mask over (j_index, c)) whose formal mask contains it.
    Returns adjoint dict, number of gates of T, list of T gate masks (partial sums in reader order)."""
    Jl = list(J)
    tbit = {(j, c): 1 << (4 * Jl.index(j) + c) for j in Jl for c in range(4)}
    readers = {}
    for g, a, b in loc["circ"]:
        for o in (a, b):
            readers.setdefault(o, []).append(("g", g))
    tg = {}
    for key, g in loc["targets"].items():
        tg.setdefault(("g", g), []).append(tbit[key])
    adj = {}
    tgates = []
    order = [("g", g) for g, _, _ in loc["circ"]][::-1]
    order += [("z", i) for i in range(len(loc["phi"]))]
    order += [("u", j, c) for j in Jl for c in range(4)]
    for s in order:
        contrib = list(tg.get(s, [])) + [adj[r] for r in readers.get(s, [])]
        if not contrib:
            adj[s] = 0
            continue
        acc = contrib[0]
        for x in contrib[1:]:
            acc ^= x
            tgates.append(acc)
        adj[s] = acc
    return adj, tgates


def fmt(v, r):
    return " | ".join("".join(str((v >> (4 * i + c)) & 1) for c in range(4)) for i in range(r))


def main():
    m = int(sys.argv[1])
    n, gates = qm.read_circuit(sys.argv[2])
    J = [int(x) for x in sys.argv[3].split(",")]
    F = [int(x) for x in sys.argv[4].split(",")]
    quiet = "--quiet" in sys.argv
    loc = local_family(m, gates, J, F)
    adj, tgates = mirror(loc, J)
    K, tau = len(loc["circ"]), len(loc["phi"])
    r = len(J)
    print(f"{os.path.basename(sys.argv[2])}: sheets {J}, free blocks {F}: K = |D| = {K}, tau = {tau}, |T| = {len(tgates)} "
          f"(K - tau = {K - tau})")
    if quiet:
        return
    print("adjoints of own units (groups in the order of J):")
    for j in J:
        for c in range(4):
            print(f"   unit ({c},{j}): {fmt(adj[('u', j, c)], r)}")
    print("entries: free operand (blocks) and export zeta:")
    for i, p in enumerate(loc["phi"]):
        d = " ".join(f"{b}:{NAMES[(p >> (4 * b)) & 15]}" for b in range(m) if (p >> (4 * b)) & 15) or "0"
        print(f"   z{i}: phi = [{d}]   zeta = {fmt(adj[('z', i)], r)}")
    print("gates of T (masks; class = parity on each group):")
    for t in tgates:
        cls = "".join("o" if bin((t >> (4 * i)) & 15).count("1") & 1 else "e" for i in range(r))
        print(f"   {fmt(t, r)}   {cls}")
    distinct = len(set(tgates))
    print(f"distinct masks among the gates of T: {distinct}")


if __name__ == "__main__":
    main()
