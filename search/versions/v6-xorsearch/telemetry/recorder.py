"""Recorder: the worker's telemetry sink (events, epochs, dossiers, ring buffer, follow-ups).

Every improvement must be traceable to the move, sub-operations, phase, plateau, root and
worker that produced it, with the search state before, during and after (DESIGN.md section 4.5;
the evidence reports list what the old runs could not answer).  The engine computes metrics and
assembles dossiers; this module owns formats, files, timing, the proposal ring buffer and the
per-move counters.  Formats are specified in ``telemetry/schema.md`` (version ``SCHEMA_VERSION``).

Cost model
    ``Recorder.proposal`` runs on every proposal (thousands per second).  It stores a reference
    in a ring buffer and bumps a few list counters (per move and per sub-operation
    combination): O(1), no I/O, no allocation except a tuple for the combination key.  Files
    are written only on improvements, epochs and events, through ``EventLog``, which buffers
    lines and appends whole lines with one ``os.write`` on an ``O_APPEND`` descriptor, so a
    crash can lose at most the unflushed buffer and can cut at most the final line (readers
    skip it).

Improvements and verification
    ``improvement(dossier, verify=fn)`` writes the dossier once *before* calling ``fn(id)``
    (the campaign's verifying record writer), so the id is reserved on disk and a crash during
    verification leaves an honest, unverified dossier; then it stores the verdict in the
    dossier, rewrites it, and only then logs the ``improve`` event (which therefore carries
    ``verified``).  A rejected candidate keeps its dossier (``rejected: true``) for debugging
    but is not counted as an improvement.

Files in the worker directory
    ``events.jsonl``             current event log; rotated to ``events-000001.jsonl`` ...
    ``dossiers/<id>.json``       one per improvement, written atomically (tmp + rename)
    ``recorder.json``            sidecar with id sequences, cumulative counters and pending
                                 follow-ups so a resumed worker continues ids and timing

``EventLog`` is reused by the coordinator for ``campaign.jsonl``.  ``NullRecorder`` has the
same API and behaviour (ring, counters, ids, follow-ups) but writes no files; it keeps the
last ``telemetry.null_keep_events`` events in memory for tests and quick runs.
"""
from __future__ import annotations

import heapq
import json
import os
import platform
import re
import socket
import sys
import time
from bisect import bisect_right
from collections import deque
from operator import itemgetter
from pathlib import Path
from typing import Any, Callable, Iterator

from ..config.schema import Knob, Section
from . import metrics

SCHEMA_VERSION = 1

TELEMETRY_KNOBS = Section("telemetry", "Event logs, epochs, dossiers and the proposal ring.", {
    "epoch_seconds": Knob(60.0, "Seconds between epoch events (per-move counters are emitted "
                          "and reset at each epoch).", min=0.001),
    "ring_size": Knob(256, "Recent proposals kept for dossiers (move, phase, deltas, score, "
                      "accepted, neutral, components).", min=1),
    "trace_values_max": Knob(64, "Longest value list kept in a proposal trace (removed, "
                             "added, ...); longer lists are cut and their length kept in "
                             "<key>_n.", min=0),
    "followup_iterations": Knob([100, 1000, 10000], "Iterations after each improvement at "
                                "which a followup event summarises what happened since "
                                "(empty list disables).", kind=list),
    "dossier_detail": Knob("full", "full: values before/after and gates after. standard: drop "
                           "values_before (recoverable from values_after and symdiff). "
                           "minimal: no value lists or gates.",
                           choices=("full", "standard", "minimal")),
    "fsync": Knob("improve", "never: rely on the OS. improve: fsync dossiers, lifecycle, "
                  "improve/record lines and the sidecar. always: fsync every flush.",
                  choices=("never", "improve", "always")),
    "flush_seconds": Knob(5.0, "Longest time a buffered event line waits before it is written "
                          "(checked whenever an event is logged; epochs always flush).", min=0),
    "flush_bytes": Knob(65536, "Buffered bytes that force a write.", min=0),
    "rotate_mb": Knob(64.0, "Rotate an event log when it exceeds this many MiB (0 disables).",
                      min=0),
    "rotate_keep": Knob(0, "Rotated segments kept per log; older ones are deleted "
                        "(0 keeps all: the log is the record of the run).", min=0),
    "combo_counters": Knob(True, "Keep the per-move counters per (move, component combination) "
                           "too, so CPU and improvements can be attributed to sub-operations; "
                           "costs one tuple per proposal."),
    "combos_max": Knob(64, "Most component combinations listed per epoch (by proposals; "
                       "combinations with improvements are always listed).", min=0),
    "warn_dead_epochs": Knob(5, "Emit warn kind=move_dead when a move made proposals but none "
                             "were valid for this many consecutive epochs (0 disables).", min=0),
    "null_keep_events": Knob(1000, "Events a NullRecorder keeps in memory.", min=0),
})

# The registry imports only this module, so the metrics sections are re-exported here.
KNOBS = (TELEMETRY_KNOBS, *metrics.KNOBS)

# Per-move counter slots (lists, not dicts, so the hot path is index arithmetic).  Combinations
# of sub-operations use the same slots.
COUNTERS = ("proposals", "valid", "accepted", "neutral", "uphill",
            "improved_chain", "improved_worker", "work", "cpu_s")
_P, _V, _A, _N, _U, _IC, _IW, _W, _C = range(len(COUNTERS))
COMBO_COUNTERS = COUNTERS


def _zero_counters() -> list:
    return [0, 0, 0, 0, 0, 0, 0, 0, 0.0]


def verification_failed(result) -> bool:
    """Did a verifier reject a candidate?  (``ok`` or ``equivalent`` explicitly False; None,
    a skipped save or a missing verifier count as not rejected.)"""
    return isinstance(result, dict) and (result.get("ok") is False
                                         or result.get("equivalent") is False)

# Events written (and flushed) at once because they are rare and precious; the others
# (plateau, phase, followup, ...) wait in the buffer up to ``flush_seconds``.
FLUSH_NOW = frozenset({"start", "resume", "stop", "epoch", "improve", "restart", "record",
                       "pull", "warn", "frontier", "pool", "fleet_diversity"})
# Events fsynced under ``fsync = "improve"``.
SYNC_ON_IMPROVE = frozenset({"start", "resume", "stop", "improve", "record"})

#: Keys every event line already carries in its envelope; never copied from caller fields.
_ENVELOPE = frozenset({"v", "t", "utc", "worker", "it", "ev"})
_SEGMENT = re.compile(r"^(?P<stem>.+)-(?P<n>\d{6})(?P<suffix>\.jsonl)$")


# --------------------------------------------------------------------------- helpers

def knob_values(settings, section: Section) -> dict[str, Any]:
    """``{name: value}`` for one section, taking defaults for keys ``settings`` lacks.

    Tests build Settings over a few sections only (``for_sections``), and the coordinator may
    pass None, so a missing key is not an error here.
    """
    values = getattr(settings, "values", None) or {}
    out = {}
    for name, knob in section.knobs.items():
        out[name] = values.get(f"{section.path}.{name}", knob.default)
    return out


def _json_default(obj):
    """JSON fallback: sets become sorted lists, bytes hex, everything else ``str``."""
    if isinstance(obj, (set, frozenset)):
        try:
            return sorted(obj)
        except TypeError:
            return list(obj)
    if isinstance(obj, (bytes, bytearray)):
        return obj.hex()
    if isinstance(obj, tuple):
        return list(obj)
    return str(obj)


def dumps(obj) -> str:
    """Compact JSON used for every line and dossier (Python dialect: inf/nan allowed)."""
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False, default=_json_default)


def utc_iso(wall: float) -> str:
    """``2026-10-28T12:34:56.789Z`` for a ``time.time()`` value."""
    ms = int((wall % 1) * 1000)
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(wall)) + f".{ms:03d}Z"


def cap_trace(trace: dict | None, limit: int) -> dict | None:
    """Copy of a proposal trace with every list longer than ``limit`` cut to ``limit``.

    The original length is kept in ``<key>_n`` so the dossier still says how big the
    destroy/repair set was.  ``components`` is never cut (it names the sub-operations).
    """
    if not trace:
        return trace
    out = {}
    for key, value in trace.items():
        if isinstance(value, (list, tuple, set, frozenset)) and key != "components" \
                and len(value) > limit:
            seq = sorted(value) if isinstance(value, (set, frozenset)) else list(value)
            out[key] = seq[:limit]
            out[f"{key}_n"] = len(value)
        else:
            out[key] = value
    return out


def environment() -> dict:
    """Process environment for start/resume events (evidence: CPU, Python, hash seed and
    affinity at discovery were never recorded)."""
    env = {
        "python": sys.version.split()[0], "implementation": platform.python_implementation(),
        "executable": sys.executable, "platform": platform.platform(),
        "machine": platform.machine(), "processor": platform.processor(),
        "cpu_count": os.cpu_count(), "pid": os.getpid(), "argv": list(sys.argv),
        "hostname": socket.gethostname(), "cwd": os.getcwd(),
        "hash_seed": os.environ.get("PYTHONHASHSEED"),
    }
    if hasattr(os, "sched_getaffinity"):
        try:
            env["affinity"] = sorted(os.sched_getaffinity(0))
        except OSError:
            env["affinity"] = None
    return env


def log_segments(path: str | Path) -> list[Path]:
    """All segments of one event log in write order: rotated ``stem-NNNNNN.jsonl`` ascending,
    then the current ``stem.jsonl``."""
    path = Path(path)
    stem, suffix = path.stem, path.suffix
    rotated = []
    if path.parent.is_dir():
        for p in path.parent.iterdir():
            m = _SEGMENT.match(p.name)
            if m and m["stem"] == stem and m["suffix"] == suffix:
                rotated.append((int(m["n"]), p))
    out = [p for _, p in sorted(rotated)]
    if path.exists():
        out.append(path)
    return out


def iter_jsonl(path: str | Path, errors: list | None = None) -> Iterator[dict]:
    """Records of one JSONL file; undecodable lines (a crash-cut last line) are skipped and,
    when ``errors`` is a list, reported into it as ``(path, line number)``."""
    with open(path, "rb") as handle:
        for number, raw in enumerate(handle, 1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except ValueError:
                if errors is not None:
                    errors.append((str(path), number))
                continue
            if isinstance(rec, dict):
                yield rec


def read_log(path: str | Path, errors: list | None = None) -> Iterator[dict]:
    """Every record of a rotated event log, oldest segment first."""
    for seg in log_segments(path):
        yield from iter_jsonl(seg, errors)


def _write_atomic(path: Path, text: str, sync: bool) -> None:
    """Write a whole file via tmp + ``os.replace`` so readers never see a partial file."""
    tmp = path.with_name(f".{path.name}.tmp")
    with open(tmp, "w", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        if sync:
            os.fsync(handle.fileno())
    os.replace(tmp, path)
    if sync and hasattr(os, "O_DIRECTORY"):
        # The rename itself is durable only once the directory is synced (POSIX).
        try:
            fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        except OSError:
            return
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


class CampaignClock:
    """Monotonic seconds since campaign start plus UTC wall time.

    ``clock`` is a monotonic seconds source (default ``time.monotonic``; inject a fake in
    tests).  ``t0`` is the clock value at campaign start: the coordinator passes the same
    ``t0`` to every worker so their ``t`` share one origin (CLOCK_MONOTONIC is system-wide).
    Without ``t0`` the origin is "now minus ``elapsed``", which is how a resumed process
    continues its own timeline.
    """
    __slots__ = ("clock", "t0", "wall")

    def __init__(self, clock: Callable[[], float] | None = None, t0: float | None = None,
                 elapsed: float = 0.0, wall: Callable[[], float] | None = None):
        self.clock = clock or time.monotonic
        self.t0 = (self.clock() - elapsed) if t0 is None else t0
        self.wall = wall or time.time

    def now(self) -> float:
        """Seconds since campaign start."""
        return self.clock() - self.t0

    def utc(self) -> str:
        """Current UTC time, ISO 8601 with milliseconds."""
        return utc_iso(self.wall())


# --------------------------------------------------------------------------- EventLog

class EventLog:
    """Buffered, line-atomic, rotating JSONL writer for one event stream.

    ``write(ev, it=None, **fields)`` adds the envelope (``v``, ``t``, ``utc``, ``worker``,
    ``it``, ``ev``) and buffers the line; lines are written with one ``os.write`` of whole
    lines on an ``O_APPEND`` descriptor when the event is in ``FLUSH_NOW``, the buffer passes
    ``flush_bytes`` or the oldest buffered line is older than ``flush_seconds``.  ``fsync``
    follows the ``telemetry.fsync`` policy.  The coordinator uses this for ``campaign.jsonl``
    with ``worker="coord"``.
    """

    def __init__(self, path: str | Path, worker: str = "coord", *, settings=None,
                 clock: CampaignClock | Callable[[], float] | None = None, t0: float | None = None,
                 **overrides):
        cfg = knob_values(settings, TELEMETRY_KNOBS)
        cfg.update({k: v for k, v in overrides.items() if v is not None})
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.worker = worker
        self.clock = clock if isinstance(clock, CampaignClock) else CampaignClock(clock, t0)
        self.fsync = cfg["fsync"]
        self.flush_seconds = cfg["flush_seconds"]
        self.flush_bytes = cfg["flush_bytes"]
        self.rotate_bytes = int(cfg["rotate_mb"] * 1024 * 1024)
        self.rotate_keep = cfg["rotate_keep"]
        self._buf: list[bytes] = []
        self._buf_bytes = 0
        self._buf_since = 0.0            # clock time of the oldest buffered line
        self._sync_pending = False
        self._fd: int | None = None
        self._size = 0
        self._open()

    # -- file handling
    def _open(self) -> None:
        self._fd = os.open(self.path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        self._size = os.fstat(self._fd).st_size

    def _rotate(self) -> None:
        segments = log_segments(self.path)[:-1]
        last = int(_SEGMENT.match(segments[-1].name)["n"]) if segments else 0
        os.close(self._fd)
        self._fd = None
        target = self.path.with_name(f"{self.path.stem}-{last + 1:06d}{self.path.suffix}")
        os.replace(self.path, target)
        self._open()
        if self.rotate_keep:
            for old in log_segments(self.path)[:-1][:-self.rotate_keep]:
                os.remove(old)

    # -- writing
    def write(self, ev: str, it: int | None = None, *, flush: bool | None = None,
              **fields) -> dict:
        """Log one event; returns the full record (envelope + fields)."""
        record = {"v": SCHEMA_VERSION, "t": round(self.clock.now(), 6), "utc": self.clock.utc(),
                  "worker": self.worker, "it": it, "ev": ev}
        record.update(fields)
        self.append(record, flush=ev in FLUSH_NOW if flush is None else flush,
                    sync=self._wants_sync(ev))
        return record

    def _wants_sync(self, ev: str) -> bool:
        return self.fsync == "always" or (self.fsync == "improve" and ev in SYNC_ON_IMPROVE)

    def append(self, record: dict, *, flush: bool = False, sync: bool = False) -> None:
        """Buffer an already enveloped record (one line)."""
        if self._fd is None:
            raise ValueError(f"event log {self.path} is closed")
        line = (dumps(record) + "\n").encode("utf-8")
        if not self._buf:
            self._buf_since = self.clock.clock()
        self._buf.append(line)
        self._buf_bytes += len(line)
        self._sync_pending |= sync
        if (flush or self._buf_bytes >= self.flush_bytes
                or self.clock.clock() - self._buf_since >= self.flush_seconds):
            self.flush()

    def flush(self, sync: bool = False) -> None:
        """Write buffered lines (one write of whole lines), fsync if due, rotate if large."""
        if self._fd is None:
            return
        if self._buf:
            data = b"".join(self._buf)
            self._buf.clear()
            self._buf_bytes = 0
            view = memoryview(data)
            while view:  # os.write may write less than asked; finish the batch
                n = os.write(self._fd, view)
                view = view[n:]
            self._size += len(data)
        if sync or self._sync_pending or self.fsync == "always":
            if self.fsync != "never":
                os.fsync(self._fd)
            self._sync_pending = False
        if self.rotate_bytes and self._size >= self.rotate_bytes:
            self._rotate()

    def now(self) -> float:
        """Seconds since campaign start (this log's clock)."""
        return self.clock.now()

    def close(self) -> None:
        """Flush and close (idempotent)."""
        if self._fd is None:
            return
        self.flush(sync=self.fsync != "never")
        os.close(self._fd)
        self._fd = None


# --------------------------------------------------------------------------- Recorder

class Recorder:
    """Telemetry for one worker (DESIGN.md section 4.5).

    Call order expected from the engine: ``begin`` once; per proposal ``proposal(rec)``
    (then, for a new worker best, ``improvement(dossier, verify=...)``); ``event(...)`` for
    restarts, plateaus, phases, sharing; ``epoch(fields)`` whenever ``epoch_due()``;
    ``close()``.  ``set_epoch_source(fn)`` lets the engine supply its fields for the final
    partial epoch that ``close`` writes.

    ``rec`` keys read by ``proposal``: ``it``, ``move``, ``accepted``, ``neutral``,
    ``d_gates``, ``d_depth``, ``gates``, ``depth``, ``work``, ``components`` (required by the
    contract) and optionally ``valid`` (default True: the move returned a proposal),
    ``uphill`` (default: accepted, not neutral and lexicographically worse in (gates, depth)),
    ``improved_chain``, ``improved_worker`` (default False), ``phase`` (shown in the ring) and
    ``cpu_s`` (seconds spent; when no proposal carries it, epoch CPU is apportioned to moves by
    work and ``cpu_est`` is set).  The recorder keeps a reference to ``rec`` in the ring: do
    not mutate it afterwards.

    ``t0``/``clock``/``wall`` make time injectable (see ``CampaignClock``).
    """

    #: subclasses that write no files set this False
    writes_files = True

    def __init__(self, directory, worker_id: str, settings=None, clock=None, *,
                 t0: float | None = None, wall: Callable[[], float] | None = None,
                 process_time: Callable[[], float] | None = None):
        cfg = knob_values(settings, TELEMETRY_KNOBS)
        self.cfg = cfg
        self.settings = settings
        self.worker = str(worker_id)
        self.directory = Path(directory) if directory is not None else None
        self._cpu = process_time or time.process_time
        self._epoch_seconds = cfg["epoch_seconds"]
        self._trace_max = cfg["trace_values_max"]
        fu = cfg["followup_iterations"]
        self._horizons = sorted({int(h) for h in (fu if isinstance(fu, list) else [fu]) if h > 0})
        self._detail = cfg["dossier_detail"]
        self._combo_on = cfg["combo_counters"]
        self._combos_max = cfg["combos_max"]
        self._warn_dead = cfg["warn_dead_epochs"]

        # Ring buffer of proposal dicts (references; formatted lazily by ring()).
        self._ring_n = cfg["ring_size"]
        self._ring: list = [None] * self._ring_n
        self._ring_i = 0

        # Counters of the current epoch per (move, component combination) -- the only ones
        # the hot path touches; per-move counters are their sums (``_per_move``) -- and
        # cumulative per-move totals of finished epochs.
        self._combos: dict[tuple, list] = {}
        self._totals: dict[str, list] = {}
        self._dead_streak: dict[str, int] = {}

        # Search position as seen by the recorder.
        self._it = 0
        self._last_accepted: dict | None = None
        self._last_chain_improve_it = 0
        self._best: dict | None = None            # latest worker best score {gates, depth}
        self._last_improvement: dict | None = None  # {id, it, t, chain}
        self._improvements = 0
        self._restarts = 0

        # Id sequences.
        self._seq = 0          # improvements / dossiers
        self._chain_seq = 0
        self._plateau_seq = 0
        self._epoch_seq = 0
        self._chain: dict = {}

        # Follow-ups: heap of (due_it, seq, improvement id, horizon, snapshot).  While any is
        # pending, the iterations of later chain improvements and restarts and the later
        # worker improvements are logged so a follow-up can say what happened *first* after
        # its improvement (pruned to what pending follow-ups still need).
        self._followups: list = []
        self._next_followup = float("inf")
        self._chain_its: list[int] = []
        self._restart_its: list[int] = []
        self._imp_log: list[tuple] = []           # (it, t, id)

        # Engine-side epoch fields for the final partial epoch (``set_epoch_source``).
        self._epoch_source: Callable[[], dict] | None = None

        elapsed = 0.0
        sidecar = {}
        if self.writes_files:
            self.directory.mkdir(parents=True, exist_ok=True)
            (self.directory / "dossiers").mkdir(exist_ok=True)
            sidecar = self._recover()
            elapsed = sidecar.get("t", 0.0)
        self.clock = clock if isinstance(clock, CampaignClock) else \
            CampaignClock(clock, t0, elapsed=elapsed, wall=wall)
        self._restore_sidecar(sidecar)
        self._log = self._open_log()
        self._epoch_clock0 = self.clock.clock()
        self._epoch_t0 = self.clock.now()
        self._epoch_cpu0 = self._cpu()
        self._epoch_it0 = self._it
        self._begin_t = self._epoch_t0
        self._begin_cpu = self._epoch_cpu0
        self._closed = False
        self._stopped = False

    # ------------------------------------------------------------------ files
    def _open_log(self):
        return EventLog(self.directory / "events.jsonl", self.worker, settings=self.settings,
                        clock=self.clock)

    def _emit(self, ev: str, it, fields: dict, flush: bool | None = None) -> dict:
        """Write one event through the log (subclasses redirect this).

        Envelope keys belong to the envelope: a caller's ``it`` (or ``t``, ``ev`` ...) inside
        ``fields`` would otherwise collide with the log's own arguments.
        """
        if not _ENVELOPE.isdisjoint(fields):
            fields = {k: v for k, v in fields.items() if k not in _ENVELOPE}
        return self._log.write(ev, it, flush=flush, **fields)

    def _sync_files(self) -> bool:
        return self.cfg["fsync"] != "never"

    def _recover(self) -> dict:
        """Continue id sequences and the timeline of an existing worker directory.

        Sources, highest wins: the sidecar (written at epochs, restarts, improvements, close),
        the dossier file names and the last megabyte of the current event log (covers plateau
        and chain ids issued after the last sidecar write)."""
        state: dict = {}
        side = self.directory / "recorder.json"
        if side.exists():
            try:
                state = json.loads(side.read_text(encoding="utf-8"))
            except ValueError:
                state = {}
        prefix = f"{self.worker}-"
        for p in (self.directory / "dossiers").glob(f"{prefix}*.json"):
            tail = p.stem[len(prefix):]
            if tail.isdigit():
                state["seq"] = max(state.get("seq", 0), int(tail))
        segments = log_segments(self.directory / "events.jsonl")
        if segments:
            last = segments[-1]
            with open(last, "rb") as handle:
                size = handle.seek(0, os.SEEK_END)
                handle.seek(max(0, size - (1 << 20)))
                lines = handle.read().splitlines()
            id_re = re.compile(re.escape(prefix) + r"(c|p)(\d+)$")
            for raw in lines:
                try:
                    rec = json.loads(raw)
                except ValueError:
                    continue
                if not isinstance(rec, dict):
                    continue
                state["t"] = max(state.get("t", 0.0), rec.get("t") or 0.0)
                if isinstance(rec.get("it"), int):
                    state["it"] = max(state.get("it", 0), rec["it"])
                for key in ("chain", "id"):
                    m = id_re.match(str(rec.get(key, "")))
                    if m:
                        name = "chain_seq" if m[1] == "c" else "plateau_seq"
                        state[name] = max(state.get(name, 0), int(m[2]))
        return state

    def _restore_sidecar(self, state: dict) -> None:
        self._seq = state.get("seq", 0)
        self._chain_seq = state.get("chain_seq", 0)
        self._plateau_seq = state.get("plateau_seq", 0)
        self._epoch_seq = state.get("epoch_seq", 0)
        self._it = state.get("it", 0)
        self._improvements = state.get("improvements", 0)
        self._restarts = state.get("restarts", 0)
        self._chain = state.get("chain", {}) or {}
        self._best = state.get("best")
        self._last_improvement = state.get("last_improvement")
        self._totals = {k: list(v) for k, v in state.get("totals", {}).items()}
        for item in state.get("followups", []):
            heapq.heappush(self._followups, tuple(item))
        self._next_followup = self._followups[0][0] if self._followups else float("inf")
        logs = state.get("followup_logs") or {}
        self._chain_its = [int(x) for x in logs.get("chain", ())]
        self._restart_its = [int(x) for x in logs.get("restart", ())]
        self._imp_log = [tuple(x) for x in logs.get("improvements", ())]

    def checkpoint(self) -> dict:
        """JSON-safe recorder state (also what the sidecar holds).  Workers may store it in
        their engine checkpoint; ``restore`` puts it back."""
        return {"v": SCHEMA_VERSION, "t": self.now(), "it": self._it, "seq": self._seq,
                "chain_seq": self._chain_seq, "plateau_seq": self._plateau_seq,
                "epoch_seq": self._epoch_seq, "improvements": self._improvements,
                "restarts": self._restarts, "chain": self._chain, "best": self._best,
                "last_improvement": self._last_improvement,
                "totals": self._cumulative(), "followups": [list(f) for f in self._followups],
                "followup_logs": {"chain": self._chain_its, "restart": self._restart_its,
                                  "improvements": [list(x) for x in self._imp_log]}}

    def restore(self, data: dict) -> None:
        """Adopt a ``checkpoint()``; id sequences only move forward."""
        data = dict(data)
        for key in ("seq", "chain_seq", "plateau_seq", "epoch_seq"):
            data[key] = max(data.get(key, 0), getattr(self, f"_{key}"))
        self._followups = []
        self._restore_sidecar(data)

    def _write_sidecar(self) -> None:
        if self.writes_files:
            _write_atomic(self.directory / "recorder.json", dumps(self.checkpoint()),
                          self._sync_files())

    # ------------------------------------------------------------------ lifecycle
    def begin(self, kind: str, info: dict) -> None:
        """Log ``start`` or ``resume`` with environment and settings digest.

        ``info`` (worker-supplied) should hold ``seed``, ``source_hash``, ``target``,
        ``objective`` and, when known, ``root`` and ``source`` of the first chain."""
        if kind not in ("start", "resume"):
            raise ValueError(f"begin kind must be start or resume, not {kind!r}")
        info = dict(info or {})
        fields = {"env": environment()}
        digest = getattr(self.settings, "digest", None)
        if callable(digest):
            fields["settings_digest"] = digest()
        if kind == "start" or not self._chain:
            self._new_chain(info.get("source", "seed"), info.get("root"), info.get("parent"),
                            info.get("chain"))
        fields["chain"] = self._chain["id"]
        it = info.pop("it", self._it)
        fields.update(info)
        self._emit(kind, it, fields)

    def set_epoch_source(self, source: Callable[[], dict] | None) -> None:
        """Register ``source() -> dict`` (the engine's ``epoch_fields``) for the final partial
        epoch written by ``close``; without it a short run's only epoch would hold recorder
        counters but no phase, weights, plateau or diversity."""
        self._epoch_source = source

    def close(self, reason: str = "normal", **fields) -> None:
        """Emit a final partial epoch (counters are never lost), pending follow-ups as
        incomplete, a ``stop`` event with cumulative totals, then flush and close."""
        if self._closed:
            return
        if self._combos:
            extra = {}
            if self._epoch_source is not None:
                try:
                    extra = dict(self._epoch_source())
                except Exception as exc:  # noqa: BLE001 - a broken engine must not lose `stop`
                    extra = {"source_error": f"{type(exc).__name__}: {exc}"}
            extra["partial"] = True
            self.epoch(extra)
        for due, _, fid, horizon, snap in sorted(self._followups):
            self._emit("followup", self._it, self._followup_fields(fid, horizon, snap, False))
        if not self._stopped:
            stop = {"reason": reason, "best": self._best, "improvements": self._improvements,
                    "restarts": self._restarts,
                    "wall_s": self.now() - self._begin_t, "cpu_s": self._cpu() - self._begin_cpu,
                    "totals": {m: dict(zip(COUNTERS, c)) for m, c in self._cumulative().items()}}
            stop.update(fields)
            self._emit("stop", self._it, stop)
            self._stopped = True
        self._write_sidecar()
        self._closed = True
        if self._log is not None:
            self._log.close()

    def now(self) -> float:
        """Seconds since campaign start (monotonic)."""
        return self.clock.now()

    @property
    def chain_id(self) -> str | None:
        """Id of the current chain (``<worker>-cNNNN``), used by the engine to label records."""
        return self._chain.get("id")

    # ------------------------------------------------------------------ hot path
    def proposal(self, rec: dict) -> None:
        """Account one proposal: ring buffer and the counters of its (move, sub-operation
        combination).  O(1), no I/O.

        The only extra work is a single comparison against the next follow-up iteration;
        when one falls due (rarely) its line is buffered like any other event."""
        i = self._ring_i
        self._ring[i] = rec
        i += 1
        self._ring_i = 0 if i == self._ring_n else i
        it = rec["it"]
        self._it = it
        comps = rec.get("components") if self._combo_on else None
        key = (rec["move"], tuple(comps) if comps else ())
        c = self._combos.get(key)
        if c is None:
            c = self._combos[key] = _zero_counters()
        c[0] += 1                                       # _P
        c[7] += rec["work"]                             # _W
        cpu = rec.get("cpu_s")
        if cpu:
            c[8] += cpu                                 # _C
        if rec.get("valid", True):
            c[1] += 1                                   # _V
        if rec["accepted"]:
            self._last_accepted = rec
            c[2] += 1                                   # _A
            if rec["neutral"]:
                c[3] += 1                               # _N
            else:
                up = rec.get("uphill")
                if up is None:
                    dg = rec["d_gates"]
                    up = dg > 0 or (dg == 0 and rec["d_depth"] > 0)
                if up:
                    c[4] += 1                           # _U
            if rec.get("improved_chain"):
                c[5] += 1                               # _IC
                self._last_chain_improve_it = it
                if self._followups:
                    self._chain_its.append(it)
            if rec.get("improved_worker"):
                c[6] += 1                               # _IW
        if it >= self._next_followup:
            self.pending_followups(it)

    def ring(self) -> list[dict]:
        """The last ``ring_size`` proposals, oldest first, as compact dicts (the search state
        *during* an improvement: which moves ran, what they did to the score)."""
        i = self._ring_i
        out = []
        for r in self._ring[i:] + self._ring[:i]:
            if r is None:
                continue
            out.append({"it": r["it"], "move": r["move"], "phase": r.get("phase"),
                        "valid": r.get("valid", True), "accepted": r["accepted"],
                        "neutral": r.get("neutral", False), "d_gates": r.get("d_gates"),
                        "d_depth": r.get("d_depth"), "gates": r.get("gates"),
                        "depth": r.get("depth"), "components": r.get("components")})
        return out

    @staticmethod
    def ring_summary(ring: list[dict]) -> dict:
        """Aggregate of a ring (dossier ``ring_summary``): span, accept/neutral/uphill counts,
        proposals and accepts per move, and the score range the chain visited."""
        if not ring:
            return {"proposals": 0}
        by_move: dict[str, list[int]] = {}
        accepted = neutral = uphill = valid = 0
        gates = [r["gates"] for r in ring if r.get("gates") is not None]
        for r in ring:
            m = by_move.setdefault(r["move"], [0, 0])
            m[0] += 1
            valid += bool(r.get("valid", True))
            if r["accepted"]:
                m[1] += 1
                accepted += 1
                if r.get("neutral"):
                    neutral += 1
                elif (r.get("d_gates") or 0) > 0:
                    uphill += 1
        return {"proposals": len(ring), "first_it": ring[0]["it"], "last_it": ring[-1]["it"],
                "valid": valid, "accepted": accepted, "neutral": neutral, "uphill": uphill,
                "gates_min": min(gates, default=None), "gates_max": max(gates, default=None),
                "by_move": {m: {"proposals": p, "accepted": a}
                            for m, (p, a) in sorted(by_move.items())}}

    # ------------------------------------------------------------------ counters
    def _per_move(self) -> dict[str, list]:
        """This epoch's per-move counters: sums over the move's combinations."""
        out: dict[str, list] = {}
        for (m, _), c in self._combos.items():
            t = out.get(m)
            if t is None:
                out[m] = list(c)
            else:
                for j, x in enumerate(c):
                    t[j] += x
        return out

    def _cumulative(self) -> dict[str, list]:
        """Cumulative per-move counters including the open epoch."""
        out = {m: list(c) for m, c in self._totals.items()}
        for m, c in self._per_move().items():
            t = out.setdefault(m, _zero_counters())
            for j, x in enumerate(c):
                t[j] += x
        return out

    def _global(self) -> dict:
        """Fleet-of-moves totals used for follow-up differences."""
        g = _zero_counters()
        for c in self._cumulative().values():
            for j, x in enumerate(c):
                g[j] += x
        return dict(zip(COUNTERS, g))

    def epoch_due(self) -> bool:
        """True once ``telemetry.epoch_seconds`` have passed since the last epoch."""
        return self.clock.clock() - self._epoch_clock0 >= self._epoch_seconds

    def epoch(self, fields: dict) -> None:
        """Emit an ``epoch`` event: engine ``fields`` plus this epoch's per-move and
        per-combination counters, iterations, CPU; then reset the epoch counters."""
        t = self.now()
        cpu = self._cpu()
        dt = t - self._epoch_t0
        cpu_epoch = cpu - self._epoch_cpu0
        its = self._it - self._epoch_it0
        combos = self._combos
        measured = sum(c[_C] for c in combos.values())
        cpu_est = bool(combos) and not measured
        if cpu_est:
            # No proposal carried cpu_s: apportion process CPU by work share (marked estimate).
            work = sum(c[_W] for c in combos.values())
            for c in combos.values():
                c[_C] = cpu_epoch * (c[_W] / work if work else 1 / len(combos))
        counters = self._per_move()
        moves = {}
        for m, c in sorted(counters.items()):
            d = dict(zip(COUNTERS, c))
            d["cpu_s"] = round(d["cpu_s"], 6)
            moves[m] = d
        self._epoch_seq += 1
        record = dict(fields or {})
        record.update({"epoch": self._epoch_seq, "dt": round(dt, 6), "its": its,
                       "it_rate": its / dt if dt > 0 else 0.0, "cpu_s": round(cpu_epoch, 6),
                       "cpu_est": cpu_est, "moves": moves,
                       "combos": self._combo_rows() if self._combo_on else []})
        if self._best is not None:
            record.setdefault("best", self._best)
        if self._last_accepted is not None:
            record.setdefault("chain", {"gates": self._last_accepted.get("gates"),
                                        "depth": self._last_accepted.get("depth")})
        record.setdefault("chain_id", self._chain.get("id"))
        self._emit("epoch", self._it, record)
        # Fold into cumulative totals and reset.
        for m, c in counters.items():
            tot = self._totals.setdefault(m, [0] * len(COUNTERS))
            for j, x in enumerate(c):
                tot[j] += x
        self._check_dead(counters)
        self._combos = {}
        self._epoch_clock0 = self.clock.clock()
        self._epoch_t0 = t
        self._epoch_cpu0 = cpu
        self._epoch_it0 = self._it
        self._write_sidecar()

    def _combo_rows(self) -> list[dict]:
        """Epoch ``combos``: every combination that improved, then the busiest."""
        rows = []
        for (m, comp), k in self._combos.items():
            row = {"move": m, "components": list(comp)}
            row.update(zip(COMBO_COUNTERS, k))
            row["cpu_s"] = round(row["cpu_s"], 6)
            rows.append(row)
        rows.sort(key=lambda r: (-(r["improved_worker"] + r["improved_chain"]), -r["proposals"]))
        keep = [r for r in rows if r["improved_chain"] or r["improved_worker"]]
        rest = [r for r in rows if not (r["improved_chain"] or r["improved_worker"])]
        return keep + rest[:max(0, self._combos_max - len(keep))]

    def _check_dead(self, counters: dict) -> None:
        """Warn when a move keeps proposing nothing valid (the old cross-pollination died
        silently for a whole campaign)."""
        if not self._warn_dead:
            return
        for m, c in counters.items():
            if c[_P] and not c[_V]:
                n = self._dead_streak.get(m, 0) + 1
                self._dead_streak[m] = n
                if n == self._warn_dead:
                    self.event("warn", kind="move_dead", move=m, epochs=n,
                               message=f"{m}: {n} epochs with proposals but none valid")
            else:
                self._dead_streak.pop(m, None)

    # ------------------------------------------------------------------ improvements
    def improvement(self, dossier: dict, verify: Callable[[str], Any] | None = None) -> str:
        """Assign an id, write ``dossiers/<id>.json`` and the ``improve`` event; returns the id.

        Fills when absent: ``it``, ``chain`` (id, root, source, start), ``lineage.parent``
        (previous improvement on this chain, else the chain's parent), ``ring`` and
        ``ring_summary``, ``timing`` (since previous improvement / chain start), ``symdiff``;
        caps trace lists; applies ``telemetry.dossier_detail``; schedules follow-ups.

        ``verify(id) -> result`` (optional) verifies and saves the record behind the
        improvement.  The dossier is written first (unsynced: it reserves the id, so a crash
        during verification leaves an unverified dossier and never a reused id), then
        ``result`` becomes ``verification`` and the dossier is written again.  When
        ``verification_failed(result)`` the dossier gets ``rejected: true`` and the candidate
        is not counted: no ``improve`` event, no follow-ups, the best is unchanged."""
        self._seq += 1
        did = f"{self.worker}-{self._seq:06d}"
        rel = f"dossiers/{did}.json"
        t = self.now()
        totals = self._global()
        cpu = totals["cpu_s"]                  # CPU spent in moves, continuous across resumes
        d = self._assemble_dossier(did, t, cpu, dossier)
        it = d["it"]
        if verify is not None:
            self._store_dossier(rel, d, sync=False)
            result = verify(did)
            d["verification"] = result
            if verification_failed(result):
                d["rejected"] = True
                self._store_dossier(rel, d)
                self._write_sidecar()
                return did
        self._store_dossier(rel, d)
        self._emit("improve", it, self._improve_fields(d, rel))

        # Bookkeeping for lineage, follow-ups and the sidecar.  A frontier point is not a new
        # best: ``best`` (epochs, follow-ups, stop) stays the worker best.
        self._improvements += 1
        self._last_improvement = {"id": did, "it": it, "t": t, "cpu": cpu,
                                  "chain": d["chain"].get("id")}
        if d.get("after") is not None and d.get("kind") != "frontier":
            self._best = d["after"]
        if self._followups:
            self._imp_log.append((it, round(t, 6), did))
        if self._horizons:
            snap = totals
            snap.update(it=it, t=t, improvements=self._improvements, restarts=self._restarts,
                        chain=d["chain"].get("id"), after=d.get("after"), kind=d.get("kind"))
            for h in self._horizons:
                heapq.heappush(self._followups, (it + h, self._seq, did, h, snap))
            self._next_followup = self._followups[0][0]
        self._write_sidecar()
        return did

    def _assemble_dossier(self, did: str, t: float, cpu: float, dossier: dict) -> dict:
        """The dossier as written: recorder keys, engine keys, filled defaults (see
        ``improvement``)."""
        it = dossier.get("it", self._it)
        d = {"v": SCHEMA_VERSION, "id": did, "worker": self.worker, "t": round(t, 6),
             "utc": self.clock.utc(), "it": it}
        for key, value in dossier.items():
            d.setdefault(key, value)
        chain = dict(self._chain)
        chain.update(d.get("chain") or {})
        d["chain"] = chain
        lineage = dict(d.get("lineage") or {})
        last = self._last_improvement
        if "parent" not in lineage:
            if last and last.get("chain") == chain.get("id"):
                lineage["parent"] = last["id"]
            else:
                lineage["parent"] = chain.get("parent")
        lineage.setdefault("chain_origin", chain.get("source"))
        d["lineage"] = lineage
        if "trace" in d:
            d["trace"] = cap_trace(d["trace"], self._trace_max)
        d.setdefault("move", (d.get("trace") or {}).get("move"))
        d.setdefault("ring", self.ring())
        timing = dict(d.get("timing") or {})
        timing.setdefault("it_since_prev", it - last["it"] if last else None)
        timing.setdefault("s_since_prev", round(t - last["t"], 6) if last else None)
        if last and last.get("cpu") is not None:
            timing.setdefault("cpu_s_since_prev", round(cpu - last["cpu"], 6))
        if "start_it" in chain:
            timing.setdefault("it_since_root", it - chain["start_it"])
            timing.setdefault("s_since_root", round(t - chain["start_t"], 6))
            if chain.get("start_cpu") is not None:
                timing.setdefault("cpu_s_since_root", round(cpu - chain["start_cpu"], 6))
        d["timing"] = timing
        vb, va = d.get("values_before"), d.get("values_after")
        if "symdiff" not in d and vb is not None and va is not None:
            d["symdiff"] = metrics.symmetric_difference(vb, va)
        if "ring_summary" not in d:
            d["ring_summary"] = self.ring_summary(d["ring"])
        self._apply_detail(d)
        d["followups_at"] = [it + h for h in self._horizons]
        return d

    def _store_dossier(self, rel: str, d: dict, sync: bool | None = None) -> None:
        """Write one dossier atomically (NullRecorder keeps it in memory instead); ``sync``
        defaults to the ``telemetry.fsync`` policy."""
        _write_atomic(self.directory / rel, dumps(d),
                      self._sync_files() if sync is None else sync)

    def _apply_detail(self, d: dict) -> None:
        if self._detail == "full":
            return
        d.pop("values_before", None)
        if self._detail == "minimal":
            for key in ("values_after", "gates_after", "outputs"):
                d.pop(key, None)
            sd = d.get("symdiff")
            if isinstance(sd, dict):
                d["symdiff"] = {"removed_n": len(sd.get("removed", ())),
                                "added_n": len(sd.get("added", ()))}

    @staticmethod
    def _improve_fields(d: dict, rel: str) -> dict:
        """Flat attribution columns of an ``improve`` event (see schema.md)."""
        trace = d.get("trace") or {}
        chain = d.get("chain") or {}
        root = chain.get("root")
        lineage = d.get("lineage") or {}
        before = d.get("state_before") or {}
        plateau = before.get("plateau") or {}
        timing = d.get("timing") or {}
        sd = d.get("symdiff") or {}
        ver = d.get("verification")
        return {
            "id": d["id"], "kind": d.get("kind"), "before": d.get("before"),
            "after": d.get("after"), "move": d.get("move"),
            "components": trace.get("components"), "phase": d.get("phase") or before.get("phase"),
            "chain": chain.get("id"),
            "root": root.get("id") if isinstance(root, dict) else root,
            "root_source": chain.get("source"),
            "parent": lineage.get("parent"), "donor": lineage.get("donor"),
            "plateau_age_it": plateau.get("age_it"), "plateau_age_s": plateau.get("age_s"),
            "plateau_distinct": plateau.get("distinct_states"),
            "plateau_drift": plateau.get("drift"),
            "neutral_rate": before.get("neutral_rate", plateau.get("neutral_rate")),
            "it_since_prev": timing.get("it_since_prev"),
            "s_since_prev": timing.get("s_since_prev"),
            "it_since_root": timing.get("it_since_root"),
            "s_since_root": timing.get("s_since_root"),
            "symdiff": (len(sd.get("removed", ())) + len(sd.get("added", ()))
                        if "removed" in sd else sd.get("removed_n", 0) + sd.get("added_n", 0))
            if sd else None,
            "cpu_s_since_prev": timing.get("cpu_s_since_prev"),
            "cpu_s_since_root": timing.get("cpu_s_since_root"),
            "verified": ver.get("ok") if isinstance(ver, dict) else None,
            "record": ver.get("record") if isinstance(ver, dict) else None,
            "deterministic": d.get("deterministic"),
            "replayable": (d.get("replay") or {}).get("replayable"),
            "dossier": rel,
        }

    # ------------------------------------------------------------------ follow-ups
    def pending_followups(self, it: int) -> int:
        """Emit every follow-up due at or before iteration ``it``; returns how many.
        Called from ``proposal``; engines that skip ``proposal`` may call it directly."""
        n = 0
        heap = self._followups
        while heap and heap[0][0] <= it:
            _, _, fid, horizon, snap = heapq.heappop(heap)
            self._emit("followup", it, self._followup_fields(fid, horizon, snap, True))
            n += 1
        self._next_followup = heap[0][0] if heap else float("inf")
        if n:
            self._prune_logs()
        return n

    def _prune_logs(self) -> None:
        """Drop log entries no pending follow-up can ask about (each asks for the first entry
        after its improvement's iteration)."""
        heap = self._followups
        if not heap:
            self._chain_its.clear()
            self._restart_its.clear()
            self._imp_log.clear()
            return
        lo = min(item[4]["it"] for item in heap)
        for log in (self._chain_its, self._restart_its):
            cut = bisect_right(log, lo)
            if cut:
                del log[:cut]
        cut = bisect_right(self._imp_log, lo, key=itemgetter(0))
        if cut:
            del self._imp_log[:cut]

    def _followup_fields(self, fid, horizon, snap, complete: bool) -> dict:
        """What happened in the ``horizon`` iterations after improvement ``fid`` (the state
        *after* it): activity, the first later improvement / chain best / restart, and how
        far the best moved."""
        now = self._global()
        it0 = snap["it"]
        last = self._last_improvement or {}
        la = self._last_accepted or {}
        later = self._improvements - snap["improvements"]
        out = {
            "id": fid, "horizon": horizon, "complete": complete,
            "it_since": self._it - it0, "s_since": round(self.now() - snap["t"], 6),
            **{k: now[k] - snap[k] for k in ("proposals", "valid", "accepted", "neutral",
                                             "uphill", "improved_chain", "improved_worker")},
            "cpu_s": round(now["cpu_s"] - snap.get("cpu_s", 0.0), 6),
            "later": later,
            "latest": last.get("id") if later > 0 else None,
            "restarts": self._restarts - snap["restarts"],
            "chain": {"gates": la.get("gates"), "depth": la.get("depth")},
            "chain_changed": (snap.get("chain") is not None
                              and self._chain.get("id") != snap.get("chain")),
            "best": self._best,
            "plateau_it": self._it - max(self._last_chain_improve_it, it0),
        }
        # First later worker improvement, chain best and restart (None: none yet).  The first
        # later chain best ends the plateau this improvement opened.
        i = bisect_right(self._imp_log, it0, key=itemgetter(0))
        nxt = self._imp_log[i] if i < len(self._imp_log) else None
        out["next"] = nxt[2] if nxt else None
        out["next_it_since"] = nxt[0] - it0 if nxt else None
        out["next_s_since"] = round(nxt[1] - snap["t"], 6) if nxt else None
        i = bisect_right(self._chain_its, it0)
        out["next_chain_best_it_since"] = (self._chain_its[i] - it0
                                           if i < len(self._chain_its) else None)
        i = bisect_right(self._restart_its, it0)
        out["restart_it_since"] = (self._restart_its[i] - it0
                                   if i < len(self._restart_its) else None)
        after, best = snap.get("after"), self._best
        if isinstance(after, dict) and isinstance(best, dict) and snap.get("kind") != "frontier":
            out["best_gain"] = {"gates": (after.get("gates") or 0) - (best.get("gates") or 0),
                                "depth": (after.get("depth") or 0) - (best.get("depth") or 0)}
        return out

    # ------------------------------------------------------------------ events
    def _new_chain(self, source, root, parent, chain_id=None) -> dict:
        self._chain_seq += 1
        self._chain = {"id": chain_id or f"{self.worker}-c{self._chain_seq:04d}",
                       "source": source, "root": root, "parent": parent,
                       "start_it": self._it, "start_t": round(self.now(), 6),
                       "start_cpu": round(self._global()["cpu_s"], 6)}
        return self._chain

    def event(self, ev: str, **fields) -> None:
        """Log any other event (restart, plateau, pull, record, followup, phase, warn).

        ``it`` defaults to the last proposal's iteration.  ``restart`` opens a new chain id
        (``<worker>-cNNNN``) and adds a summary of the previous chain under ``prev``;
        ``plateau`` gets an id ``<worker>-pNNNNNN`` and, when it closed because of the
        improvement just recorded, that improvement's id."""
        it = fields.pop("it", self._it)
        if ev == "restart":
            old = self._chain
            prev = dict(fields.get("prev") or {})
            prev.setdefault("chain", old.get("id"))
            if "start_it" in old:
                prev.setdefault("age_it", it - old["start_it"])
                prev.setdefault("age_s", round(self.now() - old["start_t"], 6))
            fields["prev"] = prev
            root = fields.get("root")
            self._new_chain(fields.get("source"), root, fields.get("parent"), fields.get("chain"))
            fields["chain"] = self._chain["id"]
            self._restarts += 1
            if self._followups:
                self._restart_its.append(it)
        elif ev == "plateau":
            if "id" not in fields:
                self._plateau_seq += 1
                fields["id"] = f"{self.worker}-p{self._plateau_seq:06d}"
            last = self._last_improvement
            if fields.get("exit") == "improve" and "improvement" not in fields and last \
                    and last["it"] == it:
                fields["improvement"] = last["id"]
            fields.setdefault("chain", self._chain.get("id"))
        self._emit(ev, it, fields)
        if ev == "restart":
            self._write_sidecar()


class NullRecorder(Recorder):
    """Same API and in-memory behaviour as ``Recorder`` but writes no files.

    Ring, counters, ids and follow-ups work identically (so engine code and tests can rely on
    them); events go to ``self.events`` (a deque of the last ``telemetry.null_keep_events``)
    and dossiers to ``self.dossiers`` (id -> dossier, same bound)."""

    writes_files = False

    def __init__(self, directory=None, worker_id: str = "w", settings=None, clock=None, **kw):
        cfg = knob_values(settings, TELEMETRY_KNOBS)
        keep = cfg["null_keep_events"]
        self.events: deque = deque(maxlen=keep)
        self.dossiers: dict = {}
        self._keep = keep
        super().__init__(None, worker_id, settings, clock, **kw)

    def _open_log(self):
        return None

    def _emit(self, ev, it, fields, flush=None) -> dict:
        record = {"v": SCHEMA_VERSION, "t": round(self.clock.now(), 6), "utc": self.clock.utc(),
                  "worker": self.worker, "it": it, "ev": ev}
        for key, value in fields.items():
            if key not in _ENVELOPE:          # same envelope rule as Recorder._emit
                record[key] = value
        if self._keep:
            self.events.append(record)
        return record

    def _store_dossier(self, rel: str, d: dict, sync: bool | None = None) -> None:
        if self._keep:
            if len(self.dossiers) >= self._keep:
                self.dossiers.pop(next(iter(self.dossiers)))  # oldest first (insertion order)
            self.dossiers[d["id"]] = d

    def _write_sidecar(self) -> None:
        return None
