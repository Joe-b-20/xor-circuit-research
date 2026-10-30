# xorsearch user guide

`xorsearch` searches for the smallest (then shallowest) XOR circuit of a GF(2) linear map, from a
few inputs up to 64+ inputs and a thousand gates. Each worker runs one search chain. A coordinator
supervises the workers, re-verifies everything they find, keeps the global frontier and shares
distinct elite circuits between them.

- **This file**: how to run, configure, monitor and extend searches.
- **[DESIGN.md](DESIGN.md)**: the method and the contract every module follows.
- **[docs/evidence/](docs/evidence/)**: the measurements behind the defaults.

Python 3.11 or newer, standard library only. Run every command from the repository root (the
directory that contains `xorsearch/`).

---

## 1. Quick start

```bash
# What targets exist?
python -m xorsearch targets list
python -m xorsearch targets show fox_mu4

# A one-minute experiment: one worker in this process, no coordinator.
python -m xorsearch quick fox_mu4 --seconds 60 --seed 1

# A real campaign: check the plan first (this starts nothing) ...
python -m xorsearch plan xorsearch/examples/fox_mu4.toml
# ... then freeze it into a run directory and start it.
python -m xorsearch run xorsearch/examples/fox_mu4.toml --out runs/fox4 --seconds 2h

# From another terminal:
python -m xorsearch status runs/fox4      # frontier, pool, diversity, per-worker table
python -m xorsearch stop runs/fox4        # checkpoint and stop
python -m xorsearch resume runs/fox4      # continue from the checkpoints
python -m xorsearch report runs/fox4      # CSV tables + report.html
python -m xorsearch verify runs/fox4      # re-verify every record independently
```

`Ctrl-C` in the terminal running `run` or `resume` also stops cleanly: every worker writes a final
checkpoint first.

## 2. Commands

| Command | What it does |
|---|---|
| `run CAMPAIGN.toml --out DIR [--seconds N] [--set k=v ...]` | Resolve the campaign file, freeze it into the new directory `DIR` (it must be empty or missing), then run the coordinator from the frozen copy. `--seconds` accepts `3600`, `90m` or `2h30m`. Without it, the `[campaign] duration` applies; without either, the run lasts until stopped. |
| `resume DIR [--seconds N]` | Continue a stopped or crashed campaign. Workers with a checkpoint resume their exact chain; workers without one start fresh. The campaign clock (`t` in every event) carries on from the previous session. |
| `stop DIR [--reason R] [--wait S]` | Write a `STOP` request addressed to the live coordinator. `--wait` blocks until it has exited. |
| `status DIR [--json]` | Human summary of the run: phase, global frontier with the worker that found each point, pool sizes, fleet diversity and one row per worker. `--json` prints the raw `status.json`. |
| `plan CAMPAIGN.toml [--set ...] [--json] [--settings]` | Resolve and print the plan (targets, workers, caps, seeds, RNG seeds, settings hashes) without starting anything. `--settings` lists every non-default setting of every worker together with its origin. |
| `report DIR` | Build CSV tables and a self-contained `report.html` (`telemetry.report.build_report`). |
| `verify DIR` | Check the frozen source, plan and snapshots. Then re-verify every record: file hash, binding to its worker, equivalence, depth cap, gate limit, and the verification sidecar and NCFF export against fresh ones. Exits with 1 on any failure. |
| `verify CIRCUIT.json --target T [--cap N]` | Verify one circuit file against a target. |
| `config show [--profile P ...] [--set ...] [--non-default] [--prefix X]` | Print the resolved settings as `key = value  # origin`. |
| `config explain KEY_OR_PREFIX` | Show a knob's documentation, type, range, choices and default, or list every knob under a prefix (`sharing`, `moves.walk`). |
| `targets list`, `targets show NAME` | The target catalog, and one target's size, matrix hash and verified seeds. |
| `quick TARGET [--seconds N] [--seed S] [--objective O] [--depth-cap N] [--gate-limit N] [--seeds ...] [--set ...] [--out DIR]` | Run one worker in this process. There is no coordinator, no sharing and no source freeze: it runs the live code. The output is a small run directory (by default `xorsearch-runs/quick-TARGET-TIME`) that `status`, `report` and `verify` all understand. |

Exit codes: 0 means success; 1 means a reported error (the message starts with `error:`) or a
failed verification; 2 means a usage error.

## 3. Campaign files

A campaign file is TOML with three kinds of tables:

- **`[campaign]`**: the run's identity and duration.
- **`[set]`**: campaign-wide setting overrides.
- **`[[workers]]`**: one table per worker group.

All relative paths in the file (targets, seeds, profile files) are resolved relative to the
campaign file itself.

```toml
[campaign]
name = "fox_mu4"                 # default: the file name
description = "capped and uncapped workers"
seed = 20261024                  # worker i (counted across all groups) gets seed + i * 1000003
duration = "8h"                  # seconds or "90m"/"2h30m"; omit = until stopped; --seconds overrides
profiles = ["default"]           # built-in profile names or TOML paths, applied in order
sharing = "pull"                 # shorthand for sharing.mode; or a table:
# [campaign.sharing]
# mode = "pull"
# scope = "group"
# backend = "xorsearch"          # advanced: "module:Class" (see section 10)

[set]                            # any knob, campaign-wide (dotted keys or nested tables)
"worker.checkpoint_seconds" = 120.0
"moves.walk.hub.weight" = 3.0

[[workers]]
name = "cap7"                    # group name; worker ids are <name>-00, <name>-01, ...
target = "fox_mu4"               # catalog name, or a path to a target JSON file
count = 4                        # workers in this group (default 1)
objective = "gates"              # "gates" (gates, then depth) or "depth_then_gates"
depth_cap = 7                    # real cap for recorded circuits; a list cycles over the
                                 # group's workers: [7, 8, "none"]
gate_limit = 130                 # record only circuits with at most this many gates (optional)
seeds = ["target"]               # cycled over the workers; each entry is one of:
                                 #   "target"          the target's built-in seed circuits
                                 #   "root"            the engine's default fresh root
                                 #   "root:<name>"     a named constructor (e.g. root:paar)
                                 #   "path/to.json"    a circuit JSON file (verified at plan time)
profiles = ["large"]             # extra profiles for this group only
per_worker = [{}, { "restart.stall_seconds" = 1200.0 }]   # cycles over the group's workers
[workers.set]                    # overrides for this group only
"sharing.sample_points" = 2
```

More examples are in [`examples/`](examples/):

- `fox_mu4.toml`: one target, capped and uncapped groups.
- `three_targets.toml`: several targets, with campaign, group and per-worker overrides.
- `sharing_ab.toml`: an A/B test of the `pull` and `push` sharing modes.

`objective`, `depth_cap` and `gate_limit` are shorthands for the knobs `objective.kind`,
`objective.depth_cap` and `objective.gate_limit`. They are applied as the group's layer, so the
frozen settings show them with origin `group:<name>`. A `[workers.set]` or `--set` value for the
same knob wins over them. The real cap is what records must meet. While searching, the engine may
go `objective.soft_depth_slack` deeper (core/objective.py).

`xorsearch plan` rejects mistakes before anything starts. It catches unknown fields and knobs (and
suggests the closest name), wrong types and out-of-range values, unknown targets, seeds that do not
compute their target, duplicate group names, and more workers than available CPUs (unless
`campaign.allow_oversubscription = true`). It prints notes for legal but surprising choices, such
as a seed that is deeper than its worker's real cap. The engine then repairs depth before it
records anything.

Two targets that resolve to the same matrix share one frontier and one pool.

## 4. Configuration: change any knob without touching code

Every tunable value is a *knob*. A knob is declared next to the code that reads it (DESIGN.md
§4.1) and has a type, a range and a doc string. Values are layered from lowest to highest
priority, and each value remembers the layer that set it:

| Layer (origin label) | Where |
|---|---|
| `default` | the knob declaration in the code |
| `profile:<name>` | `[campaign] profiles`, then the group's `profiles` (built-ins live in `xorsearch/config/profiles/`) |
| `campaign` | `[campaign] sharing` / `[campaign.sharing]` |
| `campaign:set` | the top-level `[set]` table |
| `group:<name>` | `[workers.set]` |
| `worker:<id>` | `per_worker` |
| `cli` | `--set key=value` on `run`, `plan`, `quick` and `config show` |

`--set` values use TOML syntax: `--set sharing.mode=push`, `--set worker.checkpoint_seconds=30`,
`--set moves.walk.hub.weight=0`. A bare word is read as a string.

To work with knobs:

- **See the effective values**: `python -m xorsearch config show --non-default --profile large`.
- **See the values of one planned worker**: `python -m xorsearch plan FILE --settings`.
- **Learn what a knob does**: `python -m xorsearch config explain sharing.mode`, or
  `config explain moves` for a whole subtree.
- **Change a default for every campaign**: edit `config/profiles/default.toml`.
- **Make a reusable bundle of values**: write a profile TOML file and list it in `profiles`.

`campaign.*` knobs and `sharing.pool_per_point` are read by the coordinator. They can only be set
campaign-wide (in profiles, `[campaign]`, `[set]` or `--set`). Setting them in `[workers.set]` is
an error.

Built-in profiles:

| Profile | Purpose |
|---|---|
| `default` | Empty. Change defaults for every campaign here. |
| `quick` | Short experiments: status, pool and diversity panels update every second or so. |
| `large` | 64+ inputs and long campaigns: fewer, larger writes. |
| `depth` | Depth-first objectives and tight caps. |

The resolved settings of every worker, with the origin of every value, are frozen into
`settings/<worker>.json`. Each run therefore records exactly what it ran with.

## 5. Run directory layout

```
DIR/
  plan.json              resolved plan: targets, seeds, workers (cap, objective, seed, rng seed, settings hash)
  freeze.json            hashes: plan, every snapshot below, source manifest + archive, git HEAD/dirty
  campaign.toml          the campaign file as given
  environment.json       python, OS, CPU model, logical/available CPUs, thread env, command line
  settings/<id>.json     resolved settings + origins per worker; settings/campaign.json for the coordinator
  targets/<key>.json     target snapshot (rows + matrix hash)
  seeds/<key>/<sha>.json seed circuits as verified at plan time
  source/xorsearch/...   frozen source copy: run and resume execute this, never the live tree
  source.tar.gz          byte-reproducible tarball of the same files
  campaign.lock          owner identity (pid, host, kernel start tick, token) while running
  STOP                   last stop request (addressed to one coordinator token)
  status.json            coordinator summary: phase, workers, frontier, pool, diversity, errors
  campaign.jsonl         coordinator events (section 6)
  pool/<key>.json        campaign pool: distinct DAGs per frontier point, written atomically
  sessions/<token>.json  one per run/resume: start/end, worker pids/commands, stop reason, exit codes
  error.json             coordinator failure of the latest session (older ones are moved to errors/<token>/)
  workers/<id>/
    status.json          phase, steps, steps/s, best, frontier, skipped-record counts, pool stats
    chain.json           best and current-chain value sets (input to fleet diversity)
    checkpoint.json      engine state in an envelope bound to run, worker, settings and source hashes
    records.jsonl        index of saved records (one line each) plus improvement link lines
    records/g<G>-d<D>-<dag>.json               circuit JSON (old xor-circuit-lab format) + metadata
    records/g<G>-d<D>-<dag>.verification.json independent verifier output
    records/g<G>-d<D>-<dag>.ncff               NIST circuit file format
    rejected.jsonl       circuits the verifier rejected (should never happen)
    launch.log           stdout/stderr of the process (tracebacks of import failures land here)
    error.json           the worker's failure, with traceback
    events.jsonl, dossiers/, ...   telemetry written by the Recorder (DESIGN.md §4.5)
```

Every JSON file is written atomically: a temporary file, fsync, then a rename. A crash at any
moment leaves either the old or the new version of a file. JSONL files are append-only and repair
a torn last line on the next append. A record's circuit JSON is written after its sidecars and
serves as the commit marker. A record that was committed but never indexed is re-indexed when the
worker restarts.

## 6. Logs and how to read them

All event lines use the telemetry envelope (`telemetry/schema.md`): `v`, `t` (seconds since
campaign start; it continues across resumes), `utc`, `worker` (`"coord"` for the coordinator),
`it` and `ev`. Scores are `{"gates": G, "depth": D}`.

**`campaign.jsonl`** (coordinator):

| `ev` | Meaning and key fields |
|---|---|
| `start` / `resume` / `stop` | Session lifecycle. `session`, `seconds`, `workers`, `run_id`, `source_hash`, `settings_digest`, `env`; on `stop`: `reason`, `returncodes`, `forced` (workers that had to be terminated), `error` |
| `worker_start` / `worker_exit` | `worker_id`, `pid`, `cpu`, `returncode`, `error` |
| `frontier` | A new nondominated point. Fields: `target`, `point`, `by` (worker), `group`, `kind` (`gates`/`depth`/`frontier`/`seed`), `improvement` (dossier id), `ref` (engine candidate id), `move`, `record`, `dag`, `found_t`, `removed` (points it dominates), `frontier` (all points after it) |
| `pool` | One frontier point of a target's pool changed. `point`, `size`, `distinct`, `added` (record paths), `donor` (workers), `evicted` (points now dominated) |
| `fleet_diversity` | Per target and `scope` (`bests`: each worker's best record; `chains`: each worker's current chain): `telemetry.metrics.diversity` fields (`n`, `distinct`, `modal_fraction`, `mean`/`min`/`max` pairwise Jaccard distance, `basins`, ...), `workers`, `alarm` |
| `collapse_alarm` / `collapse_cleared` | The mean best-to-best distance crossed `campaign.collapse_distance`. This means the fleet has piled onto too few DAGs. |
| `record_rejected` | A worker's record (`by`, `record`) failed independent re-verification (`reason`). It is excluded from the frontier and the pool. |

Records and dossiers are joined by the engine's candidate `ref`. The record is saved first, because
the engine verifies a candidate before it counts it. A
`{"link": "improvement", "ref", "improvement", "record"}` line in `records.jsonl` then adds the
dossier id when the engine publishes the improvement. Each `frontier` event carries both `ref` and
`improvement`.

**Worker telemetry** in `workers/<id>/` is written by the telemetry Recorder (DESIGN.md §4.5).
`events.jsonl` holds `start`/`resume`/`stop`, `epoch` (per-move counters every
`telemetry.epoch_seconds`), `improve`, `plateau`, `restart`, `pull`/`publish`, `record` and
`followup` events. It also holds `pool_sample` / `pool_offer` events, which name the donor worker,
record and point of each pooled elite this worker received. `dossiers/<id>.json` holds one dossier per improvement: the move trace, the
state before and after, and the RNG state for replay.

Useful one-liners:

```bash
# Who found what, and when (hours)
jq -r 'select(.ev=="frontier") | "\(.t/3600|.*100|round/100)h \(.target) \(.point.gates)@\(.point.depth) \(.by) \(.move) \(.improvement)"' DIR/campaign.jsonl
# Diversity of worker bests over time for one target
jq -c 'select(.ev=="fleet_diversity" and .target=="fox_mu4" and .scope=="bests") | [.t, .mean, .distinct, .n]' DIR/campaign.jsonl
# Any trouble?
jq -c 'select(.ev=="record_rejected" or .ev=="worker_exit" or .ev=="collapse_alarm")' DIR/campaign.jsonl
cat DIR/workers/*/error.json 2>/dev/null
```

## 7. Reports

`python -m xorsearch report DIR` turns a run directory into CSV tables and a self-contained
`report.html`. It covers frontier history with attribution, per-move statistics per epoch,
plateaus, restarts and sharing, and the improvement dossiers. It works on finished, stopped and
running campaigns, and on `quick` runs.

## 8. Stopping, resuming, crashes

- **Stopping is staged**. `stop` (or Ctrl-C, SIGTERM, or the duration ending) writes `STOP`.
  Workers finish their current step, checkpoint and exit. Any worker still running after
  `campaign.stop_grace_seconds` gets SIGTERM, and after `campaign.terminate_grace_seconds` it gets
  SIGKILL. The final collection then runs, `status.json` gets `phase = "stopped"` or `"failed"`,
  and the lock is released.
- **A worker never outlives its coordinator by more than `worker.owner_check_seconds`**. It
  stops when the lock no longer names its coordinator or when that coordinator has died.
- **Ownership**. Only one coordinator may own a directory. A lock whose owner is dead is reclaimed
  automatically; the check compares the pid together with its kernel start tick, so a recycled pid
  is never mistaken for the owner.
- **Resume** checks the frozen source, plan and snapshots. It refuses a checkpoint written for a
  different run, worker, settings or source. Records written after the last checkpoint are kept,
  because they are verified circuits.
- **Failures**. By default (`campaign.on_worker_failure = "stop"`), a failed worker stops the
  campaign: fail fast, never run silently degraded. Set it to `"continue"` to keep the other
  workers running. Read `workers/<id>/error.json` and `launch.log`, fix the problem, then `resume`.

## 9. Sharing

Each worker gets the campaign pool as the engine's `pool` (DESIGN.md §2). The coordinator keeps up
to `sharing.pool_per_point` distinct, re-verified DAGs per frontier point and per worker group, in
`pool/<target>.json`.

| `sharing.mode` | Behaviour |
|---|---|
| `pull` (default) | When the engine's restart controller restarts a stalled chain from the "shared" source, it draws a *distinct* elite (not already in its archive) from the best `sharing.sample_points` feasible points. Nothing ever interrupts a running chain. |
| `push` | Additionally, every `sharing.refresh_seconds` the worker hands a strictly better pooled elite to `Engine.adopt`, which restarts the chain on it. This is the old forced adoption, kept only for A/B comparison: it collapsed diversity in past campaigns. |
| `off` | No sharing. |

`sharing.scope = "group"` restricts sharing to workers of the same `[[workers]]` group
(lineage-only). By default (`sharing.exclude_own`) workers never receive their own records, which
are already in their archive.

## 10. Extending

**Add a new move.** Read DESIGN.md §4.3 (the move protocol) and §5 (code rules), then:

1. Write a `Move` subclass in a `moves/` module: `name`, `family`, `knobs`, `propose(ctx)`. It
   edits `ctx.state` speculatively and returns a `Proposal` with an undo journal and a trace.
2. Declare its knobs in that module's `KNOBS` section (always include a `weight`), and add the
   module to `config/registry.py` if it is new.
3. Register it with `@register`.
4. Write the positive-control test: a small circuit where the move must find a known one-gate
   improvement.
5. Try it without code changes elsewhere:
   `python -m xorsearch quick fox_mu4 --seconds 300 --set moves.<family>.<name>.weight=3`. Then
   run an A/B campaign with two groups that differ only in that `[workers.set]` weight, and
   compare their `frontier` events and the per-move epoch counters in the report.

**Alternative backends.** The campaign runtime calls core, the engine and telemetry only through
`campaign/records.py:Backend`. `[campaign] backend = "module:Class"` (or `quick --backend`)
substitutes a subclass. The tests use this to run the whole runtime with a stub engine
(`tests/test_campaign_stub.py`). The choice is frozen into the plan like everything else.

## 11. Campaign runtime knobs

`python -m xorsearch config explain campaign` (or `worker`, `sharing`) prints these knobs with
their current docs.

| Knob | Default | Meaning |
|---|---|---|
| `campaign.collect_seconds` | 2.0 | interval between record collection, pool update and `status.json` writes |
| `campaign.poll_seconds` | 0.2 | supervisor loop sleep (reaction time to STOP, signals and exits) |
| `campaign.diversity_seconds` | 60.0 | interval between `fleet_diversity` snapshots |
| `campaign.collapse_distance` | 0.05 | collapse alarm threshold on the mean best-to-best Jaccard distance |
| `campaign.stop_grace_seconds` | 30.0 | time workers get to checkpoint after STOP |
| `campaign.terminate_grace_seconds` | 5.0 | wait after SIGTERM before SIGKILL |
| `campaign.kill_grace_seconds` | 2.0 | wait after SIGKILL |
| `campaign.pin_cpus` | false | pin worker i to the i-th available CPU |
| `campaign.allow_oversubscription` | false | allow more workers than CPUs |
| `campaign.on_worker_failure` | "stop" | `stop` or `continue` |
| `campaign.freeze_tests` | false | include `xorsearch/tests` in the frozen copy |
| `campaign.freeze_attempts` | 3 | times the source copy is redone when a file changes during it |
| `campaign.freeze_retry_seconds` | 1.0 | wait between source copy attempts |
| `campaign.git_status` | true | record `git status --porcelain` at freeze time |
| `campaign.run_frozen` | true | execute the frozen copy (false is for development only) |
| `worker.checkpoint_seconds` | 60.0 | interval between engine checkpoints |
| `worker.status_seconds` | 2.0 | interval between `status.json` / `chain.json` writes |
| `worker.owner_check_seconds` | 1.0 | interval between coordinator liveness and STOP checks |
| `worker.records_per_point` | 32 | distinct DAGs saved per point by one worker |
| `worker.strict_verify` | true | a rejected record stops the worker (an engine bug) |
| `sharing.mode` | "pull" | `pull`, `push` or `off` |
| `sharing.scope` | "target" | `target` or `group` |
| `sharing.pool_per_point` | 64 | distinct DAGs per point and group kept by the coordinator |
| `sharing.sample_points` | 1 | restart elites come from the best this-many feasible points |
| `sharing.exclude_own` | true | never hand a worker its own records |
| `sharing.refresh_seconds` | 5.0 | minimum interval between pool file re-reads by a worker |

Worker processes run with `OMP_NUM_THREADS` and the similar thread variables set to 1, and with
`PYTHONDONTWRITEBYTECODE=1`, so the frozen copy stays byte-identical.
