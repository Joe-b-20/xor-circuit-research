#!/usr/bin/env python3
"""Launch, stop, resume, inspect, or verify a portable AES search campaign."""
from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "pipeline"))
from profiles import make_workers
from runtime_support import (atomic_json, code_manifest, file_sha256, nondominated,
                             pid_running, read_json, utc_now, verify_file)

VERSION = "2.0.0"


def configuration(args, run_dir):
    workers = make_workers(args.workers or 20, args.profile, args.seed_policy,
                           args.seed, args.chunk_seconds, args.handoff)
    seed_meta = {}
    for spec in workers:
        if spec["seed_path"] == "scratch":
            continue
        path = ROOT / spec["seed_path"]
        obj, _ = verify_file(path, cap=spec["cap"])
        seed_meta[spec["seed_path"]] = {
            "sha256": file_sha256(path), "gateCount": obj["gateCount"],
            "depth": obj["depth"], "provenance": spec["seed_provenance"],
        }
    return {"schema_version": 1, "version": VERSION, "created_utc": utc_now(),
            "profile": args.profile, "seed_policy": args.seed_policy,
            "variant": args.variant, "seed": args.seed, "workers": workers,
            "source_manifest": code_manifest(ROOT), "seed_manifest": seed_meta,
            "python": sys.version, "platform": sys.platform,
            "known_frontier": {"3": 97, "4": 90, "5": 88, "unrestricted": 88},
            "sharing": "strict gate improvements, within provenance share_group only",
            "disk_policy": {"archive_states_per_worker": 24,
                            "worker_log_bytes": 2000000, "worker_log_backups": 2,
                            "full_plateau_harvest": False}}


def take_lock(run_dir, token):
    path = run_dir / "runner.lock"
    old = read_json(path)
    if path.exists():
        if not old or old.get("host") != socket.gethostname() or pid_running(old.get("pid")):
            raise RuntimeError("This run is locked by a live or unrecognized coordinator. Use 'stop' first; do not run two coordinators in the same folder.")
        # Old workers check parent liveness themselves. Do not signal arbitrary
        # saved PIDs: a PID may have been reused by an unrelated process.
        live = []
        for status in (run_dir / "workers").glob("*/status.json"):
            item = read_json(status, {})
            if item.get("alive") and pid_running(item.get("pid")):
                live.append(item.get("label"))
        if live:
            atomic_json(run_dir / "STOP", {"requested_utc": utc_now(), "reason": "stale coordinator recovery"})
            raise RuntimeError("Old workers are still exiting: %s. Wait a few seconds and resume again." % ", ".join(live))
        path.unlink()
    fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump({"pid": os.getpid(), "host": socket.gethostname(), "token": token,
                   "started_utc": utc_now()}, stream)


def collect_frontier(run_dir, specs, cache):
    records = []
    for spec in specs:
        for record in read_json(run_dir / "workers" / spec["label"] / "frontier.json", []):
            path = run_dir / record["path"]
            try:
                stamp = (path.stat().st_size, path.stat().st_mtime_ns)
                if cache.get(str(path), (None,))[0] != stamp:
                    checked, _ = verify_file(path, cap=spec["cap"])
                    if (checked["gateCount"], checked["depth"]) != (record["gateCount"], record["depth"]):
                        raise ValueError("frontier metadata differs from verified circuit")
                    cache[str(path)] = (stamp, record)
                records.append(record)
            except FileNotFoundError:
                continue
    frontier = nondominated(records)
    if frontier != read_json(run_dir / "frontier.json", []):
        atomic_json(run_dir / "frontier.json", frontier)
        for name, cap in [("best_depth3.json", 3), ("best_depth4.json", 4),
                          ("best_depth5.json", 5), ("best_unrestricted.json", None),
                          ("best_overall.json", None)]:
            eligible = [r for r in frontier if cap is None or r["depth"] <= cap]
            if eligible:
                winner = min(eligible, key=lambda x: (x["gateCount"], x["depth"]))
                atomic_json(run_dir / name, read_json(run_dir / winner["path"]))
    return records, frontier


def offer_reseeds(run_dir, specs, records):
    for spec in specs:
        status = read_json(run_dir / "workers" / spec["label"] / "status.json", {})
        current_g = status.get("best_gates")
        eligible = [r for r in records if r["share_group"] == spec["share_group"]
                    and (spec["cap"] is None or r["depth"] <= spec["cap"])
                    and r["worker"] != spec["label"]
                    and current_g is not None and r["gateCount"] < current_g]
        if eligible:
            offer = min(eligible, key=lambda x: (x["gateCount"], x["depth"]))
            path = run_dir / "workers" / spec["label"] / "offer.json"
            if read_json(path) != offer:
                atomic_json(path, offer)


def status_data(run_dir):
    config = read_json(run_dir / "config.json")
    if not config:
        raise ValueError("No config.json in %s" % run_dir)
    workers = []
    for spec in config["workers"]:
        worker = read_json(run_dir / "workers" / spec["label"] / "status.json", {})
        if worker:
            worker["process_running"] = pid_running(worker.get("pid"))
        else:
            worker = {"label": spec["label"], "stage": "not started", "cap": spec["cap"],
                      "alive": False, "process_running": False}
        workers.append(worker)
    return {"run": str(run_dir), "variant": config["variant"],
            "profile": config["profile"], "seed_policy": config["seed_policy"],
            "frontier": read_json(run_dir / "frontier.json", []), "workers": workers,
            "session": read_json(run_dir / "session.json", {})}


def print_status(run_dir, detail=False):
    info = status_data(run_dir)
    active = sum(w.get("alive", False) and w.get("process_running", False) for w in info["workers"])
    frontier = ", ".join("%s@%s" % (x["gateCount"], x["depth"]) for x in info["frontier"]) or "initializing"
    print("[%s] active=%d/%d frontier=%s" % (utc_now(), active, len(info["workers"]), frontier), flush=True)
    if detail:
        for w in info["workers"]:
            metrics = w.get("metrics", {})
            print("  %-23s %-8s chunk=%-5s best=%s@%s current=%s verified=%s%s" % (
                w["label"], w.get("stage", "?"), w.get("chunk", 0),
                w.get("best_gates", "-"), w.get("best_depth", "-"), w.get("current_gates", "-"),
                metrics.get("candidates_verified", 0), " ERROR" if w.get("error") else ""))
    return info


def run_campaign(args):
    if sys.version_info < (3, 10):
        raise RuntimeError("Python 3.10 or newer is required.")
    if args.resume:
        run_dir = Path(args.resume).expanduser().resolve()
        config = read_json(run_dir / "config.json")
        if not config:
            raise ValueError("Resume needs an existing run folder with config.json")
        if args.workers and args.workers != len(config["workers"]):
            raise ValueError("Resume preserves the original worker count. Start a new run to change it.")
        if code_manifest(ROOT) != config["source_manifest"]:
            raise ValueError("Search code changed since this checkpoint. Resume using the unchanged code snapshot in this run's source/ folder, or start a new run.")
        for path, meta in config.get("seed_manifest", {}).items():
            if file_sha256(ROOT / path) != meta["sha256"]:
                raise ValueError("A seed changed since this run was created: %s" % path)
    else:
        run_dir = Path(args.out or ("runs/" + time.strftime("%Y%m%d_%H%M%S"))).expanduser().resolve()
        if (run_dir / "config.json").exists():
            raise ValueError("Run folder already exists. Use --resume %s" % run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        config = configuration(args, run_dir)
    token = uuid.uuid4().hex
    take_lock(run_dir, token)
    procs, logs = {}, []
    stopping = False
    reason = "interrupted"
    failures = []
    started = time.monotonic()
    previous_handlers = {}
    def stop_signal(signum, frame):
        nonlocal stopping, reason
        stopping, reason = True, "keyboard interrupt"
    for sig in (signal.SIGINT, signal.SIGTERM):
        previous_handlers[sig] = signal.signal(sig, stop_signal)
    try:
        if not args.resume:
            atomic_json(run_dir / "config.json", config)
            snapshot = run_dir / "source"
            for path in config["source_manifest"]:
                dest = snapshot / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / path, dest)
            for path in config["seed_manifest"]:
                dest = snapshot / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / path, dest)
        (run_dir / "STOP").unlink(missing_ok=True)
        session = {"coordinator_pid": os.getpid(), "started_utc": utc_now(),
                   "resumed": bool(args.resume), "hours_limit": args.hours, "status": "running",
                   "worker_count": len(config["workers"])}
        atomic_json(run_dir / "session.json", session)
        allocation = Counter("unrestricted" if w["cap"] is None else "depth%s" % w["cap"] for w in config["workers"])
        print("AES search %s | %s | %s | %s" % (VERSION, config["variant"], config["profile"], config["seed_policy"]), flush=True)
        print("Run: %s\nWorkers: %s\nCtrl+C saves checkpoints and stops. Resume with: python search.py run --resume \"%s\"" % (run_dir, dict(allocation), run_dir), flush=True)
        environment = dict(os.environ)
        environment.update({"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
                            "MKL_NUM_THREADS": "1", "PYTHONUNBUFFERED": "1"})
        for spec in config["workers"]:
            folder = run_dir / "workers" / spec["label"]
            folder.mkdir(parents=True, exist_ok=True)
            log = (folder / "process.log").open("a", encoding="utf-8")
            logs.append(log)
            command = [sys.executable, str(ROOT / "search.py"), "_worker",
                       str(run_dir), spec["label"], str(os.getpid()), token]
            procs[spec["label"]] = subprocess.Popen(command, cwd=ROOT, env=environment,
                                                     stdout=log, stderr=subprocess.STDOUT)
        cache = {}
        next_print = 0.0
        while not stopping:
            elapsed = time.monotonic() - started
            if args.hours and elapsed >= args.hours * 3600:
                stopping, reason = True, "time limit reached"
            if (run_dir / "STOP").exists():
                stopping, reason = True, "stop requested"
            exited = [label for label, proc in procs.items() if proc.poll() is not None]
            failures = [label for label in exited if procs[label].returncode != 0]
            unexpected = exited if not stopping else failures
            if unexpected:
                failures = unexpected
                stopping, reason = True, "worker exited unexpectedly: %s" % ", ".join(failures)
            records, frontier = collect_frontier(run_dir, config["workers"], cache)
            offer_reseeds(run_dir, config["workers"], records)
            if args.stop_gates is not None or args.stop_depth is not None:
                if any((args.stop_gates is None or r["gateCount"] <= args.stop_gates)
                       and (args.stop_depth is None or r["depth"] <= args.stop_depth) for r in frontier):
                    stopping, reason = True, "requested gate/depth target verified"
            if elapsed >= next_print:
                print_status(run_dir)
                next_print = elapsed + args.status_seconds
            if not stopping:
                time.sleep(0.5)
    finally:
        atomic_json(run_dir / "STOP", {"requested_utc": utc_now(), "reason": reason})
        print("Stopping: %s. Waiting for workers to checkpoint..." % reason, flush=True)
        deadline = time.monotonic() + max(15.0, args.shutdown_grace)
        while any(p.poll() is None for p in procs.values()) and time.monotonic() < deadline:
            time.sleep(0.1)
        forced = []
        for label, proc in procs.items():
            if proc.poll() is None:
                forced.append(label)
                proc.terminate()
        for proc in procs.values():
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        for stream in logs:
            stream.close()
        if procs:
            collect_frontier(run_dir, config["workers"], {})
        session = read_json(run_dir / "session.json", {})
        session.update(status="stopped", stopped_utc=utc_now(), reason=reason,
                       seconds=round(time.monotonic() - started, 2), forced_workers=forced,
                       failed_workers=failures)
        atomic_json(run_dir / "session.json", session)
        if read_json(run_dir / "runner.lock", {}).get("token") == token:
            (run_dir / "runner.lock").unlink(missing_ok=True)
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)
    print_status(run_dir, detail=True)
    if forced:
        print("Forced workers will resume from their last atomic checkpoint: %s" % ", ".join(forced))
    return 1 if failures else 0


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version", action="version", version=VERSION)
    commands = p.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="start or resume a campaign")
    run.add_argument("--workers", type=int, default=None, help="worker processes (default20)")
    run.add_argument("--profile", choices=["balanced", "hunt87", "depth4", "depth3", "calibrate90"], default="balanced")
    run.add_argument("--seed-policy", choices=["mixed", "own", "scratch"], default="mixed")
    run.add_argument("--variant", choices=["upgraded", "baseline"], default="upgraded")
    run.add_argument("--seed", type=int, default=20261020)
    run.add_argument("--out", help="new run directory")
    run.add_argument("--resume", help="existing run directory; retains its configuration")
    run.add_argument("--hours", type=float, default=0, help="wall hours this session;0 means until stopped")
    run.add_argument("--chunk-seconds", type=float, default=30)
    run.add_argument("--handoff", choices=["continue", "diverse", "best"], default="diverse")
    run.add_argument("--status-seconds", type=float, default=15)
    run.add_argument("--shutdown-grace", type=float, default=45)
    run.add_argument("--stop-gates", type=int)
    run.add_argument("--stop-depth", type=int)
    status = commands.add_parser("status", help="read current state without interrupting workers")
    status.add_argument("run_dir")
    status.add_argument("--json", action="store_true")
    stop = commands.add_parser("stop", help="ask a campaign to save and stop")
    stop.add_argument("run_dir")
    verify = commands.add_parser("verify", help="independently verify one or several circuits")
    verify.add_argument("paths", nargs="+")
    verify.add_argument("--depth", type=int)
    commands.add_parser("selftest", help="run the regression and correctness suite")
    worker = commands.add_parser("_worker", help=argparse.SUPPRESS)
    worker.add_argument("run_dir")
    worker.add_argument("label")
    worker.add_argument("parent_pid", type=int)
    worker.add_argument("token")
    return p


def main():
    args = parser().parse_args()
    if args.command == "run":
        if args.hours < 0 or args.chunk_seconds <= 0 or args.status_seconds <= 0:
            raise ValueError("hours must be nonnegative; chunk/status intervals must be positive")
        if args.resume and args.out:
            raise ValueError("use --out for a new run or --resume for an existing one")
        return run_campaign(args)
    if args.command == "_worker":
        from campaign_worker import run_worker
        return run_worker(ROOT, Path(args.run_dir), args.label, args.parent_pid, args.token)
    if args.command == "status":
        folder = Path(args.run_dir).resolve()
        if args.json:
            print(json.dumps(status_data(folder), indent=2))
        else:
            print_status(folder, detail=True)
        return 0
    if args.command == "stop":
        folder = Path(args.run_dir).resolve()
        if not (folder / "config.json").is_file():
            raise ValueError("not a run directory")
        atomic_json(folder / "STOP", {"requested_utc": utc_now(), "reason": "explicit stop command"})
        print("Stop requested. Workers will checkpoint and exit: %s" % folder)
        return 0
    if args.command == "verify":
        for name in args.paths:
            checked, _ = verify_file(name, cap=args.depth)
            print("PASS %s: %d gates, depth%d, all32 outputs exact" % (name, checked["gateCount"], checked["depth"]))
        return 0
    if args.command == "selftest":
        return subprocess.call([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=ROOT)
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, OSError) as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        raise SystemExit(2)
