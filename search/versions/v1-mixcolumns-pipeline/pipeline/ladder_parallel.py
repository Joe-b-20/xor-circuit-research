#!/usr/bin/env python3
"""
ladder_parallel.py  --  the record-hunting pipeline (parallel, reseeding).

    python3 ladder_parallel.py [--mode cascade|fixed] [--workers hunt87|sub89]
                               [--stop-gates N] [--stop-depth D]

Two modes (--mode overrides the MODE default below):

  "cascade"  the depth ladder: start depth 3 from scratch, and each time the
             frontier rung beats its baseline (or times out) launch the next
             deeper rung seeded from it -- all rungs keep running, all reseed.

  "fixed"    launch a fixed set of workers at once (each with its own depth cap
             and seed) and let them run in parallel. --workers picks the set:
             "hunt87" (default) puts one uncapped worker on each of the three
             known 88-gate families chasing 87, plus a depth-6-capped worker on
             the 89@depth5 record; "sub89" is the historic two-worker set that
             produced 89@depth5.

--stop-gates / --stop-depth make the coordinator shut everything down cleanly
as soon as a verified global best satisfies BOTH given bounds (an omitted
bound is a don't-care), e.g. to replicate the records:

    python3 ladder_parallel.py --mode fixed --workers sub89 --stop-gates 89 --stop-depth 5
    python3 ladder_parallel.py --mode cascade --stop-gates 92 --stop-depth 4

Without stop bounds the run continues until Ctrl-C; either way every best is
already on disk.

Every worker is its own OS process (real parallelism). Every worker
verifies-before-claim and uses a PARETO tie-break (accept fewer gates, or
equal gates at lower depth) so shallow equal-gate circuits are not lost. The
coordinator maintains best_overall.json and offers each worker the best circuit
that is feasible at its depth cap (reseed_<label>.json), which the worker adopts
between chunks -- unless that worker was configured with reseed=False, which is
how the 88-family workers are kept from collapsing onto one circuit.
"""
import argparse
import os, sys, json, time, shutil, subprocess

# ==========================================================================
# CONFIG  --  edit everything here
# ==========================================================================
OUT_ROOT = "runs_parallel"
MODE = "cascade"                # "cascade" or "fixed"
#   cascade = the from-scratch depth ladder (d3 anneal3, deeper rungs seeded
#             from the frontier). This is the configuration shape of the run
#             that produced 92@depth4 (see ../evidence/
#             cascade_run_2026-07-14_from_scratch_newlogic/).
#   fixed   = one of the WORKER_SETS below (--workers picks the set): the
#             current 87-hunt configuration, or the historic sub-89 one.

# ---- fixed-mode worker sets ----------------------------------------------
FIXED_WORKER_SET = "hunt87"     # "hunt87" or "sub89"; --workers overrides

WORKER_SETS = {
    # The shipped hunting configuration: one uncapped worker per known 88-gate
    # family, all chasing 87, plus one depth-capped worker still working the
    # depth frontier. The campaign's exact certificates showed every known
    # 88-gate circuit has an empty remove-2 shell (and the canonical ones an
    # empty remove-3 shell), i.e. an 87 is at least 4 masks away from each of
    # them -- so pointing one worker at each family is three independent
    # long-jump attempts, not one search with three seeds.
    #
    # A worker dict key: label, engine ("lns"/"walk"/"alt"), depth (None =
    # uncapped), start (seed path), and optionally seeds (RNG list), knobs
    # (per-worker overrides) and reseed (False = never adopt a coordinator
    # offer). The family workers set reseed=False on purpose: an offer is
    # Pareto-better if it is equal-size and shallower, so a single reseed pass
    # would collapse the 88@8 and Jean workers onto the 88@7 circuit and throw
    # the family diversity -- the whole point of the set -- away.
    #
    # PROVENANCE: f3_jean88 starts from Jean's published circuit (ePrint
    # 2026/1481), and f2's 88@8 seed is itself derived from that circuit (its
    # rho^2-symmetric 90 seed was built partly by symmetrizing Jean's 88).
    # Anything those two workers produce is DERIVED FROM PUBLISHED WORK and
    # must be reported that way (../METHODS_INDEX.md, "Provenance classes";
    # seeds/README.md). Only f1 and d6 run on circuits of our own lineage.
    "hunt87": [
        dict(label="f1_ours88_d7", engine="alt", depth=None, reseed=False,
             start="seeds/seed_88_at_depth7_ours.json"),
        dict(label="f2_third88_d8", engine="alt", depth=None, reseed=False,
             start="seeds/seed_88_at_depth8_thirdfamily.json"),
        dict(label="f3_jean88_d7", engine="alt", depth=None, reseed=False,
             start="seeds/seed_88_at_depth7_jean_imported.json"),
        # Depth-capped worker: threshold acceptance, not SA. SA's uphill
        # accepts were tuned uncapped, where rebuilds are almost never larger;
        # under a cap rebuilds are systematically larger and SA drifts uphill
        # without recovering (measured 2026-07-27: at cap 6 a threshold-greedy
        # run descended a lifted 100-gate seed to 89@5 in 61 s; SA never got
        # below 96 in 13 min from a comparable seed).
        dict(label="d6_from89at5", engine="lns", depth=6,
             knobs=dict(accept="threshold", up_prob=0.10, up_slack=1, snapback=3),
             start="seeds/seed_89_at_depth5.json"),
    ],
    # The historic sub-89 configuration, kept reachable and unchanged: two
    # reseeding workers warm-started at the then-frontier -- an uncapped hunter
    # on the 89@depth6 circuit (chasing 88, and free to surface equal-gate-
    # shallower circuits via the Pareto tie-break: this is the worker that
    # found 89@depth5 in ~10 minutes), and a depth-5-capped hunter on the
    # 90@depth5 circuit. See ../evidence/sub89_run_2026-07-14_got_89at5/
    # code/CONFIG_AS_RUN.md. NOTE it now runs the campaign engine, not the
    # engine of that archived run -- to replay the run itself, use its code/.
    "sub89": [
        dict(label="uncapped_sub89", engine="lns", depth=None,
             start="seeds/seed_89_at_depth6.json"),
        dict(label="depth5_sub90", engine="lns", depth=5,
             start="seeds/seed_90_at_depth5.json"),
    ],
}
FIXED_WORKERS = WORKER_SETS[FIXED_WORKER_SET]

# ---- cascade-mode ladder ---------------------------------------------------
DEPTHS = [3, 4, 5, 6, 7, 8, 9, 10, 11]
FINAL_UNCAPPED_DEPTH = True
MAX_WAIT_S = 2 * 3600           # a rung triggers the next after this long even without a hit
IMPROVE_BY = 1                  # ...or as soon as it beats its baseline by this many gates
DEPTH3_BASELINE = 97
ENGINE_D3 = "anneal3"
ENGINE_DEEP = "lns"

# ---- shared ---------------------------------------------------------------
SEEDS_PER_WORKER = [1, 2, 3]    # default RNG seeds (a worker dict may override)
POLL_S = 20                     # coordinator status cadence
CHUNK_S = 600                   # lns chunk length (each worker continues from its OWN best)
WALK_CHUNK_S = 300              # walk chunk length inside an "alt" worker
RESEED = True                   # coordinator offers each worker the best circuit
                                # feasible at its depth cap (as in both record
                                # runs); a worker dict may opt out with reseed=False

# Engine knobs. The values are the campaign's measured-good configuration; each
# line says what the knob does. Anything a worker wants different goes in its
# own knobs= dict (for an "alt" worker, keyed by engine: {"lns": {...}}).
LNS_KNOBS = dict(
    op_mix={"small": 0.35, "coneinj": 0.45, "biginj": 0.20},
                        # destroy operator mix. small = 1-4 random masks (the
                        # moves that actually rebuild); coneinj = a CONNECTED
                        # cone of the circuit + injected local candidates
                        # (~12x improvements/s over random destroys); biginj = a
                        # big destroy, only viable because of peel_window.
                        # "uniform" (1..kmax random masks, the v1 destroy) is
                        # also accepted here.
    kmax=4,             # victim count of the "uniform" operator
    cone_lo=2, cone_hi=4,        # coneinj victim count range
    biginj_lo=8, biginj_hi=16,   # biginj victim count range
    kshake=12,          # every 997th iteration: forced kshake..kshake+4 destroy
    nsamp=(12, 12),     # (base, extra) pool draws and kept-pair draws per rebuild
                        # -- (12,12) is ~1.3-1.8x the throughput of v1's (24,24)
                        # at the same drift (knob sweep: champ_fast)
    hot_frac=0.5,       # fraction of pool draws taken from the hot list (masks a
                        # rebuild recently reintroduced) -- ~11x accepted moves
    vic_cost=3,         # pull-in cost class of a just-destroyed victim: victims
                        # stay available, so a rebuild never dead-ends (~34x
                        # accepted moves), but cost 3 pushes it to look elsewhere
    peel_window=6,      # peel a rebuild that came out up to this many masks too
                        # big before judging it (recovers near misses v1 dropped)
    accept="sa",        # "sa" = annealing with reheat (default), or "threshold"
    sa_T0=1.2, sa_cool=0.9997, sa_reheat=4000,
                        # temperature, per-iteration cooling, and the number of
                        # iterations without a new best that triggers a reheat
    up_prob=0.5, up_slack=4,     # the v1 threshold rule; used only if accept="threshold"
    snapback=12,        # restart from best once cur drifts this far above it
    harvest=True,       # append every distinct plateau state to <label>.pop.jsonl
                        # in the run folder (worker.py turns this switch into the
                        # engine's harvest_path; the engines take a path, not a
                        # bool, so that a run always states where it harvested)
    cross_pollinate=False,
                        # merge sibling workers' harvested masks into this
                        # worker's pool. OFF by default: it is a measured-good
                        # diversifier but it mixes the mask provenance of every
                        # worker in the run, so a circuit found afterwards is
                        # only cleanly "ours" if every seed in the run was.
    pop_period_s=120.0, # how often cross-pollination re-reads sibling harvests
)
WALK_KNOBS = dict(
    hub_move_p=0.30,    # probability of a remove-2-add-1 hub move
    close_hamming=8,    # half the hub moves pick the second victim within this
                        # Hamming distance of the first
    plateau_slack_p=0.15,
                        # probability of accepting a +1 move near the best. High
                        # on purpose: with exact repair the equal-size plateau is
                        # walkable (~2-3k distinct states/min), which is where
                        # the 88s came from -- v1's 0.02 was tuned for an engine
                        # whose repair usually failed.
    harvest=True,       # as above: worker.py resolves this to a harvest_path
)
ANNEAL_KNOBS = dict(anneal_iters=150000, ils_rounds=2500, sa_T0=2.0, sa_T1=0.05)
# ==========================================================================
# END CONFIG
# ==========================================================================

HERE = os.path.dirname(os.path.abspath(__file__))

# Optional stop bounds, set from the command line in main(). The coordinator
# stops cleanly once ANY worker holds a verified best satisfying every bound.
#
# It tests every worker's best rather than only the Pareto-global one. The
# global best is a single (gates, depth) pair chosen by `pareto_better`, which
# prefers fewer gates at any depth, so a run that reaches, say, 90 gates at
# depth 6 replaces a 91 at depth 4 in that slot; testing only the global best
# then leaves `--stop-gates 91 --stop-depth 4` unsatisfiable for the rest of
# the run even though a worker is holding exactly the circuit asked for.
STOP_GATES = None
STOP_DEPTH = None


def _within_bounds(g, d):
    return (STOP_GATES is None or g <= STOP_GATES) and \
           (STOP_DEPTH is None or d <= STOP_DEPTH)


def target_reached(state):
    if STOP_GATES is None and STOP_DEPTH is None:
        return False
    for g, d in state.get("hits", ()):
        if _within_bounds(g, d):
            state["hit"] = (g, d)
            return True
    return False


def pareto_better(g2, d2, g1, d1):
    if g1 is None:
        return True
    return g2 < g1 or (g2 == g1 and d2 < d1)


def read_status(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def launch(label, engine, depth, start, out_dir, log, seeds=None):
    seeds = ",".join(str(s) for s in (seeds or SEEDS_PER_WORKER))
    depth_arg = "none" if depth is None else str(depth)
    start_abs = "scratch" if start == "scratch" else os.path.join(HERE, start) \
        if not os.path.isabs(start) else start
    cmd = [sys.executable, os.path.join(HERE, "worker.py"),
           label, engine, depth_arg, start_abs, out_dir, seeds]
    logf = open(os.path.join(out_dir, "%s.stdout" % label), "a")
    proc = subprocess.Popen(cmd, cwd=HERE, stdout=logf, stderr=subprocess.STDOUT)
    log("LAUNCH %-16s engine=%s depth=%s start=%s pid=%d"
        % (label, engine, depth_arg,
           os.path.basename(start) if start != "scratch" else "scratch", proc.pid))
    return proc


def gather_bests(meta):
    """label -> (gates, depth, best_path) for every worker with a verified best."""
    out = {}
    for lbl, m in meta.items():
        st = read_status(m["status_path"])
        if st and st.get("best_gates") is not None:
            out[lbl] = (st["best_gates"], st["best_depth"], m["best_path"])
    return out


def do_reseed(meta, procs, out_dir, log, state):
    """Update best_overall.json and offer each live worker the best circuit that
    is feasible at its depth cap (and Pareto-beats its own best)."""
    bests = gather_bests(meta)
    state["hits"] = [(g, d) for g, d, _ in bests.values()]
    if not bests:
        return
    gb_lbl = min(bests, key=lambda l: (bests[l][0], bests[l][1]))
    gg, gd, gp = bests[gb_lbl]
    if state["gb"] is None or pareto_better(gg, gd, state["gb"][0], state["gb"][1]):
        state["gb"] = (gg, gd)
        shutil.copy(gp, os.path.join(out_dir, "best_overall.json"))
        log("GLOBAL BEST %d gates depth %d (%s) -> best_overall.json" % (gg, gd, gb_lbl))
    if not RESEED:
        return
    for lbl, m in meta.items():
        if procs[lbl].poll() is not None or not m.get("reseed", True):
            continue
        cap = m["cap"]
        own = bests.get(lbl)
        own_g, own_d = (own[0], own[1]) if own else (None, None)
        cands = [(g, d, p) for l2, (g, d, p) in bests.items()
                 if l2 != lbl and (cap is None or d <= cap)]
        if not cands:
            continue
        cg, cd, cp = min(cands, key=lambda t: (t[0], t[1]))
        if pareto_better(cg, cd, own_g, own_d) and state["offer"].get(lbl) != (cg, cd, cp):
            shutil.copy(cp, os.path.join(out_dir, "reseed_%s.json" % lbl))
            state["offer"][lbl] = (cg, cd, cp)
            log("  reseed offer -> %-16s : %d gates depth %d (from %s)"
                % (lbl, cg, cd, os.path.basename(cp)))


def status_row(meta, procs):
    row = []
    for lbl, m in meta.items():
        st = read_status(m["status_path"])
        bg = st["best_gates"] if st else None
        bd = st["best_depth"] if st else None
        up = "up" if procs[lbl].poll() is None else "DOWN"
        row.append("%s=%s/%s(%s)" % (lbl, bg, bd, up))
    return "  ".join(row)


def cleanup(procs, meta, out_dir, log, state):
    for p in procs.values():
        if p.poll() is None:
            p.terminate()
    time.sleep(2)
    for p in procs.values():
        if p.poll() is None:
            p.kill()
    log("==================== FINAL BESTS ====================")
    for lbl in procs:
        st = read_status(meta[lbl]["status_path"])
        if st:
            log("%-16s depth_cap=%s  best=%s gates @ depth %s"
                % (lbl, st["cap"], st["best_gates"], st["best_depth"]))
    if state["gb"]:
        log("BEST OVERALL: %d gates @ depth %d  -> best_overall.json" % state["gb"])
    log("all circuits + logs in: %s" % out_dir)


def make_run():
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(HERE, OUT_ROOT, stamp)
    os.makedirs(out_dir, exist_ok=True)
    # self-archive the EXACT code producing this run (so results are always
    # reproducible from their own folder -- no more in-place-edit ambiguity).
    code_dir = os.path.join(out_dir, "code")
    os.makedirs(code_dir, exist_ok=True)
    for fn in ("mixcolumns_core.py", "engines.py", "worker.py", "ladder_parallel.py"):
        try:
            shutil.copy(os.path.join(HERE, fn), os.path.join(code_dir, fn))
        except Exception:
            pass
    worker_knobs = {w["label"]: w["knobs"] for w in FIXED_WORKERS if w.get("knobs")}
    json.dump({"chunk_s": CHUNK_S, "walk_chunk_s": WALK_CHUNK_S, "reseed": RESEED,
               "knobs": {"lns": LNS_KNOBS, "walk": WALK_KNOBS, "anneal3": ANNEAL_KNOBS},
               "worker_knobs": worker_knobs},
              open(os.path.join(out_dir, "config.json"), "w"), indent=2)
    return out_dir


def run_fixed():
    out_dir = make_run()
    masterlog = open(os.path.join(out_dir, "coordinator.log"), "a", buffering=1)
    t0 = time.time()
    def log(msg):
        line = "[%8.1fs %s] %s" % (time.time() - t0, time.strftime("%H:%M:%S"), msg)
        print(line, flush=True); masterlog.write(line + "\n")
    log("FIXED-mode pipeline (%s) -> %s" % (FIXED_WORKER_SET, out_dir))
    log("workers: %s" % [(w["label"], w["engine"], w["depth"]) for w in FIXED_WORKERS])

    procs, meta = {}, {}
    for w in FIXED_WORKERS:
        lbl = w["label"]
        procs[lbl] = launch(lbl, w["engine"], w["depth"], w["start"], out_dir, log,
                            seeds=w.get("seeds"))
        meta[lbl] = {"cap": w["depth"], "reseed": w.get("reseed", True),
                     "status_path": os.path.join(out_dir, "%s_status.json" % lbl),
                     "best_path": os.path.join(out_dir, "%s_best.json" % lbl)}
    state = {"gb": None, "offer": {}, "hits": []}
    try:
        while True:
            time.sleep(POLL_S)
            log("status: " + status_row(meta, procs))
            do_reseed(meta, procs, out_dir, log, state)
            if target_reached(state):
                log("STOP TARGET reached: %d gates @ depth %d -> shutting down"
                    % state["hit"])
                break
    except KeyboardInterrupt:
        log("Ctrl-C: stopping all workers")
    finally:
        cleanup(procs, meta, out_dir, log, state)


def run_cascade():
    out_dir = make_run()
    masterlog = open(os.path.join(out_dir, "coordinator.log"), "a", buffering=1)
    t0 = time.time()
    def log(msg):
        line = "[%8.1fs %s] %s" % (time.time() - t0, time.strftime("%H:%M:%S"), msg)
        print(line, flush=True); masterlog.write(line + "\n")
    log("CASCADE-mode pipeline -> %s" % out_dir)

    procs, meta = {}, {}
    started_at, baseline = {}, {}
    def rl(d): return "d%d" % d

    d0 = DEPTHS[0]; lbl = rl(d0)
    procs[lbl] = launch(lbl, ENGINE_D3 if d0 == 3 else ENGINE_DEEP, d0, "scratch", out_dir, log)
    meta[lbl] = {"cap": d0, "status_path": os.path.join(out_dir, "%s_status.json" % lbl),
                 "best_path": os.path.join(out_dir, "%s_best.json" % lbl)}
    started_at[lbl] = time.time(); baseline[lbl] = DEPTH3_BASELINE
    frontier_idx = 0; final_launched = False
    state = {"gb": None, "offer": {}, "hits": []}
    try:
        while True:
            time.sleep(POLL_S)
            log("status: " + status_row(meta, procs))
            do_reseed(meta, procs, out_dir, log, state)
            if target_reached(state):
                log("STOP TARGET reached: %d gates @ depth %d -> shutting down"
                    % state["hit"])
                break
            if final_launched:
                continue
            fd = DEPTHS[frontier_idx]; flbl = rl(fd)
            st = read_status(meta[flbl]["status_path"])
            best = st["best_gates"] if st and st.get("best_gates") is not None else None
            target = baseline[flbl] - IMPROVE_BY
            elapsed = time.time() - started_at[flbl]
            if not ((best is not None and best <= target) or elapsed >= MAX_WAIT_S):
                continue
            why = ("hit %d<=%d" % (best, target)) if (best is not None and best <= target) \
                else ("timeout %.0fs" % elapsed)
            if not os.path.exists(meta[flbl]["best_path"]):
                started_at[flbl] = time.time(); continue
            seed_file = os.path.join(out_dir, "seed_from_%s.json" % flbl)
            shutil.copy(meta[flbl]["best_path"], seed_file)
            seed_count = best if best is not None else baseline[flbl]
            if frontier_idx + 1 < len(DEPTHS):
                nd = DEPTHS[frontier_idx + 1]; nlbl = rl(nd)
                log("TRIGGER %s (%s, seed=%d) -> launch %s at depth %d" % (flbl, why, seed_count, nlbl, nd))
                procs[nlbl] = launch(nlbl, ENGINE_DEEP, nd, seed_file, out_dir, log)
                meta[nlbl] = {"cap": nd, "status_path": os.path.join(out_dir, "%s_status.json" % nlbl),
                              "best_path": os.path.join(out_dir, "%s_best.json" % nlbl)}
                started_at[nlbl] = time.time(); baseline[nlbl] = seed_count
                frontier_idx += 1
            elif FINAL_UNCAPPED_DEPTH:
                log("TRIGGER %s (%s, seed=%d) -> launch FINAL (uncapped depth)" % (flbl, why, seed_count))
                procs["final"] = launch("final", ENGINE_DEEP, None, seed_file, out_dir, log)
                meta["final"] = {"cap": None, "status_path": os.path.join(out_dir, "final_status.json"),
                                 "best_path": os.path.join(out_dir, "final_best.json")}
                started_at["final"] = time.time(); baseline["final"] = seed_count
                final_launched = True
            else:
                final_launched = True
    except KeyboardInterrupt:
        log("Ctrl-C: stopping all workers")
    finally:
        cleanup(procs, meta, out_dir, log, state)


def main():
    global STOP_GATES, STOP_DEPTH, FIXED_WORKER_SET, FIXED_WORKERS
    parser = argparse.ArgumentParser(
        description="Record-hunting pipeline for AES MixColumns XOR circuits.")
    parser.add_argument("--mode", choices=("cascade", "fixed"), default=MODE,
                        help="cascade = from-scratch depth ladder (default); "
                             "fixed = a fixed worker set (see --workers)")
    parser.add_argument("--workers", choices=tuple(WORKER_SETS), default=FIXED_WORKER_SET,
                        help="fixed-mode worker set: hunt87 = the three 88-gate "
                             "families chasing 87 + a depth-6 worker (default); "
                             "sub89 = the historic two-worker sub-89 set")
    parser.add_argument("--stop-gates", type=int, default=None, metavar="N",
                        help="stop cleanly once a verified best has <= N gates")
    parser.add_argument("--stop-depth", type=int, default=None, metavar="D",
                        help="stop cleanly once the verified best also has depth <= D")
    args = parser.parse_args()
    STOP_GATES, STOP_DEPTH = args.stop_gates, args.stop_depth
    FIXED_WORKER_SET = args.workers
    FIXED_WORKERS = WORKER_SETS[FIXED_WORKER_SET]

    os.makedirs(os.path.join(HERE, OUT_ROOT), exist_ok=True)
    if args.mode == "fixed":
        run_fixed()
    else:
        run_cascade()


if __name__ == "__main__":
    main()
