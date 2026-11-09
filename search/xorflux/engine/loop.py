"""The one search loop: a chain, a move per step, accept or undo, record what improves.

Role in the method (DESIGN.md section 2).  A worker runs one Engine.  The engine owns one *chain*
(a ``ValueSet`` built at ``objective.search_cap``, the real depth cap plus the soft slack) and
every move acts on it; there are no private per-move trajectories (59% of framework engine slots
ended >=5 gates behind their worker best because they had them).  The loop knows nothing about
a particular target: any GF(2) linear map that ``core.target`` loads runs through it.

One ``step()``:

1. the scheduler picks a move for the current phase;
2. with ``engine.replay_seeds`` the proposal RNG is reseeded with a fresh 63-bit seed drawn from
   the engine RNG; the seed is the replay handle kept in dossiers.  This is the largest fixed
   cost of a step (about 4.6 us: seeding a Mersenne Twister initialises its 624-word state;
   ``setstate`` from a tuple, ``getstate`` and fresh ``Random`` objects all cost as much or
   more), still small next to a proposal (0.25-10 ms);
3. the move edits the state speculatively and returns a Proposal (trace + undo journal);
4. the state is scored (``count()``, ``depth()``); unrealizable or over-gate-limit states are
   rolled back; a new feasible worker best is kept, otherwise the acceptance policy decides and
   rejected proposals are rolled back;
5. a kept state may be a new chain best (archive, plateau closes, burst or repair phase), a new
   worker best (best *feasible* state under the real objective) or a new nondominated point
   (at its own depth, which may exceed the real cap).  For those the journal is rolled back once to read the values before and the
   after-state is rebuilt (``dossier.DossierMixin._found``); after ``recorder.proposal`` the
   dossier and the verified record go out together (``_report``).  Distinct DAGs at the
   worker-best point are sampled into records too;
6. scheduler credit, phase budget, ``recorder.proposal``, plateau tracking;
7. every ``periodic_every`` proposals: clock read, restart check, epochs.

The hot path is attribute access and a handful of calls; everything that copies the value set
(``values()``, ``key()``, ``gates()``, rebuilding a state) happens on rare events only.

Phase state machine (phase.py): start/restart -> burst; new chain best -> burst; burst budget
spent -> plateau; new chain best that beats the worker best but breaks the real cap -> repair;
repair -> burst on a feasible worker best, -> plateau when its budget is spent.  Restarts
(restart.py) start a new chain from a fresh root, an archive elite, a pool elite or the worker
best; the worker best, frontier and archive persist across chains.

Calls made into other modules (integration contract):

* ``ValueSet(n_inputs, rows, values, cap=, pairsums=)``, ``trim()`` after every build, then
  ``ok() count() size() depth() key() values() gates() rollback(j) commit(j) check()``;
* ``objective.key(gates, depth)``, ``feasible(gates, depth)``, ``search_cap``, ``gate_limit``,
  ``kind``;  ``target.n_inputs``, ``target.rows``;
* ``move.applicable(target, objective)``, ``propose(ctx)``, ``state()``, ``load_state(d)``,
  ``move.cfg`` knobs ``weight`` / ``burst_weight`` / ``repair_weight``;
* ``construct.choose_root(rng, settings, target, cap)``,
  ``construct.build_root(name, target, rng, cap, budget, settings) -> (values, info)``;
* ``recorder.proposal(rec) improvement(dossier, verify=) event(ev, **f) epoch_due() epoch(f)
  now()``, optionally ``set_epoch_source(fn)`` and ``chain_id``;
  ``metrics.PlateauTracker.from_settings(settings)`` with ``enter observe snapshot close
  checkpoint restore``;  ``metrics.diversity``, ``metrics.shape_from_gates``;
* ``pool.sample(exclude_keys, rng) -> elite dict | None``.
"""
from __future__ import annotations

import _random
import random
import time
from dataclasses import dataclass
from time import perf_counter
from typing import Callable

from ..config.schema import Knob, Section
from ..core.budget import Budget
from ..moves.base import MoveContext
from ..telemetry import metrics
from .acceptance import Threshold
from .archive import Archive, distance
from .dossier import DossierMixin, score
from .phase import BURST, PLATEAU, REPAIR, PhaseController, phase_priors
from .restart import RestartController
from .scheduler import Scheduler, Tightness

KNOBS = (
    Section("engine", "The search loop.", {
        "proposal_work": Knob(1_000_000, "Work budget of one proposal (safety net; moves bound "
                              "themselves with their own knobs). 0 = unbounded.", min=0),
        "proposal_seconds": Knob(1.0, "Wall-clock limit of one proposal when budget.mode = "
                                 "time (such proposals are marked non-deterministic).", min=0),
        "seed_repair_tries": Knob(8, "A seed deeper than the search cap is rebuilt one level at a "
                                  "time with depth repair, this many banks per level, before a "
                                  "fresh root replaces it (2026-10-29 hunt: every 88@5 seed of "
                                  "a cap-4 group was silently replaced). 0: reject as before.",
                                  min=0),
        "seed_repair_work": Knob(20_000_000, "Work budget of one seed repair.", min=1),
        "replay_seeds": Knob(True, "Reseed a per-proposal RNG from the engine RNG so every "
                             "dossier carries a replay seed (about 4.6 us per proposal)."),
        "replay_move_state": Knob("full", "Move memory (LNS pool/hot list, depth3 partition) "
                                  "stored with an improvement for replay: full (the snapshot "
                                  "and its digest), digest (SHA-256 only), off.",
                                  choices=("full", "digest", "off")),
        "periodic_every": Knob(64, "Proposals between clock reads, restart checks and epoch "
                               "checks.", min=1),
        "gate_limit_slack": Knob(0, "The chain may exceed objective.gate_limit by this many "
                                 "gates while searching (records still obey the limit).",
                                 min=0),
        "depth_window": Knob(2, "Reject non-improving moves that take the chain more than this "
                             "many levels deeper than its best (null: no window). 2026-10-28: "
                             "an InvMixColumns 88@20 chain spent 90% of 100 min at depth 28-36 "
                             "and made no depth tie-break; every record-level tie-break came "
                             "from within one level of the best.", kind=int, nullable=True,
                             min=0),
        "frontier": Knob(True, "Record new nondominated (gates, depth) points at their own depth "
                         "(also deeper than the real cap), not only worker-best improvements."),
        "frontier_band": Knob(10, "Only points within this many gates of the worker best count "
                              "as frontier points (constructor points +69..+595 gates above "
                              "the best were useless; v2-translate's useful ones were +2..+9).",
                              min=0),
        "record_polish_nodes": Knob(20_000, "Own-depth polish of new worker bests and frontier "
                                    "points below the search cap: branch-and-bound nodes spent "
                                    "on the fewest gates that keep the point's depth (0 = off). "
                                    "2026-10-30: 5 of 32 kept circuits recorded below their "
                                    "chain's cap lost 1-2 gates this way (engine/polish.py).",
                                    min=0),
        "record_stride": Knob(16, "Kept state-changing moves at the worker-best point between "
                              "distinct-DAG samples (spreads records over the plateau).", min=1),
        "records_per_point": Knob(32, "Distinct DAGs sampled at each worker-best point (records "
                                  "held 90-154 distinct DAGs per best point; restarts and the "
                                  "pool draw on them).", min=0),
        "plateau_key_every": Knob(8, "Kept neutral moves between state keys passed to the "
                                  "plateau tracker (a key costs 8-50 us).", min=1),
        "plateau_event_min": Knob(50, "Plateaus shorter than this many proposals close without "
                                  "a plateau event (descents would flood the log).", min=0),
        "pairsums": Knob("auto", "Pair-sum index in the chain state. auto: on when a walk move "
                         "runs and |U| <= pairsums_max_values.", choices=("auto", "on", "off")),
        "pairsums_max_values": Knob(1200, "Largest |U| for which auto enables the index "
                                    "(42 MB per process at 1,100 values).", min=0),
        "canonical_checkpoint": Knob(True, "Rebuild the chain state from its values at every "
                                     "checkpoint so a resumed engine continues exactly like "
                                     "the running one."),
    }),
    Section("debug", "Self-checks (slow; off by default).", {
        "check_every": Knob(0, "Run the state's full invariant check every this many proposals "
                            "(0 = never).", min=0),
    }),
)

CHECKPOINT_VERSION = 1

# ``random.Random.seed`` without the Python wrapper (the wrapper only adds type checks for
# str/bytes and resets ``gauss_next``, which ``step`` does itself): same state as
# ``random.Random(seed)``, so dossier seeds replay exactly.
_seed_rng = _random.Random.seed


@dataclass(slots=True)
class StepResult:
    """Outcome of one proposal."""
    it: int
    move: str
    phase: str
    gates_before: int
    depth_before: int
    gates_after: int
    depth_after: int
    valid: bool               # the move produced a Proposal
    accepted: bool
    neutral: bool             # kept with an unchanged primary score
    improved_chain: bool
    improved_worker: bool     # new worker best
    work: int

    @property
    def before(self) -> tuple:
        """(gates, depth) before the proposal."""
        return (self.gates_before, self.depth_before)

    @property
    def after(self) -> tuple:
        """(gates, depth) of the chain after the step."""
        return (self.gates_after, self.depth_after)

    @property
    def improved(self) -> bool:
        """A new worker best (the campaign worker's ``improved`` counter)."""
        return self.improved_worker


def _seed_values(seed, n: int) -> list[int]:
    """Non-input values of a seed: a circuit JSON dict (index-pair ``gates``), a dict or object
    with ``values``, an object with ``gates`` (e.g. ``core.circuit.Circuit``) or masks."""
    get = seed.get if isinstance(seed, dict) else (lambda k, d=None: getattr(seed, k, d))
    values = get("values")
    if values is not None:
        return [int(v) for v in (values() if callable(values) else values)]
    gates = get("gates")
    if gates is not None:
        masks = [1 << i for i in range(n)]
        for a, b in (gates() if callable(gates) else gates):
            masks.append(masks[a] ^ masks[b])
        return masks[n:]
    return [int(v) for v in seed]


def valueset_factory(target, settings, walk: bool) -> Callable:
    """``make(values, cap) -> ValueSet`` for ``target``; the pair-sum index follows
    ``engine.pairsums`` (only walk moves need it)."""
    from ..core.valueset import ValueSet
    cfg = settings.view("engine")
    mode = cfg.pairsums
    limit = cfg.pairsums_max_values
    n = target.n_inputs
    rows = target.rows

    def make(values, cap):
        values = list(values)
        pairs = mode == "on" or (mode == "auto" and walk and n + len(values) <= limit)
        return ValueSet(n, rows, values, cap=cap, pairsums=pairs)
    return make


def canonical_state(factory: Callable, values, cap):
    """A chain state as the engine builds it: from *sorted* values (a rebuilt state never
    depends on how the values were stored, which keeps resumed runs and replays on the same
    trajectory) and trimmed (seeds may carry dead gates, and the loop scores with the O(1)
    ``count()``, exact only on trimmed states)."""
    state = factory(sorted(values), cap)
    trim = getattr(state, "trim", None)
    if trim is not None:
        trim()
    return state


def _level1(values) -> set[int]:
    """The level-1 set of a value collection: its weight-2 masks (XORs of two inputs)."""
    return {v for v in values if v.bit_count() == 2}


def _rng_to_json(state) -> list:
    version, internal, gauss = state
    return [version, list(internal), gauss]


def _rng_from_json(data) -> tuple:
    version, internal, gauss = data
    return (version, tuple(internal), gauss)


class Engine(DossierMixin):
    """One worker's search: chain, moves and policies (DESIGN.md section 4.4).

    Improvement bookkeeping, dossiers and records live in ``dossier.DossierMixin``.

    Optional keyword hooks (defaults in brackets), for tests and special campaigns:
    ``moves`` [every registered applicable move], ``state_factory`` [``valueset_factory``],
    ``construct`` [``xorflux.moves.construct``], ``plateau_tracker`` [a zero-argument factory;
    ``PlateauTracker.from_settings``].
    """

    # ------------------------------------------------------------------ construction ----
    def __init__(self, target, objective, settings, *, rng_seed, recorder, worker_id,
                 seed_circuit=None, pool=None, moves=None, state_factory=None, construct=None,
                 plateau_tracker=None):
        self._setup(target, objective, settings, recorder, worker_id, pool, moves,
                    state_factory, construct, plateau_tracker)
        self.rng_seed = rng_seed
        self.rng = random.Random(rng_seed)
        self._bind_rng()
        self._t = recorder.now()
        state, root, source = self._initial_state(seed_circuit)
        self._begin_chain(state, root, source, None)
        if self._feasible(self.cur_g, self.cur_d):
            if source == "seed" and not (isinstance(seed_circuit, dict)
                                         and seed_circuit.get("constructor")):
                # A seed circuit: the worker records it itself (kind "seed").
                self._set_worker_best(self.cur_g, self.cur_d, self.cur_key, self.chain_best_values)
            else:
                # A constructed root (fresh, or a campaign "root" seed given as values) is a
                # discovery like a restart's root, reported once a record callback exists
                # (on_record).  2026-10-28: a cap-3 worker's 101@3 root was never recorded
                # and the worker ended a 2-hour run with no best at all.
                self._root_found = self._found(
                    None, {"components": [f"root.{source}"], "root": root}, 0, True, None,
                    self.phase.phase, None, None, None, True)
        # A fresh chain is a fresh start: harvest it with a burst, as after a restart.
        self._phase_event(self.phase.on_restart(), PLATEAU, "start")

    def _setup(self, target, objective, settings, recorder, worker_id, pool, moves,
               state_factory, construct, plateau_tracker):
        """Everything that does not depend on the chain (shared by __init__ and resume)."""
        self.target = target
        self.objective = objective
        self.settings = settings
        self.recorder = recorder
        self.worker_id = worker_id
        self.pool = pool
        self._root_found = None         # a constructed initial root waiting for on_record
        self._repair_expired = False    # a repair ran out: revert at the next periodic check
        self._repair_misses = 0         # expired repairs in a row with nothing to revert to
        self._repair_exit = settings["restart.repair_exit"]
        self._n = target.n_inputs
        cfg = settings.view("engine")
        self._proposal_work = cfg.proposal_work or None
        self._time_budget = settings["budget.mode"] == "time"
        self._proposal_seconds = cfg.proposal_seconds
        self._check_every = settings["budget.check_every"]
        self._periodic_every = cfg.periodic_every
        self._frontier_on = cfg.frontier
        self._frontier_band = cfg.frontier_band
        self._polish_nodes = cfg.record_polish_nodes
        self._depth_window = cfg.depth_window
        self._record_stride = cfg.record_stride
        self._records_per_point = cfg.records_per_point
        self._plateau_key_every = cfg.plateau_key_every
        self._plateau_event_min = cfg.plateau_event_min
        self._canonical = cfg.canonical_checkpoint
        self._seed_repair_tries = cfg.seed_repair_tries
        self._seed_repair_work = cfg.seed_repair_work
        self._replay_move_state = cfg.replay_move_state
        self._debug_every = settings["debug.check_every"]
        limit = objective.gate_limit
        self._gate_limit = None if limit is None else limit + cfg.gate_limit_slack
        self._key = objective.key
        self._feasible = objective.feasible
        self._cap = objective.search_cap
        self._depth_first = objective.kind != "gates"

        # Moves: applicable ones with a nonzero weight in some phase.
        if moves is None:
            from ..moves.base import load_all
            moves = [cls(settings) for cls in load_all().values()]
        phase_cfg = settings.view("phase")
        kept = []
        for move in moves:
            reason = move.applicable(target, objective)
            if reason is not None:
                recorder.event("move", move=move.name, status="inapplicable", reason=reason)
            else:
                kept.append(move)
        priors = phase_priors(kept, phase_cfg)
        on = [any(priors[p][i] > 0 for p in priors) for i in range(len(kept))]
        for move, active in zip(kept, on):
            if not active:
                recorder.event("move", move=move.name, status="off", reason="zero weight")
        kept = [m for m, active in zip(kept, on) if active]
        if not kept:
            raise ValueError("no applicable move with a nonzero weight")
        priors = phase_priors(kept, phase_cfg)
        self._moves = kept
        self.scheduler = Scheduler(settings.view("scheduler"), [m.name for m in kept], priors)
        self._tightness = Tightness(settings.view("scheduler"))
        # Charge proposals their measured time unless replayable scheduling was asked for.
        self._cost_seconds = settings["scheduler.cost"] == "seconds"
        self.phase = PhaseController(phase_cfg, priors)
        self._repair_monotone = phase_cfg.repair_monotone
        self.acceptance = Threshold(settings.view("acceptance"))
        self.archive = Archive(settings.view("archive"))
        self.restarter = RestartController(settings.view("restart"))
        self._build_work = settings.view("restart").build_work or None
        # The pinned phase of a foundation restart (None: no restriction anywhere).  A dict
        # with ``allowed`` (frozenset), ``start``/``until`` (proposal counts) and ``length``.
        self._pin = None
        self._pending_pin = None        # set by the foundation source, taken by _restart
        self._useful = None             # useful weight-2 pairs of the target (lazy)

        if state_factory is None:
            state_factory = valueset_factory(target, settings,
                                             any(m.family == "walk" for m in kept))
        else:
            self._polish_nodes = 0              # the polish builds ValueSets of its own
        self._state_factory = state_factory
        if construct is None:
            try:
                from ..moves import construct
            except ImportError:            # no constructors: restarts use the other sources
                construct = None
        self._construct = construct
        if plateau_tracker is None:
            self._plateau = metrics.PlateauTracker.from_settings(settings)
        else:
            self._plateau = plateau_tracker()

        self._prng = random.Random(0) if cfg.replay_seeds else None
        self._ctxs = [MoveContext(state=None, target=target, objective=objective, best_key=(),
                                  rng=None, cfg=m.cfg, budget=None, archive=self.archive,
                                  phase=PLATEAU, settings=settings) for m in kept]
        self._callbacks: list[Callable] = []
        self.counters = {"noop": 0, "invalid": 0, "infeasible": 0, "gate_limit": 0,
                         "restarts": 0, "restart_failed": 0, "verify_fail": 0,
                         "records": 0, "frontier": 0, "improvements": 0, "polished": 0,
                         "chain_improvements": 0, "pulls": 0, "pull_empty": 0}
        self.it = 0
        self.work_total = 0
        self.chain_seq = 0
        self.last_improvement = None
        # value set -> id of the improvement that reached it (lineage parent of restarts)
        self._improvement_of: dict = {}
        self.worker_best_key = self.worker_best_values = None
        self.worker_best_g = self.worker_best_d = None
        self.frontier: list[tuple[int, int]] = []
        # Points found dominated by the frontier.  The frontier only gains nondominated
        # points, so a dominated point stays dominated (cleared when a rejected improvement
        # restores an older frontier): neutral plateau moves skip the frontier scan.
        self._dominated: set | None = set()
        self._best_seen: set[int] = set()
        self._at_best = 0
        self._pk = 0
        self._plateau_closed: dict | None = None   # closed by a chain best, emitted after it
        source = getattr(recorder, "set_epoch_source", None)
        if source is not None:
            source(self.epoch_fields)

    def _make_state(self, values, cap):
        """A canonical chain state from ``values`` (see ``canonical_state``), under the level-1
        restriction while a foundation pin is active."""
        state = canonical_state(self._state_factory, values, cap)
        if self._pin is not None:
            state.restrict_level1(self._pin["allowed"])
        return state

    def _bind_rng(self) -> None:
        """Point every move context at the proposal RNG (the reseeded ``_prng``, or the engine
        RNG itself without replay seeds)."""
        rng = self._prng if self._prng is not None else self.rng
        for ctx in self._ctxs:
            ctx.rng = rng

    def _set_state(self, state) -> None:
        """Make ``state`` the chain state (every move context points at it)."""
        self.state = state
        self._commit = getattr(state, "commit", None)
        self._size = getattr(state, "count", None) or state.size
        for ctx in self._ctxs:
            ctx.state = state

    def _initial_state(self, seed_circuit):
        if seed_circuit is not None:
            values = _seed_values(seed_circuit, self._n)
            state = self._make_state(values, self._cap)
            if state.ok():
                return state, {"id": "seed"}, "seed"
            state = self._repair_seed(values)
            if state is not None:
                return state, {"id": "seed", "repaired": True}, "seed"
            self.recorder.event("seed_rejected", reason="unrealizable at the search cap",
                                cap=self._cap)
        built = self._build_root()
        if built is None:
            raise ValueError("no usable seed and no root constructor")
        values, root = built
        state = self._make_state(values, self._cap)
        if not state.ok():
            raise ValueError(f"root {root['id']} is unrealizable at the search cap")
        return state, root, "fresh"

    def _repair_seed(self, values):
        """A state at the search cap rebuilt from a seed that is too deep for it, or None.

        Depth repair lowers the seed one level at a time on an uncapped copy (one long jump
        from 88@5 to depth 4 failed 60 of 60 times on MixColumns)."""
        if not self._seed_repair_tries or self._cap is None:
            return None
        from ..moves.depth import DepthRepair
        repair = next((m for m in self._moves if isinstance(m, DepthRepair)), None)
        if repair is None:
            repair = DepthRepair(self.settings)
        state = self._make_state(values, None)
        if not state.ok():
            return None
        g0, d0 = state.count(), state.depth()
        budget = Budget(self._seed_repair_work, None, None, self._check_every)
        started = perf_counter()
        ok = repair.repair_to(state, self._cap, self.rng, budget, self._seed_repair_tries)
        fields = {"before": score(g0, d0), "cap": self._cap, "work": budget.used,
                  "seconds": round(perf_counter() - started, 3)}
        if ok:
            state = self._make_state(state.values(), self._cap)
            ok = state.ok()
        if not ok:
            self.recorder.event("seed_repair_failed", **fields)
            return None
        self.recorder.event("seed_repaired", after=score(state.count(), state.depth()),
                            **fields)
        return state

    def _build_root(self):
        """``(values, root_info)`` from a fresh randomized constructor root, or None."""
        construct = self._construct
        if construct is None:
            return None
        name = construct.choose_root(self.rng, self.settings, self.target, self._cap)
        seed = self.rng.getrandbits(32)
        budget = Budget(self._build_work, None, None, self._check_every)
        started = perf_counter()
        try:
            values, info = construct.build_root(name, self.target, random.Random(seed),
                                                self._cap, budget, self.settings)
        except ValueError as exc:
            self.recorder.event("root_failed", constructor=name, seed=seed, reason=str(exc))
            return None
        root = {"id": f"{name}#{seed}", "constructor": name, "seed": seed,
                "built": info.get("built", name), "gates": info.get("gate_count"),
                "depth": info.get("depth"), "fallback": info.get("fallback"),
                "build_s": round(perf_counter() - started, 6)}
        return list(values), root

    def _begin_chain(self, state, root, source, donor) -> None:
        """Start a chain on ``state`` (construction or restart).  A start below the search cap
        is polished at its own depth first (roots and restarts become records too)."""
        if self._polish_nodes:
            g = state.count()
            values, polish = self._polish(state.key(), g, state.depth())
            if polish is not None:
                state = self._make_state(values, self._cap)
                polish["to"] = score(state.count(), state.depth())
                root = {**(root or {}), "polish": polish}
        self._set_state(state)
        # Root construction can take seconds: the chain's timers start now, not before it.
        self._t = t = self.recorder.now()
        g, d = self._size(), state.depth()
        key = self._key(g, d)
        self.chain_seq += 1
        self.root = root
        self.source = source
        self.donor = donor
        self.cur_g, self.cur_d, self.cur_key = g, d, key
        values = state.key()
        self.root_values = values
        self.chain_best_key, self.chain_best_g, self.chain_best_d = key, g, d
        self.chain_best_values = values
        self.chain_improvements = 0
        self._repair_misses = 0
        self.acceptance.set_best(key[0])
        self.restarter.started(self.it, self.work_total, t)
        self._plateau.enter(key, values, self.it, t)
        self._plateau_it = self.it
        self.archive.offer(values, g, d, key, self._feasible(g, d), f"chain{self.chain_seq}")

    # ------------------------------------------------------------------ hooks -----------
    def on_record(self, callback: Callable[[dict], dict | None]) -> None:
        """Register ``callback(record) -> entry | None`` (the worker's ``RecordWriter.save``).

        Called for every new worker best and frontier point (while its dossier is being
        written: ``record["dossier"]`` and ``record["ref"]`` are the improvement id, and the
        return value becomes the dossier's ``verification``) and for sampled distinct DAGs at
        the worker-best point (``dossier`` None).  ``record`` has ``kind``, ``circuit``
        (circuit JSON: ``inputCount``, ``gates``, ``outputSignals``, ``gateCount``, ``depth``),
        ``gate_count``, ``depth``, ``values``, ``it``, ``move``, ``worker``, ``chain``,
        ``root``.  A return value with ``ok`` or ``equivalent`` False rejects it: the worker
        best is reverted and the chain restarts on a clean state; ``None`` (skipped, or no
        verifier) accepts.
        """
        self._callbacks.append(callback)
        found, self._root_found = self._root_found, None
        if found is not None:
            self._report(found)

    def snapshot(self) -> dict:
        """Small status summary (``status.json``; scores as ``[gates, depth]``)."""
        return {"it": self.it, "work": self.work_total, "chain": self.chain_seq,
                "root": self.root.get("id"), "source": self.source, "phase": self.phase.phase,
                "cur": [self.cur_g, self.cur_d],
                "chain_best": [self.chain_best_g, self.chain_best_d],
                "worker_best": (None if self.worker_best_key is None
                                else [self.worker_best_g, self.worker_best_d]),
                "frontier": [list(p) for p in self.frontier]}

    # ------------------------------------------------------------------ the loop --------
    def run(self, stop: Callable[[], bool]) -> None:
        """Step until ``stop()`` is true (checked between proposals, so a stop never cuts a
        proposal in half)."""
        step = self.step
        while not stop():
            step()

    def step(self) -> StepResult:
        """One proposal through accept/undo/record (see the module docstring)."""
        self.it = it = self.it + 1
        rng = self.rng
        phase = self.phase.phase
        idx = self.scheduler.pick(phase, rng)
        move = self._moves[idx]
        ctx = self._ctxs[idx]
        prng = self._prng
        if prng is not None:
            seed = rng.getrandbits(63)
            _seed_rng(prng, seed)
            prng.gauss_next = None
        else:
            seed = None
        ctx.best_key = self.chain_best_key
        ctx.phase = phase
        ctx.budget = budget = Budget(
            self._proposal_work,
            time.monotonic() + self._proposal_seconds if self._time_budget else None,
            None, self._check_every)
        g0, d0, key0 = self.cur_g, self.cur_d, self.cur_key
        g1, d1 = g0, d0
        valid = accepted = neutral = uphill = False
        chain = worker = frontier = changed = False
        components = None
        found = None

        t0 = perf_counter()
        prop = move.propose(ctx)

        if prop is None:
            work = budget.used or 1
            self.counters["invalid"] += 1
        else:
            valid = True
            work = prop.work or 1
            trace = prop.trace
            components = trace.get("components")
            journal = prop.journal
            st = self.state
            if journal is None:
                self.counters["noop"] += 1
            elif not st.ok():
                st.rollback(journal)
                self.counters["infeasible"] += 1
            else:
                g1 = self._size()
                d1 = st.depth()
                limit = self._gate_limit
                if limit is not None and g1 > limit:
                    st.rollback(journal)
                    self.counters["gate_limit"] += 1
                    g1, d1 = g0, d0
                else:
                    key1 = self._key(g1, d1)
                    better = key1 < key0
                    feasible = self._feasible(g1, d1)
                    wkey = self.worker_best_key
                    worker = feasible and (wkey is None or key1 < wkey)
                    # A new feasible worker best is kept whatever the chain's acceptance says.
                    # 2026-10-28: cap-3 chains at 89@5 (soft slack) rolled back every 97-99@3
                    # proposal as uphill for two hours.
                    accepted = worker or self.acceptance.decide(key0[0], key1[0], better, rng)
                    if accepted and not better and not worker and d1 > d0 and (
                            (phase == REPAIR and self._repair_monotone)
                            or (self._depth_window is not None
                                and d1 > self.chain_best_d + self._depth_window)):
                        accepted = False
                    if not accepted:
                        st.rollback(journal)
                        g1, d1 = g0, d0
                    else:
                        # Frontier points are recorded at their own depth, feasible or not: a
                        # capped chain deeper than its cap still holds a valid circuit, and
                        # 2026-10-28 lost a fox_mu8 519@10 and an InvMixColumns 92@11 that way.
                        wg = self.worker_best_g
                        if (not worker and self._frontier_on
                                and (wg is None or g1 <= wg + self._frontier_band)):
                            frontier = self._new_frontier_point(g1, d1)
                        if worker or frontier:
                            # Rare: read the values before (roll back once) and rebuild after.
                            proposal_s = perf_counter() - t0
                            after = st.key()
                            st.rollback(journal)
                            before = st.key()
                            values, polish = self._polish(after, g1, d1)
                            self._set_state(self._make_state(values, self._cap))
                            g1, d1 = self.state.size(), self.state.depth()
                            key1 = self._key(g1, d1)
                            if polish is not None:
                                # Fewer gates at no more depth: maybe now a feasible worker best.
                                polish["removed"] = sorted(after - self.state.key())
                                feasible = self._feasible(g1, d1)
                                worker = feasible and (wkey is None or key1 < wkey)
                            found = self._found(move, trace, prop.work, prop.deterministic,
                                                seed, phase, before, g0, d0, worker,
                                                proposal_s, polish)
                        elif self._commit is not None:
                            self._commit(journal)
                        neutral = key1[0] == key0[0] and not better
                        uphill = key1[0] > key0[0]
                        changed = trace.get("changed", True)
                        # A feasible worker best also re-anchors a chain whose best is
                        # infeasible (deeper than the real cap), so the uphill window, the depth
                        # window and the stall timer work from the feasible state, not from the
                        # deeper trap.
                        chain = key1 < self.chain_best_key or (
                            worker and not self._feasible(self.chain_best_g, self.chain_best_d))
                        self.cur_g, self.cur_d, self.cur_key = g1, d1, key1
                        if chain:
                            self._chain_best(g1, d1, key1, feasible)
                        elif worker:
                            self._phase_event(self.phase.enter(BURST), phase, "worker best")
                        elif changed and feasible and key1 == self.worker_best_key:
                            self._sample_best_point(move.name)
        # A proposal's cost includes scoring and its undo (rollback is kernel work for it).
        secs = perf_counter() - t0

        self.work_total += work
        weight = self._tightness.weight(g1, d1) if (chain or worker or frontier) else 1.0
        self.scheduler.credit(idx, secs if self._cost_seconds else work,
                              neutral and changed, chain, worker, frontier, weight)
        phase_ctl = self.phase
        if phase_ctl.phase != PLATEAU:
            before_phase = phase_ctl.phase
            if phase_ctl.tick(work):
                self._phase_event(True, before_phase, "budget")
                if before_phase == REPAIR and phase_ctl.repair_revert:
                    self._repair_expired = True
        self.recorder.proposal({
            "it": it, "move": move.name, "phase": phase, "valid": valid, "accepted": accepted,
            "neutral": neutral, "uphill": uphill, "improved_chain": chain,
            "improved_worker": worker, "frontier": frontier, "d_gates": g1 - g0,
            "d_depth": d1 - d0, "gates": g1, "depth": d1, "work": work, "cpu_s": secs,
            "components": components})
        state_key = None
        if accepted and neutral and changed:
            self._pk += 1
            if self._pk >= self._plateau_key_every:
                self._pk = 0
                state_key = self.state.key()
        self._plateau.observe(state_key, accepted, neutral, it, self._t)
        if found is not None and not self._report(found):
            worker = frontier = False          # the verifier rejected it; chain restarted
        elif chain:
            self._flush_plateau(None)
        if it % self._periodic_every == 0:
            self._periodic()
        if self._debug_every and it % self._debug_every == 0:
            self.state.check()
        return StepResult(it, move.name, phase, g0, d0, self.cur_g, self.cur_d, valid,
                          accepted, neutral, chain, worker, work)

    # ------------------------------------------------------------------ step helpers ----
    def _polish(self, values, g, d):
        """``(values, polish info or None)``: the new record point ``values`` (g@d) shrunk at
        its own depth when that is below the search cap (``engine/polish.py``)."""
        cap = self._cap
        if not self._polish_nodes or d is None or (cap is not None and d >= cap):
            return values, None
        from ..core.valueset import ValueSet
        from .polish import polish
        t0 = perf_counter()
        # No pair-sum index: the polish only removes.
        state = ValueSet(self._n, self.target.rows, sorted(values), cap=d)
        state.trim()
        removed, exact, nodes = polish(state, self._polish_nodes)
        if not removed:
            return values, None
        self.counters["polished"] += 1
        return values.difference(removed), {
            "from": score(g, d), "exact": exact, "nodes": nodes,
            "seconds": round(perf_counter() - t0, 6)}

    def _new_frontier_point(self, g, d) -> bool:
        """True when point ``(g, d)`` is dominated by no frontier point."""
        point = (g, d)
        dominated = self._dominated
        if dominated is not None and point in dominated:
            return False
        for fg, fd in self.frontier:
            if fg <= g and fd <= d:
                if dominated is None:
                    self._dominated = dominated = set()
                dominated.add(point)
                return False
        return True

    def _add_frontier(self, g, d) -> None:
        self.frontier = sorted([(fg, fd) for fg, fd in self.frontier
                                if not (g <= fg and d <= fd)] + [(g, d)])

    def _set_worker_best(self, g, d, key, values) -> None:
        self.worker_best_key, self.worker_best_g, self.worker_best_d = key, g, d
        self.worker_best_values = values
        self._best_seen = {hash(values)}
        self._at_best = 0
        self._add_frontier(g, d)

    def _phase_event(self, changed: bool, old: str, reason: str) -> None:
        if changed:
            fields = {"from": old, "to": self.phase.phase, "reason": reason,
                      "budget": self.phase.left}
            self.recorder.event("phase", **fields)

    def _chain_best(self, g, d, key, feasible) -> None:
        """Bookkeeping for a new chain best (the state already holds it).  The plateau it
        ends is emitted after the improvement's dossier (``_flush_plateau``), so the plateau
        event can name the improvement that closed it."""
        self._t = t = self.recorder.now()
        values = self.state.key()
        self.chain_best_key, self.chain_best_g, self.chain_best_d = key, g, d
        self.chain_best_values = values
        self.chain_improvements += 1
        self.counters["chain_improvements"] += 1
        self.acceptance.set_best(key[0])
        self.restarter.improved(self.it, self.work_total, t)
        self.archive.offer(values, g, d, key, feasible, f"chain{self.chain_seq}")
        self._close_plateau("improve", defer=True)
        self._plateau.enter(key, values, self.it, t)
        self._plateau_it = self.it
        wkey = self.worker_best_key
        needs_repair = not feasible and (wkey is None or key < wkey)
        old = self.phase.phase
        self._phase_event(self.phase.on_chain_best(needs_repair), old,
                          "repair" if needs_repair else "chain best")

    def _close_plateau(self, exit_kind: str, defer: bool = False) -> None:
        """Close the current plateau; its event is written now, or held for
        ``_flush_plateau`` with ``defer``.  Short plateaus (descents) write no event."""
        record = self._plateau.close(exit_kind, self.it, self._t)
        if not record or self.it - self._plateau_it < self._plateau_event_min:
            return
        if defer:
            self._plateau_closed = record
        else:
            self.recorder.event("plateau", **record)

    def _flush_plateau(self, improvement) -> None:
        """Write a plateau event held by ``_close_plateau(defer=True)``."""
        record = self._plateau_closed
        if record is None:
            return
        self._plateau_closed = None
        if improvement is not None:
            record["improvement"] = improvement
        self.recorder.event("plateau", **record)

    # ------------------------------------------------------------------ periodic work ---
    def _periodic(self) -> None:
        self._t = t = self.recorder.now()
        pin = self._pin
        if pin is not None and self.it >= pin["until"]:
            self._unpin("proposals")
        if self._repair_expired:
            self._repair_expired = False
            if not self._feasible(self.chain_best_g, self.chain_best_d):
                if self.worker_best_values is not None:
                    self._restart("repair_expired", forced=(
                        self.worker_best_values, "best",
                        {"id": "best", "parent": self._parent_of(self.worker_best_values)},
                        None))
                else:
                    # Nothing to revert to: without an exit such a chain repairs forever.
                    self._repair_misses += 1
                    if self._repair_exit and self._repair_misses >= self._repair_exit:
                        self._restart("repair_exhausted")
        # Only a feasible chain best can hold the worker best: an infeasible 89@5 chain best
        # under cap 3 compared "<=" the 98@3 worker best and got the incumbent's 3x stall
        # allowance and root-age exemption (no restarts in 2 h on 19 of 20 workers).
        incumbent = (self.worker_best_key is not None
                     and self._feasible(self.chain_best_g, self.chain_best_d)
                     and self.chain_best_key <= self.worker_best_key)
        reason = self.restarter.due(self.it, self.work_total, t, self.chain_best_g, incumbent)
        if reason is not None:
            self._restart(reason)
        if self.recorder.epoch_due():
            self.recorder.epoch(self.epoch_fields())

    def epoch_fields(self) -> dict:
        """Engine-side fields of an epoch event (the recorder adds per-move counters)."""
        phase = self.phase.phase
        keys = [e.key for e in self.archive.members()]
        cur = self.state.key()
        return {
            "phase": phase, "work": self.work_total,
            "engine_chain": self.chain_seq, "root": self.root.get("id"), "source": self.source,
            "chain": score(self.cur_g, self.cur_d),
            "chain_best": score(self.chain_best_g, self.chain_best_d),
            "worker_best": score(self.worker_best_g, self.worker_best_d),
            "frontier": [score(g, d) for g, d in self.frontier],
            "acceptance": self.acceptance.summary(),
            "weights": self.scheduler.weights(phase),
            "scheduler": self.scheduler.summary(),
            "plateau": self._plateau.snapshot(self.it, self._t),
            "diversity": metrics.diversity(keys) if len(keys) > 1 else None,
            "archive": {"size": len(self.archive), **self.archive.diversity()},
            "dist_chain_best": distance(cur, self.chain_best_values),
            "dist_root": distance(cur, self.root_values),
            "restart": self.restarter.ages(self.it, self.work_total, self._t),
            "restarts_by": {"reason": dict(self.restarter.by_reason),
                            "source": dict(self.restarter.by_source)},
            "counters": dict(self.counters),
        }

    # ------------------------------------------------------------------ restarts --------
    def _pool_exclude(self) -> set:
        exclude = self.archive.keys()
        exclude.add(self.chain_best_values)
        if self.worker_best_values is not None:
            exclude.add(self.worker_best_values)
        return exclude

    @staticmethod
    def _shared_root(elite) -> dict:
        """Root info of a pooled elite.  The record's ``ref`` is the donor's dossier id when
        the record came from an improvement (sampled DAGs and seeds have ``<worker>:...``
        refs), which makes the donor improvement the new chain's lineage parent."""
        record = elite.get("record")
        ref = elite.get("ref")
        return {"id": f"shared:{record}", "record": record, "donor": elite.get("donor"),
                "dag": elite.get("dag_sha256"), "gates": elite.get("gates"),
                "depth": elite.get("depth"),
                "improvement": ref if isinstance(ref, str) and ":" not in ref else None}

    def _restart(self, reason: str, forced=None) -> bool:
        """Restart the chain from a source chosen by the restart controller, or from
        ``forced = (values, source, root_info, donor)``.  False when nothing usable was found
        (the current chain then gets another stall period)."""
        self._t = t = self.recorder.now()
        prev = {"engine_chain": self.chain_seq, "root": self.root.get("id"),
                "source": self.source, "gates": self.cur_g, "depth": self.cur_d,
                "best": score(self.chain_best_g, self.chain_best_d),
                "improvements": self.chain_improvements,
                **self.restarter.ages(self.it, self.work_total, t)}
        if forced is not None:
            plans = [forced]
            order = [forced[1]]
        else:
            avail = {"fresh": self._construct is not None,
                     "elite": any(k != self.chain_best_values for k in self.archive.keys()),
                     "shared": self.pool is not None,
                     "best": self.worker_best_values is not None}
            if self.restarter.weights["foundation"] > 0:
                avail["foundation"] = self._construct is not None and (
                    avail["best"] or avail["elite"])
            order = self.restarter.order(self.rng, avail)
            plans = None
        state = None
        # A running pin restricts the old chain, not the candidate states.
        old_pin, self._pin = self._pin, None
        for i, source in enumerate(order):
            self._pending_pin = None
            got = plans[i] if plans is not None else self._restart_source(source)
            if got is None:
                continue
            values, source, root, donor = got
            state = self._make_state(values, self._cap)
            if state.ok():
                break
            state = None
        self._pin = old_pin
        if state is None:
            self._pending_pin = None
            self.restarter.improved(self.it, self.work_total, t)
            self.counters["restart_failed"] += 1
            self.recorder.event("restart_failed", reason=reason, tried=order)
            return False
        if old_pin is not None:
            self._unpin("restart")             # the pinned chain ends before its pin did
        if source == "foundation":
            self._pin, self._pending_pin = self._pending_pin, None
            state.restrict_level1(self._pin["allowed"])
        self._close_plateau("restart")
        old_phase = self.phase.phase
        self._begin_chain(state, root, source, donor)
        self.restarter.restarted(reason, source)
        self.counters["restarts"] += 1
        parent = (self._parent_of(values) if source in ("best", "elite")
                  else root.get("improvement"))
        self.recorder.event("restart", reason=reason, source=source, root=root, parent=parent,
                            donor=donor, record=root.get("record"), prev=prev,
                            engine_chain=self.chain_seq, start=score(self.cur_g, self.cur_d))
        g, d, key = self.cur_g, self.cur_d, self.cur_key
        wkey = self.worker_best_key
        if not self._feasible(g, d) and wkey is not None and key < wkey:
            # A pulled over-cap elite (e.g. 88@6 for a cap-5 worker): repair it first.
            self._phase_event(self.phase.on_chain_best(True), old_phase, "restart: repair")
        else:
            self._phase_event(self.phase.on_restart(), old_phase, "restart")
        if self._feasible(g, d) and (wkey is None or key < wkey):
            if source == "shared":
                # Someone else's record: adopt it as the worker best without claiming it.
                self._set_worker_best(g, d, key, self.chain_best_values)
                self.recorder.event("adopt_best", point=score(g, d), donor=donor,
                                    record=root.get("record"))
            else:
                found = self._found(None, {"components": [f"restart.{source}"], "root": root},
                                    0, True, None, self.phase.phase, None, None, None, True)
                self._report(found)
        return True

    def _parent_of(self, values):
        """Id of the improvement that reached ``values`` (None for a chain best that was
        never a worker best or frontier point, or one found before a resume)."""
        return self._improvement_of.get(frozenset(values))

    def _restart_source(self, source):
        """``(values, source, root_info, donor)`` for one restart source, or None."""
        if source == "fresh":
            built = self._build_root()
            if built is None:
                return None
            values, root = built
            return values, source, root, None
        if source == "elite":
            entry = self.archive.sample_diverse(self.chain_best_values, self.rng)
            if entry is None:
                return None
            return (entry.key, source, {"id": f"elite:{entry.seq}", "seq": entry.seq,
                                        "from": entry.origin, "gates": entry.gates,
                                        "depth": entry.depth}, None)
        if source == "shared":
            elite = self.pool.sample(self._pool_exclude(), self.rng)
            if elite is None:
                self.counters["pull_empty"] += 1
                return None
            self.counters["pulls"] += 1
            self.recorder.event("pull", record=elite.get("record"), dag=elite.get("dag_sha256"),
                                point=score(elite.get("gates"), elite.get("depth")),
                                donor=elite.get("donor"))
            return (_seed_values(elite, self._n), source, self._shared_root(elite),
                    elite.get("donor"))
        if source == "best":
            return self.worker_best_values, source, {"id": "best",
                                                     "parent": self._parent_of(
                                                         self.worker_best_values)}, None
        if source == "foundation":
            return self._foundation_source()
        raise ValueError(f"unknown restart source {source}")

    # ------------------------------------------------------------------ foundations -----
    def _useful_pairs(self) -> list[int]:
        """Weight-2 masks contained in some output row, ascending (the swap-in candidates)."""
        if self._useful is None:
            n = self._n
            rows = [int(t) for t in self.target.rows]
            self._useful = [m for m in ((1 << i) | (1 << j) for i in range(n)
                                        for j in range(i + 1, n))
                            if any(t & m == m for t in rows)]
            self._useful.sort()
        return self._useful

    def _foundation_source(self):
        """``(values, "foundation", root_info, None)``: a fresh root built over a donor's
        level-1 set (optionally perturbed), or None.  Leaves the pin for ``_restart`` in
        ``_pending_pin`` (DESIGN.md, foundation restarts)."""
        construct = self._construct
        if construct is None:
            return None
        get = self.settings.__getitem__
        rng = self.rng
        best = self.worker_best_values
        entry = None
        if rng.random() < get("restart.foundation.elite_p") or best is None:
            entry = self.archive.sample_diverse(self.chain_best_values, rng)
        if entry is not None:
            donor_values, kind = entry.key, "elite"
            donor = {"seq": entry.seq, "from": entry.origin, "gates": entry.gates,
                     "depth": entry.depth}
        elif best is not None:
            donor_values, kind = best, "best"
            donor = {"gates": self.worker_best_g, "depth": self.worker_best_d}
        else:
            return None
        forced = {int(t) for t in self.target.rows if int(t).bit_count() == 2}
        base = _level1(donor_values) | forced
        removable = sorted(base - forced)
        swap = min(get("restart.foundation.swap_pairs"), len(removable))
        drop = min(get("restart.foundation.drop_pairs"), len(removable) - swap)
        out = rng.sample(removable, swap + drop) if swap + drop else []
        swapped_out, dropped = sorted(out[:swap]), sorted(out[swap:])
        swapped_in = []
        if swap:
            pool = [m for m in self._useful_pairs() if m not in base]
            swapped_in = sorted(rng.sample(pool, min(swap, len(pool))))
        allowed = frozenset(base.difference(out).union(swapped_in))
        length = get("restart.foundation.pin_proposals")
        names = list(get("restart.foundation.constructors"))
        seed = rng.getrandbits(32)
        budget = Budget(self._build_work, None, None, self._check_every)
        started = perf_counter()
        fields = {"donor_kind": kind, "donor": donor, "level1_size": len(base),
                  "swapped_out": swapped_out, "swapped_in": swapped_in, "dropped": dropped,
                  "allowed_size": len(allowed), "seed": seed}
        try:
            values, info = construct.build_restricted_root(
                names, self.target, allowed, random.Random(seed), self._cap, budget,
                self.settings)
        except ValueError as exc:
            self.recorder.event("foundation_failed", reason=str(exc), constructors=names,
                                **fields)
            return None
        root = {"id": f"foundation:{kind}#{seed}", "constructor": info["built"],
                **fields, "level1": sorted(base), "pin_proposals": length,
                "gates": info.get("gate_count"), "depth": info.get("depth"),
                "tried": info.get("tried"), "build_s": round(perf_counter() - started, 6),
                "improvement": self._parent_of(donor_values)}
        self._pending_pin = {"allowed": allowed, "start": self.it, "until": self.it + length,
                             "length": length}
        return list(values), "foundation", root, None

    def _unpin(self, reason: str) -> None:
        """End the pinned phase: lift the restriction and log ``foundation_unpin`` with the
        chain best and whether the level-1 set still equals the allowed set."""
        pin, self._pin = self._pin, None
        lift = getattr(self.state, "restrict_level1", None)
        if lift is not None:
            lift(None)
        allowed = pin["allowed"]
        cur = _level1(self.state.key())
        best = _level1(self.chain_best_values)
        self.recorder.event(
            "foundation_unpin", reason=reason, engine_chain=self.chain_seq,
            proposals=self.it - pin["start"], pin_proposals=pin["length"],
            chain_best=score(self.chain_best_g, self.chain_best_d),
            chain=score(self.cur_g, self.cur_d), allowed_size=len(allowed),
            level1_size=len(cur), level1_equals_allowed=cur == allowed,
            level1_missing=sorted(allowed - cur),
            best_level1_equals_allowed=best == allowed)

    # ------------------------------------------------------------------ persistence -----
    def checkpoint(self) -> dict:
        """JSON-safe snapshot of the whole engine.

        With ``engine.canonical_checkpoint`` the chain state is first rebuilt from its values,
        so this engine and one resumed from the snapshot hold identical states and continue on
        the same trajectory (internal set orders of a ValueSet depend on its edit history).
        Call it between steps only (a proposal leaves the state half-edited until it is
        scored).
        """
        if self._canonical:
            self._set_state(self._make_state(self.state.values(), self._cap))
        t = self.recorder.now()
        wb = None
        if self.worker_best_key is not None:
            wb = {"values": sorted(self.worker_best_values), "gates": self.worker_best_g,
                  "depth": self.worker_best_d}
        data = {
            "version": CHECKPOINT_VERSION, "worker": self.worker_id, "rng_seed": self.rng_seed,
            "rng": _rng_to_json(self.rng.getstate()), "it": self.it, "work": self.work_total,
            "chain": {"seq": self.chain_seq, "root": self.root, "source": self.source,
                      "donor": self.donor, "values": sorted(self.state.values()),
                      "root_values": sorted(self.root_values),
                      "best_values": sorted(self.chain_best_values),
                      "best": [self.chain_best_g, self.chain_best_d],
                      "improvements": self.chain_improvements, "plateau_it": self._plateau_it,
                      "repair_misses": self._repair_misses},
            "worker_best": wb,
            "frontier": [list(p) for p in self.frontier],
            "last_improvement": self.last_improvement,
            "best_seen": sorted(self._best_seen), "at_best": self._at_best, "pk": self._pk,
            "counters": dict(self.counters),
            "scheduler": self.scheduler.state(),
            "acceptance": self.acceptance.state(),
            "phase": self.phase.state(),
            "archive": self.archive.state(),
            "restart": self.restarter.state(t),
            "plateau": self._plateau.checkpoint(),
            "moves": {m.name: m.state() for m in self._moves},
        }
        if self._pin is not None:          # only while pinned: other checkpoints unchanged
            data["foundation_pin"] = {**self._pin, "allowed": sorted(self._pin["allowed"])}
        return data

    @classmethod
    def resume(cls, data, target, objective, settings, *, recorder, pool=None, moves=None,
               state_factory=None, construct=None, plateau_tracker=None) -> "Engine":
        """An engine continuing exactly where ``checkpoint()`` left off.

        Checkpoints of another ``CHECKPOINT_VERSION`` are refused (the worker then reports the
        error instead of continuing on a misread state).  Moves are matched by name: a move
        missing from the checkpoint starts fresh, a checkpointed move no longer active is
        ignored."""
        if data.get("version") != CHECKPOINT_VERSION:
            raise ValueError(f"checkpoint version {data.get('version')} is not "
                             f"{CHECKPOINT_VERSION}")
        self = cls.__new__(cls)
        self._setup(target, objective, settings, recorder, data["worker"], pool, moves,
                    state_factory, construct, plateau_tracker)
        self._load(data)
        return self

    def _load(self, data) -> None:
        self.rng_seed = data["rng_seed"]
        self.rng = random.Random()
        self.rng.setstate(_rng_from_json(data["rng"]))
        self._bind_rng()
        self.it = data["it"]
        self.work_total = data["work"]
        self._t = t = self.recorder.now()
        pin = data.get("foundation_pin")
        if pin is not None:
            self._pin = {**pin, "allowed": frozenset(pin["allowed"])}
        chain = data["chain"]
        self._set_state(self._make_state(chain["values"], self._cap))
        self.cur_g, self.cur_d = self._size(), self.state.depth()
        self.cur_key = self._key(self.cur_g, self.cur_d)
        self.chain_seq = chain["seq"]
        self.root = chain["root"]
        self.source = chain["source"]
        self.donor = chain["donor"]
        self.root_values = frozenset(chain["root_values"])
        self.chain_best_values = frozenset(chain["best_values"])
        self.chain_best_g, self.chain_best_d = chain["best"]
        self.chain_best_key = self._key(self.chain_best_g, self.chain_best_d)
        self.chain_improvements = chain["improvements"]
        self._plateau_it = chain["plateau_it"]
        self._repair_misses = chain.get("repair_misses", 0)
        wb = data["worker_best"]
        if wb is not None:
            self.worker_best_key = self._key(wb["gates"], wb["depth"])
            self.worker_best_values = frozenset(wb["values"])
            self.worker_best_g, self.worker_best_d = wb["gates"], wb["depth"]
        self.frontier = [tuple(p) for p in data["frontier"]]
        self.last_improvement = data["last_improvement"]
        self._best_seen = set(data["best_seen"])
        self._at_best = data["at_best"]
        self._pk = data["pk"]
        counters = self.counters
        counters.update({k: v for k, v in data["counters"].items() if k in counters})
        self.scheduler.load_state(data["scheduler"])
        self.acceptance.load_state(data["acceptance"])
        self.phase.load_state(data["phase"])
        self.archive.load_state(data["archive"])
        self.restarter.load_state(data["restart"], t)
        self._plateau.restore(data["plateau"])
        # The tracker does not checkpoint state keys; the plateau entry state is the chain
        # best (every plateau starts at one), so drift stays measurable after a resume.
        rekey = getattr(self._plateau, "rekey", None)
        if rekey is not None:
            rekey(self.chain_best_values, self.state.key())
        moves_state = data.get("moves", {})
        for move in self._moves:
            state = moves_state.get(move.name)
            if state is not None:
                move.load_state(state)
