#!/usr/bin/env python3
"""Prepare, run, inspect, stop, and verify reproducible XOR search campaigns."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback

import runtime as rt


def collect(run_dir, config, token, cache):
    target_api, _ = rt.api_modules()
    grouped = {target: [] for target in config["targets"]}
    for spec in config["workers"]:
        frontier = rt.read_json(run_dir / "workers" / spec["label"] / "frontier.json")
        if frontier is None:
            continue
        if (frontier.get("target_id") != spec["target_id"] or
                frontier.get("matrix_sha256") != spec["matrix_sha256"]):
            raise ValueError("Worker frontier target mismatch")
        for record in frontier["records"]:
            if (record.get("target_id") != spec["target_id"] or record.get("matrix_sha256") != spec["matrix_sha256"]
                    or record.get("worker") != spec["label"]):
                raise ValueError("Record target mismatch")
            path = rt.safe_run_path(run_dir, record["path"])
            rng_path = path.with_suffix(".rng-start.json")
            if not rng_path.is_file():
                raise ValueError("Record starting RNG evidence missing: " + str(path))
            stamp = (path.stat().st_size, path.stat().st_mtime_ns, record["file_sha256"],
                     rng_path.stat().st_size, rng_path.stat().st_mtime_ns)
            if cache.get(record["path"]) != stamp:
                if rt.file_hash(path) != record["file_sha256"]:
                    raise ValueError("Record file hash mismatch")
                circuit = rt.read_json(path)
                rt.validate_record_binding(run_dir, path, circuit, config, spec["label"])
                target = config["targets"][spec["target_id"]]["definition"]
                checked = target_api.verify(circuit, target, cap=spec["depth_cap"])
                rt.require_record_limits(checked, spec, path)
                if not checked["equivalent"] or any(checked[k] != record[k] for k in ("gate_count", "depth", "circuit_sha256")):
                    raise ValueError("Record independent verification failed")
                cache[record["path"]] = stamp
            grouped[spec["target_id"]].append(record)
    for target_id, records in grouped.items():
        frontier = rt.nondominated(records)
        rt.atomic_json(run_dir / "shared" / target_id / "frontier.json", {"target_id": target_id,
                       "matrix_sha256": config["targets"][target_id]["definition"]["matrix_sha256"], "records": frontier})
        if not config["settings"]["sharing"]:
            continue
        for spec in (s for s in config["workers"] if s["target_id"] == target_id):
            feasible = [r for r in frontier if (spec["depth_cap"] is None or r["depth"] <= spec["depth_cap"])
                        and rt.within_gate_limit(r, spec)]
            status = rt.read_json(run_dir / "workers" / spec["label"] / "status.json", {})
            own_best = status.get("best")
            if not feasible:
                continue
            objective = spec.get("objective", "gates")
            best = min(feasible, key=lambda r: rt.objective_key(r, objective))
            if best["worker"] == spec["label"] or (own_best and rt.objective_key(best, objective) >= rt.objective_key(own_best, objective)):
                continue
            offer = {**best, "run_id": config["run_id"], "config_sha256": rt.digest(config),
                     "owner_token": token, "offer_id": token + ":" + best["circuit_sha256"]}
            offer_path = run_dir / "workers" / spec["label"] / "offer.json"
            if rt.read_json(offer_path) != offer:
                rt.atomic_json(offer_path, offer)
    return {key: rt.nondominated(records) for key, records in grouped.items()}


def request_stop(run_dir, reason="requested"):
    run_dir = Path(run_dir).resolve()
    owner = rt.read_json(run_dir / "runner.lock", {})
    if not owner.get("token"):
        return {"phase": "not_running", "message": "No active campaign owner"}
    value = {"owner_token": owner["token"], "requested_utc": rt.utc_now(), "reason": reason}
    rt.atomic_json(run_dir / "STOP", value)
    return value


def campaign_status(run_dir):
    run_dir = Path(run_dir).resolve()
    config = rt.load_config(run_dir, check_snapshot=False)
    owner = rt.read_json(run_dir / "runner.lock", {})
    active = rt.identity_alive(owner)
    workers = []
    for spec in config["workers"]:
        status = rt.read_json(run_dir / "workers" / spec["label"] / "status.json", {})
        workers.append({"label": spec["label"], "target_id": spec["target_id"], "cap": spec["depth_cap"],
                        "objective": spec.get("objective", "gates"), "gate_limit": spec.get("gate_limit"),
                        "engines": spec["engines"], "status": status,
                        "alive": status.get("owner_token") == owner.get("token") and rt.identity_alive(status.get("process"))})
    return {"run_id": config["run_id"], "owner_alive": active, "coordinator": rt.read_json(run_dir / "status.json"),
            "workers": workers}


def campaign_summary(run_dir):
    """Read the coordinator's verified frontier; never alter campaign state."""
    config = rt.load_config(run_dir, check_snapshot=False)
    status = campaign_status(run_dir)
    coordinator = status["coordinator"] or {}
    live = sum(worker["alive"] for worker in status["workers"])
    phase = "running" if status["owner_alive"] else coordinator.get("phase", "unknown")
    if phase == "running" and not status["owner_alive"]:
        phase = "not running (saved status is stale)"
    names = {"aes_sbox_bottom": "AES S-box bottom", "fox_mu4": "FOX Mu4", "fox_mu8": "FOX Mu8", "joltik": "Joltik"}

    def points(records):
        return ", ".join(f"{g}@{d}" for g, d in sorted({
            (record["gate_count"], record["depth"]) for record in records}))

    rows = [("Target", "Workers alive", "Seed baseline", "Current frontier")]
    seed_sources, objectives = [], []
    for target_id, target in config["targets"].items():
        workers = [w for w in status["workers"] if w["target_id"] == target_id]
        label = names.get(target_id, target["definition"].get("name", target_id))
        kinds = set()
        for seed in target["seed_snapshots"]:
            original = next((entry for entry in target["definition"].get("seeds", []) if entry["path"] == seed["source_path"]), {})
            kinds.add(seed.get("source_kind", original.get("source_kind", "target-supplied circuit")))
        seed_sources.append(label + ": " + ", ".join(sorted(kinds)))
        spec = next(item for item in config["workers"] if item["target_id"] == target_id)
        objective = "depth then gates" if spec.get("objective") == "depth_then_gates" else "gates then depth"
        limit = "; retained gates <= " + str(spec["gate_limit"]) if spec.get("gate_limit") is not None else ""
        objectives.append(label + ": " + objective + limit)
        baseline = points([seed["verification"] for seed in target["seed_snapshots"]])
        frontier = points(coordinator.get("frontier", {}).get(target_id, []))
        rows.append((names.get(target_id, target_id),
                     f"{sum(w['alive'] for w in workers)}/{len(workers)}", baseline,
                     frontier or "no worker results yet"))
    widths = [max(len(row[i]) for row in rows) for i in range(4)]
    table = ["  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)).rstrip() for row in rows]
    return "\n".join([
        f"{phase} | {live}/{len(status['workers'])} workers alive",
        f"Snapshot: {coordinator.get('updated_utc', 'not yet saved')}", "", *table, "",
        "g@d = XOR gates @ depth. Frontier lists the best gate/depth tradeoffs.",
        "Seed sources: " + "; ".join(seed_sources) + ".",
        "Objectives: " + "; ".join(objectives) + ".",
    ])


def run_campaign(run_dir, resume=False, seconds=None):
    run_dir = Path(run_dir).resolve()
    config = rt.load_config(run_dir)
    checkpoints = list((run_dir / "workers").glob("*/checkpoint.json"))
    if checkpoints and not resume:
        raise ValueError("Campaign has checkpoints; use --resume to continue their actual states")
    seconds = config["settings"]["session_seconds"] if seconds is None else seconds
    if seconds is not None and (not math.isfinite(seconds) or seconds <= 0):
        raise ValueError("Session duration must be finite and positive")
    env_info = rt.environment()
    available = env_info["available_cpu_ids"]
    cpu_count = len(available) if available is not None else env_info["logical_cpus"]
    if cpu_count is not None and len(config["workers"]) > cpu_count and not config["settings"]["allow_oversubscription"]:
        raise ValueError("Worker count exceeds currently available CPUs")
    for spec in config["workers"]:
        if spec["cpu_id"] is not None and (available is None or spec["cpu_id"] not in available):
            raise ValueError("A planned worker CPU is no longer available")
    owner = rt.take_lock(run_dir)
    session_path = run_dir / "sessions" / (owner["token"] + ".json")
    session = {"owner": owner, "resume": resume, "seconds": seconds, "environment": env_info,
               "config_sha256": rt.digest(config), "source_manifest_sha256": config["source"]["manifest_sha256"],
               "worker_commands": [], "started_utc": rt.utc_now()}
    # Preserve earlier failures while making the current session's error files unambiguous.
    for previous in [run_dir / "error.json", *(run_dir / "workers").glob("*/error.json")]:
        if previous.exists():
            archived = run_dir / "errors" / owner["token"] / previous.relative_to(run_dir)
            rt.atomic_bytes(archived, previous.read_bytes())
            previous.unlink()
    children = []
    interrupted = False
    failure = None
    stop_reason = "duration elapsed"
    cache = {}
    frontier = {}
    previous_handlers = {}
    def interrupt(signum, frame):
        nonlocal interrupted
        interrupted = True
    for signum in (signal.SIGINT, signal.SIGTERM):
        previous_handlers[signum] = signal.signal(signum, interrupt)
    started = time.monotonic()
    last_collect = 0.0
    try:
        for spec in config["workers"]:
            worker_dir = run_dir / "workers" / spec["label"]
            worker_dir.mkdir(parents=True, exist_ok=True)
            command = [sys.executable, str(run_dir / "source" / "search" / "run.py"), "_worker",
                       str(run_dir), spec["label"], owner["token"]]
            env = {**os.environ, **rt.THREAD_ENV, "PYTHONUNBUFFERED": "1", "PYTHONDONTWRITEBYTECODE": "1"}
            # Worker exceptions go to bounded worker logs/error.json; unexpected import failures get a small launcher log.
            launch_log = worker_dir / "launchers" / (owner["token"] + ".log")
            rt.atomic_bytes(launch_log, b"")
            with launch_log.open("ab") as output:
                child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=output, env=env)
            children.append((spec, child))
            session["worker_commands"].append({"worker": spec["label"], "command": command, "pid": child.pid,
                                               "cpu_id": spec["cpu_id"], "thread_environment": rt.THREAD_ENV,
                                               "launcher_log": launch_log.relative_to(run_dir).as_posix()})
        rt.atomic_json(session_path, session)
        while True:
            if interrupted:
                stop_reason = "signal"
                break
            stop = rt.read_json(run_dir / "STOP", {})
            if stop.get("owner_token") == owner["token"]:
                stop_reason = stop.get("reason", "requested")
                break
            exited = [(spec["label"], child.returncode) for spec, child in children if child.poll() is not None]
            if exited:
                raise RuntimeError("Worker exited unexpectedly: " + str(exited))
            if seconds is not None and time.monotonic() - started >= seconds:
                break
            if time.monotonic() - last_collect >= config["settings"]["coordinator_interval_seconds"]:
                last_collect = time.monotonic()
                frontier = collect(run_dir, config, owner["token"], cache)
                rt.atomic_json(run_dir / "status.json", {"phase": "running", "updated_utc": rt.utc_now(),
                    "owner": owner, "elapsed_seconds": time.monotonic() - started, "frontier": frontier})
            time.sleep(0.1)
    except BaseException as exc:
        failure = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
        stop_reason = "coordinator failure"
        rt.atomic_json(run_dir / "error.json", failure)
    finally:
        rt.atomic_json(run_dir / "STOP", {"owner_token": owner["token"], "reason": stop_reason, "requested_utc": rt.utc_now()})
        forced = []
        for stage, grace in (("graceful", config["settings"]["stop_grace_seconds"]),
                             ("terminate", config["settings"]["terminate_grace_seconds"]),
                             ("kill", config["settings"]["kill_grace_seconds"])):
            living = [(spec, child) for spec, child in children if child.poll() is None]
            if not living:
                break
            if stage != "graceful":
                for spec, child in living:
                    forced.append({"worker": spec["label"], "action": stage})
                    child.terminate() if stage == "terminate" else child.kill()
            deadline = time.monotonic() + grace
            while any(child.poll() is None for _, child in living) and time.monotonic() < deadline:
                time.sleep(0.05)
        returns = {spec["label"]: child.poll() for spec, child in children}
        if forced and failure is None:
            failure = {"type": "ForcedShutdown", "message": "Some workers did not stop cooperatively", "actions": forced}
        if any(code != 0 for code in returns.values()) and failure is None:
            failure = {"type": "WorkerFailure", "message": "A worker failed during shutdown", "returncodes": returns}
        try:
            frontier = collect(run_dir, config, owner["token"], cache)
        except BaseException as exc:
            if failure is None:
                failure = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
        session.update({"finished_utc": rt.utc_now(), "elapsed_seconds": time.monotonic() - started,
                        "stop_reason": stop_reason, "returncodes": returns, "forced_shutdown": forced, "error": failure})
        rt.atomic_json(session_path, session)
        if failure:
            rt.atomic_json(run_dir / "error.json", failure)
        rt.atomic_json(run_dir / "status.json", {"phase": "failed" if failure else "stopped", "updated_utc": rt.utc_now(),
                       "owner": owner, "frontier": frontier, "error": failure, "stop_reason": stop_reason})
        rt.release_lock(run_dir, owner)
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)
    if failure:
        print(failure["message"], file=sys.stderr)
    return 1 if failure else 0


def verify_run(run_dir):
    run_dir = Path(run_dir).resolve()
    config = rt.load_config(run_dir)
    api, _ = rt.api_modules()
    records = 0
    for spec in config["workers"]:
        target = config["targets"][spec["target_id"]]["definition"]
        for path in sorted((run_dir / "workers" / spec["label"] / "records").glob("*.json")):
            if path.name.endswith((".verification.json", ".rng-start.json")):
                continue
            circuit = rt.read_json(path)
            checked = api.verify(circuit, target, cap=spec["depth_cap"])
            rt.require_record_limits(checked, spec, path)
            metadata = circuit.get("metadata", {})
            if (not checked["equivalent"] or metadata.get("target_id") != spec["target_id"] or
                    metadata.get("matrix_sha256") != spec["matrix_sha256"]):
                raise ValueError("Record target/equivalence failure: " + str(path))
            rt.validate_record_binding(run_dir, path, circuit, config, spec["label"])
            if rt.read_json(path.with_suffix(".verification.json")) != checked:
                raise ValueError("Verification sidecar mismatch: " + str(path))
            if path.with_suffix(".ncff").read_text() != api.ncff(circuit, target):
                raise ValueError("NCFF export mismatch: " + str(path))
            records += 1
    return {"verified": True, "records": records, "source_manifest_sha256": config["source"]["manifest_sha256"]}


def plan_summary(plan):
    return {"workers": len(plan["workers"]), "allocation": plan["settings"]["allocation"],
            "chunk_seconds": plan["settings"]["chunk_seconds"], "session_seconds": plan["settings"]["session_seconds"],
            "pin_cpus": plan["settings"]["pin_cpus"], "sharing_policy": plan["sharing_policy"],
            "plan": [{k: s[k] for k in ("label", "target_id", "depth_cap", "objective", "gate_limit", "seed_sha256", "engines", "excluded_engines", "cpu_id", "random_seed")}
                     for s in plan["workers"]]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare", help="Freeze a complete plan; never starts workers")
    prepare.add_argument("--out", type=Path)
    prepare.add_argument("--config", type=Path, default=rt.SEARCH_ROOT / "configs" / "default20.json")
    prepare.add_argument("--plan", action="store_true", help="Resolve and print settings without writing anything")
    prepare.add_argument("--pin-cpus", action="store_true", help="Assign distinct available logical CPUs")
    run = sub.add_parser("run", help="Start one process per prepared worker")
    run.add_argument("directory", type=Path)
    run.add_argument("--resume", action="store_true")
    run.add_argument("--seconds", type=float, help="Session duration; default runs until stopped (saved session_seconds=null)")
    for command in ("summary", "status", "stop", "verify-run"):
        item = sub.add_parser(command)
        item.add_argument("directory", type=Path)
    verify = sub.add_parser("verify")
    verify.add_argument("circuit", type=Path)
    verify.add_argument("--target", required=True)
    verify.add_argument("--cap", type=int)
    worker = sub.add_parser("_worker", help=argparse.SUPPRESS)
    worker.add_argument("directory", type=Path)
    worker.add_argument("label")
    worker.add_argument("token")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            overrides = rt.read_json(args.config)
            if not isinstance(overrides, dict):
                raise ValueError("Configuration must be a JSON object")
            if args.pin_cpus:
                overrides["pin_cpus"] = True
            if args.plan:
                result = plan_summary(rt.resolve_plan(overrides))
            else:
                if args.out is None:
                    parser.error("prepare needs --out unless --plan is used")
                result = plan_summary(rt.prepare(args.out, overrides))
            print(json.dumps(result, indent=2))
        elif args.command == "run":
            directory = args.directory.resolve()
            frozen = directory / "source" / "search" / "run.py"
            rt.load_config(directory)  # Integrity is checked before executing the frozen launcher.
            if frozen.resolve() != Path(__file__).resolve():
                command = [sys.executable, str(frozen), "run", str(directory)]
                if args.resume:
                    command.append("--resume")
                if args.seconds is not None:
                    command.extend(["--seconds", str(args.seconds)])
                os.environ.setdefault("XOR_CAMPAIGN_LAUNCH_COMMAND_JSON", json.dumps([sys.executable, *sys.argv]))
                os.execv(sys.executable, command)
            return run_campaign(directory, args.resume, args.seconds)
        elif args.command == "summary":
            print(campaign_summary(args.directory))
        elif args.command == "status":
            print(json.dumps(campaign_status(args.directory), indent=2))
        elif args.command == "stop":
            print(json.dumps(request_stop(args.directory), indent=2))
        elif args.command == "verify-run":
            directory = args.directory.resolve()
            frozen = directory / "source" / "search" / "run.py"
            rt.load_config(directory)
            if frozen.resolve() != Path(__file__).resolve():
                os.execv(sys.executable, [sys.executable, str(frozen), "verify-run", str(directory)])
            print(json.dumps(verify_run(directory), indent=2))
        elif args.command == "verify":
            api, _ = rt.api_modules()
            result = api.verify(rt.read_json(args.circuit), api.load_target(args.target), cap=args.cap)
            print(json.dumps(result, indent=2))
            return 0 if result["equivalent"] else 1
        else:
            try:
                from worker import Worker
                return Worker(args.directory, args.label, args.token).run()
            except BaseException as exc:
                directory = args.directory / "workers" / args.label
                rt.atomic_json(directory / "error.json", {"utc": rt.utc_now(), "type": type(exc).__name__,
                    "message": str(exc), "traceback": traceback.format_exc(), "owner_token": args.token})
                raise
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        print(type(exc).__name__ + ": " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
