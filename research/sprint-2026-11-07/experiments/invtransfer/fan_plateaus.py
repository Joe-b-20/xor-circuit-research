"""Step 2 (findings b, c, a): fan every distinct 118@5 state (neutral / down moves, binds),
cheap identity v3, exact closure per v3 class with pes_lib.compress, factor analysis.
Writes fans118.json and plateaus118.json."""
import json
import sys
import time
from collections import Counter, defaultdict
import common as C
import pes_lib

t0 = time.time()
sp = pes_lib.make_space("inv", 5)
R = C.load("records118.json")["states"]
keys = sorted(R)
print("states", len(keys), flush=True)

# ---------------------------------------------------------------- (b) fans + v3
fans = {}
fan_cache = {}


def fan(S):
    r = fan_cache.get(S)
    if r is None:
        r = pes_lib.fan(sp, S)
        fan_cache[S] = r
    return r


for i, k in enumerate(keys):
    S = frozenset(R[k]["hk"])
    g, d, neutral, downs, binds = fan(S)
    added = set()
    mobile = set()
    for Rm, A, hk, dep in neutral:
        added |= A
        mobile |= Rm | A
    v3 = C.canon_mod_rot(sp, S | added)
    fans[k] = {"gates": g, "depth": d, "nn": len(neutral), "ndown": len(downs), "binds": binds,
               "mobile": len(mobile), "core": len(S) - len(mobile), "v3": pes_lib.h64(v3),
               "nbr_depths": Counter(dep for _, _, _, dep in neutral),
               "downs": [{"dg": dg, "depth": dep} for _, dg, dep in downs]}
    if i % 100 == 0:
        print("fan", i, round(time.time() - t0, 1), flush=True)
for e in fans.values():
    e["nbr_depths"] = {str(a): b for a, b in sorted(e["nbr_depths"].items())}
C.dump("fans118.json", fans)
nn = Counter(e["nn"] for e in fans.values())
print("neutral-move histogram", dict(sorted(nn.items())))
print("states with a down move", sum(1 for e in fans.values() if e["ndown"]))
print("binds total", sum(e["binds"] for e in fans.values()))
print("depth of states", Counter(e["depth"] for e in fans.values()))
print("distinct v3", len({e["v3"] for e in fans.values()}), flush=True)

# ---------------------------------------------------------------- (c) exact closures
byv3 = defaultdict(list)
for k in keys:
    byv3[fans[k]["v3"]].append(k)
plateaus = []          # list of dicts
member_of = {}         # state key -> plateau index


def analyse(P, Z):
    """Factor analysis of Plateau P with seed Z (frozenset)."""
    inputs = set(C.INPUTS)
    facs = []
    for fi, (vals, ch) in enumerate(P.factors):
        chs = [sorted(c) for c in ch]
        single = all(len(c) == 1 for c in chs)
        x = 0
        for c in chs:
            for v in c:
                x ^= v
        rec = {"n_values": len(vals), "n_choices": len(chs), "choice_sizes": sorted(Counter(len(c) for c in chs).items()),
               "single_value": single, "xor_all_zero": x == 0, "values_hex": [[hex(v) for v in c] for c in chs]}
        if single:
            # consumer/partner analysis: for each choice state, consumers of the choice value
            common_cons = None
            partners = {}
            levels = {}
            wts = []
            for c in chs:
                v = c[0]
                S = (Z - vals) | frozenset(c)
                st = sp.state(sorted(S))
                U = set(st.key())
                allv = U | inputs
                lev = st.level
                getl = lev.get if hasattr(lev, "get") else (lambda z: None)
                cons = {w for w in U if w != v and (w ^ v) in allv}
                common_cons = cons if common_cons is None else (common_cons & cons)
                partners[v] = {w: w ^ v for w in cons}
                levels[v] = getl(v)
                wts.append(bin(v).count("1"))
            rec["value_levels"] = [levels[c[0]] for c in chs]
            rec["value_weights"] = wts
            rec["common_consumers"] = [hex(w) for w in sorted(common_cons or [])]
            # pick the consumer(s) whose partner is fixed in the core/inputs for every choice
            good = []
            for w in sorted(common_cons or []):
                ps = [partners[c[0]][w] for c in chs]
                core_ok = all(p in P.core or p in inputs or p in sp.tset for p in ps)
                px = 0
                for p in ps:
                    px ^= p
                good.append({"consumer": hex(w), "consumer_weight": bin(w).count("1"),
                             "consumer_is_output": w in sp.tset,
                             "partners_hex": [hex(p) for p in ps],
                             "partners_fixed": core_ok,
                             "partner_weights": [bin(p).count("1") for p in ps],
                             "partners_are_inputs": all(p in inputs for p in ps),
                             "partners_xor_zero": px == 0})
            rec["consumers"] = good
            rec["partner_choice_form"] = any(g["partners_fixed"] for g in good)
        facs.append(rec)
    return facs


# seeds in order of v3-class size (largest classes first); every closure is tested against ALL
# still-unassigned states (v3 over-splits coupled plateaus, so one plateau spans several classes)
order = [m for v3, members in sorted(byv3.items(), key=lambda kv: -len(kv[1])) for m in members]
pjson = []
identities = {}
for seed_key in order:
    if seed_key in member_of:
        continue
    Z = frozenset(R[seed_key]["hk"])
    P, info = pes_lib.compress(sp, tuple(sorted(Z)), verify_limit=400, closure_limit=5000,
                               time_limit=600)
    ident = (frozenset(P.core), frozenset(P.allv)) if P.kind == "product" else (frozenset(P.core), frozenset().union(*P.states))
    pid = identities.get(ident)
    if pid is not None:
        # same plateau reached from another seed (should not happen when contains() is exact)
        plateaus[pid]["duplicate_seeds"] = plateaus[pid].get("duplicate_seeds", 0) + 1
        member_of[seed_key] = pid
        plateaus[pid]["members"].append(seed_key)
        continue
    pid = len(plateaus)
    identities[ident] = pid
    mem = [m for m in keys if m not in member_of and P.contains(frozenset(R[m]["hk"]))]
    if seed_key not in mem:
        mem.append(seed_key)
    for m in mem:
        member_of[m] = pid
    facs = analyse(P, Z) if P.kind == "product" else []
    v3s = sorted({fans[m]["v3"] for m in mem})
    plateaus.append({"pid": pid, "v3_classes": len(v3s), "size": P.size(), "kind": P.kind, "radices": P.radices(),
                     "core": len(P.core), "verified": info.get("verified"), "note": info.get("note"),
                     "downs": len(info.get("downs", [])), "depth_hist": info.get("depth_hist"),
                     "seconds": info.get("seconds"), "fans": info.get("fans"),
                     "members": mem, "n_states_recorded": len(mem),
                     "files": sum(R[m]["files"] for m in mem),
                     "runs": dict(sum((Counter(R[m]["sources"]) for m in mem), Counter())),
                     "chains": sorted(set(c for m in mem for c in R[m]["chains"])),
                     "factors": facs})
    pjson.append(P.to_json())
    print(f"plateau {pid}: size {P.size()} radices {P.radices()} core {len(P.core)} "
          f"{info.get('verified')} members {len(mem)} files {plateaus[-1]['files']} v3cls {len(v3s)} "
          f"t={info.get('seconds')} total={round(time.time() - t0)}", flush=True)
    if time.time() - t0 > 3000:
        print("TIME BUDGET: stopping closures", flush=True)
        break

for p in plateaus:
    p["n_states_recorded"] = len(p["members"])
    p["files"] = sum(R[m]["files"] for m in p["members"])
    p["runs"] = dict(sum((Counter(R[m]["sources"]) for m in p["members"]), Counter()))
    p["chains"] = sorted(set(c for m in p["members"] for c in R[m]["chains"]))
C.dump("plateaus118_objects.json", pjson)
out = {"plateaus": plateaus, "member_of": member_of, "n_v3": len(byv3),
       "unassigned": [k for k in keys if k not in member_of]}
C.dump("plateaus118.json", out)
print("plateaus", len(plateaus), "v3 classes", len(byv3), "unassigned", len(out["unassigned"]))
shapes = Counter(tuple(sorted(p["radices"], reverse=True)) for p in plateaus)
for s, n in shapes.most_common():
    print("shape", "x".join(map(str, s)), "plateaus", n, "files", sum(p["files"] for p in plateaus if tuple(sorted(p["radices"], reverse=True)) == s))
print("seconds", round(time.time() - t0))
