"""CHECK (phase 10, main agent): the cancellation-copy candidate measured on specified circuits.

Ordinary linear algebra on explicitly given circuits; direct construction and evaluation only. No SAT, no
search, no enumeration of circuits, no least-gate computation.

Definitions (COPIES.md section 2). Blocks partition the coordinates. For a gate e = a + b, its cancelled blocks
are C(e) = {c : pi_c(a) != 0 and pi_c(e) = 0} (then pi_c(b) = pi_c(a)); if C(e) is nonempty e is an *event* and
its copy is kappa(e) = pi_C(e)(a), a vector of the ambient space V = F_2^n.
  Q0  = rank of all copies in V (no baseline);
  QX  = rank of the copies modulo span(inputs);  QY = modulo span(outputs);
  Q2  = rank of the copies of events whose two operands are neither inputs nor outputs (combinatorial
        exemption), with N = number of gates that are not outputs;
  recipient form: for a node h that is an ancestor of rows of >= 2 sheets and every such sheet j,
        u(h, j) = h restricted to the blocks outside W_j; reported: rank of all u, and the largest rank
        contributed by a single h.
  partner capacity: for each node b, the rank of the copies of the events having b as an operand.
usage: python3 copyrank.py [KSTE_FILE:LINE ...]   (runs every example below, then the given corpus lines)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ST = os.path.join(HERE, "..")


def rank(vs):
    basis = {}
    for v in vs:
        while v:
            h = v.bit_length() - 1
            if h in basis:
                v ^= basis[h]
            else:
                basis[h] = v
                break
    return len(basis)


def measure(name, n, gates, rows, bmasks, sheet_of=None):
    """rows: list of output masks; sheet_of: dict mask -> sheet (for the recipient form) or None."""
    vals = [1 << i for i in range(n)]
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    assert all(r in vals[n:] for r in rows), name + ": does not compute its rows"
    assert len(set(vals)) == len(vals) and 0 not in vals, name + ": not reduced"
    outs = set(rows)
    proj = lambda v, C: v & sum(bmasks[c] for c in C)
    ev, ev_out, ev2, copies, copies2 = 0, 0, 0, [], []
    by_operand = {}
    for gi, (a, b) in enumerate(gates):
        e = vals[n + gi]
        C = [c for c in range(len(bmasks)) if vals[a] & bmasks[c] and not e & bmasks[c]]
        if not C:
            continue
        k = proj(vals[a], C)
        assert k == proj(vals[b], C)          # Lemma S1
        ev += 1
        ev_out += e in outs
        copies.append(k)
        for x in (a, b):
            by_operand.setdefault(x, []).append(k)
        if a >= n and b >= n and vals[a] not in outs and vals[b] not in outs:
            ev2 += 1
            copies2.append(k)
    ins = [1 << i for i in range(n)]
    Q0 = rank(copies)
    QX = rank(copies + ins) - rank(ins)
    QY = rank(copies + list(outs)) - rank(list(outs))
    Q2 = rank(copies2)
    N = len([v for v in vals[n:] if v not in outs])
    cap = max((rank(v), x) for x, v in by_operand.items()) if by_operand else (0, -1)
    line = ("%s: G %d, |Y| %d, non-output gates N %d | events %d (outputs %d) Q0 %d QX %d QY %d | "
            "non-exempt events %d Q2 %d | max partner capacity %d (node %s)"
            % (name, len(gates), len(outs), N, ev, ev_out, Q0, QX, QY, ev2, Q2, cap[0], cap[1]))
    if sheet_of is not None:
        sheets = sorted(set(sheet_of.values()))
        win = {j: [c for c in range(len(bmasks)) if any(r & bmasks[c] for r, s in sheet_of.items() if s == j)]
               for j in sheets}
        idx = {v: i for i, v in enumerate(vals)}
        anc = {}
        for j in sheets:
            st, A = [idx[r] for r, s in sheet_of.items() if s == j], set()
            while st:
                x = st.pop()
                if x in A:
                    continue
                A.add(x)
                if x >= n:
                    st.extend(gates[x - n])
            anc[j] = A
        us, best = [], (0, -1)
        for x in range(len(vals)):
            js = [j for j in sheets if x in anc[j]]
            if len(js) < 2:
                continue
            ux = [vals[x] & ~sum(bmasks[c] for c in win[j]) for j in js]
            ux = [u for u in ux if u]
            us += ux
            best = max(best, (rank(ux), x))
        line += " | recipient form: rank %d (mod span Y %d), one node up to %d (node %s)" % (
            rank(us), rank(us + list(outs)) - rank(list(outs)), best[0], best[1])
    print(line)


def unit_blocks(n):
    return [1 << i for i in range(n)]


def sanity():
    # x, y, z, w = 0, 1, 2, 3: p = x+y; (x+z)+p = y+z; (y+w)+p = x+w
    g = [(0, 1), (0, 2), (1, 3), (5, 4), (6, 4)]
    measure("sanity (user's p = x+y)", 4, g, [0b0110, 0b1001], unit_blocks(4))


def chain(n):
    # prefix chain P_2..P_n (outputs) and outputs S + x_i: G = |Y|, every output S + x_i an event
    g, last = [(0, 1)], n
    for i in range(2, n):
        g.append((last, i))
        last = n + len(g) - 1
    for i in range(n - 1):              # S + x_(n-1) is the prefix P_(n-1), already present
        g.append((last, i))
    vals = [1 << i for i in range(n)]
    for a, b in g:
        vals.append(vals[a] ^ vals[b])
    measure("chain n=%d (prefixes and S+x_i all outputs)" % n, n, g, vals[n:], unit_blocks(n))


def pairs(k):
    # coordinates = unordered pairs {i, j}; a_i = sum of the k-1 coordinates containing i.
    P = [(i, j) for i in range(k) for j in range(i + 1, k)]
    n = len(P)
    co = {p: t for t, p in enumerate(P)}
    g, outs, a_node = [], [], {}
    for i in range(k):
        mine = [co[p] for p in P if i in p]
        acc = mine[1]
        for t in mine[2:]:              # v_i = sum of all but the first coordinate (declared outputs)
            g.append((acc, t))
            acc = n + len(g) - 1
            outs.append(acc)
        g.append((mine[0], acc))        # a_i = x_first + v_i (not an output)
        a_node[i] = n + len(g) - 1
    for i in range(k):
        for j in range(i + 1, k):
            g.append((a_node[i], a_node[j]))   # a_i + a_j: cancels coordinate {i, j}
            outs.append(n + len(g) - 1)
    vals = [1 << i for i in range(n)]
    for a, b in g:
        vals.append(vals[a] ^ vals[b])
    measure("pairs k=%d (a_i only non-outputs)" % k, n, g, [vals[o] for o in outs], unit_blocks(n))


def q3():
    sys.path.insert(0, os.path.join(ST, "cancel"))
    ls = [l.split("#")[0].strip() for l in open(os.path.join(ST, "rotation", "circuits", "q3_28.txt"))]
    ls = [l for l in ls if l]
    n, k = map(int, ls[0].split())
    g = [tuple(map(int, l.split()[:2])) for l in ls[1:1 + k]]
    m = 3
    E = lambda c: 15 ^ (1 << c)
    S = lambda c: (1 << c) | (1 << ((c + 1) % 4))
    rows = {}
    for j in range(m):
        for c in range(4):
            rows[(E(c) << (4 * j)) | (S(c) << (4 * ((j - 1) % m)))] = j
    measure("Q_3 (q3_28)", n, g, list(rows), [15 << (4 * j) for j in range(m)], rows)


def mc(spec):
    sys.path.insert(0, os.path.join(ST, "compose", "compat"))
    from clib import ROWS, bm, load  # noqa: E402
    g = [tuple(x) for x in json.load(open(spec))] if spec.endswith(".json") else load(spec)
    sheet_of = {r: t for (i, t), r in ROWS.items()}
    measure("MixColumns " + os.path.basename(spec), 32, g, list(ROWS.values()), [bm(j) for j in range(8)],
            sheet_of)


if __name__ == "__main__":
    sanity()
    chain(8)
    for k in (5, 6, 8):                  # k = 4 is not reduced: a_0 + a_1 = a_2 + a_3 (the a_i sum to 0)
        pairs(k)
    q3()
    for s in ("r88", "r89", os.path.join(ST, "cancel", "witness", "witness_mc_block.json"),
              os.path.join(ST, "cancel", "witness", "witness_mc_wire.json")) + tuple(sys.argv[1:]):
        mc(s)
