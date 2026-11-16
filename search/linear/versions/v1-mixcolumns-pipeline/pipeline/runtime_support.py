"""Portable campaign I/O and a verifier independent of the search kernel."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def jsonable(value):
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (set, frozenset)):
        return [jsonable(v) for v in sorted(value)]
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp.%s" % os.getpid())
    with tmp.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(jsonable(value), stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    # A reader can briefly hold the destination on Windows. Retry only that
    # transient condition; do not silently discard failed checkpoints.
    for attempt in range(6):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(0.02 * (attempt + 1))


def read_json(path, default=None):
    try:
        with Path(path).open(encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, ValueError):
        return default


def file_sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def mask_key(masks):
    data = ",".join(str(m) for m in sorted(masks)).encode("ascii")
    return hashlib.sha256(data).hexdigest()[:16]


def pid_running(pid):
    """Read-only process check; os.kill(pid, 0) is NOT used on Windows."""
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
        kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return ctypes.get_last_error() == 5  # access denied: conservatively live
        code = wintypes.DWORD()
        try:
            return bool(kernel.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def reference_targets():
    """AES forward MixColumns evaluated on the 32 one-bit columns.

    This byte-level formula is separate from mixcolumns_core's coefficient
    matrix construction. XOR-only circuits are linear, so these 32 basis
    checks establish equality on every possible input column.
    """
    targets = [0] * 32
    def xtime(x):
        return ((x << 1) & 255) ^ (0x1B if x & 128 else 0)
    for bit in range(32):
        column = [0, 0, 0, 0]
        column[bit // 8] = 1 << (bit % 8)
        total = column[0] ^ column[1] ^ column[2] ^ column[3]
        out = [column[b] ^ total ^ xtime(column[b] ^ column[(b + 1) % 4]) for b in range(4)]
        for j in range(32):
            if (out[j // 8] >> (j % 8)) & 1:
                targets[j] |= 1 << bit
    return tuple(targets)


REFERENCE_TARGETS = reference_targets()


def canonical_circuit(gates, cap=None, circuit_id="aes_mixcolumns_candidate", metadata=None):
    """Replay, remove dead gates, and export explicit ordered outputs.

    Reject forward references, zero values and duplicate signals. The kernel
    represents each nonzero linear value once; malformed candidates must not
    be made to look like records by forgiving their semantics.
    """
    values = [1 << i for i in range(32)]
    levels = [0] * 32
    seen = {v: i for i, v in enumerate(values)}
    normalized = []
    for k, gate in enumerate(gates):
        if not isinstance(gate, (list, tuple)) or len(gate) != 2:
            raise ValueError("gate %s must have two operands" % k)
        a, b = gate
        if type(a) is not int or type(b) is not int or not (0 <= a < 32 + k and 0 <= b < 32 + k):
            raise ValueError("gate %s has a non-earlier operand" % k)
        value = values[a] ^ values[b]
        if not value or value in seen:
            raise ValueError("gate %s produces a zero or duplicate value" % k)
        seen[value] = 32 + k
        values.append(value)
        levels.append(1 + max(levels[a], levels[b]))
        normalized.append([a, b])
    missing = [j for j, value in enumerate(REFERENCE_TARGETS) if value not in seen]
    if missing:
        raise ValueError("missing AES output indices %s" % missing)
    output_ids = [seen[value] for value in REFERENCE_TARGETS]
    live = set(output_ids)
    for k in range(len(normalized) - 1, -1, -1):
        if 32 + k in live:
            live.update(normalized[k])
    new_index = {i: i for i in range(32)}
    packed, masks = [], []
    for k, (a, b) in enumerate(normalized):
        if 32 + k in live:
            packed.append([new_index[a], new_index[b]])
            new_index[32 + k] = 31 + len(packed)
            masks.append(values[32 + k])
    depth = max(levels[i] for i in output_ids)
    if cap is not None and depth > cap:
        raise ValueError("depth %s exceeds cap %s" % (depth, cap))
    obj = {
        "id": circuit_id,
        "model": "2-input XOR SLP; free fan-out; inputs at depth 0",
        "inputCount": 32,
        "gateCount": len(packed),
        "depth": depth,
        "gates": packed,
        "outputSignals": [new_index[i] for i in output_ids],
        "outputConvention": "signal input 8*b+r is bit r (LSB first) of byte b; outputs use the same order",
    }
    if metadata is not None:
        obj["metadata"] = jsonable(metadata)
    return obj, set(masks)


def verify_file(path, cap=None):
    data = read_json(path)
    if not isinstance(data, dict) or not isinstance(data.get("gates"), list):
        raise ValueError("expected an index-pair circuit JSON")
    obj, masks = canonical_circuit(data["gates"], cap=cap)
    if "gateCount" in data and data["gateCount"] != len(data["gates"]):
        raise ValueError("claimed gateCount differs from stored gate list")
    if len(obj["gates"]) != len(data["gates"]):
        raise ValueError("stored circuit contains dead gates")
    if "depth" in data and data["depth"] != obj["depth"]:
        raise ValueError("claimed depth differs from replay")
    if "outputSignals" in data:
        values = [1 << i for i in range(32)]
        for a, b in data["gates"]:
            values.append(values[a] ^ values[b])
        ids = data["outputSignals"]
        if not isinstance(ids, list) or len(ids) != 32 or any(type(i) is not int or not 0 <= i < len(values) for i in ids):
            raise ValueError("invalid outputSignals")
        if [values[i] for i in ids] != list(REFERENCE_TARGETS):
            raise ValueError("explicit output order is not AES MixColumns")
    return obj, masks


def nondominated(records):
    """One representative of each nondominated (gate count, depth) pair."""
    by_pair = {}
    for rec in records:
        pair = (rec["gateCount"], rec["depth"])
        by_pair.setdefault(pair, rec)
    kept, shallowest = [], float("inf")
    for (g, d), rec in sorted(by_pair.items()):
        if d < shallowest:
            kept.append(rec)
            shallowest = d
    return kept


def code_manifest(root):
    root = Path(root)
    paths = [root / "search.py"] + sorted((root / "pipeline").glob("*.py"))
    return {str(p.relative_to(root)).replace("\\", "/"): file_sha256(p) for p in paths if p.is_file()}
