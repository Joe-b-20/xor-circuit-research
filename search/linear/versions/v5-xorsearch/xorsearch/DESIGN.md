# xorsearch design

One search method for the smallest (then shallowest) XOR circuit of any GF(2) linear map,
from a handful of inputs to 64+ inputs and a thousand gates. This file is the contract every
module follows. Read it before editing code.

## 1. What the evidence says

Three studies (framework campaigns, historical runs, kernel profiling; full reports in
`docs/evidence/`) fixed these decisions.

| Finding | Number | Decision |
|---|---|---|
| Walk produced nearly every historical record | every 88 and 91@4 came from walk; 736 walk vs 22 LNS improvements in the archive catalog | Walk (remove + exact repair) is the main move |
| v2 LNS / v2 walk led the generic framework | 9 and 8 of 29 strict improvements, from 13.6% of CPU | LNS with deadline-aware rebuild is the second move |
| 10 of 17 engines never improved anything | 986 of 1,871 CPU-h | v3 structural moves, BP-as-move and constructors-as-moves are off by default |
| Engines kept stale private trajectories | 59% of engine slots ≥5 gates behind the worker best | One trajectory per worker; every move acts on it |
| Fresh starts on a new best pay off fast | 15 of 29 improvements within ≤374 iterations of a fresh start | Burst phase after every new best |
| Long trajectories broke every long plateau | all 6 plateau breaks came from 2.5–24 h old chains | Adoption never resets a chain by default |
| Fresh constructor roots found new basins | 7 of 58 naive roots reached 88; median 2,234 s | Restart from fresh randomized roots when stalled |
| Forced sharing collapsed diversity | 14 Jul cascade; FOX Mu8 10 workers on 4 DAGs while 90 DAGs existed | Pull-on-stall sharing of distinct elites, not push-adopt |
| Depth slack then repair cut gates | 129/7→128/10→128/7 in 0.14 h; capped Joltik stuck 75 h | Soft depth cap during search, depth repair before recording |
| Old kernels recomputed everything | walk 0.4 it/s on FOX Mu8 | Incremental triple-index core: 119 walk it/s, 285 LNS it/s |
| Improvements could not be attributed | 89@4 not attributable; no RNG at discovery | Every improvement gets a dossier with move trace, state before/during/after and replay seed |

## 2. The method

Each worker runs one **chain**: a current value set held by the incremental core. A loop picks
a move, the move edits the chain speculatively, the engine scores the result and accepts or
undoes it.

```
seed or root ──► chain ──► pick move (scheduler, phase weights)
                   ▲            │
                   │            ▼
                   │      propose: edit state, return Proposal (trace + undo journal)
                   │            │
                   │            ▼
                   │      score (gates, depth) ─► accept? (acceptance policy) ─ no ─► undo
                   │            │ yes
                   │            ▼
                   │      new chain best? ─► new worker best within real cap? ─► record + dossier
                   │            │                                                  phase = burst
                   │            ▼
                   └──── plateau tracker, restart controller (stall ► fresh root | elite | shared),
                         periodic sharing, checkpoint, epoch metrics
```

**Phases** (only weights change; the loop is the same):
- `burst`: right after any new chain best. A fixed work budget runs all local moves near
  uniformly from the new best.
- `plateau`: the default. Adaptive weights; neutral moves accepted.
- `repair`: chain beats the worker best on gates but exceeds the real depth cap. Depth-repair
  moves dominate until the chain fits the cap or the repair budget ends.

**Restarts**: when the chain best has not improved for `restart.stall_seconds` (or work), or the
chain's root has run `restart.root_seconds`, the chain restarts from one of: a fresh randomized
constructor root, a distinct elite from the worker archive, or a distinct elite from the shared
campaign pool. Weights are configurable.

**Sharing**: workers publish records. The coordinator keeps a campaign pool of distinct DAGs
per frontier point. Workers pull from it only when they restart (default), never mid-chain.
`sharing.mode = "push"` restores the old forced adoption for comparison.

## 3. Package layout and ownership

```
xorsearch/
  __init__.py, __main__.py     python -m xorsearch
  cli.py                       commands (run, resume, stop, status, report, verify, config, targets, quick)
  DESIGN.md                    this file
  README.md                    user guide
  docs/evidence/               the three evidence reports behind the defaults
  config/
    schema.py                  Knob / Section declarations, validation (single source of truth)
    settings.py                Settings: layered, validated, dotted access, provenance of each value
    registry.py                imports every module that declares KNOBS
    profiles/*.toml            ready-made profiles: default, quick, large, depth, legacy-compat
  core/
    valueset.py                ValueSet: incremental triple-index state (the hot kernel)
    target.py                  Target model, loaders, catalog and generators
    circuit.py                 Circuit model, independent verifier, normalise, DAG hash, JSON/NCFF io
    objective.py               Objective: score keys, caps, gate limits, feasibility
    budget.py                  Budget: work counters + optional deadline, cheap gated clock checks
  moves/
    base.py                    Move protocol, Proposal, MoveContext, registry
    walk.py                    remove1, hub (remove2/add1), expand (remove1/add2), window (remove k)
    lns.py                     destroy operators (small, cone, big), injection, rebuild, peel
    rebuild.py                 rebuild strategies: greedy extract, deadline-aware beam on the triple index
    depth.py                   depth repair: deadline rebuild at a tighter cap, reschedule
    structural.py              translate, cores, component, interface, backward (wrappers over vendored code)
    depth3.py                  depth-3 partition annealer (specialist)
    construct.py               root constructors: naive balanced, Paar, Boyar–Peralta (upper-bound distance)
  engine/
    loop.py                    Engine: the one search loop
    acceptance.py              acceptance policies
    scheduler.py               move selection: fixed or adaptive (bandit) per phase
    archive.py                 elite archive with DAG dedup and diversity-aware eviction
    restart.py                 stall detection and restart source selection
    phase.py                   burst / plateau / repair controller
  telemetry/
    recorder.py                Recorder: events, ring buffer, dossiers, epochs, plateau records
    metrics.py                 diversity, plateau shape, distances, rate counters
    schema.md                  event and dossier formats
    report.py                  run directory → CSV tables + self-contained report.html
  campaign/
    coordinator.py             process supervisor, campaign pool, fleet diversity panel
    worker.py                  worker process: Engine + checkpoints + records + sharing
    sharing.py                 campaign pool files and pull/push policies
    records.py                 record files (circuit JSON, NCFF, verification, dossier link)
    checkpoint.py              atomic files, checkpoint schema, resume
    freeze.py                  freeze source + config into the run directory with hashes
  vendor/                      copied v2/v3 kernels used by structural.py (64-bit versions from search/engines)
  tests/                       unittest suites, one per module, plus positive controls for each move
```

## 4. Interfaces

### 4.1 Configuration

Every tunable value is a `Knob` declared next to the code that reads it, in a module-level
`KNOBS` section. Nothing tunable is a literal in an algorithm.

```python
from xorsearch.config.schema import Knob, Section
KNOBS = Section("moves.walk.hub", "Remove two values, add one repair.", {
    "weight": Knob(2.0, "Prior scheduler weight in the plateau phase.", min=0),
    "near_hamming": Knob(8, "Second victim within this Hamming distance of the first.", min=0),
    "near_p": Knob(0.5, "Probability the second victim is chosen near the first.", min=0, max=1),
})
```

Layering, lowest to highest: built-in defaults → profile TOML files (`profile = ["default", "large"]`)
→ campaign file → worker-group overrides → per-worker overrides → CLI `--set a.b.c=value`.
`Settings` validates types and ranges, rejects unknown keys with a suggestion, and records where
each value came from (`settings.origin("moves.walk.hub.weight")`). Code reads a subtree:
`cfg = settings.view("moves.walk.hub"); cfg.weight`. The resolved settings and origins are frozen
into every run directory.

### 4.2 Core kernel (`core/valueset.py`)

`ValueSet(n, targets, values, cap=None, pairsums=False)` keeps `U = inputs ∪ values` with the
triple index `tri[v] = {x ∈ U : v ⊕ x ∈ U}`, exact earliest levels, one witness parent and
witness children per value, and an optional lazy pair-sum counter.

| Method | Meaning |
|---|---|
| `add(w) -> bool` | insert w, update levels |
| `remove(values) -> Undo` | remove, re-level only witness descendants; `undo.stuck` = now-unrealizable values |
| `restore(undo)` | exact inverse of the matching `remove` |
| `journal() / rollback(j)` | record a sequence of add/remove and undo it exactly |
| `trim()`, `peel(rng, budget)` | drop dead values; drop any removable non-target until 1-minimal |
| `ok()`, `depth()`, `size()` | all targets realized; max target level; live gate count |
| `live()`, `values()`, `key()` | live values; all non-input values; frozenset identity |
| `gates() -> (gates, outputs)` | live witness DAG in level order |
| `dag_sha256(matrix_sha256)` | identical to `core.circuit.dag_sha256` of the emitted circuit |
| `repair_candidates(stuck, forbid)`, `valid_repairs(stuck, forbid)`, `unlocks(w, stuck)` | complete single-value repair enumeration |
| `extract(cost, rng, noise)` | greedy top-down rebuild over U (cost classes) |
| `set_cap(cap)` | change the cap and re-level |
| `check()` | full invariant recomputation (tests and `debug.check_every`) |

Targets may be unit vectors (free outputs), repeated or zero; all are handled. Inputs are never
removed.

### 4.3 Moves (`moves/base.py`)

```python
class Move:
    name: str            # registry name, e.g. "walk.hub"
    family: str          # "walk" | "lns" | "structural" | "depth" | "depth3"
    knobs: Section       # its KNOBS
    def applicable(self, ctx) -> str | None      # None if applicable, else the reason
    def propose(self, ctx) -> Proposal | None    # edit ctx.state speculatively

@dataclass
class Proposal:
    move: str
    journal: Journal | None     # undo journal of edits applied to ctx.state (None: state untouched)
    trace: dict                 # what was done: components, parameters, removed, added, rebuild, ranks
    work: int                   # work units spent
    deterministic: bool = True  # False if a wall-clock budget influenced the result
```

`MoveContext` gives a move: `target`, `objective`, `state` (the chain's ValueSet), `best_key`,
`rng` (the engine's `random.Random`), `cfg` (its own knob view), `budget`, `archive` (read-only),
`phase`, and `stats` (per-move counters it may update). A move must leave `ctx.state` either
unchanged (return None or a Proposal with `journal=None`) or trimmed and with its edits recorded in
the journal. It must not keep references to the state between calls. The engine undoes rejected
proposals with `state.rollback(journal)`.

`trace` keys are short and stable: `components` (ordered list of sub-operations such as
`["destroy.cone", "inject", "rebuild.deadline", "peel"]`), `params` (the effective parameters
used), `removed`, `added` (value lists, capped by `telemetry.trace_values_max`), and move-specific
fields documented in the move's docstring. This is what an improvement dossier attributes.

### 4.4 Engine (`engine/loop.py`)

```python
class Engine:
    def __init__(self, target, objective, settings, *, rng_seed, recorder, worker_id,
                 seed_circuit=None, pool=None): ...
    def step(self) -> StepResult          # one proposal through accept/undo/record
    def run(self, stop: Callable[[], bool]) -> None
    def checkpoint(self) -> dict          # JSON-safe: chain values, best, RNG state, scheduler,
                                          # acceptance, phase, archive, plateau tracker, counters
    @classmethod
    def resume(cls, data, target, objective, settings, *, recorder, pool=None) -> "Engine"
```

`StepResult` carries move name, score before/after, accepted, neutral, improved (chain / worker),
and work. The engine owns the scheduler, acceptance, phase controller, archive and restart
controller, and calls the recorder.

### 4.5 Telemetry (`telemetry/recorder.py`)

All files are UTF-8 JSONL or JSON in the worker directory; every event has
`t` (seconds since campaign start, monotonic), `utc`, `worker`, `it` (iteration), `ev` (type).

| Event | When | Key fields |
|---|---|---|
| `start` / `resume` / `stop` | process lifecycle | settings hash, seed, source hash, environment |
| `epoch` | every `telemetry.epoch_seconds` | per-move counters (proposals, valid, accepted, neutral, uphill, improved, work, cpu_s), acceptance state, scheduler weights, chain/best score, plateau and diversity metrics |
| `improve` | new worker best (any objective point that becomes nondominated) | id, kind (`gates`, `depth`, `frontier`), before/after score, move, components, dossier path |
| `plateau` | a plateau closes | id, score level, duration (it, s), proposals, neutral accepts, distinct states seen, drift from entry, exit kind |
| `restart` | chain restarts | reason, source (root/elite/shared), root id and seed, previous chain summary |
| `pull` / `publish` | sharing | record ids, donor worker |
| `record` | a distinct DAG saved at an existing point | point, DAG hash |
| `followup` | `telemetry.followup_iterations` after an improvement | id, further improvements, plateau length so far |

Each `improve` writes `dossiers/<id>.json`: worker, wall and monotonic time, iteration, chain id,
root id, lineage (parent improvement id, chain origin), score before/after, the full proposal
trace, values before and after (and gates after), the last `telemetry.ring_size` proposals
(move, Δgates, Δdepth, accepted, neutral), state metrics before the move (plateau age and size,
neutral rate, temperature, phase, scheduler weights, distance from chain best, root and elites),
the RNG state at proposal start for replay, and the verification result. `report.py` turns a run
directory into CSV tables and a self-contained HTML report.

The engine computes metrics and assembles dossiers; the recorder owns formats, files, the ring
buffer, counters and timing. The exact boundary:

```python
class Recorder:                                   # telemetry/recorder.py
    def __init__(self, directory, worker_id, settings, clock=None): ...
    def begin(self, kind: str, info: dict) -> None          # "start" | "resume"
    def proposal(self, rec: dict) -> None                   # every proposal; must be O(1)
        # rec: it, move, accepted, neutral, d_gates, d_depth, gates, depth, work, components
    def improvement(self, dossier: dict) -> str             # assigns id, writes dossier + event
    def event(self, ev: str, **fields) -> None              # restart, plateau, pull, publish, record, followup, phase
    def epoch_due(self) -> bool
    def epoch(self, fields: dict) -> None                   # adds and resets per-move counters
    def ring(self) -> list[dict]                            # last telemetry.ring_size proposals
    def now(self) -> float                                  # seconds since campaign start
    def close(self) -> None

class NullRecorder(Recorder): ...                           # no files; same API (tests, quick runs)

# telemetry/metrics.py
def jaccard_distance(a: frozenset, b: frozenset) -> float
def diversity(sets: list[frozenset]) -> dict              # mean/min pairwise distance, distinct count
class PlateauTracker:
    def enter(self, level_key, state_key, it, t) -> None
    def observe(self, state_key, accepted: bool, neutral: bool, it, t) -> None
    def snapshot(self) -> dict    # age_it, age_s, proposals, neutral_accepts, distinct_states, drift
    def close(self, exit_kind: str, it, t) -> dict
```

### 4.6 Campaign

A campaign TOML lists worker groups (`target`, `count`, `objective`, `depth_cap`, `set` overrides).
`xorsearch run CAMPAIGN.toml --out DIR` freezes source and resolved settings, starts the
coordinator, which starts one process per worker. Coordinator writes `campaign.jsonl`
(global frontier changes with worker attribution, fleet diversity snapshots, pool updates) and
`status.json`. `resume`, `stop`, `status`, `report` and `verify` operate on the directory.

## 5. Code rules

- Python ≥ 3.11, standard library only. `unittest` tests in `xorsearch/tests`.
- Every module starts with a docstring saying what it does and how it fits the method. Every
  public class and function has a docstring. Comments explain why, not what.
- No tunable literal in algorithm code: declare a Knob.
- Hot loops: bind attributes to locals, plain for-loops, no `deepcopy`, no JSON, no I/O, no
  per-item exceptions, clock checks gated every 64–256 operations through `Budget`.
- The state is valid by construction; the independent verifier (`core.circuit.verify`) runs on
  every record before it is written, and the kernel's `check()` runs every
  `debug.check_every` steps when enabled.
- Work units, not seconds, bound moves by default (`budget.mode = "work"`), so a proposal replays
  exactly from its RNG state. Wall-clock budgets are allowed and marked `deterministic=False`.
- Every move ships with a positive-control test: a small circuit where it must find a known
  one-gate improvement.
- Measure before optimising; keep the benchmark in `tests/bench_*.py` (not run by default).
