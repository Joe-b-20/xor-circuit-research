"""Review item 1 (numerics): Lemma 3.1 (a)-(d) and the mirror count on randomly perturbed valid pair circuits.

Base circuits: the pair sub-circuits of q4_40, q8_80, q3_28 and the three recorded MixColumns circuits.
Moves (each keeps every target value computed; most add gates, M4 can be size-neutral):
  M1 operand x -> (x + f) + f, f a random free vector
  M2 operand x -> (x + u) + u, u a random earlier signal (unit, free, gate)
  M3 g = x + y -> (x + u) + (y + u)
  M4 g = x + h, h = y + z -> (x + y) + z, h deleted if it has no other reader and is no target
  M5 g = x + f (f free) -> (x + f1) + (f + f1)
Random accumulation orders in the mirror.  A test, not a proof.
"""
import os
import random
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rlib as R  # noqa: E402

rng = random.Random(20261112)


def to_nodes(lc):
    return [[i, list(ops)] for i, ops in enumerate(lc)]


def from_nodes(nodes, tg_ids):
    pos = {nid: p for p, (nid, _) in enumerate(nodes)}
    lc = [tuple(("g", pos[o[1]]) if o[0] == "g" else o for o in ops) for _, ops in nodes]
    return lc, [pos[t] for t in tg_ids]


def avail(nodes, p):
    c = rng.random()
    if c < 0.3:
        return ("u", rng.randrange(8))
    if c < 0.5 or p == 0:
        return ("f", rng.randrange(16))
    return ("g", nodes[rng.randrange(p)][0])


def move(nodes, tg_ids, nxt):
    p = rng.randrange(len(nodes))
    nid, ops = nodes[p]
    kind = rng.choice(["M1", "M2", "M3", "M4", "M4", "M5"])
    if kind == "M1":
        r = rng.randrange(2)
        f = ("f", rng.randrange(1, 16))
        t1, t2 = nxt, nxt + 1
        nodes.insert(p, [t2, [("g", t1), f]])
        nodes.insert(p, [t1, [ops[r], f]])
        ops[r] = ("g", t2)
        return kind, nxt + 2
    if kind == "M2":
        r = rng.randrange(2)
        u = avail(nodes, p)
        t1, t2 = nxt, nxt + 1
        nodes.insert(p, [t2, [("g", t1), u]])
        nodes.insert(p, [t1, [ops[r], u]])
        ops[r] = ("g", t2)
        return kind, nxt + 2
    if kind == "M3":
        u = avail(nodes, p)
        t1, t2 = nxt, nxt + 1
        nodes.insert(p, [t2, [ops[1], u]])
        nodes.insert(p, [t1, [ops[0], u]])
        nodes[p + 2][1] = [("g", t1), ("g", t2)]
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
        t = nxt
        nodes.insert(p, [t, [ops[1 - r], y]])
        nodes[p + 1][1] = [("g", t), z]
        readers = sum(1 for _, o2 in nodes for o in o2 if o == ("g", h[1]))
        if readers == 0 and h[1] not in tg_ids:
            del nodes[hp]
        return kind, nxt + 1
    if kind == "M5":
        r = 0 if ops[0][0] == "f" else (1 if ops[1][0] == "f" else None)
        if r is None:
            return None, nxt
        f1 = rng.randrange(1, 16)
        t = nxt
        nodes.insert(p, [t, [ops[1 - r], ("f", f1)]])
        nodes[p + 1][1] = [("g", t), ("f", ops[r][1] ^ f1)]
        return kind, nxt + 1


bases = []
mc = R.mc_model()
for f in ("aes-mixcolumns-xor88-depth5.circ.txt", "aes-mixcolumns-xor89-depth4.circ.txt",
          "aes-mixcolumns-xor97-depth3.circ.txt"):
    n, g = R.read_ncff(os.path.join(R.MCDIR, f))
    for j in (1, 2, 3, 4, 5, 6, 7):
        bases.append(("%s:%d" % (f[17:22], j),) + R.local_pair(mc, n, g, j))
for f, m in (("q8_80.txt", 8), ("q3_28.txt", 3), ("q4_40.txt", 4)):
    qm = R.qm_model(m)
    n, g = R.read_qm(os.path.join(R.QDIR, f))
    for j in range(m):
        bases.append(("%s:%d" % (f, j),) + R.local_pair(qm, n, g, j))

N = 600
moves = Counter()
fails = []
minK = 99
hist_tau1 = Counter()
texit_cases = 0
nonentry_cases = 0
zero_gate_cases = 0
for trial in range(N):
    name, lc, tg = rng.choice(bases)
    nodes = to_nodes(lc)
    tg_ids = list(tg)
    nxt = len(nodes)
    for _ in range(rng.randint(1, 8)):
        kind, nxt = move(nodes, tg_ids, nxt)
        if kind:
            moves[kind] += 1
    lc2, tg2 = from_nodes(nodes, tg_ids)
    v = R.lval(lc2)
    assert [v[t] for t in tg2] == R.pair_targets_local(), "move broke the circuit"
    lc3, tg3 = R.clean(lc2, tg2)
    if any(x == 0 for x in R.lval(lc3)):
        zero_gate_cases += 1
    try:
        st = R.tstats(R.mirror(lc3, tg3, order="random", rng=rng))
    except AssertionError as e:
        fails.append((trial, name, str(e)))
        continue
    minK = min(minK, st["K"])
    hist_tau1[st["tau1"]] += 1
    texit_cases += st["texits"] > 0
    nonentry_cases += st["nonentry_dup"] > 0
print("perturbed circuits:", N, " moves applied:", dict(moves))
print("failures of the Lemma 3.1 checks / mirror count:", len(fails), fails[:5])
print("min K among perturbed:", minK, " tau' histogram:", dict(sorted(hist_tau1.items())))
print("cases with T-exits:", texit_cases, " with non-entry duplicates:", nonentry_cases,
      " with zero-valued local gates:", zero_gate_cases)
