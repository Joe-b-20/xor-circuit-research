#!/usr/bin/env python3
"""Big-map sweep: for maps over 8x8 matrices (the class that keeps gaining, F4/F7), one v8
worker per map for 1 h at the depth cap where we are weakest against NIST (NIST's depth), seeded
with our best circuit at <= cap plus NIST's.  Two batches of 6 workers.  Writes sw1.toml, sw2.toml
and seeds/*.json."""
import json, os, re, sys

REPO = "/home/joebachir20/xor-circuit-research"
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(HERE, "seeds"), exist_ok=True)
sys.path.insert(0, REPO + "/search")
from xorflux.core.circuit import parse_ncff, verify  # noqa: E402
from xorflux.core.target import load_target  # noqa: E402

# (map, cap): NIST's depth for the single-point NIST maps (from circuits/README / seeds)
BATCHES = {
    "sw1": [("grostl", 16), ("khazad", 18), ("whirlpool-maelstrom", 11), ("fox-mu8", 14),
            ("jpst17-8x8-gf256-inv", 11), ("bkl16-8x8-gf256", 10)],
    "sw2": [("klsw17-m-8x8-gf256", 11), ("skop15-8x8-gf256", 8), ("skop15-8x8-gf256-inv", 13),
            ("ss17-8x8-gf256", 9), ("ls16-8x8-gf256", 9), ("klsw17-m-8x8-gf16-0x13-inv", 12)],
}


def our_best_at(mapname, D):
    best = None
    d = os.path.join(REPO, "circuits", mapname)
    for f in os.listdir(d):
        m = re.match(r".*-xor(\d+)-depth(\d+)\.circ\.txt$", f)
        if m and int(m.group(2)) <= D:
            g = int(m.group(1))
            if best is None or g < best[0]:
                best = (g, int(m.group(2)), os.path.join(d, f))
    return best


def to_seed(mapname, circ, out):
    target = load_target(mapname)
    c = parse_ncff(open(circ).read())
    info = verify(c, target)
    assert info.equivalent, info.reason
    d = {"benchmark": mapname, "inputCount": c.n_inputs, "gates": [list(g) for g in c.gates],
         "outputSignals": list(info.outputs), "gateCount": info.gate_count, "depth": info.depth,
         "provenance": {"source_url": circ, "source_kind": "our circuit (repo)"}}
    json.dump(d, open(out, "w"), indent=1)
    return info.gate_count, info.depth


for batch, maps in BATCHES.items():
    lines = [f'[campaign]\nname = "sweep-{batch}"\nseed = 20261110\nduration = "1h"\n'
             'profiles = ["default"]\nsharing = "off"\n']
    for mapname, D in maps:
        seeds = ['"target"']
        ob = our_best_at(mapname, D)
        if ob:
            out = os.path.join(HERE, "seeds", f"{mapname}-g{ob[0]}-d{ob[1]}.json")
            g, dep = to_seed(mapname, ob[2], out)
            seeds.insert(0, f'"seeds/{os.path.basename(out)}"')
            print(batch, mapname, "cap", D, "our best", g, dep)
        else:
            print(batch, mapname, "cap", D, "NIST seed only")
        lines.append(f'[[workers]]\nname = "{mapname}"\ntarget = "{mapname}"\ncount = 1\nobjective = "gates"\n'
                     f'depth_cap = {D}\nseeds = [{", ".join(seeds)}]\n')
    open(os.path.join(HERE, batch + ".toml"), "w").write("\n".join(lines))
