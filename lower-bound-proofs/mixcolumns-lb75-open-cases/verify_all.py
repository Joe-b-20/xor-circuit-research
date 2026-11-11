#!/usr/bin/env python3
"""Replay the exact certificate checks for the open cases of the 75-gate proof at G = 75.

Run from any directory: python3 /path/to/mixcolumns-lb75-open-cases/verify_all.py
Standard library only. Do not use -O: the checkers rely on assertions.

Stages, all in a temporary copy of checkers/, certificates/ and combined/ (this folder is written to
only under verification/run_<timestamp>/):
  1-4  the sprint's four independent checkers (batches 1-4, Addenda A-D): 822 claims excluded;
  5    the independent checker of the combined certificates (sprint rows + the October 2026 push5/push6
       rows): 406 further claims excluded, plus the 43-certificate J1-free addendum;
  6    the recomputation of the finite facts behind the October rows (about a minute);
  7    the checker of the certificates for the 5,908 claims that the 75 proof's own rows exclude at
       G = 75 (package-rows-g75/), and the accounting of all 7,416 claims by identifier.
A passing run shows that 5,908 + 822 + 406 = 7,136 distinct oriented claims at G = 75 are excluded by
exact integer Farkas certificates and that the other 280 claims of the domain have none. It does not
raise the lower bound, which stays 75, and it does not check the written arguments.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parent

# SHA-256 of the inputs. The certificate files are byte-identical to their originals; the checkers
# differ from their originals only by the path edits listed in checkers/CHANGES.md.
PINNED = {
    "certificates/CERTIFICATES_EXT75.json": "68df54a7581a9760e4946c9e603f38bf8f2b8372d739e3c376daa846b722daf7",
    "certificates/CERTIFICATES_CASES75.json": "19bad1fec5e718abcc03bd078252a3ebc2ff03866545ddadc7494d0f2ed10dca",
    "certificates/CERTIFICATES_CASES75_B3.json": "567b1778e0210602c9df976940471356ce04a58bcc1b3094942443cf4985b9ac",
    "certificates/CERTIFICATES_CASES75_B4.json": "70d2bc30353d9b24d72c0afa89e1d97d5126c57fadd0fd060b067268d1708ca0",
    "combined/CERTIFICATES_COMBINED75.json": "9fc00ae3af30f6199c70720cb7b0c5a0b0cf86d7bcb6ee88c8b3ea140383edee",
    "combined/CERTIFICATES_COMBINED75_J1FREE_ADDENDUM.json": "089a140177e82e1c0b19695f415b3a6d3f9ccabf93ba48c6dd434056f30c6d07",
    "checkers/check_ext75.py": "6c6cc9ed3cbcb4127d921e402d0c846466020e0a8440996a8d836accbb2184cc",
    "checkers/check_cases75.py": "0e3c8cee0a3c268110bba98b4e97a2d34e74eb8ad028177bb68cbced9a5a18fc",
    "checkers/check_cases3.py": "d6c69cc5a80b5fd63da8edbc5e2ef36df4548b0301eb4d1c7034e100283a23a6",
    "checkers/check_cases3_copy.py": "9319b103e1f6c7a4cbff28214cd1e1ed9b80c38d9470adde55f7ee8412b8f8ec",
    "checkers/check_cases4.py": "4c40e51d34bb84a54826c93a251f8bd290ab742f0befe69212072ab12778364e",
    "checkers/check_combined75.py": "40be8f22a4e0a072182016c661031bddb86cc441318f0df79dce445c565945c7",
    "checkers/finite_facts_october.py": "c7d9bc075edf4a4bb38e285486fcc86adee91f9de599ea9bb068f1b9b531ee68",
    "checkers/finite_facts_october.recorded.json": "a5deae2157f7941d99824686e59673caa42c13116455f4b67fe7b64a2f311357",
    "package-rows-g75/CERTIFICATES_PKG75_G75.json": "d8a7f2970b3b133c1f43b2314b54ab36253afd0b9dc9b1da4e8df7bbf38eebd7",
    "package-rows-g75/check_pkg75.py": "d4da6376b7f5c876652c6d6a2ab8d4f4626121e811fe5f81069f11803e7fe77c",
    "package-rows-g75/published_sets.json": "ed84085bd755ac46cc677b0fb86afdc04b10ce445b8b06fe1b837ea2f52750e9",
}

# (batch, checker, certificate file, report the checker writes, fields the report must contain,
#  generator-recorded survivor counts before / after this batch [measured, LP status])
STAGES = (
    (1, "check_ext75.py", "CERTIFICATES_EXT75.json", "CHECKED_EXT75.json", {
        "gates": 75, "scalar_states": 3708, "claims_checked": 195, "local_certificates": 1772,
        "certificates_new": 666, "certificates_package": 1106, "coefficients_checked": 53917,
        "largest_right_side": -1, "certificate_references": 2158, "distinct_referenced": 1459,
        "direct_geometric_references": 567, "all_checks_passed": True,
    }, ("base_survivors", "extended_survivors")),
    (2, "check_cases75.py", "CERTIFICATES_CASES75.json", "CHECKED_CASES75.json", {
        "gates": 75, "scalar_states": 3708, "claims_checked": 317, "certificates": 4523,
        "certificates_case": 2497, "batch1_feasible_keys": 681, "killed_keys": 300,
        "surviving_keys": 381, "coefficients_checked": 192917, "largest_right_side": -1,
        "certificate_references": 4173, "distinct_referenced": 2232,
        "direct_geometric_references": 620, "all_checks_passed": True,
    }, ("batch1_survivors", "full_survivors")),
    (3, "check_cases3.py", "CERTIFICATES_CASES75_B3.json", "CHECKED_CASES75_B3.json", {
        "gates": 75, "scalar_states": 3708, "claims_checked": 207, "certificates": 4950,
        "certificates_case": 2925, "batch2_feasible_keys": 1713, "killed_keys": 536,
        "surviving_keys": 1177, "coefficients_checked": 251213, "largest_right_side": -1,
        "certificate_references": 3353, "distinct_referenced": 2054,
        "direct_geometric_references": 401, "all_checks_passed": True,
    }, ("batch2_survivors", "full_survivors")),
    (4, "check_cases4.py", "CERTIFICATES_CASES75_B4.json", "CHECKED_CASES75_B4.json", {
        "gates": 75, "scalar_states": 3708, "claims_checked": 103, "certificates": 4361,
        "certificates_case": 3506, "batch3_feasible_keys": 1679, "killed_keys": 375,
        "surviving_keys": 1304, "coefficients_checked": 264062, "largest_right_side": -1,
        "certificate_references": 1616, "distinct_referenced": 980,
        "direct_geometric_references": 188, "certificates_using_J1": 78,
        "killed_keys_covered_without_J1": 297, "claims_covered_without_J1": 65,
        "all_checks_passed": True,
    }, ("batch3_survivors", "new_survivors")),
)
ORIENTATIONS = {1: {"M": 122, "Mt": 73}, 2: {"M": 220, "Mt": 97}, 3: {"M": 88, "Mt": 119},
                4: {"M": 44, "Mt": 59}, 5: {"M": 224, "Mt": 182}}
CHAIN = (1508, 1313, 996, 789, 686)
COMBINED_OPEN = 280

# Stage 5: the combined checker (its own EXPECTED dictionary is pinned inside it as well).
COMBINED_EXPECTED = {
    "gates": 75, "scalar_states": 3708, "claims_checked": 406, "claims_M": 224, "certificates": 4653,
    "certificates_by_kind": {"package": 2565, "push": 645, "case": 879, "batch1": 561, "flat": 3},
    "certificates_using_push_rows": 1247, "certificates_using_LIM": 1, "keys_with_certificates": 3863,
    "distinct_referenced_keys": 3863, "coefficients_checked": 188062, "largest_weighted_rhs": -1,
    "claims_not_covered_without_LIM": 4, "addendum_certificates": 43, "addendum_claims": 4,
    "addendum_largest_weighted_rhs": -1, "all_checks_passed": True,
}

# Stage 6: headline counts of the finite-fact recomputation; the whole output (except timing) must
# also equal the recorded run checkers/finite_facts_october.recorded.json.
FINITE_EXPECTED = {
    ("M", "base", "repeated"): 440, ("Mt", "base", "repeated"): 616,
    ("M", "base", "full"): 80, ("Mt", "base", "full"): 112,
    ("M", "base", "core_outputs"): 20, ("Mt", "base", "core_outputs"): 28,
    ("M", "base", "pairs"): 2016, ("Mt", "base", "pairs"): 2016,
    ("M", "contact", "pairs_with_boundary_pair_difference"): 11520,
    ("Mt", "contact", "pairs_with_boundary_pair_difference"): 16992,
    ("M", "contact", "endpoints_outside_inputs_plus_core"): 0,
    ("Mt", "contact", "endpoints_outside_inputs_plus_core"): 0,
    ("M", "code", "dim_R10"): 32, ("Mt", "code", "dim_R10"): 29,
    ("Mt", "code", "weight12_nonzero_mod_R10"): 736,
    ("Mt", "F1F2", "splits"): 4250400, ("Mt", "F1F2", "F1_three_parts_in_P"): 0,
    ("Mt", "F1F2", "F2_rank_hist"): {"1": 2599, "2": 2544},
    ("Mt", "F3", "rank_hist"): {"1": 8804}, ("Mt", "F3", "strong_rank_hist"): {"1": 320},
    ("Mt", "F5", "pivots"): 4800, ("Mt", "F5", "PP_alternatives"): 917376,
    ("Mt", "F5", "RP_alternatives"): 199184, ("Mt", "F5", "nonzero_remainders"): 0,
}

# Stage 7: the report of package-rows-g75/check_pkg75.py (it must also equal the recorded report).
PKG_EXPECTED = {
    "gates": 75, "scalar_states": 3708, "claims": 7416, "excluded_certified": 5908, "open": 1508,
    "certificates": 15742, "coefficients_checked": 827190, "certificate_references": 33536,
    "largest_weighted_rhs": -1, "uncertified_keys_reported_by_generator": 0,
    "disjoint_from_published_sets": True, "excluded_plus_published_equals_domain": True,
    "open_here_equals_union_of_published_sets": True,
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def check_integrity():
    for rel, digest in PINNED.items():
        path = ROOT / rel
        require(path.is_file(), "Missing file: " + rel)
        require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, "SHA-256 mismatch: " + rel)
    require(not (ROOT / "certificates" / "CERTIFICATES_PARTIAL75_B4.json").exists(),
            "Unexpected CERTIFICATES_PARTIAL75_B4.json: the pinned batch-4 run is without it")
    return len(PINNED)


def check_claim_bookkeeping(work):
    """The wrapper's own check across the files: the claim lists are pairwise disjoint, have the
    recorded orientation split, and the generator-recorded survivor counts form the stated chain.
    The survivor counts themselves are LP-status measurements recorded by the generators; only the
    exclusions are certified."""
    seen = {}
    chain = [None]
    for batch, _, cert_name, _, _, (before, after) in STAGES:
        data = json.loads((work / "certificates" / cert_name).read_text(encoding="utf-8"))
        claims = [(tuple(c["state"]), c["orientation"]) for c in data["claims"]]
        require(len(set(claims)) == len(claims), f"batch {batch}: repeated claim")
        for claim in claims:
            require(claim not in seen, f"claim {claim} excluded in batch {seen.get(claim)} and {batch}")
            seen[claim] = batch
        split = {o: sum(1 for _, ori in claims if ori == o) for o in ("M", "Mt")}
        require(split == ORIENTATIONS[batch] and sum(split.values()) == len(claims),
                f"batch {batch}: orientation split {split}")
        counts = data["counts"]
        require(counts["scalar_states"] == 3708 and counts["oriented_claims"] == 7416,
                f"batch {batch}: domain counts")
        require(counts["newly_excluded_claims"] == len(claims), f"batch {batch}: newly_excluded_claims")
        require(counts[before] - len(claims) == counts[after], f"batch {batch}: {before} - claims != {after}")
        if chain[-1] is not None:
            require(counts[before] == chain[-1], f"batch {batch}: {before} does not continue the chain")
        else:
            chain[0] = counts[before]
        chain.append(counts[after])
    require(tuple(chain) == CHAIN, f"survivor chain {chain}")
    require(len(seen) == CHAIN[0] - CHAIN[-1] == 822, "distinct excluded claims")
    # the combined file: 406 claims, none excluded by a sprint batch, the J1-free addendum's 4 among them
    data = json.loads((work / "combined" / "CERTIFICATES_COMBINED75.json").read_text(encoding="utf-8"))
    claims = [(tuple(c[0]), c[1]) for c in data["claims_excluded"]]
    require(len(set(claims)) == len(claims) == data["counts"]["claims"], "combined: repeated claim")
    for claim in claims:
        require(claim not in seen, f"combined claim {claim} already excluded in batch {seen.get(claim)}")
    split = {o: sum(1 for _, ori in claims if ori == o) for o in ("M", "Mt")}
    require(split == ORIENTATIONS[5], f"combined: orientation split {split}")
    require(not data["uncovered_claims"] and not data["uncertified_keys"], "combined: uncovered claims recorded")
    addendum = json.loads((work / "combined" / "CERTIFICATES_COMBINED75_J1FREE_ADDENDUM.json").read_text(encoding="utf-8"))
    add_claims = {(tuple(c[0]), c[1]) for c in addendum["claims"]}
    require(len(add_claims) == 4 and add_claims <= set(claims), "addendum claims are not 4 of the 406")
    require(CHAIN[-1] - len(claims) == COMBINED_OPEN, "686 - 406 != 280")
    return {"distinct_claims_certified_excluded_sprint": len(seen),
            "distinct_claims_certified_excluded_combined": len(seen) + len(claims),
            "open_claim_chain": list(chain) + [COMBINED_OPEN]}


def check_domain_accounting(work):
    """package-rows-g75/published_sets.json against the certificate files: its five certified sets are
    the claim lists of those files, and its six sets are pairwise disjoint with 1,508 claims in all.
    check_pkg75.py has checked that their union is exactly the set of claims the package rows leave
    open and that it is disjoint from the 5,908 claims certified there. So the 280 claims of the sixth
    set are exactly the claims of the domain that no certificate file excludes."""
    raw = json.loads((work / "package-rows-g75" / "published_sets.json").read_text(encoding="utf-8"))
    require(set(raw) == {"batch1", "batch2", "batch3", "batch4", "combined", "open_LP"}, "published_sets.json: set names")
    sets = {name: {(tuple(s), o) for s, o in value} for name, value in raw.items()}
    require(all(len(sets[name]) == len(raw[name]) for name in raw), "published_sets.json: repeated claim")
    for batch, _, cert_name, _, _, _ in STAGES:
        data = json.loads((work / "certificates" / cert_name).read_text(encoding="utf-8"))
        claims = {(tuple(c["state"]), c["orientation"]) for c in data["claims"]}
        require(sets[f"batch{batch}"] == claims, f"published_sets.json: batch{batch} differs from {cert_name}")
    data = json.loads((work / "combined" / "CERTIFICATES_COMBINED75.json").read_text(encoding="utf-8"))
    claims = {(tuple(c[0]), c[1]) for c in data["claims_excluded"]}
    require(sets["combined"] == claims, "published_sets.json: combined differs from CERTIFICATES_COMBINED75.json")
    union = set().union(*sets.values())
    require(len(union) == sum(len(v) for v in sets.values()) == CHAIN[0], "published sets overlap or do not total 1,508")
    require(len(sets["open_LP"]) == COMBINED_OPEN, "open set is not 280 claims")
    return {"domain_claims": 7416, "claims_certified_excluded_package_rows": 5908,
            "claims_certified_excluded_total": 5908 + CHAIN[0] - COMBINED_OPEN,
            "claims_without_certificate": len(sets["open_LP"])}


def run(work, script, logs, env, folder="checkers"):
    result = subprocess.run([sys.executable, "-B", str(work / folder / script)],
                            cwd=str(work / folder), env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log = logs / (script.removesuffix(".py") + ".log")
    log.write_text(result.stdout, encoding="utf-8")
    if result.returncode != 0:
        print(result.stdout[-4000:], file=sys.stderr)
        raise RuntimeError(f"{script} failed with exit code {result.returncode}; see {log}")
    return result.stdout, log


def check_report(work, report_name, expected, logs):
    report = json.loads((work / "checkers" / report_name).read_text(encoding="utf-8"))
    for key, value in expected.items():
        require(report.get(key) == value, f"Unexpected {report_name}: {key}={report.get(key)!r}")
    shutil.copyfile(work / "checkers" / report_name, logs / report_name)
    return report


def strip_seconds(data):
    return {k: v for k, v in data.items() if k != "seconds"}


def main():
    require(sys.version_info >= (3, 10), "Python 3.10 or newer is required")
    require(sys.flags.optimize == 0, "Do not run this verifier with -O or -OO")
    require(len(sys.argv) == 1, "Usage: python3 verify_all.py")
    start = time.monotonic()
    started = datetime.now(timezone.utc)
    logs = ROOT / "verification" / ("run_" + started.strftime("%Y%m%dT%H%M%SZ"))
    logs.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.pop("PYTHONOPTIMIZE", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    n = check_integrity()
    print(f"Integrity passed: {n} pinned certificate, checker and record files.", flush=True)
    results = []
    with tempfile.TemporaryDirectory(prefix="lb75_open_cases_") as temporary:
        work = Path(temporary)
        shutil.copytree(ROOT / "checkers", work / "checkers")
        shutil.copytree(ROOT / "certificates", work / "certificates")
        shutil.copytree(ROOT / "package-rows-g75", work / "package-rows-g75")
        (work / "combined").mkdir()
        for name in ("CERTIFICATES_COMBINED75.json", "CERTIFICATES_COMBINED75_J1FREE_ADDENDUM.json"):
            shutil.copyfile(ROOT / "combined" / name, work / "combined" / name)
        for batch, script, cert_name, report_name, expected, _ in STAGES:
            print(f"Batch {batch}: {script} on {cert_name} ...", flush=True)
            t = time.monotonic()
            out, log = run(work, script, logs, env)
            require("expected counts match" in out, f"{script}: pinned counts not confirmed")
            require("INDEPENDENT CHECK PASSED" in out, f"{script}: no completion line")
            require("PARTIAL CERTIFICATES CHECKED" not in out, f"{script}: unexpected partial file")
            report = check_report(work, report_name, expected, logs)
            elapsed = round(time.monotonic() - t, 3)
            results.append({"stage": script, "exit_code": 0, "elapsed_seconds": elapsed,
                            "claims_certified": report["claims_checked"], "log": str(log.relative_to(ROOT))})
            print(f"  passed in {elapsed:.1f} s: {report['claims_checked']} claims excluded", flush=True)

        print("Combined: check_combined75.py on CERTIFICATES_COMBINED75.json (+ J1-free addendum) ...", flush=True)
        t = time.monotonic()
        out, log = run(work, "check_combined75.py", logs, env)
        require("expected counts match" in out, "check_combined75.py: pinned counts not confirmed")
        require("INDEPENDENT CHECK PASSED" in out, "check_combined75.py: no completion line")
        report = check_report(work, "CHECKED_COMBINED75.json", COMBINED_EXPECTED, logs)
        elapsed = round(time.monotonic() - t, 3)
        results.append({"stage": "check_combined75.py", "exit_code": 0, "elapsed_seconds": elapsed,
                        "claims_certified": report["claims_checked"], "log": str(log.relative_to(ROOT))})
        print(f"  passed in {elapsed:.1f} s: {report['claims_checked']} claims excluded "
              f"(4 re-covered without J1 by {report['addendum_certificates']} certificates)", flush=True)

        print("Finite facts of the October rows: finite_facts_october.py ...", flush=True)
        t = time.monotonic()
        out, log = run(work, "finite_facts_october.py", logs, env)
        require("done" in out, "finite_facts_october.py: no completion line")
        facts = json.loads((work / "checkers" / "finite_facts_october.json").read_text(encoding="utf-8"))
        recorded = json.loads((work / "checkers" / "finite_facts_october.recorded.json").read_text(encoding="utf-8"))
        for (ori, stage, key), value in FINITE_EXPECTED.items():
            require(facts[ori][stage][key] == value, f"finite fact {ori} {stage} {key}={facts[ori][stage][key]!r}")
        require(strip_seconds(facts) == strip_seconds(recorded), "finite facts differ from the recorded run")
        shutil.copyfile(work / "checkers" / "finite_facts_october.json", logs / "finite_facts_october.json")
        elapsed = round(time.monotonic() - t, 3)
        results.append({"stage": "finite_facts_october.py", "exit_code": 0, "elapsed_seconds": elapsed,
                        "log": str(log.relative_to(ROOT))})
        print(f"  passed in {elapsed:.1f} s: census 440/616, core 20/28, contact pairs 11,520/16,992, "
              f"dim R10(Mt) = 29, F1 0 of 4,250,400, F2, F3, F5 0 nonzero remainders; equal to the recorded run",
              flush=True)

        print("Package rows at G = 75: check_pkg75.py on CERTIFICATES_PKG75_G75.json ...", flush=True)
        t = time.monotonic()
        out, log = run(work, "check_pkg75.py", logs, env, folder="package-rows-g75")
        require("PASSED: 5,908 package-row exclusions" in out, "check_pkg75.py: no completion line")
        report = json.loads((work / "package-rows-g75" / "CHECKED_PKG75_G75.json").read_text(encoding="utf-8"))
        for key, value in PKG_EXPECTED.items():
            require(report.get(key) == value, f"Unexpected CHECKED_PKG75_G75.json: {key}={report.get(key)!r}")
        recorded = json.loads((ROOT / "package-rows-g75" / "CHECKED_PKG75_G75.json").read_text(encoding="utf-8"))
        require(report == recorded, "CHECKED_PKG75_G75.json differs from the recorded report")
        shutil.copyfile(work / "package-rows-g75" / "CHECKED_PKG75_G75.json", logs / "CHECKED_PKG75_G75.json")
        elapsed = round(time.monotonic() - t, 3)
        results.append({"stage": "check_pkg75.py", "exit_code": 0, "elapsed_seconds": elapsed,
                        "claims_certified": report["excluded_certified"], "log": str(log.relative_to(ROOT))})
        print(f"  passed in {elapsed:.1f} s: {report['excluded_certified']} claims excluded by the package rows "
              f"({report['certificates']} certificates); {report['open']} open under those rows", flush=True)

        bookkeeping = check_claim_bookkeeping(work)
        bookkeeping.update(check_domain_accounting(work))
    require(check_integrity() == n, "Input inventory changed during verification")
    summary = {
        "started_utc": started.isoformat(), "python": platform.python_version(),
        "platform": platform.platform(), "elapsed_seconds": round(time.monotonic() - start, 3),
        "stages": results, **bookkeeping, "all_checks_passed": True,
        "scope": ("Exact certificate arithmetic and case/claim coverage for 5,908 + 822 + 406 oriented claims at "
                  "G = 75, the accounting of the 7,416 claims by identifier, and the finite facts behind the October "
                  "rows; the survivor counts are LP-status records; that the 75 proof's framework applies at G = 75 "
                  "and the written arguments of Addenda A-D and of the October documents remain for expert review. "
                  "The lower bound stays 75."),
    }
    (logs / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Claims: 195 + 317 + 207 + 103 + 406 = {bookkeeping['distinct_claims_certified_excluded_combined']} "
          f"distinct, pairwise disjoint. Elapsed: {summary['elapsed_seconds']:.1f} seconds. "
          f"Logs: {logs.relative_to(ROOT)}")
    print("ALL CHECKS PASSED: 1,772 + 4,523 + 4,950 + 4,361 + 4,653 (+43) exact certificates; "
          "open claims at G = 75: 1,508 -> 1,313 -> 996 -> 789 -> 686 (sprint rows) -> 280 (with the October rows); "
          "finite facts of the October rows recomputed; 5,908 package-row exclusions certified (15,742 "
          "certificates) and all 7,416 claims accounted by identifier (7,136 certified excluded, 280 open); "
          "the bound stays 75.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        print("VERIFICATION FAILED: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
