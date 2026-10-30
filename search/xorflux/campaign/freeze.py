"""Campaign file -> plan -> frozen run directory.

``resolve`` reads a campaign TOML (format: search/USAGE.md and the examples) and produces a
**plan**:
the targets (loaded and hashed), the verified seeds, and one entry per worker with its target,
objective, real depth cap, gate limit, seed, RNG seed and fully layered ``Settings``.  Every
setting keeps the label of the layer that set it::

    default < profile:<name> < campaign < campaign:set < group:<name> < worker:<id> < cli

``freeze`` writes a plan into a new run directory together with everything needed to rerun or
audit it: a copy of the ``xorflux`` source and a byte-reproducible tarball with per-file hashes,
target and seed snapshots, resolved settings with origins per worker, the environment and git
revision.  Runs and resumes execute the frozen source copy, never the live tree, so later edits to
the repository cannot change a running campaign.  ``verify_freeze`` re-checks all of it.

Coordinator-only knobs (``CAMPAIGN_ONLY``) have one campaign-wide value: group and worker layers
may not set them, and a group profile that does is overruled (with a plan note).  ``freeze``
claims the run directory exclusively first and removes what it wrote if anything fails.
"""
from __future__ import annotations

import difflib
import gzip
import hashlib
import io
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from ..config.settings import Settings, flatten, load_toml, parse_assignment, profile_path
from .checkpoint import SCHEMA, atomic_bytes, atomic_json, digest, file_hash, read_json, utc_now
from .records import Backend, dag_identity, load_backend

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
THREAD_ENV = {key: "1" for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                                   "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")}

CAMPAIGN_FIELDS = ("name", "description", "seed", "duration", "profiles", "backend", "sharing")
GROUP_FIELDS = ("name", "target", "count", "objective", "depth_cap", "gate_limit", "seeds",
                "profiles", "set", "per_worker")
TOP_FIELDS = ("campaign", "workers", "set")
#: Knobs only the coordinator reads; they cannot differ between workers.
CAMPAIGN_ONLY = ("campaign.", "sharing.pool_per_point")
#: Spacing of per-worker RNG seeds (a prime, as in the old runtime): seed + ordinal * stride.
#: Part of the plan's meaning (documented in README), not a tunable.
SEED_STRIDE = 1000003
#: Created exclusively (O_EXCL) in a run directory before anything else is written.
CLAIM_NAME = ".xorflux-run"
#: Safety net for a hung `git status` (network filesystem, lock): the freeze records the error
#: and goes on.  Not a search parameter; campaign.git_status = false skips the call.
GIT_TIMEOUT_SECONDS = 30


class PlanError(ValueError):
    """The campaign file is malformed or cannot be resolved."""


# --------------------------------------------------------------------------------------------
# Small parsers
# --------------------------------------------------------------------------------------------
_DURATION = re.compile(r"(\d+(?:\.\d+)?)\s*([smhd]?)")
_UNITS = {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400}


def parse_duration(value: Any) -> float | None:
    """Seconds from a number or a string such as ``"90"``, ``"45m"``, ``"2h30m"``; 0/None = unbounded."""
    if value is None or value == 0 or value == "":
        return None
    if isinstance(value, bool):
        raise PlanError(f"duration must be seconds or a string like '2h', got {value!r}")
    if isinstance(value, (int, float)):
        if value < 0:
            raise PlanError("duration must be positive")
        return float(value)
    text = str(value).strip().lower().replace(" ", "")
    parts = _DURATION.findall(text)
    if not parts or "".join(n + u for n, u in parts) != text:
        raise PlanError(f"cannot read duration {value!r}; use seconds or e.g. '90m', '2h30m'")
    total = float(sum(float(n) * _UNITS[u] for n, u in parts))
    return total or None  # "0", "0m": unbounded, like the number 0


def _check_fields(where: str, table: Mapping, allowed) -> None:
    for key in table:
        if key not in allowed:
            match = difflib.get_close_matches(key, allowed, n=1)
            hint = f" (did you mean {match[0]}?)" if match else ""
            raise PlanError(f"{where}: unknown field {key!r}{hint}; allowed: {', '.join(allowed)}")


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_.") or "target"


def _cycle(value, index: int):
    return value[index % len(value)] if isinstance(value, list) else value


def _cap(value, where: str) -> int | None:
    if value is None or (isinstance(value, str) and value.lower() == "none"):
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise PlanError(f"{where}: depth_cap must be a nonnegative integer or 'none', got {value!r}")
    return value


# --------------------------------------------------------------------------------------------
# Resolution
# --------------------------------------------------------------------------------------------
@dataclass
class Resolved:
    """A resolved campaign: the JSON-safe ``plan`` plus the live objects freezing needs."""
    plan: dict
    settings: dict[str, Settings]               # worker id -> Settings
    campaign_settings: Settings                 # coordinator-level settings
    targets: dict[str, Any] = field(default_factory=dict)        # key -> core Target
    target_json: dict[str, dict] = field(default_factory=dict)   # key -> snapshot JSON
    seeds: dict[str, dict] = field(default_factory=dict)         # sha256 -> circuit JSON
    backend: Backend | None = None
    source_text: bytes | None = None            # original campaign file


def load_campaign(path: str | Path) -> dict:
    """Read a campaign TOML file into a dict (with a clear error on bad TOML)."""
    try:
        return load_toml(path)
    except FileNotFoundError:
        raise PlanError(f"campaign file not found: {path}") from None
    except ValueError as exc:  # bad TOML; the message names the file
        raise PlanError(str(exc)) from None


def _profile_file(name: str, base: Path) -> Path:
    try:
        return profile_path(name, base)
    except ValueError as exc:
        raise PlanError(str(exc)) from None


def _as_list(value, where: str) -> list:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if not isinstance(value, list):
        raise PlanError(f"{where}: expected a string or a list, got {value!r}")
    return value


def _assignments(texts) -> dict:
    layer = {}
    for text in texts:
        try:
            key, value = parse_assignment(text)
        except ValueError as exc:
            raise PlanError(f"--set {text!r}: {exc}") from None
        layer[key] = value
    return layer


def _reject_campaign_only(where: str, layer: Mapping) -> None:
    bad = [k for k in flatten(layer) if k.startswith(CAMPAIGN_ONLY)]
    if bad:
        raise PlanError(f"{where}: {', '.join(bad)} can only be set campaign-wide "
                        "(profiles, [campaign], [set] or --set)")


def _apply(settings: Settings, layer: Mapping, label: str) -> None:
    try:
        settings.apply(layer, label)
    except ValueError as exc:
        raise PlanError(str(exc)) from None


def available_cpus() -> list[int]:
    """Logical CPUs this process may run on."""
    if hasattr(os, "sched_getaffinity"):
        return sorted(os.sched_getaffinity(0))
    return list(range(os.cpu_count() or 1))


def resolve(campaign: Mapping, *, campaign_path: str | Path | None = None, assignments=(),
            backend: Backend | None = None) -> Resolved:
    """Resolve a campaign dict (from ``load_campaign``) into a plan.  Starts nothing.

    ``campaign_path`` anchors relative target, seed and profile paths (default: cwd).
    ``assignments`` are ``key=value`` strings applied last with origin ``cli``.
    """
    base = Path(campaign_path).resolve().parent if campaign_path else Path.cwd()
    _check_fields("campaign file", campaign, TOP_FIELDS)
    head = dict(campaign.get("campaign", {}))
    _check_fields("[campaign]", head, CAMPAIGN_FIELDS)
    groups = campaign.get("workers")
    if not isinstance(groups, list) or not groups:
        raise PlanError("campaign file needs at least one [[workers]] group")
    backend_spec = head.get("backend", "xorflux")
    backend = backend or load_backend(backend_spec)
    schema = backend.schema()
    # With core's objective section present, the [[workers]] shorthands objective / depth_cap /
    # gate_limit are layer values of objective.kind / depth_cap / gate_limit (with provenance).
    objective_knobs = "objective.kind" in schema.knobs

    seed = head.get("seed", 0)
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise PlanError(f"[campaign] seed must be an integer, got {seed!r}")
    profiles = _as_list(head.get("profiles", ["default"]), "[campaign] profiles")
    sharing = head.get("sharing")
    campaign_layer = ({"sharing": {"mode": sharing}} if isinstance(sharing, str)
                      else {"sharing": dict(sharing)} if isinstance(sharing, Mapping) else {})
    top_set = dict(campaign.get("set", {}))
    cli_layer = _assignments(assignments)
    profile_files: dict[str, str] = {}
    profile_cache: dict[str, tuple[str, dict]] = {}   # every worker sees the same file contents

    def profile_layers(names):
        for name in names:
            if str(name) not in profile_cache:
                path = _profile_file(str(name), base)
                profile_files[str(path)] = file_hash(path)
                try:
                    profile_cache[str(name)] = (f"profile:{path.stem}", load_toml(path))
                except ValueError as exc:
                    raise PlanError(str(exc)) from None
            yield profile_cache[str(name)]

    def campaign_level() -> Settings:
        settings = Settings(schema)
        for label, layer in profile_layers(profiles):
            _apply(settings, layer, label)
        _apply(settings, campaign_layer, "campaign")
        _apply(settings, top_set, "campaign:set")
        return settings

    campaign_settings = campaign_level()
    _apply(campaign_settings, cli_layer, "cli")

    resolved = Resolved(plan={}, settings={}, campaign_settings=campaign_settings, backend=backend)
    targets: dict[str, dict] = {}
    by_spec: dict[str, str] = {}
    by_matrix: dict[str, str] = {}
    seeds: dict[str, dict] = {}
    notes: list[str] = []
    plan_groups, workers = [], []
    used_names = set()

    def load_target(spec: str) -> str:
        if spec in by_spec:
            return by_spec[spec]
        looks_like_path = "/" in spec or spec.endswith((".json", ".txt"))
        resolved_spec = str((base / spec).resolve()) if looks_like_path and not Path(spec).is_absolute() else spec
        try:
            target = backend.load_target(resolved_spec)
        except (ValueError, OSError) as exc:
            raise PlanError(f"target {spec!r}: {exc}") from None
        snapshot = {k: v for k, v in backend.target_json(target).items() if k not in ("seeds", "target_path")}
        for required in ("rows", "input_count", "matrix_sha256"):
            if required not in snapshot:
                raise PlanError(f"target {spec!r}: snapshot lacks {required!r}")
        matrix = snapshot["matrix_sha256"]
        if matrix in by_matrix:  # same matrix under another name: one pool, one frontier
            key = by_matrix[matrix]
        else:
            key = _slug(Path(spec).name.split(".")[0] if looks_like_path else spec)
            while key in targets:
                key += "_"
            by_matrix[matrix] = key
            targets[key] = {"spec": spec, "name": snapshot.get("name") or snapshot.get("id") or key,
                            "matrix_sha256": matrix, "input_count": snapshot["input_count"],
                            "output_count": len(snapshot["rows"]),
                            "snapshot": f"targets/{key}.json"}
            resolved.targets[key] = target
            resolved.target_json[key] = snapshot
        by_spec[spec] = key
        return key

    def add_seed(key: str, circuit: dict, source: str, where: str) -> dict:
        circuit = {k: v for k, v in circuit.items()}
        check = backend.verify({k: v for k, v in circuit.items() if k != "metadata"},
                               resolved.targets[key], None)
        if not check.get("equivalent"):
            raise PlanError(f"{where}: seed {source} does not compute target {key}: "
                            f"{check.get('error', 'outputs missing')}")
        sha = digest(circuit)
        seeds.setdefault(sha, {"target": key, "source": source, "gates": check["gate_count"],
                               "depth": check["depth"], "dag_sha256": dag_identity(check),
                               "snapshot": f"seeds/{key}/{sha[:16]}.json"})
        resolved.seeds[sha] = circuit
        return {"kind": "file", "sha256": sha}

    def seed_entries(key: str, group_seeds: list, where: str) -> list[dict]:
        entries = []
        for item in group_seeds:
            if not isinstance(item, str):
                raise PlanError(f"{where}: seeds entries must be strings, got {item!r}")
            if item == "target":
                builtin = backend.target_seeds(resolved.targets[key])
                for label, circuit in builtin:
                    entries.append(add_seed(key, circuit, f"target:{label}", where))
                if not builtin:
                    notes.append(f"{where}: target {key} has no built-in seeds; "
                                 "workers start from the engine's default root")
                    entries.append({"kind": "root", "constructor": "default"})
            elif item == "root" or item.startswith("root:"):
                constructor = item.partition(":")[2] or "default"
                known = backend.root_names()
                if constructor != "default" and known is not None and constructor not in known:
                    raise PlanError(f"{where}: unknown root constructor {constructor!r}; "
                                    f"known: {', '.join(known)}")
                entries.append({"kind": "root", "constructor": constructor})
            else:
                path = Path(item) if Path(item).is_absolute() else (base / item).resolve()
                circuit = read_json(path)
                if not isinstance(circuit, dict) or "gates" not in circuit:
                    raise PlanError(f"{where}: seed file {path} is missing or not a circuit JSON")
                entries.append(add_seed(key, circuit, str(path), where))
        return entries

    ordinal = 0
    for number, group in enumerate(groups):
        where = f"[[workers]] #{number + 1}"
        if not isinstance(group, Mapping):
            raise PlanError(f"{where}: must be a table")
        _check_fields(where, group, GROUP_FIELDS)
        if "target" not in group:
            raise PlanError(f"{where}: missing 'target'")
        key = load_target(str(group["target"]))
        name = _slug(str(group.get("name", key)))
        if name in used_names:
            raise PlanError(f"{where}: group name {name!r} used twice; give each group a distinct name")
        used_names.add(name)
        where = f"[[workers]] {name}"
        count = group.get("count", 1)
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            raise PlanError(f"{where}: count must be a positive integer")
        objective = group.get("objective")
        if objective is not None and (not isinstance(objective, str) or not objective):
            raise PlanError(f"{where}: objective must be a string")
        gate_limit = group.get("gate_limit")
        if gate_limit is not None and (isinstance(gate_limit, bool) or not isinstance(gate_limit, int)
                                       or gate_limit < 1):
            raise PlanError(f"{where}: gate_limit must be a positive integer")
        caps = group.get("depth_cap")
        if isinstance(caps, list) and not caps:
            raise PlanError(f"{where}: depth_cap list is empty")
        entries = seed_entries(key, _as_list(group.get("seeds", ["target"]), f"{where} seeds"), where)
        if not entries:
            raise PlanError(f"{where}: no seeds")
        group_set = dict(group.get("set", {}))
        _reject_campaign_only(f"{where} set", group_set)
        per_worker = group.get("per_worker", [])
        if not isinstance(per_worker, list) or any(not isinstance(x, Mapping) for x in per_worker):
            raise PlanError(f"{where}: per_worker must be a list of tables")
        for layer in per_worker:
            _reject_campaign_only(f"{where} per_worker", layer)
        group_profiles = _as_list(group.get("profiles"), f"{where} profiles")
        plan_groups.append({"name": name, "target": key, "count": count, "objective": objective,
                            "depth_cap": caps, "gate_limit": gate_limit, "seeds": group.get("seeds", ["target"]),
                            "profiles": group_profiles})
        for index in range(count):
            wid = f"{name}-{index:02d}"
            settings = Settings(schema)
            for label, layer in profile_layers(profiles + group_profiles):
                _apply(settings, layer, label)
            _apply(settings, campaign_layer, "campaign")
            _apply(settings, top_set, "campaign:set")
            shorthand = {}
            if objective is not None:
                shorthand["objective.kind"] = objective
            if "depth_cap" in group:
                shorthand["objective.depth_cap"] = _cap(_cycle(caps, index), where)
            if "gate_limit" in group:
                shorthand["objective.gate_limit"] = gate_limit
            if objective_knobs:
                _apply(settings, shorthand, f"group:{name}")
            _apply(settings, group_set, f"group:{name}")
            if per_worker:
                _apply(settings, per_worker[index % len(per_worker)], f"worker:{wid}")
            _apply(settings, cli_layer, "cli")
            # Coordinator-only knobs have one campaign-wide value; a group profile may not make
            # a worker's frozen settings claim another one.
            for knob in [k for k in settings.values if k.startswith(CAMPAIGN_ONLY)]:
                if settings.values[knob] != campaign_settings.values[knob] and index == 0:
                    notes.append(f"{where}: {settings.origin(knob)} sets the campaign-wide knob "
                                 f"{knob}; the campaign value "
                                 f"{campaign_settings.values[knob]!r} applies")
                settings.values[knob] = campaign_settings.values[knob]
                settings.origins[knob] = campaign_settings.origins[knob]
            if objective_knobs:  # the knobs are the truth; the fields only set them
                kind, cap, limit = (settings["objective.kind"], settings["objective.depth_cap"],
                                    settings["objective.gate_limit"])
            else:
                kind, cap, limit = (objective or "gates", shorthand.get("objective.depth_cap"),
                                    gate_limit)
            seed_spec = entries[index % len(entries)]
            if seed_spec["kind"] == "file":
                info = seeds[seed_spec["sha256"]]
                if cap is not None and info["depth"] > cap:
                    notes.append(f"{wid}: seed depth {info['depth']} is above its real cap {cap}; "
                                 "the engine repairs depth before anything is recorded")
                if limit is not None and info["gates"] > limit:
                    notes.append(f"{wid}: seed has {info['gates']} gates, above gate_limit {limit}")
            workers.append({"id": wid, "group": name, "index": index, "ordinal": ordinal, "target": key,
                            "objective": kind, "depth_cap": cap, "gate_limit": limit,
                            "seed": seed_spec, "rng_seed": seed + ordinal * SEED_STRIDE,
                            "settings": f"settings/{wid}.json", "settings_sha256": settings.digest()})
            resolved.settings[wid] = settings
            ordinal += 1

    # Validate every worker's objective early by building it (cheap): per_worker layers and
    # depth_cap lists make workers of one group differ.
    for spec in workers:
        try:
            backend.objective(resolved.targets[spec["target"]], spec, resolved.settings[spec["id"]])
        except (ValueError, TypeError) as exc:
            raise PlanError(f"worker {spec['id']}: objective {spec['objective']!r}: {exc}") from None

    cpus = available_cpus()
    cfg = campaign_settings.view("campaign")
    if len(workers) > len(cpus) and not cfg.allow_oversubscription:
        raise PlanError(f"{len(workers)} workers but only {len(cpus)} available CPUs; reduce counts "
                        "or --set campaign.allow_oversubscription=true")
    if cfg.pin_cpus and len(workers) > len(cpus):
        raise PlanError("campaign.pin_cpus needs one available CPU per worker")

    source = Path(campaign_path).resolve() if campaign_path else None
    resolved.source_text = source.read_bytes() if source else None
    resolved.plan = {
        "schema": SCHEMA, "name": str(head.get("name", source.stem if source else "campaign")),
        "description": str(head.get("description", "")), "seed": seed,
        "duration": parse_duration(head.get("duration")), "profiles": profiles,
        "backend": backend_spec,
        "campaign_file": {"path": str(source), "sha256": file_hash(source)} if source else None,
        "profile_files": profile_files, "cli_set": list(assignments),
        "targets": targets, "seeds": seeds, "groups": plan_groups, "workers": workers,
        "campaign_settings": "settings/campaign.json",
        "campaign_settings_sha256": campaign_settings.digest(), "notes": notes,
    }
    return resolved


# --------------------------------------------------------------------------------------------
# Settings files
# --------------------------------------------------------------------------------------------
def settings_json(settings: Settings, label: str) -> dict:
    """Frozen form of resolved settings: values, origins and digest."""
    return {"for": label, "digest": settings.digest(), "values": settings.values,
            "origins": settings.origins}


def settings_from_json(schema, data: Mapping) -> Settings:
    """Rebuild frozen settings against ``schema``; any mismatch is an error."""
    settings = Settings(schema)
    values, origins = data["values"], data["origins"]
    if set(values) != set(settings.values):
        missing = sorted(set(settings.values) ^ set(values))[:5]
        raise ValueError(f"frozen settings do not match the knob schema: {', '.join(missing)}")
    for key, value in values.items():
        settings.values[key] = settings.schema.knobs[key].validate(key, value)
        settings.origins[key] = origins[key]
    if settings.digest() != data["digest"]:
        raise ValueError("frozen settings digest mismatch")
    return settings


# --------------------------------------------------------------------------------------------
# Source freezing
# --------------------------------------------------------------------------------------------
def source_files(root: Path = PACKAGE_ROOT, include_tests: bool = False) -> list[Path]:
    """Package files to freeze: no caches, bytecode, hidden files or run directories."""
    out = []
    for directory, names, filenames in os.walk(root):
        here = Path(directory)
        names[:] = sorted(n for n in names if n != "__pycache__" and not n.startswith(".")
                          and n != "runs" and (include_tests or not (here == root and n == "tests")))
        for name in sorted(filenames):
            if not name.startswith(".") and not name.endswith((".pyc", ".pyo")):
                out.append(here / name)
    return out


def source_manifest(root: Path = PACKAGE_ROOT, include_tests: bool = False) -> dict[str, str]:
    """``{relative posix path: sha256}`` of the package source."""
    return {p.relative_to(root).as_posix(): file_hash(p) for p in source_files(root, include_tests)}


def reproducible_tar(files: Mapping[str, bytes]) -> bytes:
    """gzip'd tar of ``{arcname: bytes}`` with fixed metadata: same bytes in, same archive out."""
    raw = io.BytesIO()
    with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as tar:
            for name in sorted(files):
                info = tarfile.TarInfo(name)
                info.size = len(files[name])
                info.mtime, info.uid, info.gid, info.uname, info.gname, info.mode = 0, 0, 0, "", "", 0o644
                tar.addfile(info, io.BytesIO(files[name]))
    return raw.getvalue()


def git_info(root: Path = PACKAGE_ROOT, probe_status: bool = True) -> dict:
    """Git HEAD read from ``.git`` files (no git process); ``git status`` only when asked."""
    info = {"commit": None, "ref": None, "dirty": None, "error": None}
    gitdir = None
    for parent in [root, *root.parents]:
        candidate = parent / ".git"
        if candidate.is_dir():
            gitdir, top = candidate, parent
            break
        if candidate.is_file():  # worktree: "gitdir: <path>"
            text = candidate.read_text().strip()
            if text.startswith("gitdir:"):
                gitdir, top = (parent / text.split(":", 1)[1].strip()).resolve(), parent
                break
    if gitdir is None:
        info["error"] = "not a git checkout"
        return info
    try:
        head = (gitdir / "HEAD").read_text().strip()
        if head.startswith("ref:"):
            ref = head.split(":", 1)[1].strip()
            info["ref"] = ref
            common = gitdir
            if (gitdir / "commondir").is_file():
                common = (gitdir / (gitdir / "commondir").read_text().strip()).resolve()
            ref_file = common / ref
            if ref_file.is_file():
                info["commit"] = ref_file.read_text().strip()
            elif (common / "packed-refs").is_file():
                for line in (common / "packed-refs").read_text().splitlines():
                    if line.endswith(" " + ref):
                        info["commit"] = line.split()[0]
        else:
            info["commit"] = head
    except OSError as exc:
        info["error"] = str(exc)
    if probe_status:
        try:
            out = subprocess.check_output(["git", "status", "--porcelain", "--", str(root)], cwd=top,
                                          text=True, stderr=subprocess.DEVNULL,
                                          timeout=GIT_TIMEOUT_SECONDS)
            info["dirty"] = bool(out.strip())
            info["status"] = out
        except (OSError, subprocess.SubprocessError) as exc:
            info["error"] = f"git status failed: {exc}"
    return info


def environment() -> dict:
    """Interpreter, OS, CPU and launch command of this process."""
    model = None
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                model = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    return {"captured_utc": utc_now(), "host": socket.gethostname(), "python": sys.version,
            "python_executable": sys.executable, "implementation": platform.python_implementation(),
            "os": platform.platform(), "machine": platform.machine(), "cpu_model": model,
            "logical_cpus": os.cpu_count(), "available_cpus": available_cpus(),
            "thread_environment": {k: os.environ.get(k) for k in THREAD_ENV},
            "command": [sys.executable, *sys.argv]}


# --------------------------------------------------------------------------------------------
# Freezing a run directory
# --------------------------------------------------------------------------------------------
class _SourceChanged(Exception):
    """A package file changed while it was being frozen."""


def _freeze_source(out: Path, include_tests: bool, probe_git: bool) -> dict:
    """Copy the package into ``out/source``, write the tarball; raises _SourceChanged on drift."""
    shutil.rmtree(out / "source", ignore_errors=True)
    files = source_manifest(PACKAGE_ROOT, include_tests)
    blobs = {}
    for relative, sha in files.items():
        try:
            data = (PACKAGE_ROOT / relative).read_bytes()
        except FileNotFoundError:
            raise _SourceChanged(f"{relative} disappeared") from None
        if hashlib.sha256(data).hexdigest() != sha:
            raise _SourceChanged(relative)
        blobs["xorflux/" + relative] = data
        atomic_bytes(out / "source" / "xorflux" / relative, data)
    if source_manifest(PACKAGE_ROOT, include_tests) != files:
        raise _SourceChanged("the file list or a file changed during the copy")
    atomic_bytes(out / "source.tar.gz", reproducible_tar(blobs))
    return {"files": files, "manifest_sha256": digest(files), "archive": "source.tar.gz",
            "archive_sha256": file_hash(out / "source.tar.gz"), "include_tests": include_tests,
            "git": git_info(PACKAGE_ROOT, probe_git)}


def freeze(resolved: Resolved, out_dir: str | Path, freeze_source: bool = True) -> dict:
    """Write a resolved plan into the new run directory ``out_dir``; returns the final plan.

    ``freeze_source=False`` (``xorflux quick``) skips the source copy; everything else is the
    same, so quick runs are still auditable.
    """
    out = Path(out_dir).resolve()
    if out.is_relative_to(PACKAGE_ROOT):
        raise PlanError(f"{out} is inside the xorflux package; put run directories elsewhere "
                        "(the package is what gets frozen)")
    existed = out.exists()
    names = sorted(p.name for p in out.iterdir()) if existed else []
    busy = PlanError(f"{out} is being frozen by another process")
    if names == [CLAIM_NAME]:
        raise busy
    if names:
        raise PlanError(f"{out} is not empty; give a new --out directory (or `xorflux resume {out}`)")
    out.mkdir(parents=True, exist_ok=True)
    try:
        # Exclusive claim: of two `run --out DIR` started together, exactly one freezes.
        fd = os.open(out / CLAIM_NAME, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        raise busy from None
    with os.fdopen(fd, "w") as stream:
        stream.write(f"pid {os.getpid()} {utc_now()}\n")
    try:
        return _freeze_into(resolved, out, freeze_source)
    except BaseException:
        # Never leave a half-frozen directory: it would be neither runnable nor re-usable.
        if not existed:
            shutil.rmtree(out, ignore_errors=True)
        else:  # the directory was given empty (a mount point, say): empty it, keep it
            for child in out.iterdir():
                if child.is_dir() and not child.is_symlink():
                    shutil.rmtree(child)
                else:
                    child.unlink()
        raise


def _freeze_into(resolved: Resolved, out: Path, freeze_source: bool) -> dict:
    """The body of ``freeze`` once ``out`` is claimed."""
    cfg = resolved.campaign_settings.view("campaign")
    snapshots: dict[str, str] = {}

    def put_json(relative: str, value, pretty: bool = True) -> None:
        atomic_json(out / relative, value, pretty=pretty)
        snapshots[relative] = file_hash(out / relative)

    source = None
    if freeze_source:
        # A file saved mid-copy (an editor, another checkout tool) is detected by hashing; the
        # copy is then redone a bounded number of times rather than freezing a mixed tree.
        for attempt in range(cfg.freeze_attempts):
            try:
                source = _freeze_source(out, cfg.freeze_tests, cfg.git_status)
                break
            except _SourceChanged as exc:
                if attempt + 1 == cfg.freeze_attempts:
                    raise PlanError(f"source kept changing while freezing ({exc}); try again "
                                    "when no files under xorflux/ are being edited") from None
                time.sleep(cfg.freeze_retry_seconds)
    plan = dict(resolved.plan)
    plan["run_id"] = uuid.uuid4().hex
    plan["created_utc"] = utc_now()
    plan["source_manifest_sha256"] = source["manifest_sha256"] if source else None
    for key, info in plan["targets"].items():
        put_json(info["snapshot"], resolved.target_json[key])
    for sha, info in plan["seeds"].items():
        put_json(info["snapshot"], resolved.seeds[sha])
    for wid, settings in resolved.settings.items():
        put_json(f"settings/{wid}.json", settings_json(settings, wid))
    put_json("settings/campaign.json", settings_json(resolved.campaign_settings, "campaign"))
    if resolved.source_text is not None:
        atomic_bytes(out / "campaign.toml", resolved.source_text)
        snapshots["campaign.toml"] = file_hash(out / "campaign.toml")
    put_json("environment.json", environment())
    put_json("plan.json", plan)
    atomic_json(out / "freeze.json", {"schema": SCHEMA, "run_id": plan["run_id"],
                                      "plan_sha256": digest(plan), "source": source,
                                      "snapshots": snapshots}, pretty=True)
    return plan


class FreezeError(ValueError):
    """The run directory does not match what was frozen."""


def load_plan(run_dir: str | Path) -> dict:
    """``plan.json`` checked against the hash in ``freeze.json`` (cheap; no source check)."""
    run_dir = Path(run_dir)
    meta = read_json(run_dir / "freeze.json")
    plan = read_json(run_dir / "plan.json")
    if not isinstance(meta, dict) or not isinstance(plan, dict):
        raise FreezeError(f"{run_dir} is not a xorflux run directory (no freeze.json/plan.json)")
    if meta.get("schema") != SCHEMA or digest(plan) != meta.get("plan_sha256"):
        raise FreezeError(f"{run_dir}/plan.json differs from the frozen plan")
    return plan


def frozen_settings(run_dir: str | Path, relative: str, schema, expected_digest: str) -> Settings:
    """Load one frozen settings file and check it is the one the plan names."""
    settings = settings_from_json(schema, read_json(Path(run_dir) / relative))
    if settings.digest() != expected_digest:
        raise FreezeError(f"{relative} does not match the plan's settings hash")
    return settings


def frozen_campaign_value(run_dir: str | Path, plan: Mapping, key: str, default: Any = None) -> Any:
    """One coordinator setting read straight from ``settings/campaign.json``, without a schema.

    The live CLI uses this to launch, stop or wait for a run frozen by *other* source: knobs
    added or removed since then would make a schema-checked load fail.
    """
    data = read_json(Path(run_dir) / plan["campaign_settings"], {}) or {}
    return (data.get("values") or {}).get(key, default)


def frozen_target(run_dir: str | Path, plan: Mapping, key: str, backend: Backend):
    """Load a frozen target snapshot through core and check its matrix hash."""
    info = plan["targets"][key]
    target = backend.load_target(str(Path(run_dir) / info["snapshot"]))
    if backend.target_json(target).get("matrix_sha256") != info["matrix_sha256"]:
        raise FreezeError(f"target snapshot {info['snapshot']} does not match the plan's matrix hash")
    return target


def verify_freeze(run_dir: str | Path, check_source: bool = True) -> dict:
    """Re-check the plan, every snapshot and (optionally) the frozen source; returns the plan."""
    run_dir = Path(run_dir)
    plan = load_plan(run_dir)
    meta = read_json(run_dir / "freeze.json")
    for relative, sha in meta["snapshots"].items():
        path = run_dir / relative
        if not path.is_file() or file_hash(path) != sha:
            raise FreezeError(f"frozen file changed or missing: {relative}")
    source = meta.get("source")
    if check_source and source:
        root = run_dir / "source" / "xorflux"
        actual = source_manifest(root, include_tests=True)
        if actual != source["files"]:
            changed = sorted(k for k in set(actual) | set(source["files"])
                             if actual.get(k) != source["files"].get(k))
            raise FreezeError("frozen source changed: " + ", ".join(changed[:8]))
        if file_hash(run_dir / source["archive"]) != source["archive_sha256"]:
            raise FreezeError("frozen source archive changed")
    return plan
