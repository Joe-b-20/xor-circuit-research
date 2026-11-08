"""Tables for the report from plateaus118.json / fans118.json / records118.json (no engine calls)."""
import json
from collections import Counter, defaultdict
import common as C

PL = C.load("plateaus118.json")
F = C.load("fans118.json")
R = C.load("records118.json")["states"]
P = PL["plateaus"]
print("plateaus", len(P), "v3 classes", PL["n_v3"], "unassigned", len(PL["unassigned"]))
print("verified:", Counter(p["verified"] for p in P), "downs inside closures:", sum(p["downs"] for p in P))
print("depth hist union:", Counter(k for p in P if p["depth_hist"] for k in p["depth_hist"]))
# shape table
rows = defaultdict(lambda: [0, 0, 0, 0, set()])
for p in P:
    s = "x".join(map(str, sorted(p["radices"], reverse=True)))
    r = rows[s]
    r[0] += 1; r[1] += p["files"]; r[2] += p["n_states_recorded"]; r[3] += len(p["chains"]); r[4].add(p["core"])
print("shape | plateaus | record files | distinct recorded states | chains | core sizes")
for s, r in sorted(rows.items(), key=lambda kv: -kv[1][0]):
    print(f"  {s:22s} {r[0]:3d} {r[1]:5d} {r[2]:4d} {r[3]:4d} {sorted(r[4])}")
# factor census
fac = Counter()
pcf = Counter()
k_fixed = Counter()
cons_out = Counter()
for p in P:
    for f in p["factors"]:
        key = (f["n_choices"], f["n_values"], f["single_value"])
        fac[key] += 1
        if f["single_value"]:
            pcf[(f["n_choices"], f["partner_choice_form"])] += 1
            good = [g for g in f["consumers"] if g["partners_fixed"]]
            if good:
                g = good[0]
                k_fixed[(f["n_choices"], g["consumer_weight"], tuple(f["value_weights"]), tuple(g["partner_weights"]),
                         g["partners_are_inputs"], g["partners_xor_zero"], f["xor_all_zero"], g["consumer_is_output"])] += 1
            cons_out[(f["n_choices"], len(good))] += 1
print("factor census (choices, values, single-value):", sorted(fac.items()))
print("single-value factors: (choices, has a consumer with fixed partners):", sorted(pcf.items()))
print("(choices, #consumers with fixed partners):", sorted(cons_out.items()))
print("single-value factor types (choices, consumer w, value weights, partner weights, partners inputs, partners xor 0, values xor 0, consumer is output): count")
for k, n in sorted(k_fixed.items(), key=lambda kv: -kv[1]):
    print("  ", k, n)
# coupled factors detail
for p in P[:3]:
    for f in p["factors"]:
        if not f["single_value"]:
            print(f"plateau {p['pid']} coupled factor: {f['n_choices']} choices over {f['n_values']} values, choice sizes {f['choice_sizes']}")
            print("   choices:", f["values_hex"][:6])
# repo plateau factors in full
p0 = [p for p in P if "repo" in p["runs"]]
if p0:
    p0 = p0[0]
    print("REPO plateau pid", p0["pid"], "size", p0["size"], "radices", p0["radices"], "core", p0["core"], "verified", p0["verified"])
    for f in p0["factors"]:
        print("  factor:", f["n_choices"], "choices", f["n_values"], "values single", f["single_value"], "xor0", f["xor_all_zero"],
              "levels", f.get("value_levels"), "wts", f.get("value_weights"))
        for g in f.get("consumers", []):
            print("     consumer", g["consumer"], "w", g["consumer_weight"], "out", g["consumer_is_output"], "partners", g["partners_hex"],
                  "fixed", g["partners_fixed"], "pw", g["partner_weights"], "inputs", g["partners_are_inputs"], "pxor0", g["partners_xor_zero"])
# landings / repeats
print("records per plateau (files):", sorted((p["files"] for p in P), reverse=True))
print("plateaus with records from both runs:", sum(1 for p in P if len({r.split(":")[0] for r in p["runs"]}) > 1))
print("plateaus reached by >1 chain:", sum(1 for p in P if len(p["chains"]) > 1), "; chains per plateau:", sorted((len(p["chains"]) for p in P), reverse=True)[:15])
print("adopt-run plateaus:", [p["pid"] for p in P if any(r.startswith("2026-10-31") for r in p["runs"])])
print("inv118-run plateaus:", len([p for p in P if any(r.startswith("2026-11-05") for r in p["runs"])]))
# mobile / core from fans
print("fan core sizes:", Counter(e["core"] for e in F.values()).most_common(8))
print("fan mobile sizes:", Counter(e["mobile"] for e in F.values()).most_common(8))
print("neighbour depths:", Counter(k for e in F.values() for k in e["nbr_depths"]))
