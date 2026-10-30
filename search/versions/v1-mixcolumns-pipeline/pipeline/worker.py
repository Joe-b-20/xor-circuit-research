#!/usr/bin/env python3
"""
worker.py  --  one search worker of the pipeline, run in CHUNKS forever.

Launched by ladder_parallel.py as its own OS process. It runs one engine at a
fixed depth cap, and between fixed-length chunks it RE-SEEDS from the best
circuit the coordinator has offered it (reseed_<label>.json) whenever that
circuit Pareto-beats its own best. It continuously:
  * saves the best VERIFIED circuit so far to  <out_dir>/<label>_best.json
  * writes live status to                      <out_dir>/<label>_status.json
  * appends a log to                           <out_dir>/<label>.log
  * (if harvesting is on) appends every distinct plateau state it visits to
    <out_dir>/<label>.pop.jsonl

verify-before-claim: a candidate is only ever accepted by improve() after the
GF(2^8) oracle verifies it at this worker's depth cap.

Pareto tie-break: improve() accepts a candidate when it has FEWER gates, OR the
same gate count at STRICTLY LOWER depth. So an 89@depth5 found while the best is
89@depth6 is kept, not discarded.

The engine name "alt" is not an engine but a worker mode: it alternates a short
`walk` chunk with a longer `lns` chunk, each starting from the worker's own
best. The walk sprays across the plateau (hundreds of iterations per second,
harvesting as it goes) and the lns then punches down from wherever the walk
ended up; this alternation is what the campaign's best-performing hunt workers
ran, and it is how all five 88-gate circuits were reached.

Usage (the coordinator calls this):
  python3 worker.py <label> <engine|alt> <depth|none> <scratch|seedfile> <out_dir> <seeds_csv>
Engine knobs, chunk lengths, and reseeding are read from <out_dir>/config.json.
"""
import os, sys, json, time
import mixcolumns_core as core
import engines


def atomic_write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


def pareto_better(g2, d2, g1, d1):
    """(g2,d2) beats (g1,d1): fewer gates, or equal gates at lower depth."""
    if g1 is None:
        return True
    return g2 < g1 or (g2 == g1 and d2 < d1)


class WorkerCtx:
    def __init__(self, label, cap, out_dir):
        self.label = label
        self.cap = cap
        self.best_path = os.path.join(out_dir, "%s_best.json" % label)
        self.status_path = os.path.join(out_dir, "%s_status.json" % label)
        self.logf = open(os.path.join(out_dir, "%s.log" % label), "a", buffering=1)
        self.t0 = time.time()
        self.best_n = None
        self.best_depth = None
        self.best_masks = None
        self.status = {"label": label, "cap": cap, "pid": os.getpid(),
                       "best_gates": None, "best_depth": None,
                       "started": self.t0, "updated": self.t0, "alive": True}
        self._flush_status()

    def _flush_status(self):
        self.status["updated"] = time.time()
        atomic_write_json(self.status_path, self.status)

    def log(self, msg):
        line = "[%8.1fs %s] %s" % (time.time() - self.t0,
                                   time.strftime("%H:%M:%S"), msg)
        print(line, flush=True)
        self.logf.write(line + "\n")
        self._flush_status()

    def _record(self, circuit, gates, depth, masks):
        self.best_n = gates; self.best_depth = depth; self.best_masks = set(masks)
        core.save(circuit, self.best_path,
                  extra={"depth": depth, "verified": True, "cap": self.cap})
        self.status["best_gates"] = gates; self.status["best_depth"] = depth
        self._flush_status()

    def improve(self, circuit, masks, note=""):
        v = core.verify(circuit, max_depth=self.cap)
        if not v["ok"]:
            self.log("  WARNING candidate REJECTED (outputs=%d/32 depth=%d) -- not claimed"
                     % (v["outputs"], v["depth"]))
            return False
        if not pareto_better(v["gates"], v["depth"], self.best_n, self.best_depth):
            return False
        self._record(circuit, v["gates"], v["depth"], masks)
        self.log("  NEW BEST %d gates depth %d VERIFIED %s -> %s"
                 % (v["gates"], v["depth"], note, os.path.basename(self.best_path)))
        return True

    def adopt(self, circuit, masks, source):
        """Adopt a coordinator-offered reseed as this worker's best (already
        verified feasible at cap by the coordinator; re-verified here)."""
        v = core.verify(circuit, max_depth=self.cap)
        if not v["ok"] or not pareto_better(v["gates"], v["depth"], self.best_n, self.best_depth):
            return False
        self._record(circuit, v["gates"], v["depth"], masks)
        self.log("  ADOPTED reseed %d gates depth %d from %s"
                 % (v["gates"], v["depth"], source))
        return True


def knobs_for(cfg, engine, label):
    """Knobs for one engine: the run's defaults plus this worker's overrides.
    An override dict is either flat (a single-engine worker) or keyed by engine
    name, which is how an "alt" worker overrides its walk and lns chunks
    separately."""
    knobs = dict(cfg["knobs"][engine])
    over = cfg.get("worker_knobs", {}).get(label, {})
    if any(name in over for name in cfg["knobs"]):
        over = over.get(engine, {})
    knobs.update(over)
    return knobs


def wire_harvest(knobs, out_dir, label):
    """Turn the harvest / cross_pollinate switches into the paths the engines
    use: this worker harvests into <label>.pop.jsonl, and -- only if explicitly
    asked -- also reads every sibling *.pop.jsonl of the run into its rebuild
    pool. Cross-pollination mixes the mask provenance of all workers in the run,
    so it is off unless a config turns it on (see ladder_parallel.py)."""
    if knobs.pop("harvest", False):
        knobs["harvest_path"] = os.path.join(out_dir, "%s.pop.jsonl" % label)
    if knobs.pop("cross_pollinate", False):
        knobs["pop_glob"] = os.path.join(out_dir, "*.pop.jsonl")
    return knobs


def main():
    label = sys.argv[1]; engine = sys.argv[2]; depth_arg = sys.argv[3]
    start_arg = sys.argv[4]; out_dir = sys.argv[5]
    seeds = [int(x) for x in sys.argv[6].split(",")] if len(sys.argv) > 6 and sys.argv[6] else [1]
    cap = None if depth_arg.lower() in ("none", "free", "-1") else int(depth_arg)

    with open(os.path.join(out_dir, "config.json")) as f:
        cfg = json.load(f)
    chunk_s = cfg.get("chunk_s", 600)
    walk_chunk_s = cfg.get("walk_chunk_s", 300)
    reseed_on = cfg.get("reseed", True)
    # "alt" alternates walk and lns chunks; any other name is a single engine.
    cycle = ("walk", "lns") if engine == "alt" else (engine,)
    knobs = {e: wire_harvest(knobs_for(cfg, e, label), out_dir, label) for e in cycle}

    ctx = WorkerCtx(label, cap, out_dir)
    ctx.log("worker start: engine=%s depth=%s start=%s seeds=%s chunk=%ds reseed=%s"
            % (engine, cap, start_arg, seeds, chunk_s, reseed_on))
    ctx.log("knobs: %s" % json.dumps(knobs, sort_keys=True))

    # initial seed
    if start_arg == "scratch":
        seed_masks = None
    else:
        seed_masks = core.load_circuit_masks(start_arg)

    reseed_path = os.path.join(out_dir, "reseed_%s.json" % label)
    chunk = 0
    try:
        while True:
            # (a) consider a coordinator reseed before this chunk
            if reseed_on and os.path.exists(reseed_path):
                try:
                    with open(reseed_path) as f:
                        rg = json.load(f)["gates"]
                    rmasks = core.load_circuit_masks(reseed_path)
                    if ctx.adopt(rg, rmasks, os.path.basename(reseed_path)):
                        seed_masks = set(rmasks)
                except Exception as e:
                    ctx.log("  reseed read failed: %s" % e)
            # (b) run one bounded chunk from the current seed (never self-stops)
            eng = cycle[chunk % len(cycle)]
            secs = walk_chunk_s if (engine == "alt" and eng == "walk") else chunk_s
            engines.run_engine(eng, seed_masks, cap, None, secs, seeds, knobs[eng], ctx)
            # (c) continue next chunk from this worker's own best
            if ctx.best_masks is not None:
                seed_masks = set(ctx.best_masks)
            seeds = [s + 1 for s in seeds]        # vary RNG across chunks
            chunk += 1
    except KeyboardInterrupt:
        pass
    finally:
        ctx.status["alive"] = False
        ctx._flush_status()
        ctx.log("worker stopped")


if __name__ == "__main__":
    main()
