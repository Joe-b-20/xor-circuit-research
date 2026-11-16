"""Campaign coordinator: worker supervisor, global frontier, campaign pool, fleet diversity.

One coordinator process owns a run directory (``campaign.lock``).  It

* starts one worker subprocess per planned worker from the **frozen** source, with
  single-threaded numeric libraries and optional CPU pinning;
* every ``campaign.collect_seconds`` reads new lines of each ``workers/<id>/records.jsonl``,
  **re-verifies each new record independently** (file hash, binding, equivalence, cap, limit),
  updates the global (gates, depth) frontier per target and the campaign pool of distinct DAGs
  per frontier point, and writes ``status.json`` and ``pool/<target>.json``;
* every ``campaign.diversity_seconds`` logs ``fleet_diversity`` snapshots
  (``telemetry.metrics.diversity``) of the workers' best DAGs (``scope = "bests"``) and current
  chains (``scope = "chains"``), and raises ``collapse_alarm`` when the mean best-to-best Jaccard
  distance falls below ``campaign.collapse_distance`` (the forced-sharing failure mode in
  DESIGN.md section 1);
* stops in stages: ``STOP`` file -> ``stop_grace_seconds`` -> SIGTERM -> ``terminate_grace_seconds``
  -> SIGKILL -> ``kill_grace_seconds``; then a final collection, status and lock release.

Events go to ``campaign.jsonl`` through the telemetry ``EventLog`` (``worker = "coord"``; formats
in ``telemetry/schema.md`` section 5): ``start`` / ``resume`` / ``stop``, ``frontier`` (``point``,
``by``, ``improvement``, ``record``, ``dag``, ``kind``, ``removed``, ``frontier``), ``pool`` (per
changed point), ``fleet_diversity``, ``collapse_alarm`` / ``collapse_cleared``, ``worker_start``,
``worker_exit`` and ``record_rejected``.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import traceback
from pathlib import Path
from typing import Mapping

from ..config.schema import Knob, Section
from .checkpoint import (STOP_NAME, CampaignLock, atomic_bytes, atomic_json, read_json, read_jsonl,
                         stop_requested, utc_now)
from .freeze import (PACKAGE_ROOT, THREAD_ENV, available_cpus, environment, frozen_settings, frozen_target,
                     verify_freeze)
from .records import check_record, dominates, load_backend, score
from .sharing import PoolBook

KNOBS = Section("campaign", "Coordinator: supervision, collection, diversity and freezing.", {
    "collect_seconds": Knob(2.0, "Seconds between record collections, pool updates and status.json "
                            "writes.", min=0.1),
    "poll_seconds": Knob(0.2, "Supervisor loop sleep (reaction time to STOP, signals, worker exits).",
                         min=0.01),
    "diversity_seconds": Knob(60.0, "Seconds between fleet_diversity snapshots.", min=1),
    "collapse_distance": Knob(0.05, "collapse_alarm when the mean pairwise Jaccard distance between "
                              "worker best DAGs of one target falls below this.", min=0, max=1),
    "stop_grace_seconds": Knob(30.0, "After STOP, how long workers get to checkpoint and exit.", min=0),
    "terminate_grace_seconds": Knob(5.0, "After SIGTERM, how long before SIGKILL.", min=0),
    "kill_grace_seconds": Knob(2.0, "After SIGKILL, how long to wait for the exit status.", min=0),
    "pin_cpus": Knob(False, "Pin worker i to the i-th available logical CPU."),
    "allow_oversubscription": Knob(False, "Allow more workers than available logical CPUs."),
    "on_worker_failure": Knob("stop", "stop: a failed worker stops the campaign (fail fast). "
                              "continue: keep the others running.", choices=("stop", "continue")),
    "freeze_tests": Knob(False, "Include xorsearch/tests in the frozen source copy."),
    "freeze_attempts": Knob(3, "Times the source copy is redone when a file changes during it.",
                            min=1),
    "freeze_retry_seconds": Knob(1.0, "Wait between source copy attempts.", min=0),
    "git_status": Knob(True, "Run `git status --porcelain` at freeze time to record whether the "
                       "source tree was dirty (HEAD is read from .git without git)."),
    "run_frozen": Knob(True, "Execute the frozen source copy (reproducible). false runs the live "
                       "package; development only."),
})


# --------------------------------------------------------------------------------------------
# Collection: records -> frontier -> pool
# --------------------------------------------------------------------------------------------
class Collector:
    """Turns worker records into the verified global frontier and campaign pool.

    Independent of processes, so tests feed it synthetic record directories.  ``log`` is the
    telemetry ``EventLog`` (anything with ``write(ev, **fields)``).
    """

    def __init__(self, run_dir: Path, plan: Mapping, backend, targets: Mapping, per_point: int,
                 log, collapse_distance: float):
        self.run_dir = Path(run_dir)
        self.plan = plan
        self.backend = backend
        self.targets = targets
        self.log = log
        self.collapse_distance = collapse_distance
        self.specs = {w["id"]: w for w in plan["workers"]}
        self.offsets = {wid: 0 for wid in self.specs}
        self.frontier: dict[str, dict[tuple[int, int], dict]] = {key: {} for key in plan["targets"]}
        self.book = PoolBook(self.run_dir, per_point)
        self.improvements: dict[str, str] = {}   # engine candidate ref -> improvement id
        self.counts = {key: 0 for key in plan["targets"]}
        self.rejected = 0
        self.collapsed: dict[str, bool] = {}
        self.diversity: dict[str, dict] = {}

    def collect(self, announce: bool = True) -> int:
        """Read, verify and merge new records; returns how many were accepted.

        ``announce=False`` (first pass of a resumed session) rebuilds state without re-emitting
        events for points already announced in an earlier session.
        """
        verified = []
        for wid, spec in self.specs.items():
            lines, self.offsets[wid] = read_jsonl(self.run_dir / "workers" / wid / "records.jsonl",
                                                  self.offsets[wid])
            for entry in lines:
                if entry.get("link") == "improvement":
                    self.improvements[entry["ref"]] = entry["improvement"]
                if "path" not in entry:
                    continue
                key = spec["target"]
                _, reason = check_record(self.run_dir, entry, spec, self.plan, self.backend,
                                         self.targets[key])
                if reason:
                    self.rejected += 1
                    self.log.write("record_rejected", by=wid, record=entry.get("path"), reason=reason)
                    continue
                verified.append((key, entry))
        # Merge in discovery order so a point found by two workers within one collection
        # interval is credited to whichever found it first.
        verified.sort(key=lambda item: item[1].get("t") or 0.0)
        for key, entry in verified:
            self.counts[key] += 1
            self._merge(key, entry, announce)
        for key in sorted(self.book.changes):
            changes = self.book.write(key, self.plan["targets"][key]["matrix_sha256"])
            if not announce:
                continue
            for point, change in sorted(changes.items()):
                size, distinct = self.book.point_size(key, point)
                self.log.write("pool", target=key, point=score(*point), size=size, distinct=distinct,
                               **change)
        return len(verified)

    def _merge(self, key: str, entry: Mapping, announce: bool) -> None:
        frontier = self.frontier[key]
        point = (entry["gates"], entry["depth"])
        if point not in frontier and not any(dominates(q, point) for q in frontier):
            removed = sorted(q for q in frontier if dominates(point, q))
            for q in removed:
                del frontier[q]
            frontier[point] = dict(entry)
            if announce:
                self.log.write("frontier", target=key, point=score(*point), by=entry["worker"],
                               group=entry.get("group"), kind=entry.get("kind"),
                               improvement=self.improvements.get(entry.get("ref")),
                               ref=entry.get("ref"), move=entry.get("move"), record=entry["path"],
                               dag=entry["dag_sha256"], found_t=entry.get("t"),
                               removed=[score(*q) for q in removed],
                               frontier=[score(*q) for q in sorted(frontier)])
        self.book.add(key, entry)

    def frontier_summary(self) -> dict:
        """``{target: [{gates, depth, worker, improvement, path}]}`` for status.json."""
        return {key: [{"gates": g, "depth": d, "worker": e["worker"], "path": e["path"],
                       "improvement": self.improvements.get(e.get("ref"))}
                      for (g, d), e in sorted(points.items())]
                for key, points in self.frontier.items()}

    def fleet_diversity(self, announce: bool = True) -> dict:
        """Diversity of worker bests and chains per target, from ``workers/*/chain.json``."""
        out = {}
        for key in self.plan["targets"]:
            bests, chains, dags = {}, {}, set()
            for wid, spec in self.specs.items():
                if spec["target"] != key:
                    continue
                data = read_json(self.run_dir / "workers" / wid / "chain.json", {}) or {}
                if data.get("best_values") is not None:
                    bests[wid] = frozenset(data["best_values"])
                    dags.add(data.get("best_dag"))
                if data.get("chain_values") is not None:
                    chains[wid] = frozenset(data["chain_values"])
            best = self.backend.diversity(list(bests.values()))
            chain = self.backend.diversity(list(chains.values()))
            collapsed = len(bests) >= 2 and best["mean"] < self.collapse_distance
            out[key] = {"bests": best, "chains": chain, "distinct_best_dags": len(dags),
                        "workers": len(bests), "alarm": collapsed}
            if announce:
                for scope, data, members in (("bests", best, bests), ("chains", chain, chains)):
                    self.log.write("fleet_diversity", target=key, scope=scope, workers=list(members),
                                   alarm=collapsed and scope == "bests", **data)
                if collapsed != self.collapsed.get(key, False):
                    self.log.write("collapse_alarm" if collapsed else "collapse_cleared", target=key,
                                   mean=best["mean"], threshold=self.collapse_distance,
                                   distinct_best_dags=len(dags), workers=list(bests))
            self.collapsed[key] = collapsed
        self.diversity = out
        return out


# --------------------------------------------------------------------------------------------
# Supervisor
# --------------------------------------------------------------------------------------------
class Coordinator:
    """Runs (or resumes) a frozen campaign until its duration, a STOP, a signal or a failure."""

    def __init__(self, run_dir: str | Path, resume: bool = False, seconds: float | None = None,
                 backend=None):
        self.run_dir = Path(run_dir).resolve()
        self.plan = verify_freeze(self.run_dir)
        self.backend = backend or load_backend(self.plan["backend"])
        self.settings = frozen_settings(self.run_dir, self.plan["campaign_settings"],
                                        self.backend.schema(), self.plan["campaign_settings_sha256"])
        self.cfg = self.settings.view("campaign")
        self.resume = resume
        self.seconds = seconds if seconds is not None else self.plan.get("duration")
        if self.seconds is not None and not self.seconds > 0:
            raise ValueError("duration must be positive")
        has_checkpoints = any((self.run_dir / "workers").glob("*/checkpoint.json"))
        if has_checkpoints and not resume:
            raise ValueError("this run has checkpoints; continue it with `xorsearch resume`")
        self.targets = {key: frozen_target(self.run_dir, self.plan, key, self.backend)
                        for key in self.plan["targets"]}
        self.lock = CampaignLock(self.run_dir)
        self.children: dict[str, subprocess.Popen] = {}
        self.returncodes: dict[str, int | None] = {}
        self.interrupted: str | None = None

    # ---- helpers ---------------------------------------------------------------------------
    def _source_root(self) -> Path:
        frozen = self.run_dir / "source"
        return frozen if self.cfg.run_frozen and (frozen / "xorsearch").is_dir() else PACKAGE_ROOT.parent

    def _check_cpus(self) -> list[int]:
        cpus = available_cpus()
        count = len(self.plan["workers"])
        if count > len(cpus) and not self.cfg.allow_oversubscription:
            raise ValueError(f"{count} workers but only {len(cpus)} CPUs are available now")
        if self.cfg.pin_cpus and count > len(cpus):
            raise ValueError("campaign.pin_cpus needs one available CPU per worker")
        return cpus

    def _archive_errors(self, token: str) -> None:
        # Old failures stay readable, but this session's error files are unambiguous.
        for path in [self.run_dir / "error.json", *(self.run_dir / "workers").glob("*/error.json")]:
            if path.exists():
                atomic_bytes(self.run_dir / "errors" / token / path.relative_to(self.run_dir), path.read_bytes())
                path.unlink()

    def _spawn(self, spec: Mapping, token: str, cpu: int | None, log) -> dict:
        worker_dir = self.run_dir / "workers" / spec["id"]
        worker_dir.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, "-P", "-m", "xorsearch", "_worker", str(self.run_dir), spec["id"], token]
        if cpu is not None:
            command += ["--cpu", str(cpu)]
        source = str(self._source_root())
        env = {**os.environ, **THREAD_ENV, "PYTHONUNBUFFERED": "1", "PYTHONDONTWRITEBYTECODE": "1",
               "PYTHONPATH": os.pathsep.join(p for p in (source, os.environ.get("PYTHONPATH")) if p)}
        with (worker_dir / "launch.log").open("ab") as output:
            output.write(f"--- {utc_now()} session {token} pid {os.getpid()}\n".encode())
            output.flush()
            child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=output,
                                     env=env, cwd=str(self.run_dir))
        self.children[spec["id"]] = child
        log.write("worker_start", worker_id=spec["id"], pid=child.pid, cpu=cpu)
        return {"worker": spec["id"], "pid": child.pid, "cpu": cpu, "command": command, "pythonpath": source}

    def _shutdown(self, token: str, reason: str) -> list[dict]:
        atomic_json(self.run_dir / STOP_NAME, {"owner_token": token, "reason": reason,
                                               "requested_utc": utc_now()})
        forced = []
        for stage, grace in (("stop", self.cfg.stop_grace_seconds),
                             ("terminate", self.cfg.terminate_grace_seconds),
                             ("kill", self.cfg.kill_grace_seconds)):
            living = {wid: c for wid, c in self.children.items() if c.poll() is None}
            if not living:
                break
            for wid, child in living.items():
                if stage == "terminate":
                    child.terminate()
                elif stage == "kill":
                    child.kill()
                if stage != "stop":
                    forced.append({"worker": wid, "action": stage})
            deadline = time.monotonic() + grace
            while any(c.poll() is None for c in living.values()) and time.monotonic() < deadline:
                time.sleep(0.05)
        self.returncodes = {wid: c.poll() for wid, c in self.children.items()}
        return forced

    def _status(self, collector: Collector, phase: str, log, started: float, token: str, **extra) -> None:
        workers = {}
        for wid in collector.specs:
            child = self.children.get(wid)
            status = read_json(self.run_dir / "workers" / wid / "status.json", {}) or {}
            workers[wid] = {"pid": child.pid if child else None,
                            "alive": child is not None and child.poll() is None,
                            "returncode": child.poll() if child else None,
                            "phase": status.get("phase"), "steps": status.get("steps"),
                            "best": status.get("best"), "updated_utc": status.get("updated_utc")}
        atomic_json(self.run_dir / "status.json", {
            "phase": phase, "name": self.plan["name"], "run_id": self.plan["run_id"],
            "owner": self.lock.owner, "session": token, "t": log.now(), "updated_utc": utc_now(),
            "elapsed_seconds": time.monotonic() - started, "duration": self.seconds,
            "workers": workers, "frontier": collector.frontier_summary(),
            "pool": {key: collector.book.summary(key) for key in self.plan["targets"]},
            "records": collector.counts, "rejected": collector.rejected,
            "diversity": collector.diversity, **extra}, pretty=True)

    def _on_signal(self, signum, frame) -> None:
        self.interrupted = f"signal {signal.Signals(signum).name}"

    # ---- main loop -------------------------------------------------------------------------
    def run(self) -> int:
        """Supervise until done; returns 0 on a clean stop, 1 on any failure."""
        cpus = self._check_cpus()
        previous_status = read_json(self.run_dir / "status.json", {}) or {}
        owner = self.lock.acquire(self.run_dir.glob("workers/*/status.json"))
        token = owner["token"]
        started = time.monotonic()
        # Campaign time continues across sessions: t0 is the monotonic value at which t = 0, and
        # every process of this session (workers included, via the session file) shares it.
        t_offset = float(previous_status.get("t") or 0.0) if self.resume else 0.0
        t0 = started - t_offset
        session_path = self.run_dir / "sessions" / f"{token}.json"
        session = {"token": token, "owner": owner, "resume": self.resume, "seconds": self.seconds,
                   "started_utc": utc_now(), "t0": t0, "t_offset": t_offset,
                   "workers": []}
        try:
            atomic_json(session_path, session, pretty=True)
            log = self.backend.event_log(self.run_dir / "campaign.jsonl", self.settings, t0)
            collector = Collector(self.run_dir, self.plan, self.backend, self.targets,
                                  self.settings["sharing.pool_per_point"], log, self.cfg.collapse_distance)
        except BaseException:
            self.lock.release()  # nothing started yet; never leave a lock behind
            raise
        previous = {s: signal.signal(s, self._on_signal) for s in (signal.SIGINT, signal.SIGTERM)}
        failure, reason, forced = None, "duration elapsed", []
        try:
            self._archive_errors(token)
            if self.resume:
                collector.collect(announce=False)
            log.write("resume" if self.resume else "start", session=token, seconds=self.seconds,
                      workers=len(self.plan["workers"]), records=sum(collector.counts.values()),
                      run_id=self.plan["run_id"], source_hash=self.plan.get("source_manifest_sha256"),
                      settings_digest=self.settings.digest(), env=environment())
            for spec in self.plan["workers"]:
                cpu = cpus[spec["ordinal"] % len(cpus)] if self.cfg.pin_cpus else None
                session["workers"].append(self._spawn(spec, token, cpu, log))
            atomic_json(session_path, session, pretty=True)
            next_collect = next_diversity = time.monotonic()
            next_diversity += min(self.cfg.diversity_seconds, self.cfg.collect_seconds * 2)
            exited: set[str] = set()
            while True:
                if self.interrupted:
                    reason = self.interrupted
                    break
                stop = stop_requested(self.run_dir, token)
                if stop:
                    reason = f"stop requested: {stop.get('reason', '')}"
                    break
                if self.seconds is not None and time.monotonic() - started >= self.seconds:
                    break
                for wid, child in self.children.items():
                    # Ctrl-C reaches the whole process group: a worker may exit before our own
                    # handler's flag is seen; that is a stop, not a failure.
                    if self.interrupted:
                        break
                    if wid not in exited and child.poll() is not None:
                        exited.add(wid)
                        error = read_json(self.run_dir / "workers" / wid / "error.json")
                        log.write("worker_exit", worker_id=wid, returncode=child.returncode,
                                  error=error.get("message") if error else None)
                        if self.cfg.on_worker_failure == "stop":
                            raise RuntimeError(f"worker {wid} exited with code {child.returncode}"
                                               + (f": {error['message']}" if error else ""))
                if len(exited) == len(self.children):
                    raise RuntimeError("every worker has exited")
                now = time.monotonic()
                if now >= next_collect:
                    collector.collect()
                    self._status(collector, "running", log, started, token)
                    next_collect = time.monotonic() + self.cfg.collect_seconds
                if now >= next_diversity:
                    collector.fleet_diversity()
                    next_diversity = time.monotonic() + self.cfg.diversity_seconds
                time.sleep(self.cfg.poll_seconds)
        except BaseException as exc:  # noqa: BLE001 - always shut down and record why
            failure = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
            reason = "coordinator failure"
        finally:
            forced = self._shutdown(token, reason)
            if forced and failure is None:
                failure = {"type": "ForcedShutdown", "message": "some workers did not stop in time",
                           "actions": forced}
            bad = {wid: code for wid, code in self.returncodes.items() if code != 0}
            if bad and failure is None:
                failure = {"type": "WorkerFailure", "message": f"workers failed: {bad}", "returncodes": bad}
            try:
                collector.collect()
                collector.fleet_diversity()
            except Exception as exc:  # noqa: BLE001
                if failure is None:
                    failure = {"type": type(exc).__name__, "message": str(exc),
                               "traceback": traceback.format_exc()}
            if failure:
                atomic_json(self.run_dir / "error.json", failure, pretty=True)
            log.write("stop", session=token, reason=reason, returncodes=self.returncodes,
                      forced=forced, error=failure["message"] if failure else None)
            session.update({"finished_utc": utc_now(), "elapsed_seconds": time.monotonic() - started,
                            "stop_reason": reason, "returncodes": self.returncodes, "forced": forced,
                            "error": failure})
            atomic_json(session_path, session, pretty=True)
            self._status(collector, "failed" if failure else "stopped", log, started, token,
                         stop_reason=reason, error=failure)
            if hasattr(log, "close"):
                log.close()
            self.lock.release()
            for signum, handler in previous.items():
                signal.signal(signum, handler)
        if failure:
            print(f"campaign stopped with an error: {failure['message']}", file=sys.stderr)
        return 1 if failure else 0


def run_coordinator(run_dir: str | Path, resume: bool = False, seconds: float | None = None) -> int:
    """Entry point of ``python -m xorsearch _coordinator`` (after re-exec into the frozen source)."""
    return Coordinator(run_dir, resume=resume, seconds=seconds).run()

