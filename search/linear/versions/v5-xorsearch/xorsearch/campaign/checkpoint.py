"""Durable files, process identity, the campaign lock and checkpoint envelopes.

Everything the campaign runtime writes goes through this module, so a crash at any instant leaves
either the old or the new version of a file, never a torn one:

* ``atomic_json`` / ``atomic_bytes`` write a temporary file, fsync it, rename it over the target
  and fsync the directory.
* ``append_jsonl`` appends one line and repairs a torn last line left by an earlier crash.
* ``process_identity`` names a process by pid *and* its kernel start tick, so a recycled pid is
  never mistaken for a live owner.
* ``CampaignLock`` gives one coordinator ownership of a run directory; stale locks of dead owners
  are reclaimed under an advisory ``flock`` so two claimants cannot race.
* ``save_checkpoint`` / ``load_checkpoint`` wrap the engine's JSON state in an envelope bound to the
  run, worker, plan, settings and source, with a content hash, so a resume never continues from a
  checkpoint written for different code or configuration.
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

#: Version of every envelope written by the campaign runtime (checkpoints, plans, status files).
SCHEMA = 1


# --------------------------------------------------------------------------------------------
# Canonical JSON and hashing
# --------------------------------------------------------------------------------------------
def utc_now() -> str:
    """Current UTC time, ISO 8601 with milliseconds."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def canonical_bytes(value: Any) -> bytes:
    """Sorted, compact JSON plus newline: equal values always give equal bytes (and hashes)."""
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def digest(value: Any) -> str:
    """SHA-256 of the canonical JSON of ``value``."""
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_hash(path: str | Path) -> str:
    """SHA-256 of a file's bytes, streamed."""
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------------------------
# Atomic writes
# --------------------------------------------------------------------------------------------
def _fsync_directory(directory: Path) -> None:
    # The rename is only durable once the directory entry is; some filesystems refuse, ignore.
    try:
        fd = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def atomic_bytes(path: str | Path, data: bytes) -> None:
    """Replace ``path`` with ``data`` atomically (readers see the old or the new file)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_json(path: str | Path, value: Any, pretty: bool = False) -> None:
    """Atomically write ``value`` as JSON (canonical unless ``pretty`` for human-read files)."""
    if pretty:
        data = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    else:
        data = canonical_bytes(value)
    atomic_bytes(path, data)


def atomic_text(path: str | Path, text: str) -> None:
    """Atomically write UTF-8 text."""
    atomic_bytes(path, text.encode("utf-8"))


def read_json(path: str | Path, default: Any = None) -> Any:
    """Read JSON; a missing file gives ``default``, a corrupt one is an error (never ignored)."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def append_jsonl(path: str | Path, value: Any) -> None:
    """Append one JSON line durably.

    A crash mid-append can leave a last line without its newline.  Before appending, such a torn
    tail is cut back to the last complete line and a ``truncated_line_recovered`` marker is
    written, so readers never see a corrupt line followed by a valid one.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        stream.seek(0, os.SEEK_END)
        end = stream.tell()
        if end:
            stream.seek(end - 1)
            if stream.read(1) != b"\n":
                stream.seek(0)
                body = stream.read()
                boundary = body.rfind(b"\n") + 1
                stream.truncate(boundary)
                stream.seek(0, os.SEEK_END)
                stream.write(canonical_bytes({"ev": "truncated_line_recovered", "utc": utc_now(),
                                              "removed_bytes": end - boundary}))
        stream.seek(0, os.SEEK_END)
        stream.write(canonical_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def read_jsonl(path: str | Path, offset: int = 0) -> tuple[list[dict], int]:
    """Complete JSON lines of ``path`` from byte ``offset``; returns (lines, next offset).

    A trailing partial line (a writer mid-append) is left for the next call.
    """
    try:
        with open(path, "rb") as stream:
            stream.seek(offset)
            data = stream.read()
    except FileNotFoundError:
        return [], offset
    complete = data.rfind(b"\n") + 1
    lines = [json.loads(line) for line in data[:complete].splitlines() if line.strip()]
    return lines, offset + complete


def safe_join(root: str | Path, relative: str) -> Path:
    """``root / relative``, refusing paths that escape ``root`` (record paths come from files)."""
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"path escapes the run directory: {relative}")
    return path


# --------------------------------------------------------------------------------------------
# Process identity
# --------------------------------------------------------------------------------------------
def _start_ticks(pid: int) -> str | None:
    # Field 22 of /proc/<pid>/stat is the start time in clock ticks; the command name (field 2)
    # may contain spaces and parentheses, so split after its closing parenthesis.
    try:
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
    except (OSError, IndexError):
        return None


def process_identity(pid: int | None = None) -> dict:
    """``{pid, host, start_ticks}`` naming one process instance unambiguously."""
    pid = os.getpid() if pid is None else int(pid)
    return {"pid": pid, "host": socket.gethostname(), "start_ticks": _start_ticks(pid)}


def identity_alive(identity: dict | None) -> bool:
    """True when the process named by ``identity`` is still running on this host."""
    if not isinstance(identity, dict) or identity.get("host") != socket.gethostname():
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
    saved = identity.get("start_ticks")
    return saved is None or _start_ticks(pid) == saved


# --------------------------------------------------------------------------------------------
# Campaign lock
# --------------------------------------------------------------------------------------------
LOCK_NAME = "campaign.lock"
STOP_NAME = "STOP"


class LockError(RuntimeError):
    """The run directory is owned by a live coordinator (or ownership cannot be recovered)."""


class CampaignLock:
    """Exclusive ownership of a run directory by one coordinator process.

    The lock file holds the owner's process identity and a random ``token``.  Workers carry the
    token and stop when the lock no longer names their coordinator, and ``STOP`` requests are
    addressed to the token, so a stale request can never stop a later session.
    """

    def __init__(self, run_dir: str | Path):
        self.run_dir = Path(run_dir)
        self.path = self.run_dir / LOCK_NAME
        self.owner: dict | None = None

    def read(self) -> dict:
        """Current lock contents (empty dict when unlocked)."""
        return read_json(self.path, {}) or {}

    def acquire(self, worker_status_files=()) -> dict:
        """Take ownership or raise LockError.  A dead owner's lock is reclaimed.

        ``worker_status_files`` are checked too: a worker of a dead coordinator may still be
        finishing its last checkpoint, and two writers of one worker directory must never overlap.
        """
        try:
            import fcntl
        except ImportError:  # pragma: no cover - non-POSIX
            fcntl = None
        guard_path = self.run_dir / ".lock.guard"
        with guard_path.open("a+b") as guard:
            if fcntl is not None:
                fcntl.flock(guard.fileno(), fcntl.LOCK_EX)
            return self._acquire_guarded(worker_status_files)

    def _acquire_guarded(self, worker_status_files) -> dict:
        owner = {**process_identity(), "token": uuid.uuid4().hex, "acquired_utc": utc_now()}
        previous = self.read()
        if previous:
            if previous.get("host") != socket.gethostname():
                raise LockError(f"{self.path} is owned by host {previous.get('host')}; "
                                "remove it by hand only if that coordinator is gone")
            if identity_alive(previous):
                raise LockError(f"campaign already has a live coordinator (pid {previous.get('pid')})")
            for status_path in worker_status_files:
                status = read_json(status_path, {}) or {}
                if identity_alive(status.get("process")):
                    raise LockError(f"an old worker is still alive ({status_path}); it stops "
                                    "itself within a few seconds of losing its coordinator")
            self.path.unlink()
        fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical_bytes(owner))
            stream.flush()
            os.fsync(stream.fileno())
        self.owner = owner
        return owner

    def release(self) -> None:
        """Remove the lock if this process still owns it."""
        if self.owner and self.read().get("token") == self.owner["token"]:
            self.path.unlink()
        self.owner = None


def request_stop(run_dir: str | Path, reason: str = "requested") -> dict:
    """Ask the live coordinator of ``run_dir`` to stop (writes ``STOP`` addressed to its token)."""
    owner = CampaignLock(run_dir).read()
    if not owner.get("token") or not identity_alive(owner):
        return {"stopped": False, "message": "no live coordinator owns this run directory"}
    value = {"owner_token": owner["token"], "reason": reason, "requested_utc": utc_now()}
    atomic_json(Path(run_dir) / STOP_NAME, value)
    return {"stopped": True, **value}


def stop_requested(run_dir: str | Path, token: str) -> dict | None:
    """The STOP request addressed to ``token``, or None."""
    stop = read_json(Path(run_dir) / STOP_NAME, {}) or {}
    return stop if stop.get("owner_token") == token else None


# --------------------------------------------------------------------------------------------
# Checkpoint envelopes
# --------------------------------------------------------------------------------------------
class CheckpointError(ValueError):
    """A checkpoint does not belong to this run/worker/configuration or is corrupt."""


def save_checkpoint(path: str | Path, binding: dict, engine_state: dict, extra: dict | None = None) -> dict:
    """Atomically write ``engine_state`` inside an envelope bound to ``binding``.

    ``binding`` identifies what the state is valid for (run id, worker, plan, settings, source
    hashes); ``extra`` carries worker-side counters.  The envelope hash covers everything.
    """
    envelope = {"schema": SCHEMA, "binding": binding, "saved_utc": utc_now(),
                "engine": engine_state, "worker": extra or {}}
    envelope["sha256"] = digest(envelope)
    atomic_json(path, envelope)
    return envelope


def load_checkpoint(path: str | Path, binding: dict) -> dict | None:
    """The envelope at ``path`` (None if absent); raises CheckpointError on any mismatch."""
    envelope = read_json(path)
    if envelope is None:
        return None
    if not isinstance(envelope, dict) or envelope.get("schema") != SCHEMA:
        raise CheckpointError(f"{path}: unsupported checkpoint schema")
    body = {k: v for k, v in envelope.items() if k != "sha256"}
    if envelope.get("sha256") != digest(body):
        raise CheckpointError(f"{path}: checkpoint hash mismatch (corrupt or edited)")
    saved = envelope.get("binding", {})
    wrong = sorted(k for k in set(binding) | set(saved) if binding.get(k) != saved.get(k))
    if wrong:
        raise CheckpointError(f"{path}: checkpoint was written for a different "
                              f"{', '.join(wrong)}; refusing to resume from it")
    return envelope
