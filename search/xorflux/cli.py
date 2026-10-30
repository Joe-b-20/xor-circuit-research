"""``python3 search/xorflux`` (from the repository root): run, inspect and configure
XOR-circuit search campaigns.

Commands (``COMMAND --help`` for details)::

    run CAMPAIGN.toml --out DIR [--seconds N] [--detach] [--set k=v ...]   freeze and start
    resume DIR [--seconds N] [--detach]                      continue a stopped campaign
    stop DIR [--wait S]                                      ask a running campaign to stop
    status DIR [--json]                                      human summary of a run
    plan CAMPAIGN.toml [--set k=v ...] [--json] [--settings] resolve and print, start nothing
    report DIR                                               CSV tables + report.html
    verify DIR | CIRCUIT.json --target T [--cap N]           independent verification
    config show [--profile P] [--set k=v] [--non-default]    resolved settings as commented TOML
    config explain [KEY_OR_PREFIX]                           knob documentation
    map list | map show NAME | map new NAME ...              the maps in circuits/; add one
    quick MAP [--seconds N] [--seed S] [--set k=v ...]       one in-process worker, small run dir

``run`` and ``resume`` start the coordinator from the run directory's frozen source copy, so the
campaign keeps running the code it was frozen with whatever happens to the live tree.  Without
``--detach`` this process becomes the coordinator (``exec``); with it the coordinator starts in a
new session, writes ``DIR/coordinator.log`` and outlives the shell that launched it.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from .campaign.checkpoint import (CampaignLock, CheckpointError, LockError, identity_alive, read_json,
                                  read_jsonl, request_stop, utc_now)
from .campaign.freeze import (PACKAGE_ROOT, FreezeError, PlanError, frozen_campaign_value,
                              load_campaign, load_plan, parse_duration, resolve, verify_freeze)
from .campaign.records import Backend, check_record, load_backend

EXPECTED_ERRORS = (PlanError, FreezeError, LockError, CheckpointError, ValueError, OSError,
                   RuntimeError, KeyError, ImportError)
#: Words ``--seconds`` accepts for "until stopped" (0 too), overriding a plan duration.
UNBOUNDED_WORDS = ("none", "inf", "unbounded", "forever")
COORDINATOR_LOG = "coordinator.log"
#: How this program was invoked, for the commands it prints (set by ``main``).
PROG = "python3 -m xorflux"
#: Default parent of ``quick`` run directories: ``search/runs/``.
RUNS_DIR = PACKAGE_ROOT.parent / "runs"


# --------------------------------------------------------------------------------------------
# Formatting helpers
# --------------------------------------------------------------------------------------------
def fmt_value(value) -> str:
    """A value for human tables (``none`` for null)."""
    if value is None:
        return "none"
    return json.dumps(value)


def fmt_seconds(seconds) -> str:
    """``h:mm:ss`` (or 'unbounded')."""
    if seconds is None or seconds == math.inf:
        return "unbounded"
    seconds = int(seconds)
    return f"{seconds // 3600}:{seconds // 60 % 60:02d}:{seconds % 60:02d}"


def table(rows: list[tuple]) -> str:
    """Left-aligned plain-text table; the first row is the header."""
    rows = [tuple(str(c) for c in row) for row in rows]
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    return "\n".join("  ".join(c.ljust(widths[i]) for i, c in enumerate(r)).rstrip() for r in rows)


def _seconds(text):
    """``--seconds``: a duration (3600, 90m, 2h30m), or 0 / none / inf for 'until stopped'."""
    if str(text).strip().lower() in UNBOUNDED_WORDS:
        return math.inf
    try:
        value = parse_duration(text)
    except PlanError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None
    return math.inf if value is None else value


# --------------------------------------------------------------------------------------------
# Starting a coordinator
# --------------------------------------------------------------------------------------------
def _campaign_knob(run_dir: Path, plan: dict, name: str):
    """``campaign.<name>`` as frozen in ``run_dir`` (read without a schema), or the live default
    when the run was frozen before the knob existed."""
    from .campaign.coordinator import KNOBS
    return frozen_campaign_value(run_dir, plan, f"campaign.{name}", KNOBS.knobs[name].default)


def _coordinator_launch(run_dir: Path, plan: dict, resume: bool, seconds) -> tuple[list, dict, bool]:
    """(command, environment, frozen) of the ``_coordinator`` process for ``run_dir``.

    The frozen-or-live decision reads the frozen campaign settings without a schema, so a run
    frozen by older or newer source still starts after the live tree gained or lost knobs.
    """
    frozen = bool(_campaign_knob(run_dir, plan, "run_frozen")) \
        and (run_dir / "source" / "xorflux").is_dir()
    root = run_dir / "source" if frozen else PACKAGE_ROOT.parent
    command = [sys.executable, "-P", "-m", "xorflux", "_coordinator", str(run_dir)]
    if resume:
        command.append("--resume")
    if seconds is not None:
        command += ["--seconds", str(seconds)]
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(p for p in (str(root), os.environ.get("PYTHONPATH")) if p)
    return command, env, frozen


def _launch(run_dir: Path, resume: bool, seconds, detach: bool) -> int:
    """Start the coordinator of ``run_dir``: replace this process, or detach it."""
    plan = verify_freeze(run_dir)
    command, env, frozen = _coordinator_launch(run_dir, plan, resume, seconds)
    if detach:
        return _detach(run_dir, plan, command, env)
    if not frozen:
        from .campaign.coordinator import run_coordinator
        return run_coordinator(run_dir, resume=resume, seconds=seconds)
    sys.stdout.flush()
    sys.stderr.flush()
    os.execve(sys.executable, command, env)
    return 0  # not reached


def _tail(path: Path, lines: int) -> str:
    try:
        return "\n".join(path.read_text(errors="replace").splitlines()[-lines:])
    except OSError:
        return ""


def _detach(run_dir: Path, plan: dict, command: list, env: dict) -> int:
    """Start the coordinator in a new session (no controlling terminal, no SIGHUP, its own
    process group) with stdio in ``coordinator.log``; return once it owns the run directory."""
    log_path = run_dir / COORDINATOR_LOG
    with log_path.open("ab") as log:
        log.write(f"--- {utc_now()} launched by pid {os.getpid()}: {' '.join(command)}\n".encode())
        log.flush()
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                 env=env, cwd=str(run_dir), start_new_session=True)
    wait = float(_campaign_knob(run_dir, plan, "detach_wait_seconds"))
    poll = float(_campaign_knob(run_dir, plan, "poll_seconds"))
    deadline = time.monotonic() + wait
    while True:
        code = child.poll()
        if CampaignLock(run_dir).read().get("pid") == child.pid:
            state = f"running detached as pid {child.pid}"
            break
        if code is not None:
            if code == 0:   # a very short session can finish before we look
                print(f"coordinator pid {child.pid} already finished (exit 0); log: {log_path}")
                return 0
            print(f"error: the detached coordinator exited with code {code}; last lines of "
                  f"{log_path}:\n{_tail(log_path, 20)}", file=sys.stderr)
            return 1
        if time.monotonic() >= deadline:
            state = (f"started as pid {child.pid} but does not own the run directory after "
                     f"{wait:g} s; check status and {log_path}")
            break
        time.sleep(poll)
    print(f"coordinator {state}\n"
          f"  log:     {log_path}\n"
          f"  status:  {PROG} status {run_dir}\n"
          f"  stop:    {PROG} stop {run_dir} --wait 120\n"
          f"  resume:  {PROG} resume {run_dir} --detach")
    return 0


# --------------------------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------------------------
def plan_text(plan: dict, settings: dict | None = None) -> str:
    """Human description of a resolved plan."""
    from .config.settings import toml_value
    lines = [f"campaign {plan['name']}  seed {plan['seed']}  duration {fmt_seconds(plan['duration'])}"
             f"  profiles {', '.join(plan['profiles'])}  backend {plan['backend']}"]
    if plan.get("description"):
        lines.append(plan["description"])
    lines.append("")
    rows = [("target", "inputs", "outputs", "matrix sha256", "spec")]
    for key, t in plan["targets"].items():
        rows.append((key, t["input_count"], t["output_count"], t["matrix_sha256"][:16], t["spec"]))
    lines += [table(rows), ""]
    rows = [("worker", "target", "objective", "cap", "gate limit", "seed", "rng seed", "settings")]
    for w in plan["workers"]:
        seed = w["seed"]
        if seed["kind"] == "file":
            info = plan["seeds"][seed["sha256"]]
            seed_text = f"{info['gates']}@{info['depth']} {info['source']}"
        else:
            seed_text = f"root:{seed['constructor']}"
        rows.append((w["id"], w["target"], w["objective"], fmt_value(w["depth_cap"]),
                     fmt_value(w["gate_limit"]), seed_text, w["rng_seed"], w["settings_sha256"][:12]))
    lines.append(table(rows))
    if settings:
        lines.append("")
        for wid, s in settings.items():
            changed = s.non_default()
            lines.append(f"{wid}: {len(changed)} non-default settings")
            for key in sorted(changed):
                value, origin = changed[key]
                lines.append(f"  {key} = {toml_value(value)}  # {origin}")
    for note in plan.get("notes", []):
        lines.append(f"note: {note}")
    return "\n".join(lines)


def cmd_plan(args) -> int:
    resolved = resolve(load_campaign(args.campaign), campaign_path=args.campaign, assignments=args.set)
    if args.json:
        print(json.dumps(resolved.plan, indent=2, sort_keys=True))
    else:
        print(plan_text(resolved.plan, resolved.settings if args.settings else None))
    return 0


def cmd_run(args) -> int:
    from .campaign.freeze import freeze
    resolved = resolve(load_campaign(args.campaign), campaign_path=args.campaign, assignments=args.set)
    out = Path(args.out).resolve()
    plan = freeze(resolved, out)
    print(plan_text(plan))
    print(f"\nfrozen into {out}")
    if not args.detach:
        print(f"stop with:   {PROG} stop {out}   (or Ctrl-C here)\n"
              f"status with: {PROG} status {out}\n")
    return _launch(out, resume=False, seconds=args.seconds, detach=args.detach)


def cmd_resume(args) -> int:
    run_dir = Path(args.dir).resolve()
    owner = CampaignLock(run_dir).read()
    if owner and identity_alive(owner):
        raise LockError(f"{run_dir} is still running (coordinator pid {owner['pid']})")
    print(f"resuming {run_dir}")
    return _launch(run_dir, resume=True, seconds=args.seconds, detach=args.detach)


def cmd_stop(args) -> int:
    run_dir = Path(args.dir).resolve()
    result = request_stop(run_dir, args.reason)
    if not result["stopped"]:
        print(result["message"])
        return 1
    print(f"stop requested ({args.reason}); workers checkpoint and exit")
    if not args.wait:
        return 0
    poll = float(_campaign_knob(run_dir, load_plan(run_dir), "poll_seconds"))
    deadline = time.monotonic() + args.wait
    while time.monotonic() < deadline:
        owner = CampaignLock(run_dir).read()
        if owner.get("token") != result["owner_token"]:
            print("stopped")
            return 0
        if not identity_alive(owner):
            print("the coordinator died without releasing its lock; `resume` reclaims it")
            return 1
        time.sleep(poll)
    print(f"still stopping after {args.wait:g} s")
    return 1


def status_text(run_dir: Path) -> str:
    """Human summary of a run directory (reads files only; never changes anything)."""
    plan = load_plan(run_dir)
    status = read_json(run_dir / "status.json", {}) or {}
    owner = CampaignLock(run_dir).read()
    live = bool(owner) and identity_alive(owner)
    worker_status = {w["id"]: read_json(run_dir / "workers" / w["id"] / "status.json", {}) or {}
                     for w in plan["workers"]}
    if not status and any(worker_status.values()):
        # A `quick` run has no coordinator: summarise from the worker's own files.
        frontier = {key: [] for key in plan["targets"]}
        for wid, s in worker_status.items():
            for gates, depth in s.get("frontier", []):
                frontier[s["target"]].append({"gates": gates, "depth": depth, "worker": wid})
        status = {"phase": "standalone (quick) run, " + ", ".join(
                      s.get("phase", "?") for s in worker_status.values()),
                  "frontier": frontier,
                  "records": {wid: s.get("records", 0) for wid, s in worker_status.items()}}
    phase = "running" if live else status.get("phase", "prepared (never started)")
    if not live and phase == "running":
        phase = f"not running (coordinator died; last update {status.get('updated_utc')})"
    head = f"campaign {plan['name']}  run {plan['run_id'][:12]}  {phase}"
    if live:
        head += f"  pid {owner['pid']}, up {fmt_seconds(status.get('elapsed_seconds'))}" \
                f" of {fmt_seconds(status.get('duration'))}"
    lines = [head]
    if status.get("stop_reason") and not live:
        lines.append(f"stopped: {status['stop_reason']}")
    if status.get("error"):
        lines.append(f"error: {status['error'].get('message')}")
    workers = status.get("workers", {})
    alive = sum(bool(w.get("alive")) for w in workers.values()) if live else 0
    restarts = sum(w.get("restarts", 0) for w in workers.values())
    lines.append(f"workers alive {alive}/{len(plan['workers'])}   records "
                 f"{sum((status.get('records') or {}).values())}   rejected {status.get('rejected', 0)}"
                 + (f"   worker restarts {restarts}" if restarts else ""))
    lines.append("")
    for key in plan["targets"]:
        points = (status.get("frontier") or {}).get(key, [])
        frontier = ", ".join(f"{p['gates']}@{p['depth']} ({p['worker']})" for p in points) or "no records yet"
        pool = (status.get("pool") or {}).get(key, {})
        lines.append(f"{key}: frontier {frontier}")
        if pool:
            lines.append(f"  pool: " + ", ".join(f"{p} x{n}" for p, n in pool.items()))
        div = (status.get("diversity") or {}).get(key)
        if div and div["workers"] >= 2:
            bests, chains = div["bests"], div["chains"]
            lines.append(f"  diversity (Jaccard): bests mean {bests['mean']:.3f} min {bests['min']:.3f}, "
                         f"chains mean {chains['mean']:.3f}; {div['distinct_best_dags']}/{div['workers']} "
                         "distinct best DAGs" + ("   COLLAPSE ALARM" if div.get("alarm") else ""))
    rows = [("worker", "phase", "steps", "steps/s", "best", "records", "updated")]
    for w in plan["workers"]:
        s = worker_status[w["id"]]
        best = s.get("best")
        rows.append((w["id"], s.get("phase", "-") if live or s.get("phase") != "running" else "stale",
                     s.get("steps", "-"), f"{s.get('steps_per_second') or 0:.1f}",
                     f"{best['gates']}@{best['depth']}" if best else "-", s.get("records", "-"),
                     (s.get("updated_utc") or "-")[11:19]))
        if (run_dir / "workers" / w["id"] / "error.json").exists():
            err = read_json(run_dir / "workers" / w["id"] / "error.json")
            rows.append(("", "error:", err.get("message", "")[:70], "", "", "", ""))
    lines += ["", table(rows), "", f"events: {run_dir / 'campaign.jsonl'}   per worker: "
              f"{run_dir / 'workers' / '<id>'}"]
    if (run_dir / COORDINATOR_LOG).exists():
        lines.append(f"detached coordinator output: {run_dir / COORDINATOR_LOG}")
    return "\n".join(lines)


def cmd_status(args) -> int:
    run_dir = Path(args.dir).resolve()
    if args.json:
        load_plan(run_dir)  # a clear error when DIR is not a run directory
        print(json.dumps(read_json(run_dir / "status.json", {}), indent=2))
    else:
        print(status_text(run_dir))
    return 0


def cmd_report(args) -> int:
    run_dir = Path(args.dir).resolve()
    plan = load_plan(run_dir)
    result = load_backend(plan["backend"]).build_report(run_dir)
    print(f"report: {result}" if isinstance(result, (str, Path)) else json.dumps(result, indent=2, default=str))
    return 0


def _verify_run(run_dir: Path) -> int:
    plan = verify_freeze(run_dir)
    backend = load_backend(plan["backend"])
    from .campaign.freeze import frozen_target
    targets = {key: frozen_target(run_dir, plan, key, backend) for key in plan["targets"]}
    good, bad = 0, []
    for spec in plan["workers"]:
        lines, _ = read_jsonl(run_dir / "workers" / spec["id"] / "records.jsonl")
        for entry in (e for e in lines if "path" in e):
            _, reason = check_record(run_dir, entry, spec, plan, backend, targets[spec["target"]], deep=True)
            if reason:
                bad.append((entry["path"], reason))
            else:
                good += 1
    print(f"frozen source, plan and snapshots: ok\nrecords verified: {good}   failed: {len(bad)}")
    for path, reason in bad:
        print(f"  FAIL {path}: {reason}")
    return 1 if bad else 0


def cmd_verify(args) -> int:
    path = Path(args.path)
    if path.is_dir():
        return _verify_run(path.resolve())
    if not args.target:
        raise PlanError("verifying a circuit file needs --target NAME_OR_PATH")
    backend = Backend()
    circuit = read_json(path)
    if circuit is None:
        raise PlanError(f"no such file: {path}")
    bare = {k: v for k, v in circuit.items() if k != "metadata"}
    result = backend.verify(bare, backend.load_target(args.target), args.cap)
    summary = {k: v for k, v in result.items() if k not in ("masks",)}
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if result.get("equivalent") else 1


def _schema():
    try:
        return Backend().schema()
    except ImportError as exc:
        raise ImportError(f"cannot build the knob schema ({exc}); a module listed in "
                          "config/registry.py is missing") from None


def cmd_config_show(args) -> int:
    from .config.settings import build, to_toml, toml_value
    profiles = args.profile or ["default"]
    settings = build(profiles, assignments=args.set, schema=_schema())
    keys = sorted(settings.values)
    if args.prefix:
        prefix = args.prefix.rstrip(".")
        keys = [k for k in keys if k == prefix or k.startswith(prefix + ".")]
    if args.non_default:
        keys = [k for k in keys if settings.origin(k) != "default"]
    if not keys:
        print("# (no settings match)")
        return 0
    if args.flat:
        for key in keys:
            print(f"{key} = {toml_value(settings[key])}  # {settings.origin(key)}")
        return 0
    sets = f"; --set {' '.join(args.set)}" if args.set else ""
    print(f"# xorflux settings: profiles {', '.join(profiles)}{sets}\n"
          "# A starting point for a profile: save this as NAME.toml, delete what you keep at the\n"
          "# default, edit the rest, then use it with `profiles = [\"path/NAME.toml\"]` in a campaign\n"
          "# or `--profile path/NAME.toml`.  Any value can also go in a campaign's [set] table or a\n"
          "# --set KEY=VALUE.  Null is written \"none\"; a trailing \"# origin\" marks a value that\n"
          "# does not come from the defaults.  Legal values are in [brackets].\n")
    print(to_toml(settings, keys), end="")
    return 0


def explain_text(schema, query: str | None) -> str:
    """Documentation of one knob, a listing of every knob under a prefix, or (no query) the
    list of sections."""
    if not query:
        lines = [f"Knob sections ({PROG} config explain SECTION for its knobs):"]
        for path, section in sorted(schema.sections.items()):
            count = len(section.knobs)
            lines.append(f"  {path:<28} {count:>3} knob{'s' if count != 1 else ' '}  {section.doc}")
        return "\n".join(lines)
    if query in schema.knobs:
        knob = schema.knobs[query]
        section = schema.section_of(query)
        lines = [query, f"  {knob.doc}", f"  legal values: {knob.constraint()}",
                 f"  default: {fmt_value(knob.default)}",
                 f"  section {section.path}: {section.doc}",
                 f"  change it: [set] \"{query}\" = ...  in a campaign file or profile, "
                 f"or --set {query}=..."]
        return "\n".join(lines)
    prefix = query.rstrip(".")
    keys = [k for k in sorted(schema.knobs) if k.startswith(prefix + ".")]
    if not keys:
        raise PlanError(f"no knob or section {query!r}{schema.suggest(query)}")
    lines = []
    for path, section in sorted(schema.sections.items()):
        if path == prefix or path.startswith(prefix + "."):
            lines.append(f"[{path}] {section.doc}")
            for name, knob in section.knobs.items():
                lines.append(f"  {name} = {fmt_value(knob.default)}  [{knob.constraint()}]  {knob.doc}")
    return "\n".join(lines)


def cmd_config_explain(args) -> int:
    print(explain_text(_schema(), args.key))
    return 0


def cmd_map_list(args) -> int:
    from .core.target import CIRCUITS_DIR
    backend = Backend()
    rows = [("name", "inputs", "outputs", "min depth", "seeds")]
    for name in backend.catalog():
        try:
            target = backend.load_target(name)
            info = backend.target_json(target)
            rows.append((name, info.get("input_count"), len(info.get("rows", [])),
                         getattr(target, "min_depth", "?"), len(backend.target_seeds(target))))
        except EXPECTED_ERRORS as exc:
            rows.append((name, "?", "?", "?", f"error: {exc}"))
    print(table(rows) if len(rows) > 1 else f"no maps in {CIRCUITS_DIR}")
    return 0


def cmd_map_show(args) -> int:
    backend = Backend()
    target = backend.load_target(args.name)
    info = backend.target_json(target)
    weights = sorted({r.bit_count() for r in info["rows"]})
    lines = [f"{target.name}: {info.get('source_path', info.get('name', ''))}",
             f"  inputs {info['input_count']}  outputs {len(info['rows'])}  row weights "
             f"{', '.join(map(str, weights))}  min depth {getattr(target, 'min_depth', '?')}",
             f"  matrix sha256 {info['matrix_sha256']}"]
    if any(info.get("affine_output_constants") or ()):
        lines.append("  output constants (not searched, linear part only): "
                     + " ".join(map(str, info["affine_output_constants"])))
    print("\n".join(lines))
    for label, seed in backend.target_seeds(target):
        check = backend.verify({k: v for k, v in seed.items() if k != "metadata"}, target, None)
        print(f"  seed {label}: {check.get('gate_count')} gates, depth {check.get('depth')}, "
              f"{'verified' if check.get('equivalent') else 'NOT EQUIVALENT'}")
    return 0


def _elements(text: str) -> list[list[int]]:
    """``"02 03 01 01; 01 02 03 01"`` (hex entries, rows split by ';' or newlines; ``@FILE``
    reads the text from a file) as a list of integer rows."""
    if text.startswith("@"):
        text = Path(text[1:]).read_text()
    rows = [r.replace(",", " ").split() for r in text.replace("\n", ";").split(";")]
    try:
        return [[int(c, 16) for c in r] for r in rows if r]
    except ValueError as exc:
        raise PlanError(f"element matrix entries must be hex bytes: {exc}") from None


def cmd_map_new(args) -> int:
    """Write circuits/NAME/NAME.mat.txt from an element matrix over GF(2^m) or a 0/1 file."""
    import re
    from .core.target import (CIRCUITS_DIR, MATRIX_SUFFIX, format_matrix_text, load_matrix_text,
                              matrix_over_field)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", args.name):
        raise PlanError("a map name uses letters, digits, '-' and '_' (e.g. twofish-mds)")
    given = [o for o in ("bytes", "circulant", "rows") if getattr(args, o)]
    if len(given) != 1:
        raise PlanError("give exactly one of --bytes, --circulant or --rows")
    constants = None
    if args.rows:
        source = load_matrix_text(args.rows)
        n, rows = source.n_inputs, list(source.rows)
        constants = source.meta.get("affine_output_constants")
    else:
        if args.gf is None:
            raise PlanError("--bytes and --circulant need --gf POLY, the field modulus (AES: 0x11b)")
        if args.bytes:
            matrix = _elements(args.bytes)
        else:
            first = _elements(args.circulant)
            if len(first) != 1:
                raise PlanError("--circulant takes one row: the first row of the matrix")
            c = first[0]
            matrix = [[c[(j - i) % len(c)] for j in range(len(c))] for i in range(len(c))]
        n, rows = matrix_over_field(matrix, int(args.gf, 0))
    if args.constants:
        constants = [int(c) for c in args.constants.replace(",", " ").split()]
    text = format_matrix_text(n, rows, constants)
    folder = Path(args.circuits) if args.circuits else CIRCUITS_DIR
    path = folder / args.name / (args.name + MATRIX_SUFFIX)
    if path.exists() and not args.force and path.read_text() != text:
        raise PlanError(f"{path} exists with a different matrix (--force overwrites it)")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    target = load_matrix_text(path, args.name)          # read back what was written
    spec = args.name if folder.resolve() == CIRCUITS_DIR.resolve() else str(path)
    print(f"wrote {path}\n  {target.n_outputs} x {target.n_inputs}, row weights "
          f"{', '.join(map(str, sorted({r.bit_count() for r in target.rows})))}, min depth "
          f"{target.min_depth}\n  matrix sha256 {target.matrix_sha256}\n"
          f"search it: {PROG} quick {spec} --seconds 60")
    return 0


def cmd_quick(args) -> int:
    from .campaign.freeze import freeze
    from .campaign.worker import run_standalone
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    label = Path(args.target).name.split(".")[0]
    out = Path(args.out or RUNS_DIR / f"quick-{label}-{stamp}").resolve()
    group = {"name": "quick", "target": args.target, "count": 1, "objective": args.objective,
             "seeds": args.seeds or ["target"]}
    if args.depth_cap is not None:
        group["depth_cap"] = args.depth_cap
    if args.gate_limit is not None:
        group["gate_limit"] = args.gate_limit
    seconds = None if args.seconds == math.inf else args.seconds
    campaign = {"campaign": {"name": f"quick-{label}", "seed": args.seed,
                             "duration": seconds or 0, "profiles": args.profile or ["default"],
                             "sharing": "off", "backend": args.backend},
                "workers": [group]}
    resolved = resolve(campaign, assignments=args.set)
    plan = freeze(resolved, out, freeze_source=False)
    wid = plan["workers"][0]["id"]
    print(f"quick run of {args.target} for {fmt_seconds(seconds)} into {out}  (Ctrl-C stops)")
    code = run_standalone(out, wid, seconds)
    status = read_json(out / "workers" / wid / "status.json", {}) or {}
    best = status.get("best")
    best_text = f"{best['gates']}@{best['depth']}" if best else "no record"
    print(f"{status.get('phase')}: {status.get('steps', 0)} steps, best {best_text}")
    if status.get("error"):
        print(f"error: {status['error']}")
    print(f"records: {out / 'workers' / wid / 'records'}\nreport:  {PROG} report {out}")
    return code


def cmd_coordinator(args) -> int:
    run_dir = Path(args.dir).resolve()
    import xorflux
    frozen = (run_dir / "source" / "xorflux").resolve()
    here = Path(xorflux.__file__).resolve().parent
    if frozen.is_dir() and here != frozen and \
            _campaign_knob(run_dir, load_plan(run_dir), "run_frozen"):
        raise RuntimeError(f"coordinator imported xorflux from {here}, not the frozen copy "
                           f"{frozen}; start campaigns with `xorflux run/resume`")
    from .campaign.coordinator import run_coordinator
    return run_coordinator(run_dir, resume=args.resume, seconds=args.seconds)


def cmd_worker(args) -> int:
    from .campaign.worker import worker_main
    return worker_main(args.dir, args.worker, args.token, args.cpu)


# --------------------------------------------------------------------------------------------
# Parser
# --------------------------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    """The argument parser (exposed for tests and documentation)."""
    parser = argparse.ArgumentParser(prog=PROG,
                                     description="Run, inspect and configure XOR-circuit search campaigns.",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="Guide: search/USAGE.md.  Method: search/HOW-IT-WORKS.md, search/xorflux/DESIGN.md.")
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    def add_set(p):
        p.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                       help="override any knob (TOML value syntax; repeatable), e.g. "
                            "--set sharing.mode=off --set moves.walk.expand.weight=1")

    seconds_help = ("session length: seconds or e.g. 90m, 2h30m; 0 or 'none' = until stopped "
                    "(default: the plan's duration)")
    detach_help = ("start the coordinator in a new session with its output in DIR/coordinator.log "
                   "and return: it keeps running after this shell (or a WSL session) ends")

    p = sub.add_parser("run", help="freeze a campaign into a new run directory and start it",
                       description="Resolve CAMPAIGN.toml, freeze source + settings + targets into "
                                   "--out, then run the coordinator from the frozen copy.")
    p.add_argument("campaign", help="campaign TOML file")
    p.add_argument("--out", required=True, help="new (or empty) run directory")
    p.add_argument("--seconds", type=_seconds, help=seconds_help)
    p.add_argument("--detach", action="store_true", help=detach_help)
    add_set(p)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("resume", help="continue a stopped campaign from its checkpoints")
    p.add_argument("dir", help="run directory")
    p.add_argument("--seconds", type=_seconds, help=seconds_help)
    p.add_argument("--detach", action="store_true", help=detach_help)
    p.set_defaults(func=cmd_resume)

    p = sub.add_parser("stop", help="ask a running campaign to checkpoint and stop")
    p.add_argument("dir", help="run directory")
    p.add_argument("--reason", default="requested", help="recorded in the session and events")
    p.add_argument("--wait", type=float, metavar="SECONDS", help="wait until the coordinator has exited")
    p.set_defaults(func=cmd_stop)

    p = sub.add_parser("status", help="summary of a run directory: frontier, pool, workers")
    p.add_argument("dir", help="run directory")
    p.add_argument("--json", action="store_true", help="print the raw status.json")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("plan", help="resolve a campaign file and print the plan; starts nothing")
    p.add_argument("campaign", help="campaign TOML file")
    p.add_argument("--json", action="store_true", help="print the full plan as JSON")
    p.add_argument("--settings", action="store_true", help="also list every non-default setting "
                   "per worker with its origin")
    add_set(p)
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("report", help="build CSV tables and report.html for a run directory")
    p.add_argument("dir", help="run directory")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("verify", help="independently verify every record of a run, or one circuit")
    p.add_argument("path", help="run directory, or a circuit JSON file")
    p.add_argument("--target", help="map name or .mat.txt path (circuit files only)")
    p.add_argument("--cap", type=int, help="real depth cap to check (circuit files only)")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("config", help="show resolved settings or explain knobs")
    config = p.add_subparsers(dest="config_command", required=True, metavar="show|explain")
    q = config.add_parser("show", help="resolved settings as a commented TOML profile",
                          description="Print resolved settings as TOML, one [section] per knob "
                                      "section, each knob preceded by its documentation: save it "
                                      "as a profile and edit it.")
    q.add_argument("--profile", action="append", help="profile name or TOML path (repeatable; "
                   "default: default)")
    q.add_argument("--non-default", action="store_true", help="only values not taken from defaults")
    q.add_argument("--prefix", help="only keys under this prefix, e.g. moves.walk")
    q.add_argument("--flat", action="store_true", help="one 'key = value  # origin' line per knob "
                   "(for grep and diff)")
    add_set(q)
    q.set_defaults(func=cmd_config_show)
    q = config.add_parser("explain", help="documentation, legal values and default of knobs")
    q.add_argument("key", nargs="?", help="a knob key (sharing.mode) or a prefix (sharing, "
                   "moves.walk); omit to list every section")
    q.set_defaults(func=cmd_config_explain)

    p = sub.add_parser("map", aliases=["targets"], help="list, describe or add maps (circuits/<name>/)")
    maps = p.add_subparsers(dest="map_command", required=True, metavar="list|show|new")
    maps.add_parser("list", help="every map in circuits/").set_defaults(func=cmd_map_list)
    q = maps.add_parser("show", help="one map: size, row weights, matrix hash, verified seeds")
    q.add_argument("name", help="map name or path to a .mat.txt file")
    q.set_defaults(func=cmd_map_show)
    q = maps.add_parser(
        "new", help="write circuits/NAME/NAME.mat.txt from a matrix over GF(2^m) or a 0/1 file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Write circuits/NAME/NAME.mat.txt (NIST matrix format) for a new linear map.\n"
                    "Element matrices use the AES bit convention: input x_(m*b+r) is bit r (LSB\n"
                    "first) of element b, output y_(m*b+r) bit r of output element b.",
        epilog="examples:\n"
               "  map new aes-mc --gf 0x11b --bytes '02 03 01 01; 01 02 03 01; 01 01 02 03; 03 01 01 02'\n"
               "  map new aes-mc --gf 0x11b --circulant '02 03 01 01'\n"
               "  map new mymap --rows my-matrix.txt          (0/1 rows, NIST or plain)")
    q.add_argument("name", help="map name (letters, digits, '-', '_'), also the folder name")
    q.add_argument("--gf", metavar="POLY", help="field modulus with its top bit, e.g. 0x11b "
                   "(AES, GF(2^8)) or 0x169 (Twofish MDS); m is its degree")
    q.add_argument("--bytes", metavar="MATRIX", help="element matrix in hex, rows separated by ';' "
                   "(or @FILE with one row per line)")
    q.add_argument("--circulant", metavar="ROW", help="first row of a circulant element matrix "
                   "(row i is the first row rotated right by i)")
    q.add_argument("--rows", metavar="FILE", help="a 0/1 matrix file instead (row i = output y_i, "
                   "column j = input x_j)")
    q.add_argument("--constants", metavar="BITS", help="optional output constants, one 0/1 per "
                   "output row (an affine map; the search works on the linear part)")
    q.add_argument("--circuits", metavar="DIR", help="write under DIR instead of the repository's "
                   "circuits/ (e.g. to try a map before adding it)")
    q.add_argument("--force", action="store_true", help="overwrite an existing, different matrix")
    q.set_defaults(func=cmd_map_new)

    p = sub.add_parser("quick", help="one in-process worker on a map, for experiments",
                       description="Run a single worker in this process (no coordinator, no "
                                   "sharing, live source) and write a small run directory.")
    p.add_argument("target", metavar="MAP", help="map name, or path to a .mat.txt / target JSON")
    p.add_argument("--seconds", type=_seconds, default=60.0, help="run length (default 60; "
                   "0 = until Ctrl-C)")
    p.add_argument("--seed", type=int, default=0, help="RNG seed (default 0)")
    p.add_argument("--objective", default="gates", help="objective kind (default gates)")
    p.add_argument("--depth-cap", type=int, help="real depth cap")
    p.add_argument("--gate-limit", type=int, help="record gate limit")
    p.add_argument("--seeds", action="append", help="seed: 'target', 'root[:constructor]' or a "
                   "circuit JSON path (repeatable; default target)")
    p.add_argument("--profile", action="append", help="profile (repeatable; default: default)")
    p.add_argument("--out", help="run directory (default search/runs/quick-MAP-TIME)")
    p.add_argument("--backend", default="xorflux", help="alternative backend 'module:Class' "
                   "(experiments and tests; see campaign/records.py)")
    add_set(p)
    p.set_defaults(func=cmd_quick)

    p = sub.add_parser("_coordinator")  # internal: no help= keeps it unlisted
    p.add_argument("dir")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--seconds", type=float)
    p.set_defaults(func=cmd_coordinator)

    p = sub.add_parser("_worker")  # internal
    p.add_argument("dir")
    p.add_argument("worker")
    p.add_argument("token")
    p.add_argument("--cpu", type=int)
    p.set_defaults(func=cmd_worker)
    return parser


def main(argv=None, prog=None) -> int:
    """Parse arguments and run one command; returns the exit code (1 on a reported error).
    ``prog`` is how the program was invoked (shown in help and printed commands)."""
    global PROG
    if prog:
        PROG = prog
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    except EXPECTED_ERRORS as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
