"""Mirror (transpose) of a given local circuit of J_01, printed in the (omega | s) notation of pair/PROOF.md.

Inspection of ONE given circuit (default: G01 of the recorded 88-gate MixColumns circuit). Proves nothing universal.

Local circuit: gates over units of b (block 0), units of b' (block 1), free vectors on a (block 7).
Entry = gate with a free operand; tau = number of entries.  T has inputs w_c (target c of sheet 0) and
w'_c (target c of sheet 1); adjoint of a signal = set of targets whose formal mask contains it.
Checks: adjoint(b_i) = A_i = (E_i | p_i), adjoint(b'_i) = B_i = (0 | E_i), p_i = u_(i-1) + u_i;
the adjoints of the entries span a space containing the diagonal {(e | e): e even}.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "rotation", "mc"))
import mc  # noqa: E402


def nib(v, j):
    return sum(((v >> (8 * c + j)) & 1) << c for c in range(4))


def s4(x):
    return "".join(str((x >> c) & 1) for c in range(4))


def fm(v):
    return s4(v & 15) + " | " + s4(v >> 4)


def rank(vs):
    basis = []
    for v in vs:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    return len(basis)


def main():
    f = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        HERE, "..", "..", "..", "circuits", "aes-mixcolumns", "aes-mixcolumns-xor88-depth5.circ.txt")
    gates = mc.parse_ncff(f)
    n = 32
    vals = [1 << i for i in range(n)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    first = {}
    for i in range(n, len(vals)):
        first.setdefault(vals[i], i)
    tgt = {}
    for j in (0, 1):
        for c in range(4):
            tgt[first[mc.TARGETS[8 * c + j]]] = 1 << (4 * j + c)
    anc, stack = set(), list(tgt)
    while stack:
        g = stack.pop()
        if g < n or g in anc:
            continue
        anc.add(g)
        stack.extend(gates[g - n])
    G = sorted(g for g in anc if mc.blocks(vals[g]) != frozenset([7]))
    Gs = set(G)
    readers = {}
    entries = []
    for g in G:
        for o in gates[g - n]:
            if o in Gs or (o < n and o % 8 in (0, 1)):
                readers.setdefault(o, []).append(g)
            else:
                assert mc.blocks(vals[o]) <= frozenset([7])
                entries.append((g, nib(vals[o], 7)))
    adj, tg = {}, []
    order = G[::-1] + [8 * c + j for j in (0, 1) for c in range(4)]
    for sgn in order:
        contrib = ([tgt[sgn]] if sgn in tgt else []) + [adj[r] for r in readers.get(sgn, [])]
        acc = contrib[0]
        for x in contrib[1:]:
            acc ^= x
            tg.append(acc)
        adj[sgn] = acc
    K, tau = len(G), len(entries)
    print("K = %d, tau = %d, |T| = %d (K - tau = %d)" % (K, tau, len(tg), K - tau))
    for i in range(4):
        E = 15 ^ (1 << i)
        p = (1 << i) | (1 << ((i - 1) % 4))
        assert adj[8 * i + 0] == E | (p << 4), "A_i"
        assert adj[8 * i + 1] == (E << 4), "B_i"
    print("adjoints of the units are A_i = (E_i | p_i) and B_i = (0 | E_i): checked")
    ex = [adj[g] for g, _ in entries]
    print("exports (adjoints of the entries), with the free operand of the entry:")
    for (g, phi), z in zip(entries, ex):
        print("   phi = %s   export = %s" % (s4(phi), fm(z)))
    diag = [(e | (e << 4)) for e in (0b0011, 0b0110, 0b1100)]
    assert rank(ex + diag) == rank(ex), "diagonal not in the export space"
    print("export space has dimension %d and contains the diagonal space: checked" % rank(ex))
    seen = {1 << i: "input" for i in range(8)}
    print("gates of T in order (omega | s), class: S0 = pure first, O0 = pure second, D0 = diagonal, gen = other;")
    print("first/dup refers to the fibre of omega")
    fib = {1 << i for i in range(4)}
    cnt = {"first": 0, "dup": 0, "N0": 0}
    for t in tg:
        om, sp = t & 15, t >> 4
        cls = "O0" if om == 0 else "S0" if sp == 0 else "D0" if om == sp else "gen"
        if om == 0:
            role = "N0"
        elif om in fib:
            role = "dup"
        else:
            role = "first"
            fib.add(om)
        cnt[role] += 1
        rep = "  (value seen before)" if t in seen else ""
        seen.setdefault(t, "gate")
        print("   %s   %-3s %-5s%s%s" % (fm(t), cls, role, "  EXPORT" if t in ex else "", rep))
    print("f = %(first)d, D = %(dup)d, N_0 = %(N0)d" % cnt)


if __name__ == "__main__":
    main()
