"""Benchmark of the local moves on real seeds: proposals/s and improvement rate per move.

Not run by the test suite.  Usage (from search/):

    python3 -m xorflux.tests.bench_moves_local [SECONDS] [CASE ...] [--cap seed|none]
        [--move NAME ...] [--set key=value ...] [--profile]

Each (case, move) pair runs a single chain for SECONDS of wall time with a simple walk-style
acceptance (keep the proposal when it does not add gates, else roll it back), so the numbers
measure the move, not an acceptance policy.  Reported per pair:

    prop/s     proposals per second (every call, including no-ops)
    edit%      proposals that changed the state
    neutral%   accepted proposals with equal gates (plateau steps)
    better     proposals with fewer gates than the chain had (count) and the best gates reached
    ms/prop    mean milliseconds per proposal

Reference numbers measured for earlier versions (it/s, cap none; legacy and v2 are older engines):

    engine            joltik44   invmc88   fox_mu8 540
    legacy-walk           55.0       9.0        0.4
    v2-walk              216.0      61.0        3.0
    legacy-lns           177.8      48.0        4.7
    v2-lns (40 ms)        33.7      27.7       22.1
    proto walk          3824       695        119
    proto lns           1211       751        285
"""
import cProfile
import pstats
import random
import sys
import time

from xorflux.config.settings import parse_assignment
from xorflux.core.budget import Budget
from xorflux.core.objective import Objective
from xorflux.core.target import load_target
from xorflux.tests import fixtures
from xorflux.core.valueset import ValueSet
from xorflux.tests.test_moves_local_util import MOVES, context, settings

CASES = {               # name -> (target id, seed gates, seed depth)
    "joltik44": ("joltik", 44, 7),
    "invmc88": ("aes-invmixcolumns", 88, 19),
    "foxmu4_130": ("fox-mu4", 130, 13),
    "foxmu8_540": ("fox-mu8", 540, 14),
}


def load_case(name, cap_mode):
    """(target, start ValueSet, cap) for a case; ``cap_mode`` is ``none`` or ``seed``."""
    tid, gates, depth = CASES[name]
    target = load_target(tid)
    seed = next(s for s in fixtures.seeds(target) if s.gates == gates and s.depth == depth)
    cap = depth if cap_mode == "seed" else None
    return target, seed.load(target.n_inputs), cap


def run(target, circuit, cap, name, seconds, seed=1, overrides=None):
    """One chain of ``name`` proposals; returns a result dict."""
    s = settings(overrides)
    move = MOVES[name](s)
    vs = ValueSet(target.n_inputs, target.rows, circuit.masks(), cap=cap,
                  pairsums=name.startswith("walk."))
    vs.trim()
    objective = Objective(depth_cap=cap)
    rng = random.Random(seed)
    g = start = best = vs.size()
    props = edits = neutral = better = 0
    sources = {}
    t0 = time.perf_counter()
    end = t0 + seconds
    while time.perf_counter() < end:
        props += 1
        ctx = context(move, vs, rng.getrandbits(32), objective, target=target)
        ctx.budget = Budget(1_000_000)
        prop = move.propose(ctx)
        if prop is None or prop.journal is None:
            continue
        edits += 1
        src = prop.trace.get("rebuild")
        if src is not None:
            sources[src] = sources.get(src, 0) + 1
        g1 = vs.size()
        if g1 <= g:
            vs.commit(prop.journal)
            if g1 < g:
                better += 1
            else:
                neutral += 1
            g = g1
            best = min(best, g)
        else:
            vs.rollback(prop.journal)
    el = time.perf_counter() - t0
    return {"move": name, "props": props, "rate": props / el, "edit": edits / max(props, 1),
            "neutral": neutral / max(props, 1), "better": better, "start": start, "best": best,
            "ms": 1000 * el / max(props, 1), "sources": sources}


def main(argv):
    seconds = 5.0
    cases = []
    moves = []
    cap_mode = "none"
    profile = False
    overrides = {}
    it = iter(argv)
    for arg in it:
        if arg == "--cap":
            cap_mode = next(it)
        elif arg == "--move":
            moves.append(next(it))
        elif arg == "--set":
            key, value = parse_assignment(next(it))
            overrides[key] = value
        elif arg == "--profile":
            profile = True
        elif arg in CASES:
            cases.append(arg)
        else:
            seconds = float(arg)
    cases = cases or list(CASES)
    moves = moves or list(MOVES)
    print("%-11s %-13s %8s %6s %8s %7s %9s %8s" % ("case", "move", "prop/s", "edit%",
                                                  "neutral%", "better", "start>best",
                                                  "ms/prop"))
    for case in cases:
        target, circuit, cap = load_case(case, cap_mode)
        for name in moves:
            if profile:
                prof = cProfile.Profile()
                prof.enable()
            r = run(target, circuit, cap, name, seconds, overrides=overrides)
            if profile:
                prof.disable()
            print("%-11s %-13s %8.1f %6.1f %8.1f %7d %4d>%-4d %8.2f" % (
                case, name, r["rate"], 100 * r["edit"], 100 * r["neutral"], r["better"],
                r["start"], r["best"], r["ms"]), r["sources"] or "", flush=True)
            if profile:
                pstats.Stats(prof).sort_stats("tottime").print_stats(12)


if __name__ == "__main__":
    main(sys.argv[1:])
