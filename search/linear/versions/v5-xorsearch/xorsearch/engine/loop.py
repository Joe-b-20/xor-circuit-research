"""The one search loop: a chain, a move per step, accept or undo, record what improves.

Role in the method (DESIGN.md section 2).  A worker runs one Engine.  The engine owns one *chain*
(a ``ValueSet`` built at ``objective.search_cap``, the real depth cap plus the soft slack) and
every move acts on it; there are no private per-move trajectories (59% of framework engine slots
ended >=5 gates behind their worker best because they had them).  One ``step()``:

1. the scheduler picks a move for the current phase;
2. a per-proposal RNG is reseeded from the engine RNG; the 63-bit seed is the replay handle kept
   in dossiers (one ``Random.seed`` call, about as costly as one ``getstate()``, and JSON-small);
3. the move edits the state speculatively and returns a Proposal (trace + undo journal);
4. the state is scored (``count()``, ``depth()``); unrealizable or over-gate-limit states are
   rolled back; otherwise the acceptance policy decides and rejected proposals are rolled back;
5. a kept state may be a new chain best (archive, plateau closes, burst or repair phase), a new
   worker best (best *feasible* state under the real objective) or a new nondominated feasible
   point.  For those the journal is rolled back once to read the values before, the after-state
   is rebuilt, and after ``recorder.proposal`` the dossier goes to ``recorder.improvement``; then
   the ``on_record`` callbacks (the worker's verifying ``RecordWriter.save``) get the record with
   the dossier id.  Distinct DAGs at the worker-best point are sampled into records too;
6. snapback, scheduler credit, phase budget, ``recorder.proposal``, plateau tracking;
7. every ``periodic_every`` proposals: clock read, restart check, push-mode offers, epochs.

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
* ``recorder.proposal(rec) improvement(dossier) event(ev, **f) epoch_due() epoch(f) ring()
  now()``;  ``metrics.PlateauTracker.from_settings(settings)`` with ``enter observe snapshot
  close checkpoint restore``;  ``metrics.diversity``, ``metrics.shape_from_gates``;
* ``pool.sample(exclude_keys, rng) -> elite dict | None`` and, in push mode,
  ``pool.offer(gates, depth, exclude_keys)``.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass
from time import perf_counter
from typing import Callable

from ..config.schema import Knob, Section
from ..core.budget import Budget
from ..moves.base import MoveContext
from ..telemetry import metrics
from . import acceptance as acceptance_mod
from .archive import Archive, distance
from .phase import BURST, PLATEAU, REPAIR, PhaseController, phase_priors
from .restart import RestartController
from .scheduler import Scheduler

KNOBS = (
    Section("engine", "The search loop.", {
        "proposal_work": Knob(1_000_000, "Work budget of one proposal (safety net; moves bound "
                              "themselves with their own knobs). 0 = unbounded.", min=0),
        "proposal_seconds": Knob(1.0, "Wall-clock limit of one proposal when budget.mode = "
                                 "time (such proposals are marked non-deterministic).", min=0),
        "replay_seeds": Knob(True, "Reseed a per-proposal RNG from the engine RNG so every "
                             "dossier carries a replay seed (about 6 us per proposal)."),
        "periodic_every": Knob(64, "Proposals between clock reads, restart checks, push offers "
                               "and epoch checks.", min=1),
        "gate_limit_slack": Knob(0, "The chain may exceed objective.gate_limit by this many "
                                 "gates while searching (records still obey the limit).",
                                 min=0),
        "frontier": Knob(True, "Record new nondominated feasible (gates, depth) points, not only "
                         "worker-best improvements."),
        "frontier_band": Knob(10, "Only points within this many gates of the worker best count "
                              "as frontier points (constructor points +69..+595 gates above "
                              "the best were useless; v2-translate's useful ones were +2..+9).",
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
        "pairsums": Knob("auto", "Pair-sum counter in the chain state. auto: on when a walk move "
                         "runs and |U| <= pairsums_max_values.", choices=("auto", "on", "off")),
        "pairsums_max_values": Knob(1200, "Largest |U| for which auto enables the counter "
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
    """``make(values, cap) -> ValueSet`` for ``target``; the pair-sum counter follows
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


def _rng_to_json(state) -> list:
    version, internal, gauss = state
    return [version, list(internal), gauss]


def _rng_from_json(data) -> tuple:
    version, internal, gauss = data
    return (version, tuple(internal), gauss)


def _failed(result) -> bool:
    """Did an on_record callback reject the candidate?"""
    return isinstance(result, dict) and (result.get("ok") is False
                                         or result.get("equivalent") is False)


class Engine:
    """One worker's search: chain, moves and policies (DESIGN.md section 4.4).

    Optional keyword hooks (defaults in brackets), for tests and special campaigns:
    ``moves`` [every registered applicable move], ``state_factory`` [``valueset_factory``],
    ``construct`` [``xorsearch.moves.construct``], ``plateau_tracker`` [a zero-argument factory;
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
        self._t = recorder.now()
        state, root, source = self._initial_state(seed_circuit)
        self._begin_chain(state, root, source, None)
        if self._feasible(self.cur_g, self.cur_d):
            self._set_worker_best(self.cur_g, self.cur_d, self.cur_key, self.chain_best_values)
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
        self._n = target.n_inputs
        cfg = settings.view("engine")
        self._proposal_work = cfg.proposal_work or None
        self._time_budget = settings["budget.mode"] == "time"
        self._proposal_seconds = cfg.proposal_seconds
        self._check_every = settings["budget.check_every"]
        self._periodic_every = cfg.periodic_every
        self._frontier_on = cfg.frontier
        self._frontier_band = cfg.frontier_band
        self._record_stride = cfg.record_stride
        self._records_per_point = cfg.records_per_point
        self._plateau_key_every = cfg.plateau_key_every
        self._plateau_event_min = cfg.plateau_event_min
        self._canonical = cfg.canonical_checkpoint
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
        # Charge proposals their measured time unless replayable scheduling was asked for.
        self._cost_seconds = settings["scheduler.cost"] == "seconds"
        self.phase = PhaseController(phase_cfg, priors)
        self._repair_monotone = phase_cfg.repair_monotone
        self.acceptance = acceptance_mod.make(settings.view("acceptance"))
        self.archive = Archive(settings.view("archive"))
        self.restarter = RestartController(settings.view("restart"))
        self._build_work = settings.view("restart").build_work or None

        if state_factory is None:
            state_factory = valueset_factory(target, settings,
                                             any(m.family == "walk" for m in kept))

        def make_state(values, cap):
            # Sorted input: a rebuilt state never depends on how the values were stored, which
            # keeps resumed runs on the same trajectory.  Trimmed: seeds may carry dead gates,
            # and the loop scores with the O(1) count(), exact only on trimmed states.
            state = state_factory(sorted(values), cap)
            trim = getattr(state, "trim", None)
            if trim is not None:
                trim()
            return state
        self._make_state = make_state
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
                                  phase=PLATEAU, stats={}, settings=settings) for m in kept]
        self._callbacks: list[Callable] = []
        self.counters = {"noop": 0, "invalid": 0, "infeasible": 0, "gate_limit": 0,
                         "snapback": 0, "restarts": 0, "restart_failed": 0, "verify_fail": 0,
                         "records": 0, "frontier": 0, "improvements": 0,
                         "chain_improvements": 0, "pulls": 0, "pull_empty": 0}
        self.it = 0
        self.work_total = 0
        self.chain_seq = 0
        self.last_improvement = None
        self.worker_best_key = self.worker_best_values = None
        self.worker_best_g = self.worker_best_d = None
        self.frontier: list[tuple[int, int]] = []
        self._best_seen: set[int] = set()
        self._at_best = 0
        self._pk = 0

    def _set_state(self, state) -> None:
        """Make ``state`` the chain state (every move context points at it)."""
        self.state = state
        self._commit = getattr(state, "commit", None)
        self._size = getattr(state, "count", None) or state.size
        for ctx in self._ctxs:
            ctx.state = state

    def _initial_state(self, seed_circuit):
        if seed_circuit is not None:
            state = self._make_state(_seed_values(seed_circuit, self._n), self._cap)
            if state.ok():
                return state, {"id": "seed"}, "seed"
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

    def _build_root(self):
        """``(values, root_info)`` from a fresh randomized constructor root, or None."""
        construct = self._construct
        if construct is None:
            return None
        name = construct.choose_root(self.rng, self.settings, self.target, self._cap)
        seed = self.rng.getrandbits(32)
        budget = Budget(self._build_work, None, None, self._check_every)
        try:
            values, info = construct.build_root(name, self.target, random.Random(seed),
                                                self._cap, budget, self.settings)
        except ValueError as exc:
            self.recorder.event("root_failed", constructor=name, seed=seed, reason=str(exc))
            return None
        root = {"id": f"{name}#{seed}", "constructor": name, "seed": seed,
                "built": info.get("built", name), "gates": info.get("gate_count"),
                "depth": info.get("depth"), "fallback": info.get("fallback")}
        return list(values), root

    def _begin_chain(self, state, root, source, donor) -> None:
        """Start a chain on ``state`` (construction, restart, adoption)."""
        self._set_state(state)
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
        self.acceptance.reset(key[0], key[0])
        self.restarter.started(self.it, self.work_total, self._t)
        self._plateau.enter(key, values, self.it, self._t)
        self._plateau_it = self.it
        self.archive.offer(values, g, d, key, self._feasible(g, d), f"chain{self.chain_seq}")

    # ------------------------------------------------------------------ hooks -----------
    def on_record(self, callback: Callable[[dict], dict | None]) -> None:
        """Register ``callback(record) -> entry | None`` (the worker's ``RecordWriter.save``).

        Called for every new worker best and frontier point (after its dossier is written, so
        ``record["dossier"]`` is the improvement id) and for sampled distinct DAGs at the
        worker-best point (``dossier`` None).  ``record`` has ``kind``, ``circuit`` (circuit
        JSON: ``inputCount``, ``gates``, ``outputSignals``, ``gateCount``, ``depth``),
        ``gate_count``, ``depth``, ``values``, ``it``, ``move``, ``chain``, ``root``.  A return
        value with ``ok`` or ``equivalent`` False rejects it: the worker best is reverted and
        the chain restarts on a clean state; ``None`` (skipped, or no verifier) accepts.
        """
        self._callbacks.append(callback)

    def adopt(self, values, donor=None) -> bool:
        """Restart the chain on ``values`` (push sharing or manual adoption)."""
        return self._restart("adopt", forced=(list(values), "shared", {"id": "adopted"}, donor))

    def snapshot(self) -> dict:
        """Small status summary."""
        return {"it": self.it, "work": self.work_total, "chain": self.chain_seq,
                "root": self.root.get("id"), "source": self.source, "phase": self.phase.phase,
                "cur": [self.cur_g, self.cur_d],
                "chain_best": [self.chain_best_g, self.chain_best_d],
                "worker_best": (None if self.worker_best_key is None
                                else [self.worker_best_g, self.worker_best_d]),
                "frontier": [list(p) for p in self.frontier]}

    # ------------------------------------------------------------------ the loop --------
    def run(self, stop: Callable[[], bool]) -> None:
        """Step until ``stop()`` is true (checked between proposals)."""
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
        seed = None
        prng = self._prng
        if prng is not None:
            seed = rng.getrandbits(63)
            prng.seed(seed)
            ctx.rng = prng
        else:
            ctx.rng = rng
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
                    accepted = self.acceptance.decide(key0[0], key1[0], better, rng)
                    if (accepted and not better and d1 > d0 and phase == REPAIR
                            and self._repair_monotone):
                        accepted = False
                    if not accepted:
                        st.rollback(journal)
                        g1, d1 = g0, d0
                    else:
                        feasible = self._feasible(g1, d1)
                        wkey = self.worker_best_key
                        worker = feasible and (wkey is None or key1 < wkey)
                        if (not worker and feasible and self._frontier_on
                                and g1 <= self.worker_best_g + self._frontier_band):
                            frontier = self._nondominated(g1, d1)
                        if worker or frontier:
                            # Rare: read the values before (roll back once) and rebuild after.
                            after = st.key()
                            st.rollback(journal)
                            before = st.key()
                            self._set_state(self._make_state(after, self._cap))
                            g1, d1 = self.state.size(), self.state.depth()
                            key1 = self._key(g1, d1)
                            found = self._found(move.name, move.family, trace, prop.work,
                                                prop.deterministic, seed, phase, before,
                                                g0, d0, worker)
                        elif self._commit is not None:
                            self._commit(journal)
                        neutral = key1[0] == key0[0] and not better
                        uphill = key1[0] > key0[0]
                        changed = trace.get("changed", True)
                        chain = key1 < self.chain_best_key
                        self.cur_g, self.cur_d, self.cur_key = g1, d1, key1
                        if chain:
                            self._chain_best(g1, d1, key1, feasible)
                        elif worker:
                            self._phase_event(self.phase.enter(BURST), phase, "worker best")
                        elif changed and feasible and key1 == self.worker_best_key:
                            self._sample_best_point(move.name)
                        if uphill and self.acceptance.snapback(key1[0],
                                                               self.chain_best_key[0]):
                            self._snapback()
        # A proposal's cost includes scoring and its undo (rollback is kernel work for it).
        secs = perf_counter() - t0

        self.work_total += work
        self.scheduler.credit(idx, secs if self._cost_seconds else work,
                              neutral and changed, chain, worker, frontier)
        phase_ctl = self.phase
        if phase_ctl.phase != PLATEAU:
            before_phase = phase_ctl.phase
            if phase_ctl.tick(work):
                self._phase_event(True, before_phase, "budget")
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
        if it % self._periodic_every == 0:
            self._periodic()
        if self._debug_every and it % self._debug_every == 0:
            self.state.check()
        return StepResult(it, move.name, phase, g0, d0, self.cur_g, self.cur_d, valid,
                          accepted, neutral, chain, worker, work)

    # ------------------------------------------------------------------ step helpers ----
    def _nondominated(self, g, d) -> bool:
        for fg, fd in self.frontier:
            if fg <= g and fd <= d:
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
        """Bookkeeping for a new chain best (the state already holds it)."""
        self._t = t = self.recorder.now()
        values = self.state.key()
        self.chain_best_key, self.chain_best_g, self.chain_best_d = key, g, d
        self.chain_best_values = values
        self.chain_improvements += 1
        self.counters["chain_improvements"] += 1
        self.acceptance.set_best(key[0])
        self.restarter.improved(self.it, self.work_total, t)
        self.archive.offer(values, g, d, key, feasible, f"chain{self.chain_seq}")
        self._close_plateau("improve")
        self._plateau.enter(key, values, self.it, t)
        self._plateau_it = self.it
        wkey = self.worker_best_key
        needs_repair = not feasible and (wkey is None or key < wkey)
        old = self.phase.phase
        self._phase_event(self.phase.on_chain_best(needs_repair), old,
                          "repair" if needs_repair else "chain best")

    def _close_plateau(self, exit_kind: str) -> None:
        record = self._plateau.close(exit_kind, self.it, self._t)
        if record and self.it - self._plateau_it >= self._plateau_event_min:
            self.recorder.event("plateau", **record)

    def _snapback(self) -> None:
        """Return the chain to its best (it drifted too far uphill)."""
        self._set_state(self._make_state(self.chain_best_values, self._cap))
        self.cur_g, self.cur_d = self.chain_best_g, self.chain_best_d
        self.cur_key = self.chain_best_key
        self.counters["snapback"] += 1

    def _record(self, kind, g, d, values, move_name, dossier) -> dict:
        """The record handed to the on_record callbacks (the current state's circuit)."""
        gates, outputs = self.state.gates()
        gates = [[a, b] for a, b in gates]
        return {"kind": kind, "dossier": dossier, "improvement": dossier,
                "circuit": {"inputCount": self._n, "gates": gates, "outputSignals": outputs,
                            "gateCount": len(gates), "depth": d},
                "gate_count": g, "depth": d, "values": sorted(values), "it": self.it,
                "move": move_name, "worker": self.worker_id, "chain": self.chain_seq,
                "root": self.root.get("id")}

    def _deliver(self, record):
        """Run the callbacks; ``(ok, last result)``."""
        result = None
        for callback in self._callbacks:
            result = callback(record)
            if _failed(result):
                return False, result
        return True, result

    def _sample_best_point(self, move_name) -> None:
        """Every ``record_stride``-th kept move at the worker-best point: record a new DAG."""
        if len(self._best_seen) >= self._records_per_point:
            return
        self._at_best += 1
        if self._at_best < self._record_stride:
            return
        self._at_best = 0
        key = self.state.key()
        h = hash(key)
        if h in self._best_seen:
            return
        self._best_seen.add(h)
        g, d = self.cur_g, self.cur_d
        self.archive.offer(key, g, d, self.cur_key, True, f"record{self.chain_seq}")
        if not self._callbacks:
            return
        ok, result = self._deliver(self._record("record", g, d, key, move_name, None))
        if not ok:
            self._verification_failed("record", None, result, None)
            return
        entry = result if isinstance(result, dict) else {}
        if entry.get("saved") is False:        # the writer skipped it (duplicate, point full)
            return
        self.counters["records"] += 1
        self.recorder.event("record", point=[g, d], dag=entry.get("dag_sha256"),
                            record=entry.get("record") or entry.get("path"),
                            distinct_at_point=len(self._best_seen), move=move_name)

    def _state_before(self, before, phase) -> dict:
        """State metrics just before an improving move (dossier ``state_before``)."""
        snap = self._plateau.snapshot(self.it, self._t) or {}
        proposals = snap.get("proposals") or 0
        return {
            "phase": phase,
            "plateau": snap,
            "neutral_rate": (snap.get("neutral_accepts", 0) / proposals) if proposals else None,
            "temperature": self.acceptance.temperature(),
            "acceptance": self.acceptance.summary(),
            "weights": self.scheduler.weights(phase),
            "cur": [self.cur_g, self.cur_d],
            "chain_best": [self.chain_best_g, self.chain_best_d],
            "worker_best": (None if self.worker_best_key is None
                            else [self.worker_best_g, self.worker_best_d]),
            "dist_chain_best": distance(before, self.chain_best_values),
            "dist_root": distance(before, self.root_values),
            "dist_elites": self.archive.distance_stats(before),
            "chain_age": self.restarter.ages(self.it, self.work_total, self._t),
        }

    def _found(self, name, family, trace, work, deterministic, seed, phase, before, g0, d0,
               worker) -> dict:
        """The (rebuilt) chain state is a new worker best or frontier point: count it and
        return the dossier fields (sent after ``recorder.proposal``, see ``_report``)."""
        st = self.state
        g1, d1 = st.size(), st.depth()
        key1 = self._key(g1, d1)
        after = st.key()
        wg, wd = self.worker_best_g, self.worker_best_d
        if not worker:
            kind = "frontier"
        elif self._depth_first:
            kind = "depth" if wd is None or d1 < wd else "gates"
        else:
            kind = "gates" if wg is None or g1 < wg else "depth"
        dossier = {
            "kind": kind, "it": self.it, "before": None if g0 is None else
            {"gates": g0, "depth": d0}, "after": {"gates": g1, "depth": d1},
            "worker_best_before": None if wg is None else {"gates": wg, "depth": wd},
            "move": name, "family": family, "phase": phase, "trace": trace, "work": work,
            "deterministic": deterministic and not self._time_budget,
            "chain": {"source": self.source, "root": self.root, "engine_chain": self.chain_seq},
            "state_before": None if before is None else self._state_before(before, phase),
            "values_before": None if before is None else sorted(before),
            "values_after": sorted(after),
            "rng": {"seed": seed, "engine_seed": self.rng_seed,
                    "replay": "random.Random(seed) as ctx.rng on a state built from "
                              "values_before"},
            "verification": None,
        }
        if self.donor is not None:
            dossier["lineage"] = {"donor": self.donor}
        saved = (self.worker_best_key, self.worker_best_values, wg, wd, list(self.frontier),
                 set(self._best_seen))
        if worker:
            self._set_worker_best(g1, d1, key1, after)
            self.counters["improvements"] += 1
        else:
            self._add_frontier(g1, d1)
            self.counters["frontier"] += 1
        return {"dossier": dossier, "saved": saved, "before": before, "after": after,
                "point": (g1, d1)}

    def _report(self, found: dict) -> bool:
        """Write the dossier (after recorder.proposal, so the ring holds the improving
        proposal), then hand the record, with the dossier id, to the callbacks.  False when a
        callback rejected it (everything it counted is undone)."""
        dossier = found["dossier"]
        g1, d1 = found["point"]
        record = self._record(dossier["kind"], g1, d1, found["after"], dossier["move"], None)
        dossier["gates_after"] = record["circuit"]["gates"]
        dossier["outputs"] = record["circuit"]["outputSignals"]
        dossier["shape_after"] = metrics.shape_from_gates(dossier["gates_after"],
                                                          dossier["outputs"], self._n)
        ident = self.recorder.improvement(dossier)
        record["dossier"] = record["improvement"] = ident
        ok, result = self._deliver(record)
        if not ok:
            self._verification_failed(dossier["kind"], ident, result, found)
            return False
        self.last_improvement = ident
        return True

    def _verification_failed(self, kind, ident, result, found) -> None:
        """A verifier rejected a state the kernel called valid: undo what it counted and
        restart on a clean state (a kernel bug; strict workers raise instead)."""
        self.counters["verify_fail"] += 1
        self.recorder.event("verify_fail", kind=kind, id=ident, point=[self.cur_g, self.cur_d],
                            result=result)
        values = self.worker_best_values
        if found is not None:
            wkey, wvalues, wg, wd, frontier, seen = found["saved"]
            self.worker_best_key, self.worker_best_values = wkey, wvalues
            self.worker_best_g, self.worker_best_d = wg, wd
            self.frontier, self._best_seen = frontier, seen
            values = found["before"] if found["before"] is not None else wvalues
        if values is not None:
            self._restart("verify_fail", forced=(values, "best", {"id": "verified"}, None))

    # ------------------------------------------------------------------ periodic work ---
    def _periodic(self) -> None:
        self._t = t = self.recorder.now()
        incumbent = (self.worker_best_key is not None
                     and self.chain_best_key <= self.worker_best_key)
        reason = self.restarter.due(self.it, self.work_total, t, self.chain_best_g, incumbent)
        if reason is not None:
            self._restart(reason)
        pool = self.pool
        if (pool is not None and getattr(pool, "mode", None) == "push"
                and self.worker_best_key is not None):
            elite = pool.offer(self.worker_best_g, self.worker_best_d, self._pool_exclude())
            if elite is not None:
                self._restart("push", forced=(_seed_values(elite, self._n), "shared",
                                              self._shared_root(elite), elite.get("donor")))
        if self.recorder.epoch_due():
            self.recorder.epoch(self.epoch_fields())

    def epoch_fields(self) -> dict:
        """Engine-side fields of an epoch event (the recorder adds per-move counters)."""
        phase = self.phase.phase
        keys = [e.key for e in self.archive.members()]
        cur = self.state.key()
        return {
            "phase": phase, "it": self.it, "work": self.work_total,
            "engine_chain": self.chain_seq, "root": self.root.get("id"), "source": self.source,
            "chain": [self.cur_g, self.cur_d],
            "chain_best": [self.chain_best_g, self.chain_best_d],
            "worker_best": (None if self.worker_best_key is None
                            else [self.worker_best_g, self.worker_best_d]),
            "frontier": [list(p) for p in self.frontier],
            "acceptance": self.acceptance.summary(),
            "weights": self.scheduler.weights(phase),
            "scheduler": self.scheduler.summary(),
            "plateau": self._plateau.snapshot(self.it, self._t),
            "diversity": metrics.diversity(keys) if len(keys) > 1 else None,
            "archive": {"size": len(self.archive), **self.archive.diversity()},
            "dist_chain_best": distance(cur, self.chain_best_values),
            "dist_root": distance(cur, self.root_values),
            "restart": self.restarter.ages(self.it, self.work_total, self._t),
            "counters": dict(self.counters),
            "move_stats": {m.name: dict(c.stats) for m, c in zip(self._moves, self._ctxs)},
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
        record = elite.get("record")
        return {"id": f"shared:{record}", "record": record, "donor": elite.get("donor"),
                "dag": elite.get("dag_sha256"), "gates": elite.get("gates"),
                "depth": elite.get("depth")}

    def _restart(self, reason: str, forced=None) -> bool:
        """Restart the chain from a source chosen by the restart controller, or from
        ``forced = (values, source, root_info, donor)``.  False when nothing usable was found
        (the current chain then gets another stall period)."""
        self._t = t = self.recorder.now()
        prev = {"engine_chain": self.chain_seq, "root": self.root.get("id"),
                "source": self.source, "gates": self.cur_g, "depth": self.cur_d,
                "best": [self.chain_best_g, self.chain_best_d],
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
            order = self.restarter.order(self.rng, avail)
            plans = None
        state = None
        for i, source in enumerate(order):
            got = plans[i] if plans is not None else self._restart_source(source)
            if got is None:
                continue
            values, source, root, donor = got
            state = self._make_state(values, self._cap)
            if state.ok():
                break
            state = None
        if state is None:
            self.restarter.improved(self.it, self.work_total, t)
            self.counters["restart_failed"] += 1
            self.recorder.event("restart_failed", reason=reason, tried=order)
            return False
        self._close_plateau("restart")
        old_phase = self.phase.phase
        self._begin_chain(state, root, source, donor)
        self.restarter.restarted(reason, source)
        self.counters["restarts"] += 1
        parent = self.last_improvement if source in ("best", "elite") else None
        self.recorder.event("restart", reason=reason, source=source, root=root, parent=parent,
                            donor=donor, record=root.get("record"), prev=prev,
                            engine_chain=self.chain_seq, start=[self.cur_g, self.cur_d])
        self._phase_event(self.phase.on_restart(), old_phase, "restart")
        g, d, key = self.cur_g, self.cur_d, self.cur_key
        wkey = self.worker_best_key
        if self._feasible(g, d) and (wkey is None or key < wkey):
            if source == "shared":
                # Someone else's record: adopt it as the worker best without claiming it.
                self._set_worker_best(g, d, key, self.chain_best_values)
                self.recorder.event("adopt_best", point=[g, d], donor=donor,
                                    record=root.get("record"))
            else:
                found = self._found(f"restart.{source}", "restart",
                                    {"components": [f"restart.{source}"], "root": root},
                                    0, True, None, self.phase.phase, None, None, None, True)
                self._report(found)
        return True

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
                                point=[elite.get("gates"), elite.get("depth")],
                                donor=elite.get("donor"))
            return (_seed_values(elite, self._n), source, self._shared_root(elite),
                    elite.get("donor"))
        if source == "best":
            return self.worker_best_values, source, {"id": "best",
                                                     "parent": self.last_improvement}, None
        raise ValueError(f"unknown restart source {source}")

    # ------------------------------------------------------------------ persistence -----
    def checkpoint(self) -> dict:
        """JSON-safe snapshot of the whole engine.

        With ``engine.canonical_checkpoint`` the chain state is first rebuilt from its values,
        so this engine and one resumed from the snapshot hold identical states and continue on
        the same trajectory (internal set orders of a ValueSet depend on its edit history).
        """
        if self._canonical:
            self._set_state(self._make_state(self.state.values(), self._cap))
        t = self.recorder.now()
        wb = None
        if self.worker_best_key is not None:
            wb = {"values": sorted(self.worker_best_values), "gates": self.worker_best_g,
                  "depth": self.worker_best_d}
        return {
            "version": CHECKPOINT_VERSION, "worker": self.worker_id, "rng_seed": self.rng_seed,
            "rng": _rng_to_json(self.rng.getstate()), "it": self.it, "work": self.work_total,
            "chain": {"seq": self.chain_seq, "root": self.root, "source": self.source,
                      "donor": self.donor, "values": sorted(self.state.values()),
                      "root_values": sorted(self.root_values),
                      "best_values": sorted(self.chain_best_values),
                      "best": [self.chain_best_g, self.chain_best_d],
                      "improvements": self.chain_improvements, "plateau_it": self._plateau_it},
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
            "move_stats": {m.name: dict(c.stats) for m, c in zip(self._moves, self._ctxs)},
        }

    @classmethod
    def resume(cls, data, target, objective, settings, *, recorder, pool=None, moves=None,
               state_factory=None, construct=None, plateau_tracker=None) -> "Engine":
        """An engine continuing exactly where ``checkpoint()`` left off."""
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
        self.it = data["it"]
        self.work_total = data["work"]
        self._t = t = self.recorder.now()
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
        self.counters.update(data["counters"])
        self.scheduler.load_state(data["scheduler"])
        self.acceptance.load_state(data["acceptance"])
        self.phase.load_state(data["phase"])
        self.archive.load_state(data["archive"])
        self.restarter.load_state(data["restart"], t)
        self._plateau.restore(data["plateau"])
        for move, ctx in zip(self._moves, self._ctxs):
            state = data["moves"].get(move.name)
            if state is not None:
                move.load_state(state)
            ctx.stats.update(data["move_stats"].get(move.name, {}))
