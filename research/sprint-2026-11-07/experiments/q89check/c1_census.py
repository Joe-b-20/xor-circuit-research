"""c1_census.py: independent census of the recorded MixColumns 89@4 and 90@4 circuits.
Own code; reads every g89-d4-*.json / g90-d4-*.json under ~/xs-campaigns (minus /import/ and
.verification.json) plus the repo .circ.txt. Writes c1_states_89.json, c1_states_90.json, c1_summary.json.
Read-only on inputs. nice -n 10 python3 -I c1_census.py
"""
import glob, json, os, re, sys
from collections import Counter, defaultdict
HOME = os.path.expanduser("~")
OUT = os.path.dirname(os.path.abspath(__file__))
N = 32
MASK = (1 << N) - 1
INPUTS = [1 << i for i in range(N)]
ISET = set(INPUTS)

def load_targets():
    lines = [l.strip() for l in open(f"{HOME}/xor-circuit-research/circuits/aes-mixcolumns/aes-mixcolumns.mat.txt") if l.strip()]
    assert lines[0] == "1"
    r, c = map(int, lines[1].split())
    assert (r, c) == (32, 32)
    rows = []
    for l in lines[2:2 + r]:
        bits = l.split()
        assert len(bits) == 32
        rows.append(sum(1 << j for j, b in enumerate(bits) if b == "1"))
    return rows

TARGETS = load_targets()
TSET = set(TARGETS)
assert len(TSET) == 32

def rot(v, s):
    return ((v << s) | (v >> (N - s))) & MASK

# fix the rotation convention: the byte rotation must map the target set onto itself
for s in (8, 16, 24):
    assert {rot(t, s) for t in TARGETS} == TSET, s
# check that a non-byte shift does not (so Z4 is the right symmetry here)
NONSYM = [s for s in range(1, 32) if {rot(t, s) for t in TARGETS} == TSET]
assert NONSYM == [8, 16, 24], NONSYM

def values_from_gates(gates, n_in=32):
    val = list(INPUTS)
    for a, b in gates:
        val.append(val[a] ^ val[b])
    return val[n_in:]

def least_levels(vals):
    """least level of every value in vals (set of non-input values), levels of inputs 0.
    Iterates: v gets level L at the first round where v = a ^ b with both a, b already levelled < L."""
    lev = {v: 0 for v in INPUTS}
    todo = set(vals) - ISET
    L = 0
    while todo:
        L += 1
        known = list(lev)
        new = set()
        for v in todo:
            for a in known:
                if (v ^ a) in lev and (v ^ a) != a:
                    new.add(v); break
        if not new:
            return lev, todo
        for v in new:
            lev[v] = L
        todo -= new
    return lev, set()

def parse_circ(path):
    names = {}
    for i in range(N):
        names[f"x{i}"] = 1 << i
    vals = []
    outs = {}
    for l in open(path):
        l = l.strip()
        if not l.startswith("XOR "):
            continue
        _, o, a, b = l.split()
        v = names[a] ^ names[b]
        names[o] = v
        vals.append(v)
        if o.startswith("y"):
            outs[o] = v
    return vals, outs

def canon(helpers):
    keys = [tuple(sorted(rot(v, s) for v in helpers)) for s in (0, 8, 16, 24)]
    k = min(keys)
    return k, keys.index(k) * 8

def main():
    summary = {}
    states = {}
    repo_vals, repo_outs = parse_circ(f"{HOME}/xor-circuit-research/circuits/aes-mixcolumns/aes-mixcolumns-xor89-depth4.circ.txt")
    assert set(repo_outs.values()) == TSET, "repo circuit outputs are not the MixColumns rows"
    assert all(repo_outs[f"y{i}"] == TARGETS[i] for i in range(32)), "output order differs from matrix rows"
    repo_h = frozenset(repo_vals) - TSET
    print("repo 89@4: gates", len(set(repo_vals)), "helpers", len(repo_h))
    for g in (89, 90):
        files = glob.glob(f"{HOME}/xs-campaigns/**/g{g}-d4-*.json", recursive=True)
        files = sorted(f for f in files if "/import/" not in f and not f.endswith(".verification.json"))
        rej = Counter()
        by_h = {}
        camps = Counter()
        for f in files:
            try:
                r = json.load(open(f))
            except Exception:
                rej["unreadable"] += 1; continue
            gates = r.get("gates") or r.get("circuit")
            if not gates:
                rej["no gates"] += 1; continue
            if r.get("inputCount", 32) != 32:
                rej["inputs!=32"] += 1; continue
            vals = values_from_gates(gates)
            vs = set(vals)
            if not TSET <= vs:
                rej["not MixColumns (targets missing)"] += 1; continue
            if len(vs) != len(vals):
                rej["duplicate gate values (counted once)"] += 1
            if len(vs - ISET) != g:
                rej[f"distinct non-input values != {g}"] += 1; continue
            if r.get("depth") not in (4, None):
                rej["depth field != 4"] += 1; continue
            camp = f.split("xs-campaigns/")[1].split("/")[0]
            camps[camp] += 1
            h = frozenset(vs - TSET)
            e = by_h.setdefault(h, {"n": 0, "camps": Counter(), "file": f.replace(HOME, "~")})
            e["n"] += 1
            e["camps"][camp] += 1
        if g == 89:
            e = by_h.setdefault(repo_h, {"n": 0, "camps": Counter(), "file": "repo"})
            e["n"] += 1; e["camps"]["repo"] += 1
            camps["repo"] += 1
        nfiles = sum(camps.values())
        print(f"\n=== {g}@4: files scanned {len(files)}, accepted {nfiles}, rejected {dict(rej)}")
        print("  accepted by campaign:", dict(camps))
        print("  distinct helper sets (= distinct value sets):", len(by_h))
        # rotation classes
        classes = defaultdict(list)
        for h in by_h:
            k, s = canon(h)
            classes[k].append((h, s))
        print("  distinct modulo Z4 byte rotation:", len(classes),
              " classes with >1 member:", sum(1 for c in classes.values() if len(c) > 1))
        # levels, profiles, L1 sets
        rows = []
        profiles = Counter(); L1sets = Counter(); L1size = Counter(); unreach = 0; depth_hist = Counter()
        for h in by_h:
            lev, un = least_levels(set(h) | TSET)
            if un:
                unreach += 1
            d = max(lev.values())
            depth_hist[d] += 1
            prof = tuple(sum(1 for v in (set(h) | TSET) if lev[v] == L) for L in range(1, d + 1))
            profiles[prof] += 1
            L1 = frozenset(v for v in h if lev[v] == 1)
            assert all(bin(v).count("1") == 2 for v in L1)
            w2 = frozenset(v for v in (set(h) | TSET) if bin(v).count("1") == 2)
            assert w2 == L1, "weight-2 values are exactly the level-1 values"
            L1sets[L1] += 1; L1size[len(L1)] += 1
            rows.append({"helpers": sorted(h), "n_files": by_h[h]["n"], "camps": dict(by_h[h]["camps"]),
                         "profile": list(prof), "depth": d, "L1": sorted(L1), "rotclass": canon(h)[1], "file": by_h[h]["file"]})
        print("  depth (least levels) histogram:", dict(depth_hist), " unreachable-value states:", unreach)
        print("  profiles:", profiles.most_common(6), " (distinct profiles:", len(profiles), ")")
        print("  distinct level-1 sets:", len(L1sets), " first-layer size histogram:", dict(sorted(L1size.items())))
        states[g] = rows
        summary[g] = {"files_scanned": len(files), "accepted": nfiles, "rejected": dict(rej), "by_campaign": dict(camps),
                      "distinct": len(by_h), "distinct_mod_rot": len(classes),
                      "profiles": [[list(p), c] for p, c in profiles.most_common()],
                      "distinct_L1_sets": len(L1sets), "L1_size_hist": dict(sorted(L1size.items())), "depth_hist": dict(depth_hist)}
    # the 89 family
    r89 = states[89]
    repo_row = [r for r in r89 if frozenset(r["helpers"]) == repo_h][0]
    L1_89 = frozenset(repo_row["L1"])
    rots89 = [frozenset(rot(v, s) for v in L1_89) for s in (0, 8, 16, 24)]
    assert len(set(rots89)) == 4
    same = Counter()
    for r in r89:
        L1 = frozenset(r["L1"])
        same[[s for s in range(4) if rots89[s] == L1][0] * 8 if L1 in rots89 else "other"] += 1
    print("\n89@4 states by first layer (rotation of the repo 89's L1 by s bits):", dict(same))
    summary["89_L1_rotation_of_repo"] = {str(k): v for k, v in same.items()}
    # 90@4 first-layer comparison
    r90 = states[90]
    ov = Counter(); eq = Counter(); size26 = []
    for r in r90:
        L1 = frozenset(r["L1"])
        best = max(len(L1 & R) for R in rots89)
        ov[best] += 1
        if L1 in rots89:
            eq[rots89.index(L1) * 8] += 1
        if len(L1) == 26:
            size26.append(L1)
    print("90@4: states whose L1 equals the 89's L1 under some rotation:", dict(eq))
    print("90@4: histogram of max overlap with the 89's 26 pairs over rotations:", dict(sorted(ov.items(), reverse=True)))
    print("90@4: states with 26 first-layer gates:", len(size26), " distinct L1 sets among them:", len(set(size26)))
    for s in set(size26):
        diff_minus = sorted(L1_89 - s); diff_plus = sorted(s - L1_89)
        print("   26-set vs the 89's L1: missing", [bitnames(v) for v in diff_minus], "extra", [bitnames(v) for v in diff_plus],
              " max overlap over rotations", max(len(s & R) for R in rots89))
    summary["90_vs_89_L1"] = {"equal_any_rotation": dict(eq), "max_overlap_hist": dict(ov), "n_states_L1_26": len(size26)}
    json.dump(summary, open(f"{OUT}/c1_summary.json", "w"), indent=1)
    json.dump({"targets": TARGETS, "repo_helpers": sorted(repo_h), "L1_89": sorted(L1_89), "states": r89}, open(f"{OUT}/c1_states_89.json", "w"))
    json.dump({"states": r90}, open(f"{OUT}/c1_states_90.json", "w"))

def bitnames(v):
    return "+".join(f"x{i}" for i in range(N) if v >> i & 1)

if __name__ == "__main__":
    main()
