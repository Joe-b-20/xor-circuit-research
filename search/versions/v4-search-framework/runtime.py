"""Durable campaign files, immutable plans, and ownership primitives."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid

SCHEMA = 1
SEARCH_ROOT = Path(__file__).resolve().parent
DEFAULTS = {
    "schema": SCHEMA, "allocation": {"aes_sbox_bottom": 6, "fox_mu4": 8, "joltik": 6},
    "base_seed": 20261024, "chunk_seconds": 30.0, "session_seconds": None,
    "engines": "all", "engine_knobs": {}, "objective": "gates", "gate_limit": None, "target_overrides": {}, "cap_cycle": ["seed", "seed_plus_one", None],
    "sharing": True, "pin_cpus": False, "allow_oversubscription": False, "coordinator_interval_seconds": 2.0,
    "status_interval_seconds": 2.0, "parent_check_seconds": 0.5,
    "stop_grace_seconds": 30.0, "terminate_grace_seconds": 5.0,
    "kill_grace_seconds": 2.0, "worker_log_bytes": 2000000, "worker_log_backups": 2, "equal_point_circuits": 32,
}
THREAD_ENV = {key: "1" for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                                   "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")}


def utc_now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def canonical_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_bytes(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        try:
            directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except OSError:
            pass
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_json(path, value):
    atomic_bytes(path, canonical_bytes(value))


def read_json(path, default=None):
    """Missing optional files are allowed; corrupt existing state is always an error."""
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        return default


def append_event(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        stream.seek(0, os.SEEK_END)
        end = stream.tell()
        if end:
            stream.seek(end - 1)
            if stream.read(1) != b"\n":
                cursor, boundary = end, 0
                while cursor:
                    start = max(0, cursor - 65536)
                    stream.seek(start)
                    block = stream.read(cursor - start)
                    position = block.rfind(b"\n")
                    if position >= 0:
                        boundary = start + position + 1
                        break
                    cursor = start
                stream.truncate(boundary)
                stream.seek(0, os.SEEK_END)
                stream.write(canonical_bytes({"event": "truncated_event_recovered", "utc": utc_now(),
                                               "removed_bytes": end - boundary}))
        stream.seek(0, os.SEEK_END)
        stream.write(canonical_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def process_identity(pid=None):
    pid = os.getpid() if pid is None else int(pid)
    result = {"pid": pid, "host": socket.gethostname(), "start_ticks": None}
    try:
        result["start_ticks"] = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
    except (OSError, IndexError):
        pass
    return result


def identity_alive(identity):
    if not identity or identity.get("host") != socket.gethostname():
        return False
    pid = identity.get("pid")
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    saved_ticks = identity.get("start_ticks")
    return saved_ticks is None or process_identity(pid)["start_ticks"] == saved_ticks


def _take_lock_guarded(run_dir):
    run_dir = Path(run_dir)
    path = run_dir / "runner.lock"
    owner = {**process_identity(), "token": uuid.uuid4().hex, "started_utc": utc_now()}
    for _ in range(2):
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            previous = read_json(path)
            if not isinstance(previous, dict) or previous.get("host") != socket.gethostname():
                raise RuntimeError("Campaign ownership cannot be safely recovered on this host")
            if identity_alive(previous):
                raise RuntimeError("Campaign already has a live coordinator")
            for status in (run_dir / "workers").glob("*/status.json"):
                if identity_alive(read_json(status, {}).get("process")):
                    raise RuntimeError("An old worker is still alive; wait for its ownership check to stop it")
            path.unlink()
            continue
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical_bytes(owner))
            stream.flush()
            os.fsync(stream.fileno())
        return owner
    raise RuntimeError("Could not acquire campaign ownership")


def take_lock(run_dir):
    # All reclamation is serialized: a second claimant cannot unlink a new owner's lock.
    try:
        import fcntl
    except ImportError:
        if (Path(run_dir) / "runner.lock").exists():
            raise RuntimeError("Automatic stale ownership recovery requires advisory file locks on this platform")
        return _take_lock_guarded(run_dir)
    with (Path(run_dir) / ".ownership.guard").open("a+b") as guard:
        fcntl.flock(guard.fileno(), fcntl.LOCK_EX)
        return _take_lock_guarded(run_dir)


def release_lock(run_dir, owner):
    path = Path(run_dir) / "runner.lock"
    if read_json(path, {}).get("token") == owner["token"]:
        path.unlink()


def environment():
    model = None
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                model = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    affinity = sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None
    return {"captured_utc": utc_now(), "host": socket.gethostname(), "os": platform.platform(),
            "machine": platform.machine(), "cpu_model": model, "logical_cpus": os.cpu_count(),
            "available_cpu_ids": affinity, "python": sys.version, "python_executable": sys.executable,
            "thread_environment": {key: os.environ.get(key) for key in THREAD_ENV},
            "command": [sys.executable, *sys.argv],
            "original_launch_command": json.loads(os.environ["XOR_CAMPAIGN_LAUNCH_COMMAND_JSON"])
            if os.environ.get("XOR_CAMPAIGN_LAUNCH_COMMAND_JSON") else None}


def source_files(root=None):
    root = Path(root) if root is not None else SEARCH_ROOT
    files = []
    for directory, names, filenames in os.walk(root):
        names[:] = sorted(name for name in names if name not in ("__pycache__", ".pytest_cache", ".git")
                          and not (Path(directory) == root and name == "runs"))
        for name in filenames:
            path = Path(directory) / name
            if path.suffix.lower() not in (".pyc", ".pyo"):
                files.append(path)
    return sorted(files)


def source_manifest(root=None):
    root = Path(root) if root is not None else SEARCH_ROOT
    return {p.relative_to(root).as_posix(): file_hash(p) for p in source_files(root)}


def check_sources(config, root=None):
    root = Path(root) if root is not None else SEARCH_ROOT
    expected = config["source"]["files"]
    actual = source_manifest(root)
    if actual != expected:
        changed = sorted(k for k in set(actual) | set(expected) if actual.get(k) != expected.get(k))
        raise ValueError("Source snapshot hash drift: " + ", ".join(changed[:8]))


def load_config(run_dir, check_snapshot=True):
    run_dir = Path(run_dir)
    config = read_json(run_dir / "config.json")
    if not isinstance(config, dict) or config.get("schema") != SCHEMA:
        raise ValueError("Missing or unsupported campaign config")
    if (run_dir / "config.sha256").read_text().strip() != digest(config):
        raise ValueError("Campaign config hash drift")
    if check_snapshot:
        check_sources(config, run_dir / "source" / "search")
        if file_hash(run_dir / "source.tar.gz") != config["source"]["archive_sha256"]:
            raise ValueError("Source archive hash drift")
        for target in config["targets"].values():
            for entry in [target["matrix_snapshot"], *target["seed_snapshots"]]:
                if file_hash(run_dir / entry["path"]) != entry["sha256"]:
                    raise ValueError("Target/seed snapshot hash drift: " + entry["path"])
    return config


def api_modules():
    import target
    import engine_api
    return target, engine_api


def objective_key(metrics, objective="gates"):
    if objective == "depth_then_gates":
        return metrics["depth"], metrics["gate_count"]
    if objective != "gates":
        raise ValueError("Unknown search objective: " + str(objective))
    return metrics["gate_count"], metrics["depth"]


def within_gate_limit(metrics, spec):
    return spec.get("gate_limit") is None or metrics["gate_count"] <= spec["gate_limit"]


def require_record_limits(verified, spec, path):
    """Apply the saved-record limit to independently evaluated gate counts."""
    if not within_gate_limit(verified, spec):
        raise ValueError("Retained record exceeds gate_limit: " + str(path))


def search_binding(spec):
    # Old prepared plans did not have these fields and retain their original bindings.
    return {key: spec[key] for key in ("objective", "gate_limit", "seed_sha256") if key in spec}


def _validate_search_settings(settings):
    objective_key({"gate_count": 0, "depth": 0}, settings["objective"])
    limit = settings["gate_limit"]
    if limit is not None and (type(limit) is not int or limit < 1):
        raise ValueError("gate_limit must be a positive integer or null")
    cycle = settings["cap_cycle"]
    if not isinstance(cycle, list) or not cycle or any(
            x not in (None, "seed", "seed_plus_one") and (type(x) is not int or x < 1) for x in cycle):
        raise ValueError("Invalid depth cap cycle")


def resolve_plan(overrides=None):
    target_api, engines = api_modules()
    overrides = overrides or {}
    unknown = set(overrides) - set(DEFAULTS)
    if unknown:
        raise ValueError("Unknown campaign settings: " + ", ".join(sorted(unknown)))
    settings = {**DEFAULTS, **overrides}
    if settings["schema"] != SCHEMA:
        raise ValueError("Unsupported settings schema")
    if type(settings["base_seed"]) is not int:
        raise ValueError("base_seed must be an integer")
    if not isinstance(settings["engine_knobs"], dict):
        raise ValueError("engine_knobs must be an object")
    allocation = settings["allocation"]
    if (not isinstance(allocation, dict) or not allocation or
            any(type(n) is not int or n < 0 for n in allocation.values()) or sum(allocation.values()) < 1):
        raise ValueError("Allocation must contain nonnegative integer worker counts")
    target_overrides = settings["target_overrides"]
    allowed_target_keys = {"seed_paths", "objective", "gate_limit", "cap_cycle", "engines", "engine_knobs"}
    if not isinstance(target_overrides, dict) or set(target_overrides) - set(allocation):
        raise ValueError("target_overrides must reference allocated target IDs")
    for target_id, values in target_overrides.items():
        if not isinstance(values, dict) or set(values) - allowed_target_keys:
            raise ValueError("Unknown or malformed target overrides for " + target_id)
    for name in ("chunk_seconds", "coordinator_interval_seconds", "status_interval_seconds",
                 "parent_check_seconds", "stop_grace_seconds", "terminate_grace_seconds", "kill_grace_seconds"):
        if not isinstance(settings[name], (int, float)) or not 0 < settings[name] < float("inf"):
            raise ValueError(name + " must be finite and positive")
    duration = settings["session_seconds"]
    if duration is not None and (not isinstance(duration, (int, float)) or not 0 < duration < float("inf")):
        raise ValueError("session_seconds must be null or finite and positive")
    for name in ("sharing", "pin_cpus", "allow_oversubscription"):
        if not isinstance(settings[name], bool):
            raise ValueError(name + " must be boolean")
    for name in ("worker_log_bytes", "worker_log_backups", "equal_point_circuits"):
        if type(settings[name]) is not int or settings[name] < 1:
            raise ValueError(name + " must be a positive integer")
    _validate_search_settings(settings)
    available = engines.available_engines()
    available_cpus = environment()["available_cpu_ids"]
    count = sum(allocation.values())
    cpu_count = len(available_cpus) if available_cpus is not None else os.cpu_count()
    if cpu_count is not None and count > cpu_count and not settings["allow_oversubscription"]:
        raise ValueError("Worker count exceeds available CPUs; reduce allocation or explicitly allow_oversubscription")
    if settings["pin_cpus"] and (available_cpus is None or len(available_cpus) < count):
        raise ValueError("CPU pinning needs one available logical CPU per worker")
    targets, specs, ordinal = {}, [], 0
    for target_id, workers in allocation.items():
        if not workers:
            continue
        resolved = {key: settings[key] for key in ("objective", "gate_limit", "cap_cycle", "engines", "engine_knobs")}
        resolved.update(target_overrides.get(target_id, {}))
        _validate_search_settings(resolved)
        explicit_engines = resolved["engines"] != "all"
        selected = resolved["engines"] if explicit_engines else available
        if not isinstance(selected, list) or not selected or any(e not in available for e in selected):
            raise ValueError("Unknown or empty engine portfolio")
        if not isinstance(resolved["engine_knobs"], dict) or set(resolved["engine_knobs"]) - set(available):
            raise ValueError("Knob overrides reference an unknown engine")
        knobs = {e: engines.effective_knobs(e, resolved["engine_knobs"].get(e, {})) for e in selected}
        target = target_api.load_target(target_id)
        explicit_seeds = "seed_paths" in resolved
        if explicit_seeds:
            paths = resolved["seed_paths"]
            if not isinstance(paths, list) or not paths or any(not isinstance(path, str) or not path for path in paths):
                raise ValueError("seed_paths must be a nonempty list of paths relative to search/")
            entries = [{"path": path, "source_kind": "explicit local circuit"} for path in paths]
        else:
            entries = target["seeds"]
        seeds = []
        for entry in entries:
            relative = Path(entry["path"])
            path = (SEARCH_ROOT / relative).resolve()
            if relative.is_absolute() or not path.is_relative_to(SEARCH_ROOT):
                raise ValueError("Seed path escapes search directory")
            circuit = read_json(path)
            checked = target_api.verify(circuit, target)
            if not checked["equivalent"]:
                raise ValueError("Seed is not equivalent to target " + target_id)
            normalized = target_api.normalise(circuit["gates"], target)
            checked = target_api.verify(normalized, target)
            if not within_gate_limit(checked, resolved):
                raise ValueError("Initial seed exceeds gate_limit for " + target_id)
            seeds.append({"source_path": relative.as_posix(), "source_sha256": file_hash(path),
                          "source_kind": circuit.get("provenance", {}).get("source_kind", entry.get("source_kind", "target-supplied circuit"))
                                         if explicit_seeds else entry.get("source_kind", "target-supplied circuit"),
                          "source_details": entry, "source_metadata": circuit.get("metadata"),
                          "source_provenance": circuit.get("provenance"),
                          "circuit": normalized, "verification": checked})
        if not seeds:
            raise ValueError("Target has no verified seeds: " + target_id)
        seeds = [seed for seed in seeds if not any(
            other["verification"]["gate_count"] <= seed["verification"]["gate_count"] and
            other["verification"]["depth"] <= seed["verification"]["depth"] and
            (other["verification"]["gate_count"], other["verification"]["depth"]) !=
            (seed["verification"]["gate_count"], seed["verification"]["depth"]) for other in seeds)]
        targets[target_id] = {"definition": target, "seeds": seeds, "search_settings": resolved,
                              "seed_selection": "explicit local paths" if explicit_seeds else "target defaults"}
        for index in range(workers):
            seed_index = index % len(seeds)
            seed_depth = seeds[seed_index]["verification"]["depth"]
            cap_mode = resolved["cap_cycle"][index % len(resolved["cap_cycle"])]
            cap = seed_depth if cap_mode == "seed" else seed_depth + 1 if cap_mode == "seed_plus_one" else cap_mode
            if cap is not None and cap < seed_depth:
                raise ValueError("Initial seed exceeds requested cap")
            applicable, exclusions = [], {}
            for engine in selected:
                options = {"objective": resolved["objective"], "gate_limit": resolved["gate_limit"]}
                # Preserve the old adapter call contract for the unchanged default objective.
                applicability = engines.engine_applicability(target, engine, cap, **options) if (
                    resolved["objective"] != "gates" or resolved["gate_limit"] is not None) else engines.engine_applicability(target, engine, cap)
                if applicability["applicable"]:
                    applicable.append(engine)
                else:
                    exclusions[engine] = applicability["reason"]
            if explicit_engines and exclusions:
                raise ValueError("Explicit engine portfolio is inapplicable: " + str(exclusions))
            if not applicable:
                raise ValueError("No applicable engine for " + target_id)
            offset = index * len(applicable) // workers
            applicable = applicable[offset:] + applicable[:offset]
            specs.append({"label": f"{target_id}-{index:02d}", "target_id": target_id,
                          "matrix_sha256": target["matrix_sha256"], "seed_index": seed_index,
                          "seed_sha256": digest(seeds[seed_index]["circuit"]),
                          "random_seed": int(settings["base_seed"]) + ordinal * 1000003,
                          "depth_cap": cap, "objective": resolved["objective"], "gate_limit": resolved["gate_limit"],
                          "engines": applicable, "excluded_engines": exclusions,
                          "engine_knobs": {e: knobs[e] for e in applicable},
                          "cpu_id": available_cpus[ordinal] if settings["pin_cpus"] else None})
            ordinal += 1
    return {"schema": SCHEMA, "settings": settings, "targets": targets, "workers": specs,
            "rng": {"algorithm": "CPython random.Random / MT19937", "engine_state": "actual getstate in engine checkpoints",
                    "initial_seed_derivation": "base_seed + global_worker_ordinal * 1000003; per-engine seed offset engine_index * 104729"},
            "sharing_policy": "same target ID and exact matrix hash only; recipient objective improvement within depth/gate limits; engine states reset on adoption",
            "symmetry": "none; no rotations or input permutations are applied",
            "checkpoint_policy": "every completed engine chunk and graceful exit; an interrupted chunk may be replayed from its saved start"}


def prepare(run_dir, overrides=None):
    run_dir = Path(run_dir).resolve()
    if run_dir.is_relative_to(SEARCH_ROOT) and not run_dir.is_relative_to(SEARCH_ROOT / "runs"):
        raise ValueError("Campaigns inside search/ must be placed under search/runs/")
    if run_dir.exists() and any(run_dir.iterdir()):
        raise ValueError("Preparation requires an empty output directory")
    files = source_manifest()
    plan = resolve_plan(overrides)
    if source_manifest() != files:
        raise ValueError("Source changed while resolving the campaign")
    run_dir.mkdir(parents=True, exist_ok=True)
    for relative, sha in files.items():
        data = (SEARCH_ROOT / relative).read_bytes()
        if hashlib.sha256(data).hexdigest() != sha:
            raise ValueError("Source changed while freezing: " + relative)
        atomic_bytes(run_dir / "source" / "search" / relative, data)
    archive = run_dir / "source.tar.gz"
    # gzip mtime and tar metadata are fixed: the same source bytes give the same archive.
    import gzip
    with archive.open("wb") as raw, gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w") as tar:
            for relative in files:
                path = run_dir / "source" / "search" / relative
                info = tar.gettarinfo(str(path), arcname="search/" + relative)
                info.mtime = 0
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                info.mode = 0o644
                with path.open("rb") as stream:
                    tar.addfile(info, stream)
    git_probe_error = None
    try:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SEARCH_ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        dirty = subprocess.check_output(["git", "status", "--porcelain", "--", "search"], cwd=SEARCH_ROOT.parent, text=True, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError) as exc:
        revision, dirty = None, None
        git_probe_error = str(exc)
    plan["source"] = {"git_commit": revision, "search_worktree_status": dirty, "git_probe_error": git_probe_error,
                      "files": files, "manifest_sha256": digest(files), "archive_path": "source.tar.gz",
                      "archive_sha256": file_hash(archive), "commit_is_exact_snapshot": dirty == ""}
    for target_id, entry in plan["targets"].items():
        definition = entry["definition"]
        matrix_path = f"targets/{target_id}/matrix.json"
        atomic_json(run_dir / matrix_path, definition)
        entry["matrix_snapshot"] = {"path": matrix_path, "sha256": file_hash(run_dir / matrix_path)}
        snapshots = []
        for index, seed in enumerate(entry.pop("seeds")):
            seed_path = f"seeds/{target_id}/{index:03d}.json"
            atomic_json(run_dir / seed_path, seed["circuit"])
            snapshots.append({"path": seed_path, "sha256": file_hash(run_dir / seed_path),
                              "source_path": seed["source_path"], "source_sha256": seed["source_sha256"],
                              "verification": seed["verification"], "source_kind": seed["source_kind"],
                              "source_details": seed["source_details"], "source_metadata": seed["source_metadata"],
                              "source_provenance": seed["source_provenance"]})
        entry["seed_snapshots"] = snapshots
    if source_manifest() != files:
        raise ValueError("Source changed while preparing the campaign")
    plan["run_id"] = uuid.uuid4().hex
    plan["prepared_utc"] = utc_now()
    plan["preparation_environment"] = environment()
    atomic_json(run_dir / "config.json", plan)
    atomic_bytes(run_dir / "config.sha256", (digest(plan) + "\n").encode())
    atomic_json(run_dir / "status.json", {"phase": "prepared", "workers_launched": 0, "updated_utc": utc_now()})
    return plan


def nondominated(records):
    selected = {}
    for record in sorted(records, key=lambda r: (r["gate_count"], r["depth"], r["path"])):
        pair = record["gate_count"], record["depth"]
        if pair not in selected and not any(g <= pair[0] and d <= pair[1] for g, d in selected):
            selected[pair] = record
    return list(selected.values())


def valid_offer(offer, config, spec, owner_token):
    return (isinstance(offer, dict) and offer.get("owner_token") == owner_token and
            offer.get("run_id") == config["run_id"] and offer.get("target_id") == spec["target_id"] and
            offer.get("matrix_sha256") == spec["matrix_sha256"] and
            offer.get("config_sha256") == digest(config) and
            (spec["depth_cap"] is None or offer.get("depth", float("inf")) <= spec["depth_cap"]) and
            (spec.get("gate_limit") is None or offer.get("gate_count", float("inf")) <= spec["gate_limit"]))


def safe_run_path(run_dir, relative):
    path = (Path(run_dir) / relative).resolve()
    if not path.is_relative_to(Path(run_dir).resolve()):
        raise ValueError("Run path escapes campaign directory")
    return path


def validate_record_binding(run_dir, path, circuit, config, worker_label):
    """Validate authoritative record and RNG evidence before recovery or sharing."""
    run_dir = Path(run_dir).resolve()
    path = Path(path).resolve()
    spec = next((item for item in config["workers"] if item["label"] == worker_label), None)
    if spec is None:
        raise ValueError("Record provenance binding references an unknown worker")
    if path.parent != run_dir / "workers" / worker_label / "records":
        raise ValueError("Record provenance path does not match its worker")
    expected = {"run_id": config["run_id"], "worker": worker_label,
                "target_id": spec["target_id"], "matrix_sha256": spec["matrix_sha256"],
                "config_sha256": digest(config), "source_manifest_sha256": config["source"]["manifest_sha256"],
                **search_binding(spec)}
    metadata = circuit.get("metadata", {}) if isinstance(circuit, dict) else {}
    if not isinstance(metadata, dict) or any(metadata.get(key) != value for key, value in expected.items()):
        raise ValueError("Record provenance binding mismatch: " + str(path))
    if not within_gate_limit({"gate_count": len(circuit.get("gates", []))}, spec):
        raise ValueError("Retained record exceeds gate_limit: " + str(path))
    rng_path = path.with_suffix(".rng-start.json")
    rng_start = read_json(rng_path)
    if not isinstance(rng_start, dict) or any(rng_start.get(key) != value for key, value in expected.items()):
        raise ValueError("Record starting RNG evidence missing or mismatched: " + str(path))
    if metadata.get("chunk_start_state_path") != rng_path.relative_to(run_dir).as_posix():
        raise ValueError("Record RNG evidence path mismatch: " + str(path))
    return spec
