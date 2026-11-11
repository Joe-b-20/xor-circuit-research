#!/usr/bin/env python3
"""Build the residual coverage manifest (machine-readable) from the scope measurements.

Inputs (all in this folder): ladders.json (per-claim key ladders, open leaves with integer status, status under hypotheses),
hypo_*.json (driver-based hypothetical scans), hypo_kill_*.json (block closures), leaves_int.json, share_pairs.json,
/tmp/noint101.json (the sprint's 101 MILP-classified keys, key order (h,y,F,ori,q,z)).
Output: coverage_manifest.json (+ a short printed summary).  Everything is LP / MILP status [measured]; the only certified
objects are the certificate files of the published package.
"""
import json, sys
from pathlib import Path
from collections import Counter, defaultdict
HERE = Path(__file__).resolve().parent
L = json.load(open(HERE / "ladders.json"))
FULL = json.load(open(HERE / "hypo_full.json"))
LB229 = {tuple(k) for k in FULL["load_bearing_keys"]}
HYPO = {v: json.load(open(HERE / f"hypo_{v}.json")) for v in ("A01", "A01_or_dark", "A01_or_A5", "A0")}
KILL = {p.stem[len("hypo_kill_"):]: json.load(open(p)) for p in HERE.glob("hypo_kill_*.json")}
SHARE = json.load(open(HERE / "share_pairs.json"))
NOINT = [tuple(k) for k in json.load(open("/tmp/noint101.json"))["keys_no_int_solution"]]
KEYS = {tuple(eval(k)): v for k, v in L["keys"].items()}

claims = []
key_claims = defaultdict(list)
for c in L["claims"]:
    st = tuple(c["state"]); cid = f"{st}|{c['ori']}"
    st_full = {h: c["status"][h]["open"] for h in c["status"]}
    even = {int(s): [tuple(k) for k in ks] for s, ks in c["even_ladder"].items()}
    odd = {int(s): [tuple(k) for k in ks] for s, ks in c["odd_ladder"].items()}
    for s, ks in even.items():
        for k in ks: key_claims[k].append((cid, "even", s))
    for s, ks in odd.items():
        for k in ks: key_claims[k].append((cid, "odd", s))
    # the inequality that closes the claim: every feasible level pair (s_e, s_o) within the three tests must disappear
    pairs = [(se, so) for se in even for so in odd if se <= c["Se"] and so <= c["So"] and se + so <= c["budget"]]
    bound = ("k + l > budget" if c["k"] + c["l"] == c["budget"] else f"k + l > budget needs {c['budget'] - c['k'] - c['l'] + 1} more level step(s), or k > Se (needs {c['Se'] - c['k'] + 1}), or l > So (needs {c['So'] - c['l'] + 1})")
    def leafsum(ks):
        out = []
        for k in ks:
            inf = KEYS[k]
            out.append({"key": str(k), "layer": "first" if k in LB229 else "behind", "n_open_leaves": len(inf["leaves"]),
                        "min_A": min(lf["A"] for lf in inf["leaves"]), "has_A0_leaf": any(lf["A"] == 0 for lf in inf["leaves"]),
                        "all_leaves_integer_infeasible": all(lf["int"] == "infeasible" for lf in inf["leaves"])})
        return out
    claims.append({
        "id": cid, "state": list(st), "orientation": c["ori"], "state_fields": "(a, b, Y, V, h_even, h_odd, l_even, l_odd, S_even, S_odd, budget)",
        "k": c["k"], "l": c["l"], "Se": c["Se"], "So": c["So"], "budget": c["budget"], "shortfall": c["shortfall"],
        "bound_needed": bound, "feasible_level_pairs": pairs,
        "even_phase_key_pattern": f"(h_even={st[4]}, y={st[2]}, F={st[3]}, {c['ori']}, q, z) with q + z = level",
        "odd_phase_key_pattern": f"(h_odd={st[5]}, y={st[3]}, F={st[2]}, {'Mt' if c['ori']=='M' else 'M'}, q, z) with q + z = level",
        "even_ladder": {str(s): leafsum(ks) for s, ks in sorted(even.items())},
        "odd_ladder": {str(s): leafsum(ks) for s, ks in sorted(odd.items())},
        "configurations_that_can_still_violate": "every LP-feasible open leaf (A, q_D) of every key in the two ladders; the leaf's integer status says whether an integer type vector exists",
        "open_under_hypothesis": st_full,
        "covered_by_A_ge_2_enumeration": not st_full["A01"],
        "covered_by_any_hub_route_A_ge_1": not st_full["A0"],
        "closable_by_integer_certificates_alone": not st_full["INT"],
        "closable_by_integer_certificates_plus_A_ge_2": not st_full["INT_A01"],
    })

keys = {}
for k, inf in KEYS.items():
    keys[str(k)] = {"key": list(k), "layer": "first (load-bearing now)" if k in LB229 else "behind the first layer",
                    "open_leaves": [{"A": lf["A"], "qD": lf["qD"], "int": lf["int"]} for lf in inf["leaves"]], "claims": key_claims.get(k, []),
                    "sprint_MILP_classified_integer_infeasible_2026_11_07": k in set(NOINT)}
hist = Counter()
for c in claims:
    for h, o in c["open_under_hypothesis"].items(): hist[(h, o)] += 1

manifest = {
    "title": "Residual coverage manifest for the open oriented claims at G = 75 (AES MixColumns 75-gate proof framework)",
    "date": "2026-11-10",
    "status_of_everything_here": "LP / MILP status [measured] with the published combined rows (sprint Addenda A-D + October push5/push6); not certificates. The lower bound stays 75.",
    "definitions": {
        "claim": "an oriented claim (scalar state, orientation) of the package's final test at G = 75; open iff k <= Se, l <= So and k + l <= budget with k, l the least LP-feasible levels of the even and odd phase keys",
        "key": "(h, y, F, orientation, q, z): a local linear system on helper type counts (r, u, v); level s = q + z",
        "leaf": "(A = a, q_D = d): the exact hub case (a = number of full-met missing labels) and dark case (d = number of dark missing labels) of a key's case tree; a key is excluded iff every leaf is",
        "ladder": "for a claim, the LP-feasible keys at every level that could keep it open (even: le <= s <= min(Se, budget - lo); odd: lo <= s <= min(So, budget - le)); the 229 'load-bearing' keys are the first-level keys only",
        "hypotheses": {"A01": "every leaf with A >= 2 excluded", "A01_or_dark": "every leaf with A >= 2 and q_D = 0 excluded", "A0": "every leaf with A >= 1 excluded",
                        "INT": "every integer-infeasible leaf certified (type counts are integers)", "INT_A01": "INT and A01 together"}},
    "counts": {
        "open_claims": len(claims), "first_layer_keys": len(LB229), "ladder_keys_total": len(KEYS),
        "ladder_keys_behind_first_layer": sum(1 for k in KEYS if k not in LB229),
        "open_leaves_first_layer": 572, "first_layer_leaves_by_A": FULL and {str(a): n for a, n in json.load(open(HERE.parent.parent / "xor-circuit-research/lower-bound-proofs/mixcolumns-lb75-open-cases/combined/measurement/scan_leaves.json"))["by_A"]} if False else {"0": 66, "1": 81, "2": 115, "3": 167, "4": 98, "5": 38, "6": 7},
        "first_layer_leaves_integer_status": dict(Counter(lf["int"] for k in LB229 for lf in KEYS[k]["leaves"])),
        "ladder_leaves_integer_status": dict(Counter(lf["int"] for inf in KEYS.values() for lf in inf["leaves"])),
        "open_claims_by_hypothesis_ladder_evaluation": {h: hist[(h, True)] for h in ("full", "A01", "A01_or_dark", "A0", "INT", "INT_A01")},
        "open_claims_by_hypothesis_driver_scan": {"full": FULL["survivors"], **{v: HYPO[v]["survivors"] for v in HYPO}},
        "block_closures_driver_scan": {n: {"killed_keys": d["killed_keys"], "open_claims_after": d["survivors"], "new_load_bearing_keys": len(d["new_load_bearing_keys"])} for n, d in sorted(KILL.items())},
    },
    "explanations": {
        "concentrated_vs_covered": "'The open leaves are concentrated at A = 2..4 with no dark label' is a statement about the 572 first-layer leaves (380 have A in 2..4, 481 have q_D = 0). 'All remaining claims are covered by that region' would require every claim to die once those leaves are excluded. It is false: excluding every leaf with A >= 2 leaves 119 claims open (driver scan; the ladder evaluation gives the per-claim list), because 62 of the 229 first-layer keys have an open leaf with A <= 1 and further keys behind the first layer take over. Excluding every leaf with A >= 1 still leaves 88 claims open on A = 0 configurations, where no hub argument applies.",
        "old_enumerations": "The sprint's two unrun enumerations (M^T q = 1 with 7-8 full helpers; M q = 2 with ten) address no live obligation: no key with q <= 2 is in any ladder's first layer, the sprint's q = 1 representatives (19,0,0,Mt,1,5), (18,1,1,Mt,1,4), (12,5,1,Mt,1,4), (11,7,1,Mt,1,4) are LP-infeasible under the combined rows, and the 82 LP-feasible q <= 2 keys appear only behind the first layer (listed in the ladders where they do). They are removed from the immediate task.",
        "the_101_keys": "The 101 keys the sprint's MILP oracle classified integer-infeasible (20 s limit, status not recorded) were never used as exclusions: the 280 count is LP status. None of them is a first-layer key today; one, (11,7,0,M,4,2), is LP-feasible behind the first layer. Their classification stays unresolved; today's leaf survey (status recorded, all solves terminated with status 0 or 2) is a separate measurement and also not a certificate.",
        "pairwise_sharing": "Finite GF(2) rank check (share_pairs.py): anchored hubs with no full-met label CAN share a hub-only label with the Lemma-J family independent (M: 361,168 / 58,172 / 3,900 mask pairs for classes r = 1/1, 1/2, 2/2; M^T: 481,440 / 83,940 / 5,748). So no per-pair finite fact yields a row; remaining obstructions are joint over whole configurations.",
    },
    "pairwise_sharing_table": SHARE,
    "claims": claims,
    "keys": keys,
    "unresolved_items": {
        "sprint_MILP_101_keys": {"keys": [list(k) for k in NOINT], "in_first_layer_now": [list(k) for k in NOINT if k in LB229], "in_ladders_now": [list(k) for k in NOINT if k in KEYS], "status": "unresolved; never used as exclusions"},
        "obsolete_enumerations": {"Mt_q1_7_8_full_helpers": "no live obligation (see explanations.old_enumerations)", "M_q2_ten_full_helpers": "no live obligation"},
        "package_LP_only_exclusions_at_75": "the package's 5,908 claims excluded only by LP status at G = 75 are NOT certified; a bound of 76 would need certificates for them as well as for the 280 (see the README of the published folder)",
    },
}
json.dump(manifest, open(HERE / "coverage_manifest.json", "w"), separators=(",", ":"))
print("claims", len(claims), "ladder keys", len(KEYS), "behind first layer", manifest["counts"]["ladder_keys_behind_first_layer"])
print("open by hypothesis (ladder):", manifest["counts"]["open_claims_by_hypothesis_ladder_evaluation"])
print("open by hypothesis (driver):", manifest["counts"]["open_claims_by_hypothesis_driver_scan"])
print("leaf integer status (ladders):", manifest["counts"]["ladder_leaves_integer_status"])
