"""Durable single-process search worker, launched by search.py."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import random
import signal
import time
import traceback

import mixcolumns_core as core
from runtime_support import (atomic_json, canonical_circuit, mask_key,
                             nondominated, pid_running, read_json, utc_now, verify_file)


class CampaignContext:
    def __init__(self, root, run_dir, spec, variant, parent_pid, token):
        self.root, self.run_dir = Path(root), Path(run_dir)
        self.spec, self.variant = spec, variant
        self.label, self.cap = spec["label"], spec["cap"]
        self.worker_dir = self.run_dir / "workers" / self.label
        self.worker_dir.mkdir(parents=True, exist_ok=True)
        self.parent_pid, self.token = parent_pid, token
        self.stop_requested = False
        self.started = time.monotonic()
        self.last_save = 0.0
        self.last_status = 0.0
        self.last_archive = 0.0
        self.last_reschedule = 0.0
        self.last_parent_check = 0.0
        self.parent_ok = True
        self.state_path = self.worker_dir / "checkpoint.json"
        state = read_json(self.state_path, {})
        self.engine_states = state.get("engine_states", {}) if variant == "upgraded" else {}
        self.metrics = state.get("metrics", {})
        self.chunk = int(state.get("chunk", 0))
        self.current_masks = set(state.get("current_masks", [])) or None
        self.best_n = None
        self.best_depth = None
        self.best_masks = None
        self.frontier = state.get("frontier", [])
        self.archive = state.get("archive", [])
        self.sources = state.get("sources", [{"path": spec["seed_path"],
                        "provenance": spec["seed_provenance"],
                        "byte_rotation": spec["byte_rotation"]}])
        self.handoff_rng = random.Random(spec["random_seed"] ^ 0xAE5)
        if "handoff_rng" in state:
            def tuples(x):
                return tuple(tuples(v) for v in x) if isinstance(x, list) else x
            self.handoff_rng.setstate(tuples(state["handoff_rng"]))
        self.logger = logging.getLogger("aes.%s.%s" % (os.getpid(), self.label))
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        for old_handler in list(self.logger.handlers):
            old_handler.close()
            self.logger.removeHandler(old_handler)
        handler = RotatingFileHandler(self.worker_dir / "worker.log", maxBytes=2_000_000,
                                      backupCount=2, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        self.logger.addHandler(handler)
        best = read_json(self.worker_dir / "best.json")
        if best is not None:
            checked, masks = verify_file(self.worker_dir / "best.json", cap=self.cap)
            self.best_n, self.best_depth = checked["gateCount"], checked["depth"]
            self.best_masks = masks
            for source in best.get("metadata", {}).get("sources", []):
                if source not in self.sources:
                    self.sources.append(source)
        # Records and best are committed immediately, while the trajectory
        # checkpoint is periodic. Recover every verified record independently
        # so a crash in that interval cannot roll the saved frontier backwards.
        recovered = []
        for path in sorted((self.worker_dir / "records").glob("*.json")):
            data = read_json(path)
            if not data:
                raise ValueError("unreadable saved record: %s" % path)
            checked, recovered_masks = verify_file(path, cap=self.cap)
            recovered.append({"gateCount": checked["gateCount"], "depth": checked["depth"],
                "path": path.relative_to(self.run_dir).as_posix(), "worker": self.label,
                "share_group": self.spec["share_group"]})
            for source in data.get("metadata", {}).get("sources", []):
                if source not in self.sources:
                    self.sources.append(source)
            if self.best_n is None or (checked["gateCount"], checked["depth"]) < (self.best_n, self.best_depth):
                best = data
                self.best_n, self.best_depth = checked["gateCount"], checked["depth"]
                self.best_masks = recovered_masks
        if best is not None:
            checked, masks = canonical_circuit(best["gates"], cap=self.cap)
            pair = (checked["gateCount"], checked["depth"])
            if not any((r["gateCount"], r["depth"]) == pair for r in recovered):
                path = self.worker_dir / "records" / ("g%d_d%d_%s.json" % (*pair, mask_key(masks)))
                atomic_json(path, best)
                recovered.append({"gateCount": pair[0], "depth": pair[1],
                    "path": path.relative_to(self.run_dir).as_posix(), "worker": self.label,
                    "share_group": self.spec["share_group"]})
            atomic_json(self.worker_dir / "best.json", best)
        self.frontier = nondominated(recovered)
        if self.frontier:
            atomic_json(self.worker_dir / "frontier.json", self.frontier)
        self.stage = "starting"

    def metric(self, name, delta=1):
        self.metrics[name] = self.metrics.get(name, 0) + delta

    def close(self):
        for handler in list(self.logger.handlers):
            handler.close()
            self.logger.removeHandler(handler)

    def log(self, message):
        self.logger.info(message)

    def should_stop(self):
        if self.stop_requested or (self.run_dir / "STOP").exists():
            return True
        now = time.monotonic()
        if now - self.last_parent_check >= 2:
            self.last_parent_check = now
            owner = read_json(self.run_dir / "runner.lock", {})
            self.parent_ok = (owner.get("token") == self.token and pid_running(self.parent_pid))
        return not self.parent_ok

    def _metadata(self, note):
        return {"verified": True, "verification": "independent AES byte-formula, all32 basis inputs",
                "worker": self.label, "variant": self.variant, "cap": self.cap,
                "sources": self.sources, "share_group": self.spec["share_group"],
                "random_seed": self.spec["random_seed"], "note": note,
                "saved_utc": utc_now()}

    def improve(self, gates, masks=None, note=""):
        self.metric("candidates_verified")
        try:
            obj, actual = canonical_circuit(gates, cap=self.cap,
                circuit_id="%s_%s" % (self.label, mask_key(masks or [])),
                metadata=self._metadata(note))
        except (ValueError, TypeError, IndexError) as exc:
            self.metric("invalid_candidates")
            self.log("REJECT %s" % exc)
            return False
        g, d = obj["gateCount"], obj["depth"]
        record = {"gateCount": g, "depth": d,
                  "path": "workers/%s/records/g%d_d%d_%s.json" % (self.label, g, d, mask_key(actual)),
                  "worker": self.label, "share_group": self.spec["share_group"]}
        new_frontier = nondominated(self.frontier + [record])
        if record in new_frontier and not any((r["gateCount"], r["depth"]) == (g, d) for r in self.frontier):
            atomic_json(self.run_dir / record["path"], obj)
            self.frontier = new_frontier
            atomic_json(self.worker_dir / "frontier.json", self.frontier)
            self.metric("frontier_updates")
        better = self.best_n is None or (g, d) < (self.best_n, self.best_depth)
        if better:
            self.best_n, self.best_depth, self.best_masks = g, d, actual
            atomic_json(self.worker_dir / "best.json", obj)
            self.metric("best_updates")
            self.log("BEST gates=%d depth=%d note=%s" % (g, d, note))
        self._archive(actual, g, d)
        return better

    def _archive(self, masks, gates, depth, force=False):
        now = time.monotonic()
        if not force and now - self.last_archive < 2:
            return
        self.last_archive = now
        if self.best_n is not None and gates > self.best_n + 2:
            return
        key = mask_key(masks)
        if any(x["key"] == key for x in self.archive):
            return
        entry = {"key": key, "masks": sorted(masks), "gates": gates, "depth": depth}
        if len(self.archive) < 24:
            self.archive.append(entry)
            return
        # Retain a bounded diverse collection, using actual value-set distance.
        # Gate/depth selection remains the real acceptance objective.
        self.archive.append(entry)
        def distance(a, b):
            aa, bb = set(a["masks"]), set(b["masks"])
            return 1 - len(aa & bb) / max(1, len(aa | bb))
        worst = min(range(len(self.archive)), key=lambda i: (
            min(distance(self.archive[i], r) for j, r in enumerate(self.archive) if i != j)
            - 0.03 * max(0, self.archive[i]["gates"] - (self.best_n or gates)), i))
        self.archive.pop(worst)

    def checkpoint_engine(self, name, state):
        self.engine_states[name] = state
        if state.get("current_masks"):
            self.current_masks = set(state["current_masks"])
        self.stage = name
        now = time.monotonic()
        # Reschedule occasional uphill endpoints too: they can be shallower
        # than a lower-gate uncapped record. This cannot manufacture new masks.
        if self.variant == "upgraded" and self.current_masks and now - self.last_reschedule >= 60:
            self.last_reschedule = now
            import engines
            try:
                gates = engines.indexpairs_from_masks(self.current_masks, self.cap)
                self.improve(gates, self.current_masks, note="periodic exact reschedule")
                self.metric("checkpoint_reschedules")
            except (ValueError, RuntimeError):
                self.metric("checkpoint_reschedule_rejections")
        self.save()

    def save(self, force=False, alive=True, error=None):
        now = time.monotonic()
        if force or now - self.last_save >= 10:
            self.last_save = now
            atomic_json(self.state_path, {
                "schema_version": 1, "label": self.label, "chunk": self.chunk,
                "current_masks": sorted(self.current_masks or []),
                "engine_states": self.engine_states, "metrics": self.metrics,
                "frontier": self.frontier, "archive": self.archive,
                "sources": self.sources, "handoff_rng": self.handoff_rng.getstate(),
                "saved_utc": utc_now(), "variant": self.variant,
            })
        if force or now - self.last_status >= 2:
            self.last_status = now
            atomic_json(self.worker_dir / "status.json", {
                "label": self.label, "pid": os.getpid(), "alive": alive,
                "cap": self.cap, "stage": self.stage, "chunk": self.chunk,
                "best_gates": self.best_n, "best_depth": self.best_depth,
                "current_gates": len(self.current_masks or []),
                "session_seconds": round(now - self.started, 2),
                "metrics": self.metrics, "updated_utc": utc_now(), "error": error,
            })

    def adopt_offer(self):
        offer = read_json(self.worker_dir / "offer.json")
        if not offer or offer.get("share_group") != self.spec["share_group"]:
            return
        path = self.run_dir / offer["path"]
        data = read_json(path)
        if not data:
            return
        if self.best_n is not None and (data["gateCount"], data["depth"]) >= (self.best_n, self.best_depth):
            return
        try:
            checked, masks = canonical_circuit(data["gates"], cap=self.cap)
        except (ValueError, TypeError):
            return
        for source in data.get("metadata", {}).get("sources", []):
            if source not in self.sources:
                self.sources.append(source)
        if self.improve(checked["gates"], masks, note="coordinator reseed from %s" % offer["worker"]):
            self.current_masks = masks
            self.metric("reseed_adoptions")

    def next_start(self):
        mode = self.spec["handoff"]
        if self.variant == "baseline" or mode == "best":
            return set(self.best_masks or self.current_masks or [])
        if mode == "continue" or not self.archive:
            return set(self.current_masks or self.best_masks or [])
        r = self.handoff_rng.random()
        if r < 0.65:
            return set(self.current_masks or self.best_masks or [])
        if r < 0.80:
            return set(self.best_masks or self.current_masks or [])
        options = [x for x in self.archive if self.cap is None or x["depth"] <= self.cap]
        if not options:
            return set(self.current_masks or self.best_masks or [])
        current = set(self.current_masks or [])
        options.sort(key=lambda x: (len(current & set(x["masks"])) / max(1, len(current | set(x["masks"]))),
                                    x["gates"], x["key"]))
        self.metric("diverse_handoffs")
        return set(self.handoff_rng.choice(options[:max(1, len(options) // 3)])["masks"])


def run_worker(root, run_dir, label, parent_pid, token):
    run_dir = Path(run_dir)
    config = read_json(run_dir / "config.json")
    spec = next(w for w in config["workers"] if w["label"] == label)
    variant = config["variant"]
    if variant == "baseline":
        import engines_baseline as engine
    else:
        import engines as engine
    ctx = CampaignContext(root, run_dir, spec, variant, parent_pid, token)
    def request_stop(signum, frame):
        ctx.stop_requested = True
    signal.signal(signal.SIGINT, request_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, request_stop)
    error = None
    try:
        if not ctx.current_masks:
            if spec["seed_path"] == "scratch":
                gates = core.naive_circuit()
            else:
                data = read_json(Path(root) / spec["seed_path"])
                gates = data["gates"]
            rotation = spec["byte_rotation"] * 8
            gates = [[(a + rotation) % 32 if a < 32 else a,
                      (b + rotation) % 32 if b < 32 else b] for a, b in gates]
            checked, masks = canonical_circuit(gates, cap=ctx.cap)
            ctx.current_masks = masks
            ctx.improve(checked["gates"], masks, note="starting seed")
        else:
            # Checkpoint recovery is verified before continuing; corrupt state
            # is a visible failure rather than a silent fresh restart.
            gates = engine.indexpairs_from_masks(ctx.current_masks, ctx.cap)
            ctx.improve(gates, ctx.current_masks, note="verified checkpoint resume")
        ctx.save(force=True)
        while not ctx.should_stop():
            ctx.adopt_offer()
            stage = spec["cycle"][ctx.chunk % len(spec["cycle"])]
            ctx.stage = stage
            start = ctx.next_start()
            ctx.current_masks = start
            ctx.save(force=True)
            result = engine.run_engine(stage, start, ctx.cap, None,
                spec["chunk_seconds"], [spec["random_seed"] + ctx.chunk],
                dict(spec["knobs"][stage]), ctx)
            if isinstance(result, dict):
                ctx.engine_states[stage] = result
                ctx.current_masks = set(result.get("current_masks", ctx.current_masks))
            elif ctx.best_masks:
                ctx.current_masks = set(ctx.best_masks)
            ctx.chunk += 1
            ctx.save(force=True)
    except Exception:
        error = traceback.format_exc()
        ctx.log(error)
        atomic_json(ctx.worker_dir / "error.json", {"error": error, "utc": utc_now()})
    finally:
        ctx.save(force=True, alive=False, error=error)
        ctx.close()
    return 1 if error else 0
