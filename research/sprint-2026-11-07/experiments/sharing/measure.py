"""Task 2: measure S (multiplicity and count readings), delta, per-group cone sizes, k-distribution,
pairwise cone intersections/unions on the repo circuits (their own wiring) and on sampled 88s
(greedy wiring + random wirings to show wiring dependence).  Writes measure.json and prints tables."""
import json
import os
import random
import statistics as st
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib

HERE = os.path.dirname(os.path.abspath(__file__))
res = {"repo": {}, "samples": []}


def summarize(name, stt, verbose=True):
    d = {k: stt[k] for k in ("G", "dead", "S_mult", "S_cnt", "delta", "delta_g", "sizes", "kdist",
                             "shared_by_depth", "private", "outside_inputs", "identity_ok")}
    d["S_minus_delta"] = stt["S_mult"] - stt["delta"]
    d["pair_int"] = {f"{g}{h}": v for (g, h), v in stt["pair_int"].items()}
    d["pair_union"] = {f"{g}{h}": v for (g, h), v in stt["pair_union"].items()}
    if verbose:
        print(f"== {name}: G={d['G']} dead={d['dead']} S_mult={d['S_mult']} S_cnt={d['S_cnt']} delta={d['delta']} "
              f"S-delta={d['S_minus_delta']} identity_ok={d['identity_ok']}")
        print(f"   cone sizes |C_g| = {d['sizes']}  (minima {lib.M_GROUP})  delta_g = {d['delta_g']}")
        print(f"   private gates per group (k=1) = {d['private']}   inputs outside supp touched by cone = {d['outside_inputs']}")
        print(f"   k-distribution (k: #gates) = {d['kdist']}   shared units by depth = {d['shared_by_depth']}")
        print("   pairwise |C_g & C_h| (upper) / |C_g | C_h| (lower):")
        for g in range(8):
            row = []
            for h in range(8):
                if h > g:
                    row.append(f"{stt['pair_int'][(g, h)]:3d}")
                elif h < g:
                    row.append(f"{stt['pair_union'][(h, g)]:3d}")
                else:
                    row.append(f"{stt['sizes'][g]:3d}")
            print("     " + " ".join(row))
    return d


# repo circuits with their own wiring
for name, path in lib.CIRC.items():
    order = lib.load_repo_circ(path)
    G, depth = lib.check_circuit(order)
    stt = lib.sharing_stats(order)
    d = summarize(f"repo {name} (file wiring, depth {depth})", stt)
    # wiring dependence on the same value set
    vals = [v for v, _, _ in order]
    rng = random.Random(1)
    alt = []
    for i in range(50):
        o2 = lib.wiring_from_values(vals, rng)
        s2 = lib.sharing_stats(o2)
        alt.append((s2["S_mult"], s2["delta"]))
    d["random_wirings_S_range"] = [min(a for a, _ in alt), max(a for a, _ in alt)]
    d["random_wirings_delta_range"] = [min(b for _, b in alt), max(b for _, b in alt)]
    d["random_wirings_S_minus_delta"] = sorted(set(a - b for a, b in alt))
    print(f"   50 random re-wirings of the same value set: S in {d['random_wirings_S_range']}, delta in "
          f"{d['random_wirings_delta_range']}, S-delta always in {d['random_wirings_S_minus_delta']}")
    # how many splits does each value admit (wiring freedom)
    avail = set(lib.INPUTS) | set(vals)
    multi = sum(1 for v in vals if len(lib.splits(v, avail)) > 1)
    d["values_with_multiple_splits"] = multi
    print(f"   values with >1 split inside INPUTS u V: {multi} of {G}")
    res["repo"][name] = d

# sampled 88s
samples = lib.load_samples(88)
print(f"\n== sampled 88 circuits (deduplicated value sets): {len(samples)}")
rows = []
for smp in samples:
    order = lib.wiring_from_values(smp["values"])
    if order is None:
        continue
    G, depth = lib.check_circuit(order)
    stt = lib.sharing_stats(order)
    d = summarize(smp["hash"], stt, verbose=False)
    d["depth_greedy"] = depth
    d["hash"] = smp["hash"]; d["src"] = smp["src"]
    rows.append(d)
res["samples"] = rows


def dist(name, xs):
    xs = sorted(xs)
    c = {}
    for x in xs:
        c[x] = c.get(x, 0) + 1
    print(f"   {name}: min {xs[0]} median {st.median(xs)} mean {st.mean(xs):.2f} max {xs[-1]}  hist {c}")


print(f"   usable: {len(rows)} (greedy wiring)")
dist("S_mult", [r["S_mult"] for r in rows])
dist("S_cnt", [r["S_cnt"] for r in rows])
dist("delta", [r["delta"] for r in rows])
dist("S-delta", [r["S_minus_delta"] for r in rows])
dist("dead", [r["dead"] for r in rows])
for g in range(8):
    dist(f"delta_{g}", [r["delta_g"][g] for r in rows])
for g in range(8):
    dist(f"|C_{g}|", [r["sizes"][g] for r in rows])
print("   number of groups realised minimally (delta_g = 0) per circuit:")
dist("#min groups", [sum(1 for x in r["delta_g"] if x == 0) for r in rows])
print("   mean pairwise |C_g & C_h| over samples (upper) / mean |C_g | C_h| (lower):")
for g in range(8):
    row = []
    for h in range(8):
        if h > g:
            row.append(f"{st.mean(r['pair_int'][f'{g}{h}'] for r in rows):5.1f}")
        elif h < g:
            row.append(f"{st.mean(r['pair_union'][f'{h}{g}'] for r in rows):5.1f}")
        else:
            row.append(f"{st.mean(r['sizes'][g] for r in rows):5.1f}")
    print("     " + " ".join(row))
print("   min pairwise |C_g | C_h| over samples (upper triangle):")
for g in range(8):
    row = []
    for h in range(8):
        if h > g:
            row.append(f"{min(r['pair_union'][f'{g}{h}'] for r in rows):3d}")
        else:
            row.append("  .")
    print("     " + " ".join(row))
print("   max pairwise |C_g & C_h| over samples (upper triangle):")
for g in range(8):
    row = []
    for h in range(8):
        if h > g:
            row.append(f"{max(r['pair_int'][f'{g}{h}'] for r in rows):3d}")
        else:
            row.append("  .")
    print("     " + " ".join(row))
kd = {}
for r in rows:
    for k, c in r["kdist"].items():
        kd[int(k)] = kd.get(int(k), 0) + c
tot = sum(kd.values())
print("   pooled k-distribution over all sample gates: " + ", ".join(f"k={k}: {c} ({100*c/tot:.1f}%)" for k, c in sorted(kd.items())))
sd = {}
for r in rows:
    for k, c in r["shared_by_depth"].items():
        sd[int(k)] = sd.get(int(k), 0) + c
print("   pooled shared units (k-1) by greedy-wiring depth: " + str(dict(sorted(sd.items()))))
json.dump(res, open(os.path.join(HERE, "measure.json"), "w"), indent=1)
