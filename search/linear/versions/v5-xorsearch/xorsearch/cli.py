"""``python -m xorsearch``: run, inspect and configure XOR-circuit search campaigns.

Commands (``python -m xorsearch COMMAND --help`` for details)::

    run CAMPAIGN.toml --out DIR [--seconds N] [--set k=v ...]   freeze and start a campaign
    resume DIR [--seconds N]                                    continue a stopped campaign
    stop DIR [--wait S]                                         ask a running campaign to stop
    status DIR [--json]                                         human summary of a run
    plan CAMPAIGN.toml [--set k=v ...] [--json] [--settings]    resolve and print, start nothing
    report DIR                                                  CSV tables + report.html
    verify DIR | CIRCUIT.json --target T [--cap N]              independent verification
    config show [--profile P] [--set k=v] [--non-default]       resolved settings with origins
    config explain KEY_OR_PREFIX                                knob documentation
    targets list | targets show NAME                            target catalog
    quick TARGET [--seconds N] [--seed S] [--set k=v ...]       one in-process worker, small run dir

``run`` and ``resume`` re-execute the coordinator from the run directory's frozen source copy,
so the campaign keeps running the code it was frozen with whatever happens to the live tree.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from .campaign.checkpoint import (CampaignLock, CheckpointError, LockError, identity_alive, read_json,
                                  read_jsonl, request_stop)
from .campaign.freeze import (FreezeError, PlanError, load_campaign, load_plan, parse_duration,
                              resolve, verify_freeze)
from .campaign.records import Backend, check_record, load_backend

EXPECTED_ERRORS = (PlanError, FreezeError, LockError, CheckpointError, ValueError, OSError,
                   RuntimeError, KeyError, ImportError)


# --------------------------------------------------------------------------------------------
# Formatting helpers
# --------------------------------------------------------------------------------------------
def fmt_value(value) -> str:
    """A settings value in TOML-like syntax."""
    if value is None:
        return "none"
    return json.dumps(value)


def fmt_seconds(seconds) -> str:
    """``h:mm:ss`` (or 'unbounded')."""
    if seconds is None:
        return "unbounded"
    seconds = int(seconds)
    return f"{seconds // 3600}:{seconds // 60 % 60:02d}:{seconds % 60:02d}"


def table(rows: list[tuple]) -> str:
    """Left-aligned plain-text table; the first row is the header."""
    rows = [tuple(str(c) for c in row) for row in rows]
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    return "\n".join("  ".join(c.ljust(widths[i]) for i, c in enumerate(r)).rstrip() for r in rows)


def _seconds(text):
    try:
        return parse_duration(text)
    except PlanError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None


def _frozen_env(run_dir: Path) -> dict:
    source = run_dir / "source"
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(p for p in (str(source), os.environ.get("PYTHONPATH")) if p)
    return env


def _exec_coordinator(run_dir: Path, resume: bool, seconds) -> int:
    """Replace this process with the frozen coordinator (or run it here if not frozen)."""
    plan = verify_freeze(run_dir)
    backend = load_backend(plan["backend"])
    from .campaign.freeze import frozen_settings
    cfg = frozen_settings(run_dir, plan["campaign_settings"], backend.schema(),
                          plan["campaign_settings_sha256"]).view("campaign")
    if not cfg.run_frozen or not (run_dir / "source" / "xorsearch").is_dir():
        from .campaign.coordinator import run_coordinator
        return run_coordinator(run_dir, resume=resume, seconds=seconds)
    command = [sys.executable, "-P", "-m", "xorsearch", "_coordinator", str(run_dir)]
    if resume:
        command.append("--resume")
    if seconds is not None:
        command += ["--seconds", str(seconds)]
    sys.stdout.flush()
    os.execve(sys.executable, command, _frozen_env(run_dir))
    return 0  # not reached


# --------------------------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------------------------
def plan_text(plan: dict, settings: dict | None = None) -> str:
    """Human description of a resolved plan."""
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
                lines.append(f"  {key} = {fmt_value(value)}  # {origin}")
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
    print(f"\nfrozen into {out}\nstop with:   python -m xorsearch stop {out}\n"
          f"status with: python -m xorsearch status {out}\n")
    return _exec_coordinator(out, resume=False, seconds=args.seconds)


def cmd_resume(args) -> int:
    run_dir = Path(args.dir).resolve()
    owner = CampaignLock(run_dir).read()
    if owner and identity_alive(owner):
        raise LockError(f"{run_dir} is still running (coordinator pid {owner['pid']})")
    print(f"resuming {run_dir}")
    return _exec_coordinator(run_dir, resume=True, seconds=args.seconds)


def cmd_stop(args) -> int:
    run_dir = Path(args.dir).resolve()
    result = request_stop(run_dir, args.reason)
    if not result["stopped"]:
        print(result["message"])
        return 1
    print(f"stop requested ({args.reason}); workers checkpoint and exit")
    if args.wait:
        deadline = time.monotonic() + args.wait
        while time.monotonic() < deadline:
            if CampaignLock(run_dir).read().get("token") != result["owner_token"]:
                print("stopped")
                return 0
            time.sleep(0.5)
        print(f"still stopping after {args.wait:g} s")
        return 1
    return 0


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
    lines.append(f"workers alive {alive}/{len(plan['workers'])}   records "
                 f"{sum((status.get('records') or {}).values())}   rejected {status.get('rejected', 0)}")
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
                     s.get("steps", "-"), f"{s.get('steps_per_second', 0):.1f}",
                     f"{best['gates']}@{best['depth']}" if best else "-", s.get("records", "-"),
                     (s.get("updated_utc") or "-")[11:19]))
        if (run_dir / "workers" / w["id"] / "error.json").exists():
            err = read_json(run_dir / "workers" / w["id"] / "error.json")
            rows.append(("", "error:", err.get("message", "")[:70], "", "", "", ""))
    lines += ["", table(rows), "", f"events: {run_dir / 'campaign.jsonl'}   per worker: "
              f"{run_dir / 'workers' / '<id>'}"]
    return "\n".join(lines)


def cmd_status(args) -> int:
    run_dir = Path(args.dir).resolve()
    if args.json:
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
    from .config.settings import Settings, load_toml, parse_assignment, profile_path
    settings = Settings(_schema())
    for name in args.profile or ["default"]:
        path = profile_path(name)
        settings.apply(load_toml(path), f"profile:{path.stem}")
    for text in args.set:
        key, value = parse_assignment(text)
        settings.apply({key: value}, "cli")
    keys = sorted(settings.values)
    if args.prefix:
        keys = [k for k in keys if k == args.prefix or k.startswith(args.prefix + ".")]
    if args.non_default:
        keys = [k for k in keys if settings.origin(k) != "default"]
    for key in keys:
        print(f"{key} = {fmt_value(settings[key])}  # {settings.origin(key)}")
    if not keys:
        print("(no settings match)")
    return 0


def explain_text(schema, query: str) -> str:
    """Documentation of one knob, or a listing of every knob under a prefix."""
    if query in schema.knobs:
        knob = schema.knobs[query]
        section = schema.sections[query.rsplit(".", 1)[0]]
        kind = knob.value_type()
        kind = " or ".join(k.__name__ for k in kind) if isinstance(kind, tuple) else kind.__name__
        lines = [query, f"  {knob.doc}", f"  type: {kind}{' (nullable)' if knob.nullable else ''}",
                 f"  default: {fmt_value(knob.default)}"]
        if knob.min is not None or knob.max is not None:
            lines.append(f"  range: {fmt_value(knob.min)} .. {fmt_value(knob.max)}")
        if knob.choices:
            lines.append(f"  choices: {', '.join(map(str, knob.choices))}")
        lines.append(f"  section {section.path}: {section.doc}")
        lines.append(f"  change it: [set] \"{query}\" = ...  in a campaign file, or --set {query}=...")
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
                lines.append(f"  {name} = {fmt_value(knob.default)}  -- {knob.doc}")
    return "\n".join(lines)


def cmd_config_explain(args) -> int:
    print(explain_text(_schema(), args.key))
    return 0


def cmd_targets_list(args) -> int:
    backend = Backend()
    rows = [("name", "inputs", "outputs", "seeds")]
    for name in backend.catalog():
        try:
            target = backend.load_target(name)
            info = backend.target_json(target)
            rows.append((name, info.get("input_count"), len(info.get("rows", [])),
                         len(backend.target_seeds(target))))
        except EXPECTED_ERRORS as exc:
            rows.append((name, "?", "?", f"error: {exc}"))
    print(table(rows))
    return 0


def cmd_targets_show(args) -> int:
    backend = Backend()
    target = backend.load_target(args.name)
    info = backend.target_json(target)
    print(f"{args.name}: {info.get('name', '')}\n  inputs {info['input_count']}  outputs "
          f"{len(info['rows'])}\n  matrix sha256 {info['matrix_sha256']}")
    for label, seed in backend.target_seeds(target):
        check = backend.verify({k: v for k, v in seed.items() if k != "metadata"}, target, None)
        print(f"  seed {label}: {check.get('gate_count')} gates, depth {check.get('depth')}, "
              f"{'verified' if check.get('equivalent') else 'NOT EQUIVALENT'}")
    return 0


def cmd_quick(args) -> int:
    from .campaign.freeze import freeze
    from .campaign.worker import run_standalone
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = Path(args.out or Path("xorsearch-runs") / f"quick-{Path(args.target).stem}-{stamp}").resolve()
    group = {"name": "quick", "target": args.target, "count": 1, "objective": args.objective,
             "seeds": args.seeds or ["target"]}
    if args.depth_cap is not None:
        group["depth_cap"] = args.depth_cap
    if args.gate_limit is not None:
        group["gate_limit"] = args.gate_limit
    campaign = {"campaign": {"name": f"quick-{Path(args.target).stem}", "seed": args.seed,
                             "duration": args.seconds, "profiles": args.profile or ["default"],
                             "sharing": "off", "backend": args.backend},
                "workers": [group]}
    resolved = resolve(campaign, assignments=args.set)
    plan = freeze(resolved, out, freeze_source=False)
    wid = plan["workers"][0]["id"]
    print(f"quick run of {args.target} for {fmt_seconds(args.seconds)} into {out}  (Ctrl-C stops)")
    code = run_standalone(out, wid, args.seconds)
    status = read_json(out / "workers" / wid / "status.json", {}) or {}
    best = status.get("best")
    best_text = f"{best['gates']}@{best['depth']}" if best else "no record"
    print(f"{status.get('phase')}: {status.get('steps', 0)} steps, best {best_text}")
    if status.get("error"):
        print(f"error: {status['error']}")
    print(f"records: {out / 'workers' / wid / 'records'}\nreport:  python -m xorsearch report {out}")
    return code


def cmd_coordinator(args) -> int:
    run_dir = Path(args.dir).resolve()
    import xorsearch
    frozen = (run_dir / "source" / "xorsearch").resolve()
    here = Path(xorsearch.__file__).resolve().parent
    if frozen.is_dir() and here != frozen:
        plan = load_plan(run_dir)
        from .campaign.freeze import frozen_settings
        cfg = frozen_settings(run_dir, plan["campaign_settings"], load_backend(plan["backend"]).schema(),
                              plan["campaign_settings_sha256"]).view("campaign")
        if cfg.run_frozen:
            raise RuntimeError(f"coordinator imported xorsearch from {here}, not the frozen copy "
                               f"{frozen}; start campaigns with `xorsearch run/resume`")
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
    parser = argparse.ArgumentParser(prog="python -m xorsearch", description="Run, inspect and configure XOR-circuit search campaigns.",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="Guide: xorsearch/README.md.  Method: xorsearch/DESIGN.md.")
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    def add_set(p):
        p.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                       help="override any knob (TOML value syntax; repeatable), e.g. "
                            "--set sharing.mode=push --set moves.walk.hub.weight=3")

    p = sub.add_parser("run", help="freeze a campaign into a new run directory and start it",
                       description="Resolve CAMPAIGN.toml, freeze source + settings + targets into "
                                   "--out, then run the coordinator from the frozen copy.")
    p.add_argument("campaign", help="campaign TOML file")
    p.add_argument("--out", required=True, help="new (or empty) run directory")
    p.add_argument("--seconds", type=_seconds, help="session length, e.g. 3600 or 2h (default: "
                   "[campaign] duration; unbounded if absent)")
    add_set(p)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("resume", help="continue a stopped campaign from its checkpoints")
    p.add_argument("dir", help="run directory")
    p.add_argument("--seconds", type=_seconds, help="length of this session (default: plan duration)")
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
    p.add_argument("--target", help="target name or JSON path (circuit files only)")
    p.add_argument("--cap", type=int, help="real depth cap to check (circuit files only)")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("config", help="show resolved settings or explain knobs")
    config = p.add_subparsers(dest="config_command", required=True, metavar="show|explain")
    q = config.add_parser("show", help="resolved settings with the origin of each value")
    q.add_argument("--profile", action="append", help="profile name or TOML path (repeatable; "
                   "default: default)")
    q.add_argument("--non-default", action="store_true", help="only values not taken from defaults")
    q.add_argument("--prefix", help="only keys under this prefix, e.g. moves.walk")
    add_set(q)
    q.set_defaults(func=cmd_config_show)
    q = config.add_parser("explain", help="documentation, type, range and default of knobs")
    q.add_argument("key", help="a knob key (sharing.mode) or a prefix (sharing, moves.walk)")
    q.set_defaults(func=cmd_config_explain)

    p = sub.add_parser("targets", help="list or describe catalog targets")
    targets = p.add_subparsers(dest="targets_command", required=True, metavar="list|show")
    targets.add_parser("list", help="every catalog target").set_defaults(func=cmd_targets_list)
    q = targets.add_parser("show", help="one target: size, matrix hash, verified seeds")
    q.add_argument("name", help="catalog name or target JSON path")
    q.set_defaults(func=cmd_targets_show)

    p = sub.add_parser("quick", help="one in-process worker on a target, for experiments",
                       description="Run a single worker in this process (no coordinator, no "
                                   "sharing, live source) and write a small run directory.")
    p.add_argument("target", help="catalog name or target JSON path")
    p.add_argument("--seconds", type=_seconds, default=60.0, help="run length (default 60)")
    p.add_argument("--seed", type=int, default=0, help="RNG seed (default 0)")
    p.add_argument("--objective", default="gates", help="objective kind (default gates)")
    p.add_argument("--depth-cap", type=int, help="real depth cap")
    p.add_argument("--gate-limit", type=int, help="record gate limit")
    p.add_argument("--seeds", action="append", help="seed: 'target', 'root[:constructor]' or a "
                   "circuit JSON path (repeatable; default target)")
    p.add_argument("--profile", action="append", help="profile (repeatable; default: default)")
    p.add_argument("--out", help="run directory (default xorsearch-runs/quick-TARGET-TIME)")
    p.add_argument("--backend", default="xorsearch", help="alternative backend 'module:Class' "
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


def main(argv=None) -> int:
    """Parse arguments and run one command; returns the exit code (1 on a reported error)."""
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    except EXPECTED_ERRORS as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
