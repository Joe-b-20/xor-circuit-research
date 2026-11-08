"""Shared helpers for the inverse-transfer study (sprint 2026-11-07, agent invtransfer).
Read-only outside ~/xs-campaigns/2026-11-07-sprint/invtransfer.  Space = pes_lib.make_space("inv", 5)."""
import glob
import json
import os
import re
import sys

sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
import pes_lib  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")
REPO = HOME + "/xor-circuit-research"
INVDIR = REPO + "/circuits/aes-invmixcolumns"
MAT = INVDIR + "/aes-invmixcolumns.mat.txt"
N = 32
INPUTS = [1 << j for j in range(N)]
INSET = set(INPUTS)

RECORD_GLOBS = [
    HOME + "/xs-campaigns/2026-10-31-adopt/runs/*/workers/*/records/g118-d5-*.json",
    HOME + "/xs-campaigns/2026-11-05-inv118/runs/*/workers/*/records/g118-d5-*.json",
    HOME + "/xs-campaigns/2026-11-06-layout/workers/runs/*/workers/*/records/g118-d5-*.json",
    HOME + "/xs-campaigns/2026-11-03-waits/runs/*/workers/*/records/g118-d5-*.json",
    HOME + "/xs-campaigns/2026-11-04-12h/runs/*/workers/*/records/g118-d5-*.json",
    HOME + "/xs-campaigns/2026-11-05-inv-star/runs/*/workers/*/records/g118-d5-*.json",
    INVDIR + "/logs/*/record.json",
]
ARCHIVE88 = {
    "arch88d19": HOME + "/xs-campaigns/2026-11-07-sprint/import/zip/research/AES_OPTIMALITY_ALL_FINDINGS_COMPLETE_PUSH9_2026-10-20/AES_OPTIMALITY_ALL_FINDINGS_2026-10-17/audits/AES_NEW_FACTS_AUDIT_2026-10-15/run/controls/inverse/invmc_bigen_88_depth19_idx1571840.json",
    "arch88d33": HOME + "/xs-campaigns/2026-11-07-sprint/import/zip/research/AES_OPTIMALITY_ALL_FINDINGS_COMPLETE_PUSH9_2026-10-20/AES_OPTIMALITY_ALL_FINDINGS_2026-10-17/audits/AES_NEW_FACTS_AUDIT_2026-10-15/run/controls/inverse/invmc_walk_88_depth33.json",
}


def load_targets():
    toks = " ".join(l.split("%")[0] for l in open(MAT).read().splitlines()).split()
    r, c = int(toks[1]), int(toks[2])
    bits = list(map(int, toks[3:3 + r * c]))
    return [sum(bits[i * c + j] << j for j in range(c)) for i in range(r)]


TARGETS = load_targets()
TSET = set(TARGETS)
GROUPS = [[j, 8 + j, 16 + j, 24 + j] for j in range(8)]
GROUP_TARGETS = [[TARGETS[i] for i in rows] for rows in GROUPS]
M_GROUP_INV = [23, 27, 27, 35, 35, 31, 27, 23]   # archive claim (INVENTORY item 7), not re-derived here


def wiring_of_record(d):
    """Record JSON (gates = index pairs, inputs 0..n-1) -> wiring [(v, a, b)] in gate order."""
    n = d.get("inputCount", N)
    masks = [1 << i for i in range(n)]
    out = []
    for a, b in d["gates"]:
        v = masks[a] ^ masks[b]
        out.append((v, masks[a], masks[b]))
        masks.append(v)
    return out


def wiring_of_ncff(path):
    vals = {f"x{j}": 1 << j for j in range(N)}
    out = []
    for line in open(path):
        m = re.match(r"^\s*XOR\s+(\S+)\s+(\S+)\s+(\S+)", line)
        if not m:
            continue
        o, a, b = m.groups()
        vals[o] = vals[a] ^ vals[b]
        out.append((vals[o], vals[a], vals[b]))
    return out


def wiring_of_archive(d):
    """Archive JSON formats vary; try the common ones."""
    if "gates" in d and d["gates"] and isinstance(d["gates"][0], list) and len(d["gates"][0]) == 2 \
            and all(isinstance(x, int) for x in d["gates"][0]):
        return wiring_of_record(d)
    return None


def is_inverse(wiring):
    vals = {v for v, _, _ in wiring}
    return TSET <= vals


def run_of(path):
    m = re.search(r"xs-campaigns/([^/]+)/(?:runs/([^/]+)/)?(?:workers/)?(?:runs/[^/]+/workers/)?([^/]+)/records/", path)
    if m:
        return f"{m.group(1)}:{m.group(2) or '-'}:{m.group(3)}"
    if path.startswith(INVDIR):
        return "repo"
    return path


def canon_mod_rot(sp, vals):
    vals = tuple(sorted(vals))
    best = None
    for s in sp.shifts:
        k = tuple(sorted(sp.rot(vals, s))) if s else vals
        if best is None or k < best:
            best = k
    return best


def dump(name, obj):
    p = os.path.join(HERE, name)
    with open(p + ".tmp", "w") as f:
        json.dump(obj, f)
    os.replace(p + ".tmp", p)


def load(name):
    return json.load(open(os.path.join(HERE, name)))
