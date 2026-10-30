#!/usr/bin/env python3
"""Reproduce the AES MixColumns 75-gate review package using Python's standard library.

Run from any directory: python3 /path/to/package/verify_all.py
The original proof checkers and certificate files are unchanged.
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
CHECKS = ROOT / "source" / "lower_bounds" / "checks"
STAGES = (
    "finite_facts.py", "check72.py", "check73.py", "check_dark_source.py",
    "certify74.py", "independent74.py", "certify75.py", "independent75.py",
    "stress.py",
)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def read_report(checks, name):
    return json.loads((checks / name).read_text(encoding="utf-8"))


def check_source_integrity():
    manifest = json.loads((ROOT / "provenance" / "source_hashes.json").read_text())
    for item in manifest["files"]:
        path = ROOT / item["path"]
        require(path.is_file(), "Missing source file: " + item["path"])
        require(hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"],
                "Source-integrity mismatch: " + item["path"])
    return len(manifest["files"])


def validate_reports(checks):
    for name, expected in (
        ("INDEPENDENT74.json", {
            "gates_excluded": 73, "scalar_states": 262, "oriented_claims": 524,
            "local_certificates": 484, "independently_checked_coefficients": 13819,
            "largest_right_side": -1, "certificate_references": 1456,
            "distinct_referenced_certificates": 383, "all_checks_passed": True,
        }),
        ("INDEPENDENT75.json", {
            "gates_excluded": 74, "scalar_states": 1102, "oriented_claims": 2204,
            "local_certificates": 4057, "helper_type_coefficients": 163599,
            "largest_right_side": -1, "certificate_references": 9604,
            "distinct_referenced_certificates": 3481, "direct_geometric_references": 927,
            "all_checks_passed": True,
        }),
    ):
        actual = read_report(checks, name)
        for key, value in expected.items():
            require(actual.get(key) == value, f"Unexpected {name}: {key}={actual.get(key)!r}")
    for name in ("VERIFIED74.json", "VERIFIED75.json", "DARK_SOURCE_VERIFIED.json"):
        require(read_report(checks, name).get("all_checks_passed") is True,
                "Unsuccessful report: " + name)
    stress = read_report(checks, "stress.json")
    require(type(stress.get("circuits")) is int and stress["circuits"] == 13,
            "The stress test did not check the 13 included control circuits")
    require(stress.get("failures") == [], "The stress test reported a failure")
    return {"excludes_73": read_report(checks, "INDEPENDENT74.json"),
            "excludes_74": read_report(checks, "INDEPENDENT75.json"),
            "stress_control_circuits": stress["circuits"], "stress_failures": 0}


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
    source_count = check_source_integrity()
    print(f"Source integrity passed: {source_count} unchanged source/input files.", flush=True)
    results = []
    with tempfile.TemporaryDirectory(prefix="nist_aes75_") as temporary:
        working_source = Path(temporary) / "source"
        shutil.copytree(ROOT / "source", working_source)
        working_checks = working_source / "lower_bounds" / "checks"
        for script in STAGES + ("verify_circuits",):
            path = working_source / "verify.py" if script == "verify_circuits" else working_checks / script
            print(f"Checking {script} ...", flush=True)
            t = time.monotonic()
            result = subprocess.run([sys.executable, "-B", str(path)], cwd=str(working_checks), env=env,
                                    text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            log = logs / (script.removesuffix(".py") + ".log")
            log.write_text(result.stdout, encoding="utf-8")
            if result.returncode != 0:
                print(result.stdout, file=sys.stderr)
                raise RuntimeError(f"{script} failed with exit code {result.returncode}; see {log}")
            if script == "finite_facts.py":
                require("ALL FINITE PREMISES RECOMPUTED AND MATCH" in result.stdout,
                        "Finite-fact checker did not report completion")
            if script == "verify_circuits":
                require("ALL CIRCUITS VERIFIED." in result.stdout,
                        "Circuit verifier did not report successful completion")
            results.append({"stage": script, "exit_code": 0,
                            "elapsed_seconds": round(time.monotonic()-t, 3),
                            "log": str(log.relative_to(ROOT))})
        report = validate_reports(working_checks)
        report_dir = logs / "reports"
        report_dir.mkdir()
        for name in ("finite_facts.json", "CHECK72.json", "CHECK73.json", "DARK_SOURCE_VERIFIED.json",
                     "VERIFIED74.json", "INDEPENDENT74.json", "VERIFIED75.json", "INDEPENDENT75.json", "stress.json"):
            shutil.copyfile(working_checks / name, report_dir / name)
    require(check_source_integrity() == source_count, "Source inventory changed during verification")
    summary = {
        "started_utc": started.isoformat(), "python": platform.python_version(),
        "platform": platform.platform(), "source_integrity_files": source_count,
        "elapsed_seconds": round(time.monotonic()-start, 3), "stages": results,
        **report, "all_checks_passed": True,
        "scope": "Finite facts, exact certificates, coverage, control circuits and stress checks; the mathematical reductions remain for expert review.",
    }
    (logs / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (ROOT / "verification" / "latest_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("ALL CHECKS PASSED: 484 + 4,057 exact certificates; complete coverage; 13 circuit controls.")
    print(f"Elapsed: {summary['elapsed_seconds']:.1f} seconds. Logs: {logs.relative_to(ROOT)}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as exc:
        print("VERIFICATION FAILED: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
