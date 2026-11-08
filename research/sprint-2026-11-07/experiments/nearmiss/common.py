"""Shared loaders for the near-miss campaign (candidate D, A75/A76, 18-pair foundation state)."""
import json, os, sys
SAT = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/sat")
sys.path.insert(0, SAT)
import sat87
from sat87 import INPUTS, TARGETS, TSET, N

ARCH = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/import/zip/research")
DEEP = os.path.join(ARCH, "AES_Deep_Repair_75_76_Profiles_2026_10_02/aes_deep_repair/results/selected")
PAIR18 = os.path.join(ARCH, "18_pair_87_checkpoint/18_pair_87_checkpoint.txt")


def load_deep(tag, ngates):
    """First  gates of the known_completion file = the partial circuit itself; checked
    against the profile rows (signal -> actual mask)."""
    prof = json.load(open(os.path.join(DEEP, tag + ".json")))
    kc = json.load(open(os.path.join(DEEP, tag + ".known_completion.json")))
    assert prof["gates"] == ngates
    wire = list(INPUTS)
    order = []
    for a, b in kc["gates"][:ngates]:
        v = wire[a] ^ wire[b]
        order.append((v, wire[a], wire[b]))
        wire.append(v)
    for r in prof["rows"]:
        assert r["signal"] < 32 + ngates, "profile cites a signal beyond the partial circuit"
        assert wire[r["signal"]] == r["actual"]
    missing = [r["output"] for r in prof["rows"] if r["residual"]]
    return order, missing, prof


def depth_of(order):
    d = {v: 0 for v in INPUTS}
    for v, a, b in order:
        d[v] = 1 + max(d[a], d[b])
    return d


def parents(order):
    return {v: (a, b) for v, a, b in order}


def pairs18():
    txt = open(PAIR18).read()
    line = [l for l in txt.splitlines() if l.startswith("[(")][0]
    return [tuple(p) for p in json.loads(line.replace("(", "[").replace(")", "]"))]




P19 = os.path.join(ARCH, "mixcolumns_88_19_primitive_pairs/mixcolumns_88_19_primitive_pairs.txt")


def load_19pair_88():
    """The Sep 9 baseline: 88 gates, 19 primitive pairs (archive file, Full circuit section)."""
    import re
    sig = {"x%d" % j: 1 << j for j in range(N)}
    order = []
    started = False
    for line in open(P19):
        if line.startswith("Full circuit"):
            started = True
            continue
        if not started:
            continue
        m = re.match(r"^(g\d+)\s*=\s*(\S+)\s+XOR\s+(\S+)", line.strip())
        if not m:
            continue
        o, a, b = m.groups()
        sig[o] = sig[a] ^ sig[b]
        order.append((sig[o], sig[a], sig[b]))
    return order


def foundation18():
    """18 pairs + the rich values of the 19-pair 88 that regenerate (any-pair closure)."""
    order = load_19pair_88()
    vals = sat87.values_of(order)
    pv = [(1 << a) | (1 << b) for a, b in pairs18()]
    pg = [v for v, a, b in order if a in INPUTS and b in INPUTS]
    rich = [v for v in vals if v not in pg]
    K = pv + rich
    comp = set(sat87.values_of(sat87.wiring_from_values_partial(K)))
    missing = [v for v in K if v not in comp]
    K = [v for v in K if v in comp]
    assert sat87.split_closed(K)
    return order, K, missing, pv, rich
