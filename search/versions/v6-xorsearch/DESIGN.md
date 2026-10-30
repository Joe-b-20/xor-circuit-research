# xorsearch design

One search method for the smallest (then shallowest) XOR circuit of any GF(2) linear map,
from a handful of inputs to 64+ inputs and a thousand gates. This file is the contract every
module follows, kept in step with the code. Read it before editing code; the user guide is
[README.md](README.md).

## 1. What the evidence says

Three studies (framework campaigns, historical runs, kernel profiling; full reports in
`docs/evidence/`) fixed these decisions.

| Finding | Number | Decision |
|---|---|---|
| Walk produced nearly every historical record | every 88 and 91@4 came from walk; 736 walk vs 22 LNS improvements in the archive catalog | Walk (remove + exact repair) is the main move |
| v2 LNS / v2 walk led the generic framework | 9 and 8 of 29 strict improvements, from 13.6% of CPU | LNS with deadline-aware rebuild is the second move |
| 10 of 17 engines never improved anything | 986 of 1,871 CPU-h | No BP-as-move or constructors-as-moves; the v3 structural kernels were removed after the 2026-10-28 campaigns (≤ 0.11× the average weighted yield per CPU) |
| Engines kept stale private trajectories | 59% of engine slots ≥5 gates behind the worker best | One trajectory per worker; every move acts on it |
| Fresh starts on a new best pay off fast | 15 of 29 improvements within ≤374 iterations of a fresh start | Burst phase after every new best |
| Long trajectories broke every long plateau | all 6 plateau breaks came from 2.5–24 h old chains | Nothing from outside resets a running chain |
| Fresh constructor roots found new basins | 7 of 58 naive roots reached 88; median 2,234 s | Restart from fresh randomized roots when stalled |
| Forced sharing collapsed diversity | 14 Jul cascade; FOX Mu8 10 workers on 4 DAGs while 90 DAGs existed | Pull-on-stall sharing of distinct elites, never forced adoption |
| Depth slack then repair cut gates | 129/7→128/10→128/7 in 0.14 h; capped Joltik stuck 75 h | Soft depth cap during search, depth repair before recording |
| Old kernels recomputed everything | walk 0.4 it/s on FOX Mu8 | Incremental triple-index core: 119 walk it/s, 285 LNS it/s |
| Improvements could not be attributed | 89@4 not attributable; no RNG at discovery | Every improvement gets a dossier with move trace, state before/during/after and replay seed |

## 2. The method

Each worker runs one **chain**: a current value set held by the incremental core, built at the
objective's *search* cap (the real cap plus the soft slack). A loop picks a move, the move edits
the chain speculatively, the engine scores the result and keeps or undoes it.

```
seed or root ──► chain ──► pick move (scheduler, phase weights)
                   ▲            │
                   │            ▼
                   │      propose: edit state in a journal, return Proposal (trace + journal)
                   │            │
                   │            ▼
                   │      score (gates, depth) ─► accept? (acceptance policy) ─ no ─► rollback
                   │            │ yes
                   │            ▼
                   │      new chain best? ─► new worker best / frontier point within the real
                   │            │            cap? ─► dossier + verified record; phase = burst
                   │            ▼
                   └──── plateau tracker, restart controller (stall ► fresh root | elite |
                         shared | best), checkpoint, epoch metrics
```

**Phases** (only weights change; the loop is the same):
- `burst`: right after any new chain best (and every restart). `phase.burst_budget` proposals
  run the local moves near uniformly from the new best.
- `plateau`: the default. Adaptive weights; neutral moves accepted.
- `repair`: the chain beats the worker best on gates but exceeds the real depth cap. Depth-repair
  moves get `phase.repair_share` of the selection until the chain fits or the budget ends.

**Restarts**: when the chain best has not improved for `restart.stall_seconds` (or
`stall_work` / `stall_proposals`), or the chain's root has run `restart.root_seconds`, the chain
restarts from a fresh randomized constructor root, a distinct elite of the worker archive, a
distinct elite of the campaign pool or the worker best (weights `restart.w_*`). Timers scale with
circuit size above `restart.size_ref` gates; a chain holding the worker best gets
`incumbent_factor` more time.

**Sharing**: workers save verified records. The coordinator keeps a campaign pool of distinct
verified DAGs per frontier point. Workers pull from it only when they restart (`sharing.mode =
"pull"`, the default; `"off"` disables sharing), never mid-chain.

## 3. Package layout

```
xorsearch/
  __init__.py, __main__.py     python -m xorsearch
  cli.py                       commands: run, resume, stop, status, plan, report, verify, config, targets, quick
  DESIGN.md, README.md         this file; the user guide
  docs/BENCHMARKS.md           head-to-head runs against search/
  docs/evidence/               the three evidence reports behind the defaults (source reports, frozen)
  examples/*.toml              campaign files: fox_mu4, fox_mu8, three_targets, sharing_ab, legacy_ab
  targets/*.json               xorsearch catalog entries (mixcolumns); search/targets/*.json are read too
  config/
    schema.py                  Knob / Section declarations, validation (single source of truth)
    settings.py                Settings: layered, validated, dotted access, provenance; TOML output
    registry.py                imports every module that declares KNOBS
    profiles/*.toml            default, quick, large, depth, legacy-compat
  core/
    valueset.py                ValueSet: incremental triple-index state (the hot kernel)
    target.py                  Target model, loaders, catalog and generators
    circuit.py                 Circuit model, independent verifier, normalise, DAG hash, JSON/NCFF io
    objective.py               Objective: score keys, caps, gate limits, soft slack, feasibility
    budget.py                  Budget: work counters + optional deadline, cheap gated clock checks
  moves/
    base.py                    Move protocol, Proposal, MoveContext, registry
    walk.py                    remove1 (remove one, exact repair), expand (remove1/add2)
    lns.py                     destroy operators (small, cone, big), injection, rebuild, peel
    rebuild.py                 rebuild strategies: greedy extract, deadline-aware beam on the triple index
    depth.py                   depth repair: deadline rebuild at a tighter cap
    structural.py              translate, cores (wrappers over the vendored v2 kernels)
    depth3.py                  depth-3 partition annealer (move and restart root)
    construct.py               root constructors: naive balanced, Paar, Boyar–Peralta, anneal3
  engine/
    loop.py                    Engine: the one search loop
    dossier.py                 improvements, records and dossiers (DossierMixin), replay metadata
    acceptance.py              threshold acceptance (neutral moves, bounded uphill steps)
    scheduler.py               move selection: fixed or adaptive (bandit) per phase
    archive.py                 elite archive with DAG dedup and diversity-aware eviction
    restart.py                 stall detection and restart source selection
    phase.py                   burst / plateau / repair controller
  telemetry/
    recorder.py                Recorder (worker) and EventLog (coordinator): events, ring, dossiers, epochs
    metrics.py                 diversity, plateau tracker, distances, circuit shape
    schema.md                  event and dossier formats
    report.py                  run directory → CSV tables + self-contained report.html
  campaign/
    freeze.py                  campaign TOML → plan (layered settings) → frozen run directory
    coordinator.py             process supervisor, record collection, global frontier, pool, fleet diversity
    worker.py                  worker process: Engine + checkpoints + status + records + pool
    sharing.py                 campaign pool files (coordinator) and the engine's Pool (pull/off)
    records.py                 record files, independent re-verification, the Backend seam
    checkpoint.py              atomic files, process identity, campaign lock, checkpoint envelopes
  vendor/                      copied v2 kernels used by structural.py
  tests/                       unittest suites, one per module, positive controls for each move, bench_*.py
```

## 4. Interfaces

### 4.1 Configuration

Every tunable value is a `Knob` declared next to the code that reads it, in a module-level
`KNOBS` section (or a tuple of sections). Nothing tunable is a literal in an algorithm.

```python
from xorsearch.config.schema import Knob, Section
KNOBS = Section("moves.walk.expand", "Remove one helper, add two values (up to +1).", {
    "weight": Knob(0.6, "Prior scheduler weight in the plateau phase.", min=0),
    "victims": Knob(4, "Victims tried per proposal (v2 tried up to 4).", min=1),
    "head_fraction": Knob(0.5, "Share of first values taken by unlock count.", min=0, max=1),
})
```

`Knob(default, doc, min=, max=, choices=, kind=, nullable=)`: the default fixes the type (float
knobs accept ints); lists whose default holds one scalar type check every element; nullable
knobs accept null, written `"none"` in TOML and on `--set`. `Knob.constraint()` is the short
legal-values text shown by `config explain` and `config show`.

Layering, lowest to highest, with the origin label every value keeps:

```
default < profile:<name> < campaign < campaign:set < group:<name> < worker:<id> < cli
```

`Settings` validates types and ranges, rejects unknown keys with a suggestion, and records where
each value came from (`settings.origin("moves.walk.expand.weight")`). Code reads a subtree once:
`cfg = settings.view("moves.walk.expand"); cfg.weight`. `config.settings.to_toml(settings)` writes
settings back as a commented TOML profile (`config show`). `campaign.*` and
`sharing.pool_per_point` are coordinator knobs with one campaign-wide value. The resolved settings
and origins of every worker are frozen into its run directory.

### 4.2 Core kernel (`core/valueset.py`)

`ValueSet(n, targets, values, cap=None, pairsums=False)` keeps `U = inputs ∪ targets ∪ values`
with the triple index `tri[v] = {x ∈ U : v ⊕ x ∈ U}`, exact earliest levels, one **canonical
witness** parent per value (of the recipes achieving its level, the one with the smaller operand)
and witness children, plus an optional lazy pair-sum index. Because witnesses are canonical,
levels, the live DAG and its gate count are a pure function of (U, cap): undo is exact, a state
rebuilt from its sorted values is identical (checkpoints and replays store only the values), and
random choices replay regardless of history.

| Method | Meaning |
|---|---|
| `add(w, partners=None) -> bool` | insert w, update levels (one O(\|U\|) scan) |
| `remove(values) -> Undo` | remove, re-level only witness descendants; `undo.stuck` = now-unrealizable values |
| `restore(undo)` | exact inverse of the matching `remove` |
| `retain(keep) -> Undo` | remove every non-input, non-target value not in `keep` |
| `journal()`, `commit(j)`, `rollback(j)` | record a sequence of edits; keep it or undo it exactly |
| `trim()`, `peel(rng, budget)` | drop dead / stuck values; drop removable non-targets until 1-minimal |
| `ok()`, `depth()`, `size()`, `count()` | all targets realized; max target level; live gate count; O(1) realized count (= `size()` on a trimmed state, what the loop scores) |
| `live()`, `values()`, `key()` | live values; all non-input values (sorted); frozenset identity |
| `gates() -> (gates, outputs)` | live witness DAG in level order (`core.circuit.Circuit(n, gates, outputs)` is the circuit the verifier checks) |
| `repair_candidates(stuck, forbid)`, `valid_repairs(stuck, forbid)`, `unlocks(w, stuck)` | complete single-value repair enumeration |
| `strands(v, among=None) -> bool` | would removing v leave something unrealizable (cap-free, no state change); cheap screen used by `peel` and local peel |
| `extract(cost, rng, noise) -> values` | greedy top-down rebuild over U (cost classes); apply with `retain` |
| `enable_pairsums()`, `p2_sync()`, `p2_multi` | the lazy pair-sum index (walk repairs, \|U\| ≤ `engine.pairsums_max_values`): one pair or the pair count per sum, plus the pairs and adjacency of the sums with ≥ 2 representations (`p2_multi`), so a repair query visits only those neighbours and `add` finds a value's triples from its pairs; it syncs when the outermost journal opens, and queries inside a journal correct pending edits exactly, so a rolled-back speculative add costs nothing |
| `check()` | full invariant recomputation (tests and `debug.check_every`) |

Targets may be unit vectors (free outputs), repeated or zero; all are handled. Inputs are never
removed.

### 4.3 Moves (`moves/base.py`)

```python
class Move:
    name: str            # registry name, e.g. "walk.remove1"
    family: str          # "walk" | "lns" | "structural" | "depth" | "depth3"
    knobs: Section       # its KNOBS; self.cfg is its view
    def applicable(self, target, objective) -> str | None   # None if it can run here, else why not
    def propose(self, ctx: MoveContext) -> Proposal | None  # edit ctx.state speculatively
    def state(self) -> dict / load_state(self, d)           # move memory for checkpoints

@dataclass
class Proposal:
    move: str
    journal: Journal | None     # undo journal of edits applied to ctx.state (None: state untouched)
    trace: dict                 # what was done: components, parameters, removed, added, rebuild, ranks
    work: int = 0               # work units spent
    deterministic: bool = True  # False if a wall-clock budget influenced the result
```

`applicable` is asked once per engine (not per proposal), so moves that cannot work on a target
or cap (depth3 on wide rows, structural kernels on huge circuits) cost nothing.
`MoveContext` gives a move `state` (the chain's ValueSet), `target`, `objective`, `best_key`,
`rng` (the per-proposal `random.Random`), `cfg`, `budget`, `archive` (read-only), `phase`
and `settings`. A move must leave `ctx.state` either
unchanged (return None or a Proposal with `journal=None`) or trimmed with its edits in the
journal, and must not keep references to the state between calls. The engine undoes rejected
proposals with `state.rollback(journal)`.

`trace` keys are short and stable: `components` (ordered sub-operations such as
`["destroy.cone", "inject", "rebuild.deadline", "peel"]`), `params` (the effective parameters),
`removed`, `added` (value lists, capped by `telemetry.trace_values_max`), and move-specific fields
documented in the move's docstring. This is what an improvement dossier attributes.

### 4.4 Engine (`engine/loop.py`, `engine/dossier.py`)

```python
class Engine:
    def __init__(self, target, objective, settings, *, rng_seed, recorder, worker_id,
                 seed_circuit=None, pool=None, moves=None, state_factory=None,
                 construct=None, plateau_tracker=None): ...
    def on_record(self, callback)       # callback(record) -> verification summary | None
    def step(self) -> StepResult        # one proposal through accept/undo/record
    def run(self, stop: Callable[[], bool]) -> None
    def snapshot(self) -> dict          # it, work, chain, root, phase, cur, chain_best, worker_best, frontier
    def checkpoint(self) -> dict        # JSON-safe: chain values, bests, RNG, scheduler, acceptance,
                                        # phase, archive, restart, plateau tracker, moves, counters
    @classmethod
    def resume(cls, data, target, objective, settings, *, recorder, pool=None, ...) -> "Engine"
```

`StepResult` (slots dataclass): `it`, `move`, `phase`, `gates_before`/`depth_before`,
`gates_after`/`depth_after`, `valid`, `accepted`, `neutral`, `improved_chain`, `improved_worker`,
`work`. The engine owns the scheduler, acceptance, phase controller, archive and restart
controller, and calls the recorder. For a new worker best or frontier point it writes the
dossier through the recorder and hands the record to the `on_record` callbacks (the worker's
verifying `RecordWriter.save`); a callback answer with `ok` False reverts the improvement and
restarts the chain on a clean state. With `engine.canonical_checkpoint` a checkpoint rebuilds
the chain from its sorted values, so a resumed engine continues exactly like the running one.

Selection cost (`scheduler.cost`) is **seconds** by default: the measured time of a proposal is
the only unit comparable across moves (work units count different things per move). Each
proposal still replays exactly from its seed when its move is work-bounded; `scheduler.cost =
"work"` makes the whole trajectory, scheduler included, replayable.

Pool contract (what `pool=` must provide; `campaign/sharing.py:Pool` is the implementation):
`sample(exclude_keys, rng) -> elite | None` for the "shared" restart source, where `elite` is a
dict with `values` (sorted masks), `donor`, `record`, `dag_sha256`, `gates`, `depth`.
Records reach the pool through the `on_record` callbacks (the worker's `RecordWriter.save`).

### 4.5 Telemetry (`telemetry/recorder.py`, `telemetry/metrics.py`)

All files are UTF-8 JSONL or JSON in the worker directory (formats: `telemetry/schema.md`);
every event has `v`, `t` (seconds since campaign start, monotonic, continuing across resumes),
`utc`, `worker`, `it`, `ev`.

| Event | When | Key fields |
|---|---|---|
| `start` / `resume` / `stop` | process lifecycle | settings hash, seed, source hash, environment, owner token |
| `epoch` | every `telemetry.epoch_seconds` | per-move counters (proposals, valid, accepted, neutral, uphill, improved, work, cpu_s), per-combination counters, acceptance state, scheduler weights, chain/best score, plateau and diversity metrics |
| `improve` | new worker best or nondominated feasible point | id, kind (`gates`, `depth`, `frontier`), before/after score, move, components, phase, plateau age, root, dossier path, verified |
| `plateau` | a plateau closes | id, level, duration (it, s), proposals, neutral accepts, distinct states, drift, exit kind |
| `restart` | chain restarts | reason, source (fresh/elite/shared/best), root, donor, previous chain summary |
| `pull`, `pool_sample` | a restart drew a pooled elite | record id, donor worker, point, pool version |
| `record` | a distinct DAG saved at an existing point | point, DAG hash |
| `followup` | `telemetry.followup_iterations` after an improvement | id, further improvements, plateau length so far |
| `move`, `phase`, `warn`, `verify_fail`, `root_failed` | moves left out at start (inapplicable / zero weight), phase changes, dead moves, rejected records, failed roots | |

Each `improve` writes `dossiers/<id>.json`: worker, wall and campaign time, iteration, chain and
root, lineage, score before/after, the proposal trace, values before and after (per
`telemetry.dossier_detail`), the last `telemetry.ring_size` proposals, state metrics before the
move, shape after, the replay block (seed and what exact replay needs) and the verification.

The engine computes metrics and assembles dossiers; the recorder owns formats, files, the ring
buffer, counters and timing:

```python
class Recorder:                                   # telemetry/recorder.py
    def __init__(self, directory, worker_id, settings=None, clock=None, *,
                 t0=None, wall=None, process_time=None): ...   # t0: shared campaign start
    def begin(self, kind: str, info: dict) -> None          # "start" | "resume"
    def proposal(self, rec: dict) -> None                   # every proposal; O(1)
        # rec: it, move, accepted, neutral, d_gates, d_depth, gates, depth, work, components
        #      [, valid, uphill, improved_chain, improved_worker, cpu_s, phase]
    def improvement(self, dossier: dict, verify=None) -> str
        # assigns id, writes the dossier, calls verify(id) (the worker's verifying record
        # save), rewrites the dossier with the verdict, then writes the improve event
    def set_epoch_source(self, source) -> None              # engine.epoch_fields for the final epoch
    def chain_id(self) -> str | None                        # current chain id, labels records
    def event(self, ev: str, **fields) -> None
    def epoch_due(self) -> bool;  def epoch(self, fields: dict) -> None
    def ring(self) -> list[dict];  def now(self) -> float
    def checkpoint(self) -> dict;  def restore(self, data) -> None
    def close(self, reason="normal", **fields) -> None      # writes the stop event

class NullRecorder(Recorder): ...      # no files; same API (tests, benchmarks)
class EventLog:                        # campaign.jsonl: write(ev, it=None, **fields), now(), close()

# telemetry/metrics.py
def jaccard_distance(a, b) -> float
def diversity(sets, *, max_pairs=None, basin_radius=None, basin_sample=None, seed=None) -> dict
class PlateauTracker:                  # from_settings(settings); enter, observe, snapshot, close,
                                       # checkpoint, restore; exact distinct states, then HyperLogLog
def shape_from_gates(...); def symmetric_difference(before, after)
```

### 4.6 Campaign (`campaign/`)

```
campaign.toml ──resolve──► plan + Settings per worker ──freeze──► run directory
                                                                   │
            run/resume ──► coordinator (frozen source, owns campaign.lock)
                             │  spawns one `_worker` process per planned worker
                             │  every collect_seconds: read records.jsonl, re-verify, frontier, pool, status.json
                             │  every diversity_seconds: fleet_diversity of bests and chains
                             ▼
                           workers: Engine + RecordWriter (verify, save) + Pool + checkpoints
```

- **freeze.py**: `resolve(campaign)` → `Resolved(plan, settings, ...)` checks everything (targets,
  seeds, knobs, objectives, CPUs) and starts nothing; `freeze(resolved, out)` claims `out`
  exclusively and writes source copy + reproducible tarball, snapshots, settings with origins,
  environment and git state, with hashes in `freeze.json`; `verify_freeze` re-checks them.
- **coordinator.py**: `Collector` (records → verified frontier, `PoolBook`, diversity; testable
  without processes) and `Coordinator` (lock, sessions, worker processes, failure policy
  `stop | continue | restart`, staged shutdown on STOP / SIGINT / SIGTERM / SIGHUP / duration).
  Campaign time `t` continues across sessions from the largest `t` any process wrote.
- **worker.py**: `WorkerProcess` drives `engine.step()` itself, so checkpoints and status writes
  happen between whole proposals; `CoordinatorLink` stops it when its coordinator
  is gone; `DeadlineLink` serves `xorsearch quick`.
- **records.py**: `RecordWriter` (verify → NCFF + verification sidecar → circuit JSON as commit
  marker → index line), `check_record` (independent re-verification), and `Backend`: every call
  the runtime makes into core, engine and telemetry, so a stub can replace them all.
- **checkpoint.py**: atomic JSON/bytes, torn-line-safe JSONL, process identity (pid + kernel start
  tick), `CampaignLock`, STOP requests, checkpoint envelopes bound to run, worker, plan, settings,
  source and matrix hashes.
- **cli.py**: `run`/`resume` exec the coordinator from the frozen copy, or with `--detach` start it
  in a new session with output in `coordinator.log`. The launcher reads the frozen campaign
  settings without a schema, so a run frozen by older or newer code still starts.

## 5. Code rules

- Python ≥ 3.11, standard library only. `unittest` tests in `xorsearch/tests`.
- Every module starts with a docstring saying what it does and how it fits the method. Every
  public class and function has a docstring. Comments explain why, not what.
- No tunable literal in algorithm or runtime code: declare a Knob.
- Hot loops: bind attributes to locals, plain for-loops, no `deepcopy`, no JSON, no I/O, no
  per-item exceptions, clock checks gated every 64–256 operations through `Budget`.
- The state is valid by construction; the independent verifier (`core.circuit.verify`) runs on
  every record before it is written and again in the coordinator, and the kernel's `check()`
  runs every `debug.check_every` proposals when enabled.
- Work units, not seconds, bound moves by default (`budget.mode = "work"`), so a proposal replays
  exactly from its seed. Wall-clock budgets are allowed and marked `deterministic=False`.
- Every move ships with a positive-control test: a small circuit where it must find a known
  one-gate improvement.
- Measure before optimising; keep the benchmark in `tests/bench_*.py` (not run by default).

## 6. Defaults chosen

`python -m xorsearch config explain KEY` gives each knob's evidence in its doc string. The ones
that shape the method:

| Knob | Default | Why |
|---|---|---|
| move weights (`moves.*.weight`) | walk.remove1 6, lns.rebuild 3, depth.repair 1, walk.expand 0.6, structural.translate 0.2, structural.cores 0.2; depth3.anneal 12 where it applies (real cap 3) | walk made nearly every record, LNS second; depth repair had the highest weighted yield per CPU-h in 2026-10-28; moves that never paid off were removed |
| `scheduler.mode`, `scheduler.cost` | `adaptive`, `seconds` | credit per second moves CPU to what pays off (52.7% of framework CPU went to engines that never improved) |
| `acceptance.*` | threshold: +1 uphill at p 0.15 within 2 of the chain best, neutral moves always kept | the v2 walk that made the records |
| `phase.burst_budget` | 400 proposals | 15 of 29 improvements came within 374 iterations of a fresh start |
| `objective.default_slack_gates` | 2 (soft depth slack for the gates objective) | slack then repair cut gates under caps |
| `restart.stall_seconds`, `root_seconds` | 2,000 s, 5,400 s at 100 gates, scaled by size | historical stalls of 1,500–2,400 s; every 88 came within 3,855 s of its root |
| `restart.w_fresh / w_elite / w_shared / w_best` | 0.6 / 0.2 / 0.1 / 0.1 | fresh roots found new basins |
| `sharing.mode` | `pull` | forced adoption of better elites collapsed diversity |
| `worker.checkpoint_seconds`, `telemetry.epoch_seconds` | 60 s, 60 s | at most a minute of search lost on a crash; per-minute move statistics |
| `campaign.on_worker_failure` | `stop` (the `large` profile uses `restart`) | fail fast rather than run silently degraded |

## 7. Results so far

On 9-minute, 2-workers-per-target head-to-head runs with the same seeds, every record re-verified
by the old verifier, xorsearch matched or dominated the old framework on every shared target
(FOX Mu4 125@7 vs 130@10; FOX Mu8 536@11 vs 540@12; InvMixColumns from NIST 119@5: 90@27 and
102@8 vs 107@6). Table and caveats: [docs/BENCHMARKS.md](docs/BENCHMARKS.md). These are short
runs, not optimality claims.
