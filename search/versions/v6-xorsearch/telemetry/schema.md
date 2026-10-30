# xorsearch telemetry formats — schema version 1

This file is the contract between the engine, the campaign runtime, the recorder
(`telemetry/recorder.py`) and the report (`telemetry/report.py`). Every record carries
`v` (the schema version). A change that renames or removes a field bumps `v`; adding an
optional field does not. Readers must ignore unknown fields and unknown event types.

## 1. Run directory layout

```
RUN/
  campaign.jsonl                 coordinator events (EventLog, worker = "coord")
  campaign-000001.jsonl ...      rotated coordinator segments (older first)
  workers/<worker>/
    events.jsonl                 worker events (Recorder)
    events-000001.jsonl ...      rotated segments; read segments ascending, then events.jsonl
    dossiers/<id>.json           one per improvement, written atomically (also kept, with
                                 `rejected: true`, for a candidate a verifier rejected)
    recorder.json                recorder sidecar (id sequences, cumulative counters,
                                 pending follow-ups); not an analysis input
  report/                        default output of `xorsearch report RUN`
```

Files are UTF-8. JSONL lines are compact JSON objects, one per line, written as whole
lines with `O_APPEND`; a crash can cut only the final line, which readers skip. Floats may
be `Infinity`/`NaN` (Python `json` dialect). Value sets are lists of ints: bit `i` of a
value is input `i`.

## 2. Event envelope (every line)

| field | type | meaning |
|---|---|---|
| `v` | int | schema version (1) |
| `t` | float | seconds since campaign start, monotonic (never jumps; continues across resume) |
| `utc` | str | wall time, `YYYY-MM-DDTHH:MM:SS.mmmZ` (for humans; may drift against `t`) |
| `worker` | str | worker id, or `"coord"` for the coordinator |
| `it` | int\|null | worker iteration when the event happened (null for coordinator events) |
| `ev` | str | event type (below) |

Ids are stable and sortable strings:

| id | format | example |
|---|---|---|
| improvement / dossier | `<worker>-NNNNNN` | `fox8-03-000017` |
| chain | `<worker>-cNNNN` | `fox8-03-c0004` |
| plateau | `<worker>-pNNNNNN` | `fox8-03-p000112` |

Scores are objects `{"gates": int, "depth": int}`.

## 3. Worker events

### `start` / `resume`
Process lifecycle. Flushed and fsynced.

| field | meaning |
|---|---|
| `env` | `python`, `implementation`, `executable`, `platform`, `machine`, `processor`, `cpu_count`, `affinity` (CPU list), `pid`, `argv`, `hostname`, `cwd`, `hash_seed` (`PYTHONHASHSEED`) |
| `settings_digest` | SHA-256 of the resolved settings (`Settings.digest()`) |
| `chain` | id of the chain the process starts on |
| worker-supplied | `seed` (RNG seed), `source_hash`, `target`, `objective`, `root`, `source`, anything else |

### `stop`
| field | meaning |
|---|---|
| `reason` | `normal`, `error`, `signal`, `budget`, ... |
| `best` | worker best score |
| `improvements`, `restarts` | counts since the worker started (cumulative over resumes) |
| `wall_s`, `cpu_s` | this process's elapsed and CPU seconds |
| `totals` | cumulative per-move counters `{move: {counter: value}}` (section 4) |

### `epoch`
Every `telemetry.epoch_seconds` (and once, `partial: true`, at close). Recorder fields:

| field | meaning |
|---|---|
| `epoch` | epoch number (1, 2, ...; continues across resume) |
| `dt` | seconds covered by this epoch |
| `its`, `it_rate` | iterations in the epoch, iterations per second |
| `cpu_s` | process CPU seconds in the epoch |
| `cpu_est` | true when per-move `cpu_s` were apportioned by work (no proposal carried `cpu_s`) |
| `moves` | `{move: counters}` for moves active in this epoch (section 4) |
| `combos` | list of `{move, components}` plus every counter of section 4 per sub-operation combination; every combination that improved, then the busiest up to `telemetry.combos_max` (empty with `telemetry.combo_counters = false`) |
| `chain_id` | current chain |
| `best` | worker best score (if any; frontier points do not change it) |
| `chain` | score of the last accepted proposal (the engine overrides it with the current chain score) |
| `partial` | true for the epoch `close()` writes for the unfinished interval |

Engine fields (merged in; recorder fields win on a clash), also in the final partial epoch
(the engine registers them with `Recorder.set_epoch_source`): `phase`, `work`,
`engine_chain`, `root`, `source`, `chain`, `chain_best`, `worker_best` (scores),
`frontier` (list of scores), `acceptance` (`{kind, best, neutral_p}`), `weights`
(`{move: probability}` in the current phase), `scheduler`
(`{move: {pulls, reward, work}}`), `plateau` (a `PlateauTracker.snapshot()`),
`diversity` (`metrics.diversity` of the archive members, null below 2), `archive`
(`{size, count, points, nn_mean, nn_min, best}`), `dist_chain_best`, `dist_root` (Jaccard
distance of the chain from its best and its root), `restart` (`{root_s, root_it, stall_s,
stall_it, stall_work}`), `restarts_by` (`{reason: {...}, source: {...}}` counts),
`counters` (engine counters: noop, invalid, infeasible, gate_limit, restarts,
restart_failed, verify_fail, records, frontier, improvements, chain_improvements, pulls,
pull_empty).

### `improve`
A new worker best or a new nondominated feasible point (`kind = frontier`). Flushed and
fsynced. Order: the dossier is written (unsynced, reserving the id), the record writer
verifies and saves the circuit, the dossier is rewritten with the verdict, then this line is
logged, so `verified` is known. A candidate the verifier rejects gets no `improve` line (its
dossier says `rejected: true`; a `verify_fail` event follows). Flat attribution columns so one
line answers "who, what, where, after how long":

| field | meaning |
|---|---|
| `id` | improvement id = dossier id |
| `kind` | `gates`, `depth` or `frontier` |
| `before`, `after` | scores |
| `move`, `components` | the move and its ordered sub-operations (`trace.components`) |
| `phase` | `burst`, `plateau` or `repair` at the proposal |
| `chain`, `root`, `root_source` | chain id, root id, how the chain started (`seed`, `fresh`, `elite`, `shared`, `resume`) |
| `parent` | previous improvement in this lineage (same chain), else the chain's parent (e.g. the donor improvement of a shared elite) |
| `donor` | donor worker when the lineage came through sharing |
| `plateau_age_it`, `plateau_age_s`, `plateau_distinct`, `plateau_drift` | plateau shape just before the move |
| `neutral_rate` | neutral accepts per proposal on that plateau |
| `it_since_prev`, `s_since_prev` | since the worker's previous improvement |
| `it_since_root`, `s_since_root` | since the chain started |
| `cpu_s_since_prev`, `cpu_s_since_root` | CPU seconds spent in moves since then (cumulative move CPU, continuous across resumes) |
| `symdiff` | values removed + added versus the state before |
| `verified` | verification result (`verification.ok`; null when no verifier ran) |
| `record` | record file written for it (`verification.record`), run-relative |
| `deterministic` | false when a wall-clock budget shaped the proposal |
| `replayable` | `exact`, `move_state` or `no` (dossier `replay`, section 6) |
| `dossier` | path relative to the worker directory |

### `plateau`
A plateau closed (fields of `PlateauTracker.close()` plus ids). Plateaus shorter than
`engine.plateau_event_min` proposals are not logged. A plateau closed by an improvement is
logged right after that improvement's `improve` line and names it.

| field | meaning |
|---|---|
| `id` | plateau id (assigned by the recorder) |
| `chain` | chain id |
| `index` | per-worker plateau number from the tracker |
| `level` | score level held, `[gates, depth]` |
| `entry_it`, `entry_t` | when the plateau started |
| `age_it`, `age_s` | duration |
| `proposals`, `accepted`, `neutral_accepts`, `neutral_rate` | activity on the plateau |
| `distinct_states`, `distinct_exact` | distinct equal-score states visited; exact up to `telemetry.plateau.distinct_cap`, HyperLogLog estimate beyond |
| `visits`, `revisit_ratio` | accepted moves that reported a state; visits per distinct state |
| `drift`, `max_drift` | Jaccard distance from the entry state at exit; largest sampled |
| `exit` | `improve` (a new chain best), `restart`, ... |
| `improvement` | the worker improvement id when the chain best that closed it was one (absent for a chain best that is not a worker best) |

### `restart`
| field | meaning |
|---|---|
| `reason` | `stall_seconds`, `stall_work`, `root_seconds`, `manual`, ... |
| `source` | `fresh` (new randomized root), `elite` (worker archive), `shared` (campaign pool) |
| `chain` | the new chain id (assigned by the recorder unless given) |
| `root` | `{id, constructor, seed, hash, gates, depth}` of the new root |
| `parent` | improvement id the new chain descends from (elite/shared), if any |
| `donor`, `record` | donor worker and record id for `shared` |
| `start` | score of the new chain |
| `engine_chain` | the engine's chain sequence number |
| `prev` | previous chain: `chain`, `age_it`, `age_s` (added by the recorder) plus engine fields `engine_chain`, `root`, `source`, `gates`, `depth` (where it ended), `best` (score), `improvements` (chain bests), `root_s`, `root_it`, `stall_s`, `stall_it`, `stall_work` |

A `shared` root carries `improvement`: the donor's dossier id when the pooled record came from
an improvement (record `ref`), which becomes the new chain's lineage `parent`, so lineage
edges cross workers.

### `pull` / `pool_sample`
A restart drew a pooled elite: the engine logs `pull`, the worker's pool `pool_sample` (with
`pool_version`, the pool file version it read).

| field | meaning |
|---|---|
| `record` | record id (path) pulled |
| `point` | score of the record (an object) |
| `dag` | DAG hash |
| `donor` | donor worker |

### `record`
A distinct DAG saved at an existing point: `point` (score), `dag`, `record`,
`distinct_at_point`, `move`.

### `followup`
`telemetry.followup_iterations` after an improvement (each horizon), or at close with
`complete: false` (re-emitted complete after a resume; readers keep the last per
`(id, horizon)`).

| field | meaning |
|---|---|
| `id`, `horizon` | the improvement and the horizon (iterations) |
| `complete` | horizon reached |
| `it_since`, `s_since` | elapsed since the improvement |
| `proposals`, `valid`, `accepted`, `neutral`, `uphill`, `improved_chain`, `improved_worker` | counter differences since the improvement (all moves) |
| `cpu_s` | CPU seconds spent in moves since |
| `later`, `latest` | number of worker improvements since, and the latest id |
| `next`, `next_it_since`, `next_s_since` | the first later worker improvement (null: none yet) and how long it took |
| `next_chain_best_it_since` | iterations to the first later chain best, i.e. how long the plateau this improvement opened lasted (null: still open) |
| `restarts`, `restart_it_since` | restarts since, and iterations to the first (null: none) |
| `chain`, `chain_changed` | chain score (last accepted proposal); true when the chain has been restarted since |
| `best`, `best_gain` | worker best now; `{gates, depth}` gained since (after minus now; not for frontier points) |
| `plateau_it` | iterations since the last chain improvement (plateau length so far) |

### `phase`
`from`, `to`, `reason`, optional `budget`. Buffered.

### `warn`
`kind`, `message` and context. The recorder emits `kind = "move_dead"` (`move`, `epochs`)
when a move proposed for `telemetry.warn_dead_epochs` epochs without one valid proposal.

### Other engine events
| event | fields |
|---|---|
| `move` | `move`, `status` (`inapplicable` / `off`), `reason`: moves left out at start |
| `seed_rejected` | `reason`, `cap`: the seed circuit is unrealizable at the search cap (a root is built instead) |
| `root_failed` | `constructor`, `seed`, `reason` |
| `restart_failed` | `reason`, `tried` (sources in order): nothing usable; the chain gets another stall period |
| `adopt_best` | `point`, `donor`, `record`: a pulled elite became the worker best without a dossier (not this worker's discovery) |
| `verify_fail` | `kind`, `id` (rejected dossier, or null for a sampled record), `point`, `result` (the verifier's summary); the chain restarts from the last verified best |

## 4. Per-move counters

In `epoch.moves`, `epoch.combos`, `stop.totals`, sidecar `totals` (as a list in this order).
The recorder counts per (move, combination of `components`); per-move counters are their
sums.

| counter | meaning |
|---|---|
| `proposals` | `propose()` calls |
| `valid` | calls that returned a proposal (`rec.valid`, default true) |
| `accepted` | accepted proposals (includes neutral) |
| `neutral` | accepted at equal score |
| `uphill` | accepted at a worse score |
| `improved_chain` | new chain best |
| `improved_worker` | new worker best (each has an `improve` event) |
| `work` | work units |
| `cpu_s` | CPU seconds (measured, or apportioned when `cpu_est`) |

## 5. Coordinator events (`campaign.jsonl`, `worker = "coord"`)

### `frontier`
The global frontier changed. `point` (score), `worker` is `"coord"`, attribution in
`by` (worker id), `group`, `ref` (the record's engine candidate ref), `improvement` (the
worker improvement id = dossier id: the `ref` when it has the form `<worker>-NNNNNN`, null for
a sampled DAG `<worker>:it<N>` or a seed `<worker>:seed`), `move`, `record`, `dag`, `kind`
(`gates`/`depth`/`frontier`/`seed`), `found_t` (campaign time the worker saved it), `removed`
(points it dominates), `frontier` (all points after the change, list of scores).

### `fleet_diversity`
Snapshot at fixed intervals: `metrics.diversity()` of the workers' current chains
(`n`, `distinct`, `modal_fraction`, `mean`, `min`, `max`, `pairs`, `sampled`, `basins`),
plus `scope` (`chains`, `bests` or `pool`), `point` (when restricted to one frontier
point), `workers` (ids in the order measured), and an `alarm` flag when it collapses.

### `pool`
Campaign pool change: `point`, `size`, `distinct`, `added` (record ids), `evicted`,
`donor` (worker).

Coordinator lifecycle uses `start` / `resume` / `stop` with the same fields as workers.

## 6. Dossier (`dossiers/<id>.json`)

Written by `Recorder.improvement(dossier, verify=...)`. Keys set by the recorder are marked
R; the engine (`engine/dossier.py`) supplies the rest (E). With `telemetry.dossier_detail =
"standard"` the `values_before` list is dropped (it equals `values_after - added + removed`);
with `"minimal"` all value lists and gates are dropped and `symdiff` becomes counts.

What each part answers: *what found it* (`move`, `family`, `trace`, `phase`,
`state_before.weights`), *from where* (`chain`, `lineage`, distances in `state_before`),
*before* (`state_before`), *during* (`ring`, `ring_summary`), *after* (`shape_after`, then the
`followup` events at `followups_at`), *is it real* (`verification`), *can it be re-run*
(`replay`).

```jsonc
{
  "v": 1,                                   // R
  "id": "w03-000017", "worker": "w03",       // R
  "t": 5321.42, "utc": "2026-10-28T12:01:02.003Z", // R
  "it": 182733,                              // E (default R: last proposal)
  "kind": "gates",                           // E: gates | depth | frontier
  "before": {"gates": 129, "depth": 8},      // E: chain score before the proposal
  "after":  {"gates": 128, "depth": 8},      // E
  "worker_best_before": {"gates": 129, "depth": 8}, // E
  "move": "lns.rebuild", "family": "lns",    // E (restart improvements: "restart.<source>")
  "phase": "plateau",                        // E
  "work": 412, "proposal_s": 0.0031,         // E: work units; seconds to score the proposal
  "deterministic": true,                     // E: false when a wall clock shaped it
  "trace": {                                 // E: Proposal.trace, lists capped (R) at
    "components": ["destroy.cone", "inject", "bank", "rebuild.greedy", "peel"],
    "params": {"op": "cone", "k": 9},        //   telemetry.trace_values_max with <key>_n
    "removed": [/*ints*/], "added": [/*ints*/], "removed_n": 9
  },
  "chain": {                                 // R from begin/restart, E extends
    "id": "w03-c0004", "source": "fresh", "parent": null, "donor": null,
    "root": {"id": "naive#1958", "constructor": "naive", "seed": 1958, "gates": 140,
             "depth": 9, "build_s": 0.4},
    "engine_chain": 4, "start_it": 120000, "start_t": 4100.2, "start_cpu": 4021.7
  },
  "lineage": {"parent": "w03-000016", "chain_origin": "fresh", "donor": null}, // R defaults
  "timing": {"it_since_prev": 3311, "s_since_prev": 81.2, "cpu_s_since_prev": 80.1, // R
             "it_since_root": 62733, "s_since_root": 1221.2, "cpu_s_since_root": 1200.4},
  "state_before": {                          // E: the search state just before the move
    "phase": "plateau",
    "plateau": { /* PlateauTracker.snapshot(): age_it, age_s, distinct_states, drift, ... */ },
    "neutral_rate": 0.31,
    "acceptance": {"kind": "threshold", "best": 129, "neutral_p": 1.0},
    "weights": {"walk.remove1": 0.68, "lns.rebuild": 0.15},   // selection probabilities
    "cur": {"gates": 129, "depth": 8}, "chain_best": {...}, "worker_best": {...},
    "dist_chain_best": 0.0, "dist_root": 0.41, "dist_worker_best": 0.12,
    "dist_elites": {"n": 12, "min": 0.08, "mean": 0.3},
    "archive": {"size": 12, "count": 12, "points": 3, "nn_mean": 0.1, "nn_min": 0.02},
    "chain_age": {"root_s": 1221.2, "root_it": 62733, "stall_s": 81.2, "stall_it": 3311,
                  "stall_work": 120000},
    "chain_improvements": 7
  },
  "shape_after": { /* metrics.shape_from_gates(...) */ },  // E
  "values_before": [/*ints*/],               // E (dropped unless detail = full)
  "values_after":  [/*ints*/],               // E
  "gates_after": [[0, 1], [2, 8]], "outputs": [9, 12],     // E (ValueSet.gates())
  "symdiff": {"removed": [/*ints*/], "added": [/*ints*/]},  // R if both value lists given
  "ring": [{"it": 182732, "move": "walk.remove1", "phase": "plateau", "valid": true,
            "accepted": true, "neutral": true, "d_gates": 0, "d_depth": 0,
            "gates": 129, "depth": 8, "components": ["remove1", "repair"]}], // R
  "ring_summary": {"proposals": 256, "first_it": 182478, "last_it": 182733, "valid": 250,
                   "accepted": 80, "neutral": 75, "uphill": 2, "gates_min": 128,
                   "gates_max": 130, "by_move": {"walk.remove1": {"proposals": 170,
                   "accepted": 70}}},       // R
  "rng": {"seed": 12345, "engine_seed": 7}, // E: per-proposal seed, engine seed
  "replay": {                                // E: see below
    "seed": 12345, "engine_seed": 7, "cap": 10, "work_limit": 1000000, "move_calls": 5210,
    "replayable": "move_state", "reasons": ["move_state"],
    "move_state_sha256": "...", "move_state": {"pool": [...], "hot": [...]},
    "recipe": "..."
  },
  "verification": {"ok": true, "saved": true, "equivalent": true, "gate_count": 128,
                   "depth": 8, "dag_sha256": "...", "circuit_sha256": "...",
                   "record": "workers/w03/records/g128-d8-....json",
                   "verifier": "core.circuit.verify (campaign record writer)"}, // R: verify()
  "rejected": true,                          // R: only when the verifier rejected it
  "followups_at": [182833, 183733, 192733]   // R: iterations of the followup events
}
```

`verification` is the return value of the engine's `on_record` callbacks (the campaign's
`RecordWriter.save`), null when no verifier ran and also left null when the process died
while verifying (the dossier is first written before verification). `ok` false or
`equivalent` false rejects the candidate. The record written for an improvement carries
the dossier id as `ref`.

### Replay

With `engine.replay_seeds` every proposal runs on `random.Random(seed)` for a fresh 63-bit
seed drawn from the engine RNG, so one proposal is a function of `values_before` (the state
rebuilt from them as the engine builds states: sorted values, trimmed, at `replay.cap`), the
seed, the move's knobs (frozen settings), `replay.work_limit` and the move's own memory.
`engine.replay.replay_dossier(dossier, target, objective, settings)` re-runs it and compares
with `values_after`.

| `replayable` | meaning |
|---|---|
| `exact` | a work-bounded move that is stateless, or made its first proposal (`move_calls` 0: its memory was the freshly constructed one): the recorded inputs determine the proposal |
| `move_state` | the move keeps memory between proposals (LNS pool, hot list and peel cache; depth3 partition). The snapshot in `move_state` (with `engine.replay_move_state = full`; only its SHA-256 with `digest`; neither with `off`) is taken *after* the proposal, because snapshotting before every proposal costs more than the proposals. `replay_dossier` undoes what the proposal itself added (a move's `replay_state(snapshot, trace)` hook, else `engine.replay.PRE_PROPOSAL`: for `lns.rebuild` the peel cache when the trace shows a peel, and its `pending` change) |
| `no` | a wall clock shaped it (structural moves, `budget.mode = time`), no seed (`engine.replay_seeds = false`), or it was made by a restart rather than a proposal |

`reasons` lists the causes (`move_state`, `wall_clock`, `no_seed`, `not_a_proposal`);
`move_calls` is the number of earlier proposals by the move. Measured: every one of 24
dossiers from two 45-60 s fox_mu4 runs replayed exactly (walk, LNS with and without peel,
depth repair, and the structural ones, whose wall clock did not bind), and
`tests/test_engine_realstack.py` replays every non-`no` dossier of a real-move run.

## 7. One-line queries

```sh
# which move / sub-operations found each improvement, in which phase, after how long flat
jq -c 'select(.ev=="improve") | [.worker,.id,.move,(.components|join("+")),.phase,.plateau_age_s]' RUN/workers/*/events*.jsonl
# improvements from fresh roots and their time since the root
jq -c 'select(.ev=="improve" and .root_source=="fresh") | [.id,.root,.s_since_root]' RUN/workers/*/events*.jsonl
# lineage edges
jq -r 'select(.ev=="improve") | "\(.parent) -> \(.id)"' RUN/workers/*/events*.jsonl
# per-move improvements per CPU-hour of one worker
jq -s '[.[]|select(.ev=="epoch")|.moves|to_entries[]]|group_by(.key)|map({move:.[0].key,iw:(map(.value.improved_worker)|add),cpu_h:((map(.value.cpu_s)|add)/3600)})' RUN/workers/w03/events*.jsonl
# the state before, during and after one improvement
jq '{before:.state_before, during:.ring_summary, last:.ring[-5:], after:.shape_after, verified:.verification.ok, replay:.replay.replayable}' RUN/workers/w03/dossiers/w03-000017.json
# did it lead anywhere: next improvement, plateau length after it, restart, best gain
jq -c 'select(.ev=="followup" and .complete) | [.id,.horizon,.next,.next_it_since,.next_chain_best_it_since,.restart_it_since,.best_gain.gates]' RUN/workers/*/events*.jsonl
# what happened 1000 iterations later
jq -c 'select(.ev=="followup" and .id=="w03-000017")' RUN/workers/w03/events*.jsonl
```

`xorsearch report RUN` writes the same joins as CSV tables (`improvements.csv`,
`epochs.csv`, `moves.csv`, `combos.csv`, `plateaus.csv`, `restarts.csv`,
`restart_sources.csv`, `frontier.csv`, `fleet_diversity.csv`) and `report.html`.
`improvements.csv` joins each improvement with its dossier (move weight, distances, ring
summary), the plateau it opened and its follow-ups (`fu<horizon>_*`).
