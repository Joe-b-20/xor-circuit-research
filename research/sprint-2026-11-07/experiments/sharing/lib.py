"""Shared helpers for the sharing study (sprint 2026-11-07, agent 'sharing').

Conventions: a value is a 32-bit mask, bit j = x_j.  TARGETS[i] = row i of the matrix = y_i.
Group j (j = 0..7) = output rows {j, 8+j, 16+j, 24+j} (bit j of each of the 4 output bytes).
A wiring is a list of (v, a, b) with v = a ^ b, a and b earlier values or inputs.
"""
import json
import os
import random
import re

REPO = os.path.expanduser("~/xor-circuit-research")
MAT = os.path.join(REPO, "circuits/aes-mixcolumns/aes-mixcolumns.mat.txt")
CIRC = {
    "88@5": os.path.join(REPO, "circuits/aes-mixcolumns/aes-mixcolumns-xor88-depth5.circ.txt"),
    "89@4": os.path.join(REPO, "circuits/aes-mixcolumns/aes-mixcolumns-xor89-depth4.circ.txt"),
    "97@3": os.path.join(REPO, "circuits/aes-mixcolumns/aes-mixcolumns-xor97-depth3.circ.txt"),
}
SPRINT = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint")
SAMPLES = [os.path.join(SPRINT, "hunt", p) for p in ("samples.jsonl", "samplesC/samples.jsonl", "samplesD/samples.jsonl")]
N = 32
INPUTS = [1 << j for j in range(N)]
INSET = set(INPUTS)


def load_targets():
    toks = " ".join(l.split("%")[0] for l in open(MAT).read().splitlines()).split()
    r, c = int(toks[1]), int(toks[2])
    bits = list(map(int, toks[3:3 + r * c]))
    return [sum(bits[i * c + j] << j for j in range(c)) for i in range(r)]


TARGETS = load_targets()
TSET = set(TARGETS)
GROUPS = [[j, 8 + j, 16 + j, 24 + j] for j in range(8)]
GROUP_OF = {}
for g, rows in enumerate(GROUPS):
    for i in rows:
        GROUP_OF[TARGETS[i]] = g
GROUP_TARGETS = [[TARGETS[i] for i in rows] for rows in GROUPS]


def support(mask):
    return [j for j in range(N) if (mask >> j) & 1]


def group_support(g):
    m = 0
    for t in GROUP_TARGETS[g]:
        m |= t
    return support(m)


M_GROUP = [12, 16, 12, 16, 16, 12, 12, 12]   # archive's claim; re-derived in group_minima.py


# ------------------------------------------------------------------ loaders
def load_repo_circ(path):
    """Returns wiring list [(v, a, b)] in file order (gate order = topological)."""
    vals = {f"x{j}": 1 << j for j in range(N)}
    order = []
    for line in open(path):
        m = re.match(r"^XOR\s+(\S+)\s+(\S+)\s+(\S+)", line.strip())
        if not m:
            continue
        o, a, b = m.groups()
        vals[o] = vals[a] ^ vals[b]
        order.append((vals[o], vals[a], vals[b]))
    return order


def splits(v, avail):
    """All unordered pairs {a, b} within avail with a ^ b = v, a < b."""
    out = []
    for a in avail:
        b = a ^ v
        if b in avail and a < b:
            out.append((a, b))
    return out


def wiring_from_values(values, rng=None):
    """Topological wiring for a value set.  Greedy closure; if rng is given, the split and the
    order are chosen at random among the legal ones (to probe wiring dependence).  None if not
    closed."""
    avail = set(INPUTS)
    todo = set(values) - avail
    order = []
    while todo:
        cands = []
        for v in sorted(todo):
            sp = splits(v, avail)
            if sp:
                if rng is None:
                    cands.append((v, sp[0]))
                    break
                cands.append((v, rng.choice(sp)))
        if not cands:
            return None
        v, (a, b) = cands[0] if rng is None else rng.choice(cands)
        order.append((v, a, b))
        avail.add(v)
        todo.discard(v)
    return order


def load_samples(gates=88, paths=SAMPLES, dedup=True):
    out = []
    seen = set()
    for p in paths:
        if not os.path.exists(p):
            continue
        for i, line in enumerate(open(p)):
            d = json.loads(line)
            if d.get("gates") != gates:
                continue
            key = tuple(sorted(d["values"]))
            if dedup and key in seen:
                continue
            seen.add(key)
            out.append({"src": os.path.relpath(p, SPRINT), "line": i, "hash": d.get("hash"), "values": d["values"]})
    return out


def check_circuit(order):
    avail = {v: 0 for v in INPUTS}
    for v, a, b in order:
        assert a in avail and b in avail and a != b and a ^ b == v, "bad gate"
        avail[v] = 1 + max(avail[a], avail[b])
    for t in TARGETS:
        assert t in avail, "target missing"
    return len(order), max(avail[t] for t in TARGETS)


# ------------------------------------------------------------------ cones and sharing
def cones(order):
    """For a wiring: parents map and, per group, the cone (set of gate values that are ancestors
    of, or equal to, the group's 4 target values).  Inputs are not gates and are excluded."""
    par = {v: (a, b) for v, a, b in order}
    cone = []
    for g in range(8):
        seen = set()
        stack = [t for t in GROUP_TARGETS[g] if t in par]
        while stack:
            v = stack.pop()
            if v in seen:
                continue
            seen.add(v)
            for o in par[v]:
                if o in par and o not in seen:
                    stack.append(o)
        cone.append(seen)
    return par, cone


def sharing_stats(order):
    par, cone = cones(order)
    G = len(order)
    gate_vals = [v for v, _, _ in order]
    k = {v: sum(1 for g in range(8) if v in cone[g]) for v in gate_vals}
    dead = [v for v in gate_vals if k[v] == 0]
    S_mult = sum(max(k[v] - 1, 0) for v in gate_vals)
    S_cnt = sum(1 for v in gate_vals if k[v] >= 2)
    sizes = [len(c) for c in cone]
    delta_g = [sizes[g] - M_GROUP[g] for g in range(8)]
    delta = sum(delta_g)
    kdist = {}
    for v in gate_vals:
        kdist[k[v]] = kdist.get(k[v], 0) + 1
    pair_int = {}
    pair_union = {}
    for g in range(8):
        for h in range(g + 1, 8):
            pair_int[(g, h)] = len(cone[g] & cone[h])
            pair_union[(g, h)] = len(cone[g] | cone[h])
    # depth of each gate
    depth = {v: 0 for v in INPUTS}
    for v, a, b in order:
        depth[v] = 1 + max(depth[a], depth[b])
    shared_by_depth = {}
    for v in gate_vals:
        if k[v] >= 2:
            shared_by_depth[depth[v]] = shared_by_depth.get(depth[v], 0) + (k[v] - 1)
    # private gates per group (k == 1)
    private = [sum(1 for v in cone[g] if k[v] == 1) for g in range(8)]
    # inputs outside the group's support that the cone touches
    outside = []
    for g in range(8):
        sup = set(group_support(g))
        touched = set()
        for v in cone[g]:
            for o in par[v]:
                if o in INSET:
                    touched.add(o.bit_length() - 1)
        outside.append(len(touched - sup))
    return {
        "G": G, "dead": len(dead), "S_mult": S_mult, "S_cnt": S_cnt, "delta": delta,
        "delta_g": delta_g, "sizes": sizes, "kdist": dict(sorted(kdist.items())),
        "pair_int": pair_int, "pair_union": pair_union, "shared_by_depth": dict(sorted(shared_by_depth.items())),
        "private": private, "outside_inputs": outside, "k": k, "cone": cone, "depth": depth,
        "identity_ok": (G == sum(M_GROUP) + delta - S_mult + len(dead)),
    }


def relabel(mask, sup):
    """Compress a 32-bit mask to the bit positions in sup (list), i.e. restrict to the support."""
    return sum(((mask >> j) & 1) << i for i, j in enumerate(sup))
