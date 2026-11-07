"""s4_collect.py: census of every recorded MixColumns depth-4 circuit at 89, 90 (and 91) gates.

Reads every g89-d4-*.json / g90-d4-*.json / g91-d4-*.json under ~/xs-campaigns (records and pools) plus the
repo record, rebuilds the value set from the gate list, dedupes by value set and modulo the Z4 byte
rotation, and reports per-level profiles (least levels from the value set), level-1 (weight-2) sets,
and the differences between members. Writes q89/s4_summary.json and q89/states_{89,90,91}.json.
Read-only on all inputs. Run: nice -n 10 python3 -I s4_collect.py
"""
import glob
import json
import os
import sys
from collections import Counter, defaultdict

HOME = os.path.expanduser("~")
OUT = os.path.join(HOME, "xs-campaigns/2026-11-07-sprint/q89")
MAT = os.path.join(HOME, "xor-circuit-research/circuits/aes-mixcolumns/aes-mixcolumns.mat.txt")
N = 32


def load_targets():
    rows = []
    with open(MAT) as fh:
        lines = [l.strip() for l in fh if l.strip()]
    assert lines[0] == "1", lines[0]
    r, c = map(int, lines[1].split())
    for l in lines[2:2 + r]:
        bits = l.replace(" ", "")
        v = 0
        for j, ch in enumerate(bits):
            if ch == "1":
                v |= 1 << j
        rows.append(v)
    return rows


TARGETS = load_targets()
TSET = set(TARGETS)
INPUTS = [1 << i for i in range(N)]


def rot(v, s):
    """byte rotation: input i -> i + s (mod 32), s multiple of 8"""
    return ((v << s) | (v >> (N - s))) & ((1 << N) - 1)


def values_of(rec):
    if "values" in rec and rec["values"]:
        vals = list(rec["values"])
        return [v for v in vals if v not in INPUTS]
    gates = rec.get("gates") or rec.get("circuit")
    val = list(INPUTS)
    for a, b in gates:
        val.append(val[a] ^ val[b])
    return val[N:]


def least_levels(vals):
    """least level of each value: inputs 0; v at level L if v = a ^ b with a, b of level < L, one at L-1."""
    lev = {v: 0 for v in INPUTS}
    todo = set(vals) - set(INPUTS)
    L = 0
    while todo:
        L += 1
        known = list(lev)
        kset = set(known)
        prev = [a for a in known if lev[a] == L - 1]
        new = {}
        for a in prev:
            for b in known:
                x = a ^ b
                if x in todo and x not in new:
                    new[x] = L
        if not new:
            return lev, sorted(todo)  # unreachable values (should not happen)
        lev.update(new)
        todo -= set(new)
    return lev, []


def canon_rot(valset):
    keys = []
    for s in (0, 8, 16, 24):
        keys.append(tuple(sorted(rot(v, s) for v in valset)))
    k = min(keys)
    return k, keys.index(k) * 8


def main():
    files = []
    for g in (89, 90, 91):
        files += [(g, f) for f in glob.glob(os.path.join(HOME, f"xs-campaigns/**/g{g}-d4-*.json"), recursive=True)]
    files.append((89, os.path.join(HOME, "xor-circuit-research/circuits/aes-mixcolumns/logs/aes-mixcolumns-xor89-depth4/record.json")))
    files = [(g, f) for g, f in files if "/import/" not in f and not f.endswith(".verification.json")]
    print("files", Counter(g for g, _ in files))
    by_g = defaultdict(dict)       # g -> valset tuple -> info
    src = defaultdict(Counter)
    bad = Counter()
    for g, f in files:
        try:
            rec = json.load(open(f))
        except Exception as e:
            bad["unreadable"] += 1
            continue
        if rec.get("depth") not in (4, None):
            bad["depth!=4"] += 1
            continue
        if not (rec.get("values") or rec.get("gates") or rec.get("circuit")):
            bad["no gates"] += 1
            continue
        if rec.get("inputCount", 32) != 32:
            bad["inputs!=32"] += 1
            continue
        vals = values_of(rec)
        vs = frozenset(vals)
        if len(vs) != len(vals):
            bad["dup values"] += 1
        if not TSET <= vs:
            bad["targets missing"] += 1
            continue
        helpers = tuple(sorted(vs - TSET))
        ngates = len(vs)  # one gate per distinct non-input value in a trimmed circuit
        if ngates != g:
            bad[f"gates!={g}"] += 1
        camp = f.split("xs-campaigns/")[1].split("/")[0] if "xs-campaigns/" in f else "repo"
        src[g][camp] += 1
        info = by_g[g].setdefault(helpers, {"n": 0, "files": [], "camps": Counter()})
        info["n"] += 1
        info["camps"][camp] += 1
        if len(info["files"]) < 3:
            info["files"].append(f.replace(HOME, "~"))
    print("bad", bad)
    summary = {"files": {g: dict(c) for g, c in src.items()}, "bad": dict(bad)}
    out_states = {}
    for g in sorted(by_g):
        states = by_g[g]
        lev_sets = {}
        profiles = Counter()
        L1sets = Counter()
        L1size = Counter()
        rotkeys = {}
        unreach = 0
        per_level_sets = defaultdict(list)
        for hk in states:
            vs = set(hk) | TSET
            lev, un = least_levels(vs)
            if un:
                unreach += 1
            prof = tuple(Counter(lev[v] for v in vs).get(L, 0) for L in range(1, 1 + max(lev.values())))
            profiles[prof] += 1
            L1 = frozenset(v for v in vs if lev[v] == 1)
            L1sets[L1] += 1
            L1size[len(L1)] += 1
            for L in range(1, len(prof) + 1):
                per_level_sets[L].append(frozenset(v for v in vs if lev[v] == L))
            rk, s = canon_rot(vs)
            rotkeys.setdefault(rk, []).append((hk, s))
            lev_sets[hk] = {"profile": prof, "L1": sorted(L1)}
        n_rot = len(rotkeys)
        rot_classes_multi = sum(1 for v in rotkeys.values() if len(v) > 1)
        # intersections / unions per level
        lvl_stats = {}
        for L, sets in per_level_sets.items():
            inter = frozenset.intersection(*sets)
            union = frozenset.union(*sets)
            lvl_stats[L] = {"distinct_sets": len(set(sets)), "in_all": len(inter), "union": len(union),
                            "sizes": dict(Counter(len(s) for s in sets))}
        # 89 L1 reference
        res = {"records": sum(i["n"] for i in states.values()), "distinct_valuesets": len(states),
               "distinct_mod_rotation": n_rot, "rotation_classes_with_more_than_one_member": rot_classes_multi,
               "unreachable_values_states": unreach,
               "profiles": {" ".join(map(str, p)): n for p, n in profiles.most_common()},
               "distinct_L1_sets": len(L1sets), "L1_size_hist": dict(sorted(L1size.items())),
               "per_level": lvl_stats,
               "sources_by_campaign": dict(src[g])}
        summary[str(g)] = res
        out_states[g] = {"states": [{"helpers": list(hk), "n": i["n"], "camps": dict(i["camps"]), "files": i["files"],
                                     "profile": lev_sets[hk]["profile"], "L1": lev_sets[hk]["L1"]} for hk, i in states.items()]}
        print(g, json.dumps(res, indent=1)[:3000])
    # 89-vs-90 comparisons
    if 89 in by_g and 90 in by_g:
        L1_89 = set()
        for hk in by_g[89]:
            L1_89 = set(out_states[89]["states"][0]["L1"])
            break
        all_L1_89 = {frozenset(s["L1"]) for s in out_states[89]["states"]}
        ov = Counter()
        sup = 0
        eq = 0
        for s in out_states[90]["states"]:
            L1 = set(s["L1"])
            ov[len(L1 & L1_89)] += 1
            if L1_89 <= L1:
                sup += 1
            if frozenset(L1) in all_L1_89:
                eq += 1
        summary["90_vs_89"] = {"ref_L1_89_size": len(L1_89), "overlap_hist_90_L1_with_89_L1": dict(sorted(ov.items())),
                               "90_states_whose_L1_contains_89_L1": sup, "90_states_with_an_89_L1": eq}
        # which 89 values are variable
        vals89 = Counter()
        for s in out_states[89]["states"]:
            for v in s["helpers"]:
                vals89[v] += 1
        n89 = len(out_states[89]["states"])
        var = {v: c for v, c in vals89.items() if c != n89}
        summary["89_variable_values"] = {"n_always": sum(1 for c in vals89.values() if c == n89),
                                         "n_variable": len(var), "variable_value_counts": dict(sorted(var.items()))}
        print(json.dumps(summary["90_vs_89"], indent=1))
        print(json.dumps(summary["89_variable_values"], indent=1))
    json.dump(summary, open(os.path.join(OUT, "s4_summary.json"), "w"), indent=1)
    for g, d in out_states.items():
        json.dump(d, open(os.path.join(OUT, f"states_{g}.json"), "w"))


if __name__ == "__main__":
    main()
