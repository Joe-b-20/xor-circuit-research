#!/usr/bin/env python3
"""
mixcolumns_core.py  --  shared math + verification for the record hunter.

Pure fact, no tuning knobs: the AES MixColumns spec (rebuilt from GF(2^8)), a
few bit helpers, the independent verifier used as the ground-truth oracle, and
two utilities the hunter needs -- loading a seed circuit into a value-set, and
building a from-scratch starting circuit.

Circuit format everywhere: a list of index pairs `gates = [[a, b], ...]` where
signals 0..31 are the inputs x0..x31 (signal i = mask 1<<i) and gate k produces
signal 32+k whose mask = sig[a] ^ sig[b].
"""
import json

# --------------------------------------------------------------------------
# AES MixColumns spec from GF(2^8).
# --------------------------------------------------------------------------
def _xtime(a):
    a <<= 1
    return (a ^ 0x11B) & 0xFF if (a & 0x100) else (a & 0xFF)


def _gf_mul(a, b):
    r = 0
    for i in range(8):
        if (b >> i) & 1:
            t = a
            for _ in range(i):
                t = _xtime(t)
            r ^= t
    return r & 0xFF


def mixcolumns_masks():
    coef = [2, 3, 1, 1]
    M = [[0] * 32 for _ in range(32)]
    for col in range(4):
        for k in range(4):
            c, ib = coef[k], (col + k) % 4
            for in_bit in range(8):
                v = _gf_mul(c, 1 << in_bit)
                for out_bit in range(8):
                    if (v >> out_bit) & 1:
                        M[col * 8 + out_bit][ib * 8 + in_bit] ^= 1
    return [sum(1 << c for c in range(32) if M[r][c]) for r in range(32)]


TARGETS = mixcolumns_masks()
TARGET_SET = frozenset(TARGETS)
INPUTS = [1 << i for i in range(32)]
INPUT_SET = frozenset(INPUTS)
assert sorted(bin(m).count("1") for m in TARGETS).count(5) == 20
assert sorted(bin(m).count("1") for m in TARGETS).count(7) == 12


def bits_of(m):
    return [b for b in range(32) if (m >> b) & 1]


def wt(m):
    return bin(m).count("1")


# --------------------------------------------------------------------------
# The verifier / oracle.
# --------------------------------------------------------------------------
def verify(gates, max_depth=None):
    """Replay an index-pair circuit; check every gate references earlier
    signals, all 32 outputs are produced, and (if given) depth <= max_depth.
    Returns {gates, depth, outputs, ok, problems}."""
    sig = [1 << i for i in range(32)]
    depth = [0] * 32
    problems = []
    for k, g in enumerate(gates):
        if len(g) != 2:
            problems.append("gate %d not 2-input" % k)
            sig.append(0); depth.append(0); continue
        a, b = g
        idx = 32 + k
        if not (0 <= a < idx and 0 <= b < idx):
            problems.append("gate %d references non-earlier signal" % k)
            sig.append(0); depth.append(0); continue
        sig.append(sig[a] ^ sig[b])
        depth.append(max(depth[a], depth[b]) + 1)
    built = set(sig)
    outputs = sum(1 for t in TARGETS if t in built)
    D = max(depth) if depth else 0
    ok = outputs == 32 and not problems and (max_depth is None or D <= max_depth)
    return {"gates": len(gates), "depth": D, "outputs": outputs,
            "ok": ok, "problems": problems}


def save(gates, path, extra=None):
    obj = {"gateCount": len(gates), "gates": gates}
    if extra:
        obj.update(extra)
    with open(path, "w") as f:
        json.dump(obj, f)
    return path


# --------------------------------------------------------------------------
# Load a seed circuit into a value-set (set of non-input masks).
# --------------------------------------------------------------------------
def load_circuit_masks(path):
    """Read a circuit JSON and return the SET of non-input signal masks it
    computes. Accepts index-pair gates {"gates":[[a,b],...]} or mask-triple
    gates {"gates":[{"m","a","b"}]} or a bare list of either."""
    with open(path) as f:
        data = json.load(f)
    gates = data["gates"] if isinstance(data, dict) else data
    if gates and isinstance(gates[0], dict):
        return set(int(g["m"]) & 0xFFFFFFFF for g in gates)
    sig = [1 << i for i in range(32)]
    for a, b in gates:
        sig.append(sig[a] ^ sig[b])
    return set(sig[32:])


# --------------------------------------------------------------------------
# From-scratch starting circuit: a balanced XOR tree per output (no sharing).
# 152 gates, depth 3 -- feasible for any depth cap >= 3. This is the cold start
# the reducing engines shrink down.
# --------------------------------------------------------------------------
def naive_circuit():
    """Return index-pair gates building every output as a balanced XOR tree
    (opportunistically reusing subexpressions). Depth 3."""
    sig_index = {1 << i: i for i in range(32)}
    gates = []

    def combine(a, b):
        m = a ^ b
        if m not in sig_index:
            gates.append([sig_index[a], sig_index[b]])
            sig_index[m] = 32 + len(gates) - 1
        return m

    for t in TARGETS:
        items = [1 << b for b in bits_of(t)]
        while len(items) > 1:
            nxt = []
            for k in range(0, len(items) - 1, 2):
                nxt.append(combine(items[k], items[k + 1]))
            if len(items) % 2 == 1:
                nxt.append(items[-1])
            items = nxt
    return gates


def naive_masks():
    """The value-set (non-input masks) of naive_circuit()."""
    sig = [1 << i for i in range(32)]
    for a, b in naive_circuit():
        sig.append(sig[a] ^ sig[b])
    return set(sig[32:])
