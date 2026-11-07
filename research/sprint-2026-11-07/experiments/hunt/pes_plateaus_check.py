#!/usr/bin/env python3
"""Over every stored PES plateau (MC), check the 3-input-tree signature (each factor's choices
XOR to zero) and summarise radices, sizes, core sizes and the helper vocabulary modulo rotation.
Usage: pes_plateaus_check.py [glob of P*.json]
"""
import glob, json, sys

pat = sys.argv[1] if len(sys.argv) > 1 else "/home/joebachir20/xs-campaigns/2026-11-05-exit/runs/*/run/mc/plateaus/P*.json"
files = sorted(glob.glob(pat))
print("plateau files:", len(files))


def rot(v, s, n=32):
    s %= n
    return ((v << s) | (v >> (n - s))) & ((1 << n) - 1)


def rkey(vals):
    return min(tuple(sorted(rot(v, s) for v in vals)) for s in (0, 8, 16, 24))


seen = {}
rad = {}
sig_ok = sig_bad = 0
cores = set()
vocab = set()
for f in files:
    d = json.load(open(f))
    if d.get("cost") != 88:
        continue
    allv = set(d["core"])
    for fac in d["factors"]:
        for ch in fac["choices"]:
            allv |= set(ch)
        flat = [x for ch in fac["choices"] for x in ch]
        x = 0
        for v in flat:
            x ^= v
        if len(fac["choices"]) == 3 and all(len(ch) == 1 for ch in fac["choices"]):
            if x == 0:
                sig_ok += 1
            else:
                sig_bad += 1
    k = rkey(allv)
    if k in seen:
        continue
    seen[k] = f
    r = tuple(len(fac["choices"]) for fac in d["factors"])
    rad[r] = rad.get(r, 0) + 1
    cores.add(rkey(d["core"]))
    vocab |= set(allv)
print("distinct plateaus mod rotation:", len(seen))
print("radices:", rad)
print("3-way factors with xor-to-zero:", sig_ok, "without:", sig_bad)
print("helper vocabulary (values in any plateau, mod rotation):", len({rkey([v])[0] for v in vocab}),
      "raw:", len(vocab))
w = {}
for v in vocab:
    p = bin(v).count("1")
    w[p] = w.get(p, 0) + 1
print("vocabulary by popcount:", dict(sorted(w.items())))
