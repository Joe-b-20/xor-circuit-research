#!/usr/bin/env python3
"""Build the prediction-test campaigns from crossmap's predict.csv rules: per map, cap D (NIST's
weakest depth), seeds = our best circuit at depth <= D (converted from circuits/) plus NIST's seed
at D, 2 workers for 2 h (= the 4 worker-hours of the stated prediction '1 h on 4 workers').
Writes predtest/<batch>.toml and predtest/seeds/*.json."""
import json, os, subprocess, sys

REPO = "/home/joebachir20/xor-circuit-research"
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(HERE, "seeds"), exist_ok=True)
sys.path.insert(0, REPO + "/search")
from xorflux.core.circuit import parse_ncff, verify  # noqa: E402
from xorflux.core.target import load_target  # noqa: E402

# (map, cap D, predicted gates) from crossmap/REPORT.txt section 6 and predict.csv
BATCHES = {
    "pt1": [("skop15-8x8-gf16", 19, 140), ("ss17-8x8-gf16", 10, 161), ("klsw17-m-8x8-gf256-inv", 12, 335)],
    "pt2": [("skop15-4x4-gf256-inv", 6, 85), ("anubis-clefia-m0", 9, 89), ("khazad", 18, None), ("fox-mu8", 14, None)],
}


def our_best_at(mapname, D):
    best = None
    d = os.path.join(REPO, "circuits", mapname)
    for f in os.listdir(d):
        if f.endswith(".circ.txt"):
            g = int(f.split("-xor")[1].split("-")[0])
            dep = int(f.split("-depth")[1].split(".")[0])
            if dep <= D and (best is None or g < best[0]):
                best = (g, dep, os.path.join(d, f))
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
    lines = [f'[campaign]\nname = "predtest-{batch}"\nseed = 2026110{len(batch)}\nduration = "2h"\n'
             'profiles = ["default"]\nsharing = "pull"\n']
    for mapname, D, pred in maps:
        seeds = ['"target"']
        ob = our_best_at(mapname, D)
        if ob:
            out = os.path.join(HERE, "seeds", f"{mapname}-g{ob[0]}-d{ob[1]}.json")
            g, dep = to_seed(mapname, ob[2], out)
            seeds.insert(0, f'"seeds/{os.path.basename(out)}"')
            print(batch, mapname, "cap", D, "our best", g, dep, "predicted", pred)
        else:
            print(batch, mapname, "cap", D, "no circuit of ours at <= D; NIST seed only", "predicted", pred)
        lines.append(f'[[workers]]\nname = "{mapname}"\ntarget = "{mapname}"\ncount = 2\nobjective = "gates"\n'
                     f'depth_cap = {D}\nseeds = [{", ".join(seeds)}]\n')
    open(os.path.join(HERE, batch + ".toml"), "w").write("\n".join(lines))
