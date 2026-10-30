"""Fakes shared by the engine tests (this module holds no tests).

The engine is tested against small stand-ins for the parts other modules provide, written to
the documented APIs (DESIGN.md section 4):

* ``FakeState``     ValueSet subset: ok/size/depth/values/key/gates/rollback/commit/check.
                    A state is a set of ints; ``size()`` counts them and the depth is encoded
                    in the high bits (``v >> DEPTH_SHIFT``), so tests build states with
                    ``mk(gates, depth, variant)``.  The value ``BAD`` makes a state unrealizable.
* ``FakeObjective`` key/feasible/search_cap/gate_limit/kind.
* ``FakeRecorder``  Recorder API with an in-memory ring, events and a controllable clock.
* ``FakePlateau``   PlateauTracker API.
* ``FakeConstruct`` choose_root/build_root;  ``FakePool`` sample.
* Moves: ``ScriptMove`` (replays a script of value sets), ``RandomMove`` (random walk that
  only uses ``ctx.rng``, so proposals replay from the dossier seed), ``NoopMove``.
"""
from __future__ import annotations

from collections import deque

from xorsearch.config.schema import Knob, Section
from xorsearch.config.settings import for_sections
from xorsearch.core import budget as budget_mod
from xorsearch.engine import SECTIONS, Engine
from xorsearch.moves.base import Move, Proposal

DEPTH_SHIFT = 16
BAD = (1 << DEPTH_SHIFT) - 1          # depth 0, marks an unrealizable state


def mk(gates: int, depth: int, variant: int = 0) -> list[int]:
    """A fake value set with ``gates`` values and depth ``depth``; variants are disjoint."""
    return [depth << DEPTH_SHIFT] + [variant * 1000 + i for i in range(1, gates)]


class FakeState:
    """Value set whose score is (len, max depth marker)."""

    def __init__(self, values, cap=None):
        self.vals = set(values)
        self.cap = cap
        self.commits = 0
        self.checks = 0

    def depth(self):
        return max((v >> DEPTH_SHIFT for v in self.vals), default=0)

    def size(self):
        return len(self.vals)

    def ok(self):
        return BAD not in self.vals and (self.cap is None or self.depth() <= self.cap)

    def edit(self, values):
        """Replace the values; returns the journal (the old set)."""
        old = self.vals
        self.vals = set(values)
        return old

    def rollback(self, journal):
        self.vals = journal

    def commit(self, journal):
        self.commits += 1

    def values(self):
        return list(self.vals)

    def key(self):
        return frozenset(self.vals)

    def gates(self):
        return [[0, 1] for _ in self.vals], [0]

    def check(self):
        self.checks += 1
        return True


def fake_factory(values, cap):
    return FakeState(values, cap)


class FakeTarget:
    n_inputs = 4
    rows = (3, 5, 6, 9)
    name = "fake"


class FakeObjective:
    """Lexicographic (gates, depth) or (depth, gates) with a real cap and a soft slack."""

    def __init__(self, kind="gates", depth_cap=None, gate_limit=None, soft_depth_slack=0):
        self.kind = kind
        self.depth_cap = depth_cap
        self.gate_limit = gate_limit
        self.soft_depth_slack = soft_depth_slack
        self.search_cap = None if depth_cap is None else depth_cap + soft_depth_slack

    def key(self, gates, depth):
        return (gates, depth) if self.kind == "gates" else (depth, gates)

    def feasible(self, gates, depth):
        return ((self.depth_cap is None or depth <= self.depth_cap)
                and (self.gate_limit is None or gates <= self.gate_limit))


class FakeClock:
    def __init__(self, t=0.0):
        self.t = t

    def advance(self, seconds):
        self.t += seconds


class FakeRecorder:
    """In-memory recorder; ``now()`` reads a FakeClock."""

    def __init__(self, clock=None, ring_size=16):
        self.clock = clock or FakeClock()
        self.proposals = 0
        self._ring = deque(maxlen=ring_size)
        self.improvements = []
        self.rejected = []
        self.events = []
        self.epochs = []
        self.epoch_flag = False

    def begin(self, kind, info):
        self.events.append((kind, info))

    def proposal(self, rec):
        self.proposals += 1
        self._ring.append(rec)

    def improvement(self, dossier, verify=None):
        """Like ``Recorder.improvement``: the verdict of ``verify(id)`` lands in the dossier
        and a rejected dossier is kept apart (``rejected``)."""
        ident = f"imp{len(self.improvements) + len(self.rejected) + 1}"
        if verify is not None:
            result = verify(ident)
            dossier["verification"] = result
            if isinstance(result, dict) and (result.get("ok") is False
                                             or result.get("equivalent") is False):
                dossier["rejected"] = True
                self.rejected.append(dossier)
                return ident
        self.improvements.append(dossier)
        return ident

    def event(self, ev, **fields):
        self.events.append((ev, fields))

    def epoch_due(self):
        return self.epoch_flag

    def epoch(self, fields):
        self.epochs.append(fields)

    def ring(self):
        return list(self._ring)

    def now(self):
        return self.clock.t

    def close(self):
        pass

    def of(self, ev):
        """Fields of every event of type ``ev``."""
        return [f for e, f in self.events if e == ev]


class FakePlateau:
    """PlateauTracker API (enter/observe/snapshot/close/checkpoint/restore)."""

    def __init__(self):
        self.level = None
        self.entry_it = 0
        self.proposals = 0
        self.neutral = 0
        self.keys = set()
        self.closed = []

    def enter(self, level_key, state_key, it, t):
        self.level = tuple(level_key)
        self.entry_it = it
        self.proposals = 0
        self.neutral = 0
        self.keys = set()

    def observe(self, state_key, accepted, neutral, it, t):
        self.proposals += 1
        if accepted and neutral:
            self.neutral += 1
        if state_key is not None:
            self.keys.add(hash(state_key))

    def snapshot(self, it=None, t=None):
        return {"level": list(self.level) if self.level else None,
                "proposals": self.proposals, "neutral_accepts": self.neutral,
                "distinct_states": len(self.keys)}

    def close(self, exit_kind, it, t):
        rec = dict(self.snapshot(), exit=exit_kind, age_it=it - self.entry_it)
        self.closed.append(rec)
        return rec

    def checkpoint(self):
        return {"level": list(self.level) if self.level else None, "entry_it": self.entry_it,
                "proposals": self.proposals, "neutral": self.neutral, "keys": sorted(self.keys)}

    def restore(self, data):
        self.level = tuple(data["level"]) if data["level"] else None
        self.entry_it = data["entry_it"]
        self.proposals = data["proposals"]
        self.neutral = data["neutral"]
        self.keys = set(data["keys"])


class FakeConstruct:
    """Root constructor: fixed score, a seed-dependent variant (so roots are distinct)."""

    def __init__(self, gates=20, depth=3):
        self.gates = gates
        self.depth = depth
        self.calls = []

    def choose_root(self, rng, cfg=None, target=None, cap=None):
        return "naive"

    def build_root(self, name, target, rng, cap=None, budget=None, cfg=None):
        variant = rng.randrange(1, 60)
        self.calls.append((name, variant, cap))
        values = mk(self.gates, self.depth, variant)
        return values, {"name": name, "built": name, "gate_count": len(values),
                        "depth": self.depth, "fallback": None}


class FakePool:
    """campaign.sharing.Pool API: ``sample(exclude_keys, rng) -> elite dict | None``."""

    def __init__(self, items=()):
        self.items = [list(v) for v in items]
        self.samples = 0

    def _elite(self, i, values):
        g = len(values)
        d = max(v >> DEPTH_SHIFT for v in values)
        return {"values": list(values), "gates": g, "depth": d, "donor": "w9",
                "record": f"rec{i}", "dag_sha256": f"dag{i}"}

    def sample(self, exclude_keys=(), rng=None):
        self.samples += 1
        for i, values in enumerate(self.items):
            if frozenset(values) not in exclude_keys:
                return self._elite(i, values)
        return None


# -- moves ----------------------------------------------------------------------------------
def move_section(name, weight=1.0, burst_weight=None, repair_weight=None):
    """Knob section ``moves.fake.<name>`` for a fake move."""
    knobs = {"weight": Knob(weight, "prior weight", min=0)}
    if burst_weight is not None:
        knobs["burst_weight"] = Knob(burst_weight, "burst weight", min=0)
    if repair_weight is not None:
        knobs["repair_weight"] = Knob(repair_weight, "repair weight", min=0)
    return Section(f"moves.fake.{name}", f"fake move {name}", knobs)


class FakeMove(Move):
    """Base for fake moves: name, family and knob section are per instance."""

    def __init__(self, settings, name, family="walk"):
        self.name = name
        self.family = family
        self.knobs = Section(f"moves.fake.{name}", "", {})
        super().__init__(settings)
        self.calls = 0


class ScriptMove(FakeMove):
    """Plays a script: a value list (edit), ``None`` (no proposal), ``"noop"`` (journal None)
    or ``"bad"`` (an unrealizable edit).  After the script it returns None."""

    def __init__(self, settings, name, script=(), family="walk", work=3, trace=None):
        super().__init__(settings, name, family)
        self.script = deque(script)
        self.work = work
        self.trace = trace or {}

    def propose(self, ctx):
        self.calls += 1
        if not self.script:
            return None
        item = self.script.popleft()
        if item is None:
            return None
        if item == "noop":
            return Proposal(self.name, None, {"components": [self.name]}, self.work)
        if item == "bad":
            values = ctx.state.values() + [BAD]
        else:
            values = item
        journal = ctx.state.edit(values)
        trace = {"components": [self.name, "edit"], "params": {"n": len(values)}}
        trace.update(self.trace)
        return Proposal(self.name, journal, trace, self.work)


class RandomMove(FakeMove):
    """Random remove / swap / add on the value set, driven only by ``ctx.rng``."""

    def __init__(self, settings, name, family="walk", p_remove=0.2, p_add=0.3):
        super().__init__(settings, name, family)
        self.p_remove = p_remove
        self.p_add = p_add
        self.counter = 0              # persistent move state (checkpointed)

    def propose(self, ctx):
        self.calls += 1
        self.counter += 1
        rng = ctx.rng
        st = ctx.state
        plain = sorted(v for v in st.vals if v < (1 << DEPTH_SHIFT) and v != BAD)
        r = rng.random()
        values = set(st.vals)
        if r < self.p_remove and len(plain) > 2:
            values.discard(rng.choice(plain))
            kind = "remove"
        elif r < self.p_remove + self.p_add:
            values.add(rng.randrange(1, 60000))
            kind = "add"
        else:
            if plain:
                values.discard(rng.choice(plain))
            values.add(rng.randrange(1, 60000))
            kind = "swap"
        journal = st.edit(values)
        return Proposal(self.name, journal, {"components": [self.name, kind]},
                        1 + int(rng.random() * 4))

    def state(self):
        return {"counter": self.counter}

    def load_state(self, data):
        self.counter = data["counter"]


class NoopMove(FakeMove):
    """Never proposes anything (stall tests, overhead benchmark)."""

    def propose(self, ctx):
        self.calls += 1
        return None


# -- assembly -------------------------------------------------------------------------------
def settings_for(move_sections=(), overrides=None):
    """Settings over the engine sections, ``budget`` and the given fake move sections."""
    return for_sections(*SECTIONS, budget_mod.KNOBS, *move_sections, overrides=overrides)


def make_engine(settings, moves, *, objective=None, seed=None, recorder=None, pool=None,
                construct=None, rng_seed=1, worker_id="w0"):
    """An Engine over fakes.  ``moves`` is a list of Move instances."""
    return Engine(FakeTarget(), objective or FakeObjective(), settings, rng_seed=rng_seed,
                  recorder=recorder or FakeRecorder(), worker_id=worker_id,
                  seed_circuit=seed, pool=pool, moves=moves, state_factory=fake_factory,
                  construct=construct or FakeConstruct(), plateau_tracker=FakePlateau)
