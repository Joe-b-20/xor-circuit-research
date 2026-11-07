#!/usr/bin/env python3
"""Count odd-weight helper values (helpers that are not outputs) in our 88 circuits.
The archive claims: any circuit with <= 87 gates needs 3..31 odd non-output helpers; 0 odd -> >= 92;
exactly 2 odd -> >= 88.  Check what our 88s do (a regularity check, not a test of the theorem)."""
import glob, json, os, sys
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
import pes_lib
sp = pes_lib.make_space("mc", None)
tset = set(sp.tset)
H = os.path.expanduser("~/xs-campaigns/2026-11-07-sprint/hunt")
states = {}
for p in (f"{H}/samples.jsonl", f"{H}/samplesC/samples.jsonl", f"{H}/samplesD/samples.jsonl"):
    if os.path.exists(p):
        for line in open(p):
            r = json.loads(line)
            if r["gates"] == 88:
                states[r["hash"]] = r["values"]
# repo 88@5 and 89@4, 97@3
def circ_values(path):
    vals = []
    n_in = None
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if n_in is None and parts[0].isdigit():
            n_in = int(parts[0]); masks = [1 << i for i in range(n_in)]; continue
        if "=" in line:
            lhs, rhs = line.split("=")
            a, b = [t.strip() for t in rhs.replace("XOR", "+").replace("^", "+").split("+")]
            idx = {}
            # generic: names like x3 / y5 / t12 ; map by order of appearance
    return None
from collections import Counter
dist = Counter(); odd_total = Counter()
for h, vals in states.items():
    helpers = [v for v in vals if v not in tset]
    odd = sum(1 for v in helpers if bin(v).count("1") % 2 == 1)
    oddall = sum(1 for v in vals if bin(v).count("1") % 2 == 1)
    dist[odd] += 1; odd_total[oddall] += 1
print("88 states:", len(states))
print("odd-weight NON-OUTPUT helpers per 88 circuit:", dict(sorted(dist.items())))
print("odd-weight values incl. outputs per 88 circuit:", dict(sorted(odd_total.items())))
ow = Counter(bin(t).count("1") for t in tset)
print("output weights:", dict(ow))
# repo 88@5 via its record json if present
for rec in glob.glob(os.path.expanduser("~/xor-circuit-research/circuits/aes-mixcolumns/logs/*/record.json")):
    d = json.load(open(rec))
    vals = d.get("values")
    if not vals and d.get("circuit"):
        c = d["circuit"]; masks = [1 << i for i in range(c["inputCount"])]
        for a, b in c["gates"]:
            masks.append(masks[a] ^ masks[b])
        vals = masks[c["inputCount"]:]
    if vals:
        helpers = [v for v in vals if v not in tset]
        print(os.path.basename(os.path.dirname(rec)), "gates", len(vals), "odd non-output helpers",
              sum(1 for v in helpers if bin(v).count("1") % 2), "of", len(helpers))
