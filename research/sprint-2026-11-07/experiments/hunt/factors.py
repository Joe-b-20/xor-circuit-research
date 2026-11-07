#!/usr/bin/env python3
"""Test the reading "a 3-way plateau factor is an unshared 3-input XOR tree": for a circuit,
compress its remove1 plateau and, for every factor, check (a) the three choices XOR to 0
(c1 ^ c2 ^ c3 == 0, as for {a^b, a^c, b^c}), (b) each choice value has exactly one consumer in
the circuit, (c) the consumer's value s = choice ^ third input is the same for all choices.
Usage: factors.py CIRCUIT.circ.txt|record.json|values.json
"""
import json, sys

sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
import pes_lib  # noqa: E402

sp = pes_lib.make_space("mc", None)
path = sys.argv[1]
if path.endswith(".json"):
    d = json.load(open(path))
    c = d.get("circuit", d)
    masks = [1 << i for i in range(c["inputCount"])]
    for a, b in c["gates"]:
        masks.append(masks[a] ^ masks[b])
    values = masks[c["inputCount"]:]
    helpers = [v for v in values if v not in sp.tset]
else:
    hk, g, dd, ok = pes_lib.load_circuit_helpers(sp, path)
    helpers = list(hk)
st = sp.state(helpers)
print("gates", st.count(), "depth", st.depth())
pl, info = pes_lib.compress(sp, sp.hkey(st))
print("plateau kind", pl.kind, "size", pl.size(), "radices", pl.radices(), "core", len(pl.core))
U = set(st.key())
inputs = {1 << i for i in range(sp.n)}
allv = U | inputs
def consumers(v):
    """values w in U such that w = v ^ u for some u in allv (u != v)"""
    return sorted(w for w in U if w != v and (w ^ v) in allv)
for i, (vals, ch) in enumerate(pl.factors):
    chs = [sorted(cc) for cc in ch]
    flat = [x for cc in chs for x in cc]
    x = 0
    for v in flat:
        x ^= v
    print(f"factor {i}: choices {[[hex(v) for v in cc] for cc in chs]}  xor_all={'0' if x == 0 else hex(x)}")
    # consumers in the seed state's choice
    cur = [v for v in flat if v in U]
    for v in cur:
        cons = consumers(v)
        print(f"   {hex(v)} popcount {bin(v).count('1')} consumers {len(cons)}: {[hex(w) for w in cons][:6]}")
