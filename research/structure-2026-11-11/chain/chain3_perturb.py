"""Chain of three: the checks of chain3.py on randomly perturbed valid local circuits (these have exits,
non-entry duplicates, zero gates).  Base circuits: runs of three sheets of q4_40 and q8_80.
Moves (each keeps every target value; none is a search for small circuits):
  M2 operand x -> (x + u) + u, u a random earlier signal (unit, free vector, gate)
  M3 g = x + y -> (x + u) + (y + u)
  M4 g = x + h, h = y + z -> (x + y) + z; h deleted if it has no other reader and is no target
  M5 g = x + f (f free) -> (x + f1) + (f + f1)
A test on perturbed existing circuits; it proves nothing universal.  Standard library only.
"""
import os
import random
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import chain3 as C  # noqa: E402
R = C.R

rng = random.Random(20261112)


def avail(nodes, p):
    c = rng.random()
    if c < 0.3:
        return ("u", rng.randrange(C.NU))
    if c < 0.45 or p == 0:
        return ("f", rng.randrange(16))
    return ("g", nodes[rng.randrange(p)][0])


def move(nodes, tg_ids, nxt):
    p = rng.randrange(len(nodes))
    ops = nodes[p][1]
    kind = rng.choice(["M2", "M3", "M4", "M4", "M5"])
    if kind == "M2":
        r = rng.randrange(2)
        u = avail(nodes, p)
        nodes.insert(p, [nxt + 1, [("g", nxt), u]])
        nodes.insert(p, [nxt, [ops[r], u]])
        ops[r] = ("g", nxt + 1)
        return kind, nxt + 2
    if kind == "M3":
        u = avail(nodes, p)
        nodes.insert(p, [nxt + 1, [ops[1], u]])
        nodes.insert(p, [nxt, [ops[0], u]])
        nodes[p + 2][1] = [("g", nxt), ("g", nxt + 1)]
        return kind, nxt + 2
    if kind == "M4":
        r = rng.randrange(2)
        h = ops[r]
        if h[0] != "g":
            return None, nxt
        hp = next(q for q, (i, _) in enumerate(nodes) if i == h[1])
        y, z = nodes[hp][1]
        if rng.random() < 0.5:
            y, z = z, y
        nodes.insert(p, [nxt, [ops[1 - r], y]])
        nodes[p + 1][1] = [("g", nxt), z]
        readers = sum(1 for _, o2 in nodes for o in o2 if o == ("g", h[1]))
        if readers == 0 and h[1] not in tg_ids:
            del nodes[hp]
        return kind, nxt + 1
    r = 0 if ops[0][0] == "f" else (1 if ops[1][0] == "f" else None)
    if r is None:
        return None, nxt
    f1 = rng.randrange(1, 16)
    nodes.insert(p, [nxt, [ops[1 - r], ("f", f1)]])
    nodes[p + 1][1] = [("g", nxt), ("f", ops[r][1] ^ f1)]
    return kind, nxt + 1


def main():
    bases = []
    for fn, m in (("q4_40.txt", 4), ("q8_80.txt", 8)):
        model = R.qm_model(m)
        n, g = R.read_qm(os.path.join(R.QDIR, fn))
        for j in range(m):
            bases.append(C.local_chain(model, n, g, j))
    want = [(R.E4(c) << (4 * (k + 1))) | (R.S4(c) << (4 * k)) for k in range(C.L) for c in range(4)]
    N = 600
    fails, hist = [], Counter()
    with_exit3 = with_exit1 = with_nonentry = skipped = 0
    mink = 99
    for trial in range(N):
        lc, tg = rng.choice(bases)
        nodes = [[i, list(ops)] for i, ops in enumerate(lc)]
        tg_ids = list(tg)
        nxt = len(nodes)
        for _ in range(rng.randint(1, 10)):
            _, nxt = move(nodes, tg_ids, nxt)
        pos = {nid: q for q, (nid, _) in enumerate(nodes)}
        lc2 = [tuple(("g", pos[o[1]]) if o[0] == "g" else o for o in ops) for _, ops in nodes]
        tg2 = [pos[t] for t in tg_ids]
        v = R.lval(lc2)
        assert [v[t] for t in tg2] == want, "move broke the circuit"
        try:
            lc3, tg3 = R.clean(lc2, tg2)
        except AssertionError:
            skipped += 1
            continue
        try:
            s = C.stats(C.mirror(lc3, tg3, rng))
        except AssertionError as e:
            fails.append((trial, str(e)))
            continue
        mink = min(mink, s["red"] + s["tau_red"])
        hist[(s["p3"]["D"] + s["p3"]["N"])] += 1
        with_exit3 += s["p3"]["exits"] > 0
        with_exit1 += s["p1"]["exits"] > 0
        with_nonentry += s["p3"]["nonentry"] > 0
    print("perturbed chain circuits: %d (skipped in cleaning: %d)" % (N, skipped))
    print("failures of the checks (mirror form, f12 + tau >= 20, D + N >= 9, f1 + tau >= 10, 29):", len(fails), fails[:5])
    print("smallest reduced |T| + tau:", mink)
    print("histogram of D + N at the last group:", dict(sorted(hist.items())))
    print("with last-group exits: %d; with level-1 exits: %d; with non-entry duplicates: %d" % (
        with_exit3, with_exit1, with_nonentry))


if __name__ == "__main__":
    main()
