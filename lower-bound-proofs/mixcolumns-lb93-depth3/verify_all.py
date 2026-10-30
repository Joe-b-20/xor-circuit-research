#!/usr/bin/env python3
"""Run the complete depth-three lower-bound verification in an isolated copy.

The proof programs and certificate files are unchanged archive sources.
This packaging wrapper checks their provenance hashes, adds the four inherited
modules from supplement/ (hash-checked; missing from the original ZIP edition),
and runs the inherited full checker; it does not accept cached-only
verification as a proof. --quick runs only the first finite stages.
"""
from __future__ import annotations

import datetime as dt
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import os
import tarfile

ROOT = Path(__file__).resolve().parent
SUPPLEMENT = ROOT / "supplement"
QUICK_STAGES = ("verify_structure.py", "verify_boundary_tax.py", "verify_cluster_results.py",
                "weighted_cluster_certificate.py", "verify_component_conditionals.py")


def check_file(path: Path, entry: dict) -> None:
    if not path.is_file() or path.is_symlink():
        raise ValueError("Missing or invalid archived source path: " + entry["path"])
    if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
        raise ValueError("Archived source hash mismatch: " + entry["path"])


def load_inventory() -> dict:
    inventory = json.loads((ROOT / "verification" / "source_inventory.json").read_text())
    seen = set()
    for entry in inventory["entries"]:
        rel = PurePosixPath(entry["path"])
        if (rel.is_absolute() or ".." in rel.parts or "." in rel.parts
                or not rel.parts or rel.parts[0] not in {"technical", "source_notes", "verification"}
                or rel.as_posix() != entry["path"] or entry["path"] in seen):
            raise ValueError("Invalid or duplicate source-inventory path: " + entry["path"])
        seen.add(entry["path"])
        if rel.parts[0] != "technical":
            path = (ROOT / entry["path"]).resolve()
            if not path.is_relative_to(ROOT):
                raise ValueError("Source path escapes package directory")
            check_file(path, entry)
    return inventory


def stage_supplement(technical: Path) -> int:
    """Add the inherited modules that verify_structure.py imports from technical/inherited/."""
    manifest = json.loads((SUPPLEMENT / "SOURCE_HASHES.json").read_text())
    check_file(SUPPLEMENT / manifest["license"]["path"], manifest["license"])
    for entry in manifest["files"]:
        rel = PurePosixPath(entry["path"])
        if rel.is_absolute() or ".." in rel.parts or rel.parts[0] != "inherited":
            raise ValueError("Invalid supplement path: " + entry["path"])
        source = SUPPLEMENT / entry["path"]
        check_file(source, entry)
        target = technical / entry["path"]
        if target.exists():
            raise ValueError("Supplement would overwrite an original file: " + entry["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        check_file(target, entry)
    return len(manifest["files"])


def stage_technical(destination: Path, inventory: dict) -> Path:
    """Materialize precisely the manifest's regular files; never use extractall."""
    expected = {e["path"]: e for e in inventory["entries"]
                if e["path"].startswith("technical/")}
    archive = ROOT / "technical.tar.xz"
    if archive.is_file():
        seen = set()
        with tarfile.open(archive, "r:xz") as tar:
            for member in tar:
                if member.name not in expected or member.name in seen or not member.isfile():
                    raise ValueError("Unexpected, duplicate, or non-regular archive member: " + member.name)
                target = destination / member.name
                if not target.resolve().is_relative_to(destination.resolve()):
                    raise ValueError("Archive path escapes extraction directory")
                target.parent.mkdir(parents=True, exist_ok=True)
                stream = tar.extractfile(member)
                if stream is None:
                    raise ValueError("Cannot read archive member: " + member.name)
                with stream, target.open("xb") as output:
                    shutil.copyfileobj(stream, output)
                check_file(target, expected[member.name])
                seen.add(member.name)
        if seen != set(expected):
            raise ValueError("Technical archive is missing manifest entries: " + str(sorted(set(expected)-seen)))
    else:
        for name, entry in expected.items():
            source = ROOT / name
            check_file(source, entry)
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            check_file(target, entry)
    stage_supplement(destination / "technical")
    return destination / "technical"


def child_env() -> dict:
    env = dict(os.environ)
    env.pop("PYTHONOPTIMIZE", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def quick(inventory: dict) -> int:
    with tempfile.TemporaryDirectory(prefix="aes_depth3_93_quick_") as temp:
        work = stage_technical(Path(temp), inventory)
        print("All " + str(len(inventory["entries"])) + " original files and 4 supplement files: hashes PASS", flush=True)
        for script in QUICK_STAGES:
            start = time.perf_counter()
            proc = subprocess.run([sys.executable, "-B", script], cwd=work, env=child_env(),
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            seconds = time.perf_counter() - start
            if proc.returncode != 0:
                print(proc.stdout, file=sys.stderr)
                print("FAIL " + script, file=sys.stderr)
                return 1
            print(f"PASS {script} ({seconds:.1f} s)", flush=True)
    print("QUICK CHECKS PASSED. These are the first finite premises only, not the proof replay;")
    print("run without flags for the complete verification.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--quick", action="store_true",
                       help="hash checks plus the first finite stages (seconds); not proof verification")
    modes.add_argument("--check-package", action="store_true",
                       help="check and unpack every source hash only; this is not proof verification")
    modes.add_argument("--extract-source", metavar="NEW_DIRECTORY",
                       help="extract original technical files to a new directory for inspection")
    args = parser.parse_args()
    if not __debug__ or sys.flags.optimize:
        print("ERROR: Run Python normally, without -O or PYTHONOPTIMIZE.", file=sys.stderr)
        return 2
    if sys.version_info < (3, 10):
        print("ERROR: Python 3.10 or later is required.", file=sys.stderr)
        return 2
    compiler = shutil.which("g++")
    if not compiler and not (args.check_package or args.extract_source):
        print("ERROR: A C++17 compiler named g++ must be on PATH.", file=sys.stderr)
        return 2
    inventory = load_inventory()
    if args.extract_source:
        destination = Path(args.extract_source).resolve()
        if destination.exists():
            raise ValueError("Choose a new, nonexistent extraction directory: " + str(destination))
        destination.mkdir(parents=True)
        work = stage_technical(destination, inventory)
        print("Original technical sources and supplement extracted and every hash checked: " + str(work))
        print("Extraction does not rerun the mathematical checks.")
        return 0
    if args.check_package:
        with tempfile.TemporaryDirectory(prefix="aes_depth3_93_integrity_") as temp:
            stage_technical(Path(temp), inventory)
        print("PACKAGE INTEGRITY PASSED: " + str(len(inventory["entries"])) + " original files and 4 supplement files checked.")
        print("Integrity only; run without flags for complete proof verification.")
        return 0
    if args.quick:
        return quick(inventory)

    now = dt.datetime.now(dt.timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%S_%fZ")
    output = ROOT / "verification" / ("run_" + stamp)
    output.mkdir(parents=True)
    log_path = output / "full_verification.log"
    summary_path = output / "summary.json"
    summary = {
        "status": "RUNNING",
        "started_at_utc": now.isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "compiler": subprocess.check_output([compiler, "--version"], text=True).splitlines()[0],
        "source_inventory_entries_expected": len(inventory["entries"]),
        "source_archive_sha256": inventory["source_sha256"],
        "supplement_sha256": {e["path"]: e["sha256"] for e in
                              json.loads((SUPPLEMENT / "SOURCE_HASHES.json").read_text())["files"]},
        "technical_transport": "technical.tar.xz" if (ROOT/"technical.tar.xz").is_file() else "technical/",
        "command": ["python3", "verify_complete_92_exclusion.py", "--full"],
        "cached_only_mode": False,
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print("Supporting source records: PASS; checking the technical sources next.", flush=True)
    print("Running the complete proof, including all finite premises.", flush=True)
    print("Detailed progress log: " + str(log_path.relative_to(ROOT)), flush=True)
    start = time.perf_counter()
    code = 1
    try:
        with tempfile.TemporaryDirectory(prefix="aes_depth3_93_review_") as temp:
            work = stage_technical(Path(temp), inventory)
            summary["source_inventory_entries_checked"] = len(inventory["entries"])
            print("All original source, certificate and supplement hashes: PASS", flush=True)
            with log_path.open("w") as log:
                proc = subprocess.run(
                    [sys.executable, "-u", "verify_complete_92_exclusion.py", "--full"],
                    cwd=work, env=child_env(), stdout=log, stderr=subprocess.STDOUT, check=False,
                )
            code = proc.returncode
            for path in sorted(work.glob("*.json")):
                if path.name.endswith("_checks.json") or path.name == "pair_rank_result.json":
                    shutil.copy2(path, output / path.name)
            result_path = work / "depth3_93_checks.json"
            if code == 0 and result_path.is_file():
                result = json.loads(result_path.read_text())
                if not (
                    result.get("status") == "PASS"
                    and result.get("new_lower_bound") == 93
                    and result.get("known97_rechecked") is True
                    and result.get("source_certificate_checker_rerun") is True
                    and result.get("reused_completed_checks") is False
                    and set(result.get("case_coverage", {})) == {"6", "7"}
                    and result["case_coverage"]["6"]["total_partitions"] == 275354
                    and result["case_coverage"]["7"]["total_partitions"] == 22060
                    and all(x["uncovered"] == 0 for x in result["case_coverage"].values())
                ):
                    raise ValueError("Final result does not establish the full requested verification.")
                eight = json.loads((work/"eight_component_tradeoff_checks.json").read_text())
                partitions = json.loads((work/"partition_conditional_checks.json").read_text())
                if not (eight.get("status") == "PASS"
                        and eight["independent_parity_enumeration"]["surviving_partitions"] == 110712
                        and eight["parent_prices"]["covered_partitions"] == 1552
                        and eight["pair_recipe_exclusions"]["rejected_partitions"] == 109160
                        and partitions.get("status") == "PASS"
                        and partitions.get("verified_certificates") == 1113):
                    raise ValueError("Eight-component coverage or conditioned certificates are incomplete.")
                summary["result"] = result
                summary["status"] = "PASS"
            else:
                summary["status"] = "FAIL"
    except BaseException as error:
        summary["status"] = "FAIL"
        summary["error"] = type(error).__name__ + ": " + str(error)
        code = 1
    summary["return_code"] = code
    summary["seconds"] = round(time.perf_counter() - start, 3)
    summary["finished_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    summary["log_sha256"] = hashlib.sha256(log_path.read_bytes()).hexdigest() if log_path.exists() else None
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print("Full proof verification: " + summary["status"], flush=True)
    print("Report: " + str(summary_path.relative_to(ROOT)), flush=True)
    return 0 if summary["status"] == "PASS" else (code or 1)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, tarfile.TarError) as error:
        print("VERIFICATION FAILED: " + str(error), file=sys.stderr)
        raise SystemExit(1)
