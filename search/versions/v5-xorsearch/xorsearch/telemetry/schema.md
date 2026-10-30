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
    dossiers/<id>.json           one per improvement, written atomically
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
| `combos` | list of `{move, components, proposals, accepted, improved_chain, improved_worker}` per sub-operation combination; every combination that improved, then the busiest up to `telemetry.combos_max` |
| `chain_id` | current chain |
| `best` | worker best score (if any) |
| `chain` | score of the last accepted proposal (engine may override) |

Engine fields (merged in; recorder fields win on a clash): `phase`, `acceptance`
(`{kind, temperature, threshold, ...}`), `weights` (`{move: weight}` of the scheduler),
`plateau` (a `PlateauTracker.snapshot()`), `diversity` (`metrics.diversity` of the
archive), `archive` (`{size, distinct}`), `dist_chain_best`, `dist_root`, anything else.

### `improve`
A new worker best (any objective point that becomes nondominated). Flushed and fsynced;
the dossier is written first. Flat attribution columns so one line answers "who, what,
where, after how long":

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
| `symdiff` | values removed + added versus the state before |
| `verified` | verification result (`verification.ok`) |
| `deterministic` | false when a wall-clock budget shaped the proposal |
| `dossier` | path relative to the worker directory |

### `plateau`
A plateau closed (fields of `PlateauTracker.close()` plus ids).

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
| `exit` | `improve`, `restart`, `repair`, `stop`, ... |
| `improvement` | the improvement id when `exit = improve` |

### `restart`
| field | meaning |
|---|---|
| `reason` | `stall_seconds`, `stall_work`, `root_seconds`, `manual`, ... |
| `source` | `fresh` (new randomized root), `elite` (worker archive), `shared` (campaign pool) |
| `chain` | the new chain id (assigned by the recorder unless given) |
| `root` | `{id, constructor, seed, hash, gates, depth}` of the new root |
| `parent` | improvement id the new chain descends from (elite/shared), if any |
| `donor`, `record` | donor worker and record id for `shared` |
| `prev` | previous chain: `chain`, `age_it`, `age_s` (added by the recorder) plus engine fields such as `best`, `gates`, `depth`, `improvements` |

### `pull` / `publish`
| field | meaning |
|---|---|
| `records` / `record` | record id(s) pulled / published |
| `point` | score of the record |
| `dag` | DAG hash |
| `donor` | donor worker (pull) |
| `improvement` | improvement id behind a published record |

### `record`
A distinct DAG saved at an existing point: `point`, `dag`, `record`, `distinct_at_point`.

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
| `later`, `latest` | number of worker improvements since, and the latest id |
| `restarts` | restarts since |
| `chain`, `best` | chain score (last accepted proposal) and worker best now |
| `plateau_it` | iterations since the last chain improvement (plateau length so far) |

### `phase`
`from`, `to`, `reason`, optional `budget`. Buffered.

### `warn`
`kind`, `message` and context. The recorder emits `kind = "move_dead"` (`move`, `epochs`)
when a move proposed for `telemetry.warn_dead_epochs` epochs without one valid proposal.

## 4. Per-move counters

In `epoch.moves`, `stop.totals`, sidecar `totals` (as a list in this order):

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
`by` (worker id), `improvement` (worker improvement id), `record`, `dag`, `kind`
(`gates`/`depth`/`frontier`), `removed` (points it dominates), `frontier` (all points
after the change, list of scores).

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

Written by `Recorder.improvement(dossier)`. Keys set by the recorder are marked R; the
engine supplies the rest (E). With `telemetry.dossier_detail = "standard"` the
`values_before` list is dropped (it equals `values_after - added + removed`); with
`"minimal"` all value lists and gates are dropped and `symdiff` becomes counts.

```jsonc
{
  "v": 1,                                   // R
  "id": "w03-000017", "worker": "w03",       // R
  "t": 5321.42, "utc": "2026-10-28T12:01:02.003Z", // R
  "it": 182733,                              // E (default R: last proposal)
  "kind": "gates",                           // E: gates | depth | frontier
  "before": {"gates": 129, "depth": 8},      // E
  "after":  {"gates": 128, "depth": 8},      // E
  "move": "lns.cone",                        // E
  "phase": "plateau",                        // E
  "deterministic": true,                     // E
  "trace": {                                 // E: Proposal.trace, lists capped (R) at
    "components": ["destroy.cone", "inject", "rebuild.deadline", "peel"],
    "params": {"k": 9, "cap": 8},            //   telemetry.trace_values_max with <key>_n
    "removed": [/*ints*/], "added": [/*ints*/], "removed_n": 9
  },
  "chain": {                                 // R from begin/restart, E may extend
    "id": "w03-c0004", "source": "fresh", "parent": null,
    "root": {"id": "naive#1958", "constructor": "naive", "seed": 1958, "hash": "..."},
    "start_it": 120000, "start_t": 4100.2
  },
  "lineage": {"parent": "w03-000016", "chain_origin": "fresh", "donor": null}, // R defaults
  "timing": {"it_since_prev": 3311, "s_since_prev": 81.2,   // R defaults
             "it_since_root": 62733, "s_since_root": 1221.2, "cpu_s_since_root": 1200.4},
  "state_before": {                          // E: metrics before the move
    "plateau": { /* PlateauTracker.snapshot() */ },
    "neutral_rate": 0.31, "temperature": 0.0, "phase": "plateau",
    "weights": {"walk.remove1": 4.0, "lns.cone": 2.0},
    "dist_chain_best": 0.0, "dist_root": 0.41,
    "dist_elites": {"n": 12, "min": 0.08, "mean": 0.3}
  },
  "shape_after": { /* metrics.shape_from_gates(...) */ },  // E
  "values_before": [/*ints*/],               // E (dropped unless detail = full)
  "values_after":  [/*ints*/],               // E
  "gates_after": [[0, 1], [2, 8]], "outputs": [9, 12],     // E (ValueSet.gates())
  "symdiff": {"removed": [/*ints*/], "added": [/*ints*/]},  // R if both value lists given
  "ring": [{"it": 182732, "move": "walk.remove1", "d_gates": 0, "d_depth": 0,
            "accepted": true, "neutral": true, "components": ["remove1", "repair"]}], // R
  "rng": {"seed": 12345, "state": "..."},    // E: RNG state at proposal start (replay)
  "verification": {"ok": true, "dag_sha256": "..."},       // E
  "followups_at": [182833, 183733, 192733]   // R: iterations of the followup events
}
```

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
jq '{before:.state_before, during:.ring[-20:], after:.shape_after}' RUN/workers/w03/dossiers/w03-000017.json
# what happened 1000 iterations later
jq -c 'select(.ev=="followup" and .id=="w03-000017")' RUN/workers/w03/events*.jsonl
```

`xorsearch report RUN` writes the same joins as CSV tables (`improvements.csv`,
`epochs.csv`, `moves.csv`, `combos.csv`, `plateaus.csv`, `restarts.csv`, `frontier.csv`,
`fleet_diversity.csv`) and `report.html`.
