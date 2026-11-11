#!/usr/bin/env python3
"""Full-domain accounting of the oriented claims at G = 75, by identifier (not by totals).

Domain: every (scalar state, orientation) of the package's final test at G = 75 (lp_regen.scalar_states(75) x {M, Mt}).
Partition claimed by the published folder:
   package-row exclusions (LP status only at G = 75; the package ships certificates for G = 74 only)
 + batch 1 (195) + batch 2 (317) + batch 3 (207) + batch 4 (103)   [certified, sprint]
 + combined (406)                                                  [certified, sprint + October rows]
 + open (280)                                                      [LP status]
This script recomputes the package-only LP scan (the package's own driver and rows, scipy HiGHS), loads the claim lists
of the five certificate files and the open list of the combined scan (hypo_full.json, reproduced 2026-11-10), and checks
that the seven sets are pairwise disjoint and that their union is the whole domain.  Output: domain_accounting.json.
LP status is a measurement; the certified sets are certified by the published checkers, not by this script.
"""
import json, sys, importlib.util
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = Path.home() / "xor-circuit-research"
OC = REPO / "lower-bound-proofs/mixcolumns-lb75-open-cases"
PKG = REPO / "lower-bound-proofs/mixcolumns-lb75/source/lower_bounds/checks"
spec = importlib.util.spec_from_file_location("lp_regen_pkg", PKG / "lp_regen.py"); LR = importlib.util.module_from_spec(spec); spec.loader.exec_module(LR)

states, claims, surv = LR.run(75)
domain = set(claims)
pkg_open = {(st, o) for st, o, k, l in surv}
pkg_dead = domain - pkg_open
print("domain", len(domain), "package-open", len(pkg_open), "package-dead (LP only)", len(pkg_dead), "LP unknown statuses", len(LR.UNKNOWN))


def cl(path, field="claims"):
    d = json.load(open(path)); out = set()
    for c in d[field]:
        if isinstance(c, dict): out.add((tuple(c["state"]), c["orientation"]))
        else: out.add((tuple(c[0]), c[1]))
    return out


sets = {
    "batch1_certified": cl(OC / "certificates/CERTIFICATES_EXT75.json"),
    "batch2_certified": cl(OC / "certificates/CERTIFICATES_CASES75.json"),
    "batch3_certified": cl(OC / "certificates/CERTIFICATES_CASES75_B3.json"),
    "batch4_certified": cl(OC / "certificates/CERTIFICATES_CASES75_B4.json"),
    "combined_certified": cl(OC / "combined/CERTIFICATES_COMBINED75.json", "claims_excluded"),
    "open_combined_LP": {(tuple(st), o) for st, o, k, l in json.load(open(HERE / "hypo_full.json"))["survivor_list"]},
}
names = list(sets)
disjoint = all(not (sets[a] & sets[b]) for i, a in enumerate(names) for b in names[i + 1:])
union = set().union(*sets.values())
res = {
    "domain_claims": len(domain), "scalar_states": len(states),
    "package_rows_dead_LP_status_only": len(pkg_dead), "package_rows_open": len(pkg_open),
    "sizes": {n: len(s) for n, s in sets.items()},
    "pairwise_disjoint": disjoint,
    "union_equals_package_open_set": union == pkg_open,
    "union_minus_package_open": len(union - pkg_open), "package_open_minus_union": len(pkg_open - union),
    "every_listed_claim_in_domain": union <= domain,
    "partition_of_domain_holds": disjoint and union == pkg_open and (pkg_dead | union) == domain and not (pkg_dead & union),
    "J1_dependent_batch4_claims": len(sets["batch4_certified"]) - len(cl(OC / "certificates/CERTIFICATES_CASES75_B4.json", "claims_excluded_without_LIM")),
    "note": "package_rows_dead are excluded at G = 75 by LP status only; the package's exact certificates are for G = 74. Certified sets are certified by the published checkers (verify_all.py).",
}
json.dump(res, open(HERE / "domain_accounting.json", "w"), indent=1)
print(json.dumps(res, indent=1))
