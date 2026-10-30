"""Shared fixtures for the local-move tests (walk, lns, rebuild, depth) and their benchmark.

Not a test suite itself: the controls live in ``test_moves_local_controls.py`` and the randomized
invariants in ``test_moves_local_random.py``.  Everything here builds plain kernel objects so a
move can be exercised without the engine: a trimmed ``ValueSet``, a ``MoveContext`` with a work
budget, settings over only the local-move sections, and an independent check of a state through
``core.circuit.verify``.
"""
import random

from xorflux.config.settings import for_sections
from xorflux.core.budget import Budget
from xorflux.core.circuit import Circuit, verify
from xorflux.core.objective import Objective
from xorflux.core.target import Target
from xorflux.core.valueset import ValueSet
from xorflux.moves import depth, lns, rebuild, walk
from xorflux.moves.base import MoveContext

SECTIONS = tuple(walk.KNOBS) + (lns.KNOBS, rebuild.KNOBS, depth.KNOBS)

# Every local move class, by registry name.
MOVES = {cls.name: cls for cls in (walk.RemoveOne, walk.Expand, lns.LNSRebuild,
                                   depth.DepthRepair)}


def settings(overrides=None):
    """Settings over the local-move sections only, with optional ``{key: value}`` overrides."""
    return for_sections(*SECTIONS, overrides=overrides)


def target_of(n, rows, name="toy"):
    """A ``core.target.Target`` for hand-made rows."""
    return Target.make(name, n, rows)


def make_state(n, rows, values, cap=None, pairsums=True):
    """Trimmed ValueSet over ``values`` (targets are added by the kernel)."""
    vs = ValueSet(n, rows, values, cap=cap, pairsums=pairsums)
    vs.trim()
    return vs


def context(move, state, seed, objective=None, work=10 ** 6, target=None):
    """MoveContext for one proposal: fresh RNG from ``seed`` and a work budget."""
    return MoveContext(state=state, target=target, objective=objective or Objective(),
                       best_key=(), rng=random.Random(seed), cfg=move.cfg,
                       budget=Budget(work), settings=move.settings)


def frozen(vs):
    """Observable state for exact before/after comparisons (levels, witnesses, index, cap).

    The lazy pair-sum counter is left out on purpose: a repair query may fold pending changes
    into its committed base (``p2_sync``), which changes its bookkeeping but not its meaning;
    ``check()`` verifies the counter itself.
    """
    return (dict(vs.level), dict(vs.par), {k: frozenset(v) for k, v in vs.kids.items()},
            {k: frozenset(v) for k, v in vs.tri.items()}, vs.cap)


def check_state(case, target, vs, cap):
    """Assert that ``vs`` is a valid trimmed circuit for ``target`` within ``cap``.

    Independent replay through ``core.circuit.verify`` (no kernel code), plus the kernel's own
    from-scratch invariant check and the trimmed-state contract of DESIGN 4.3.
    """
    case.assertTrue(vs.ok(), "state does not realise every target")
    vs.check()
    case.assertEqual(vs.count(), vs.size(), "state not trimmed (dead or stuck values left)")
    verdict = verify(Circuit(vs.n, *vs.gates()), target, cap=cap)
    case.assertTrue(verdict.ok, verdict.reason)
    case.assertEqual(verdict.live_gates, vs.size())
    case.assertEqual(verdict.dead_gates, 0)
    case.assertEqual(verdict.depth, vs.depth())


def propose_many(case, cls, n, rows, values, seeds, cap=None, overrides=None,
                 objective=None):
    """Run one fresh proposal per seed from the same start; return the (gates, depth) results
    of every proposal that edited the state (each verified, then rolled back exactly)."""
    s = settings(overrides)
    target = target_of(n, rows)
    out = []
    for seed in seeds:
        move = cls(s)
        vs = make_state(n, rows, values, cap=cap)
        before = frozen(vs)
        prop = move.propose(context(move, vs, seed, objective, target=target))
        case.assertIsNotNone(prop)
        if prop.journal is None:
            case.assertEqual(frozen(vs), before, "journal-free proposal changed the state")
            continue
        check_state(case, target, vs, cap)
        out.append((vs.size(), vs.depth()))
        vs.rollback(prop.journal)
        case.assertEqual(frozen(vs), before, "rollback did not restore the state")
    return out
