# xorsearch user guide

`xorsearch` searches for the smallest (then shallowest) XOR circuit of any GF(2) linear map, from
a few inputs up to 64+ inputs and a thousand gates, with one method for every size. Each worker
runs one search chain. A coordinator supervises the workers, re-verifies everything they find,
keeps the global frontier and shares distinct elite circuits between them.

- **This file**: how to run, configure, monitor and extend searches.
- **[DESIGN.md](DESIGN.md)**: the method, the module contracts and the defaults.
- **[docs/BENCHMARKS.md](docs/BENCHMARKS.md)**: head-to-head runs against the old `search/` framework.
- **[docs/evidence/](docs/evidence/)**: the measurements behind the defaults.
- **[telemetry/schema.md](telemetry/schema.md)**: every log and dossier field.

Python 3.11 or newer, standard library only. Run commands from the repository root (the directory
that contains `xorsearch/`); put run directories anywhere *outside* `xorsearch/`.

---

## 1. Quick start

```bash
# What can be searched?
python -m xorsearch targets list
python -m xorsearch targets show fox_mu4

# A one-minute experiment: one worker in this process, no coordinator.
python -m xorsearch quick fox_mu4 --seconds 60 --seed 1

# A campaign: check the plan (starts nothing), then freeze it and start it detached.
python -m xorsearch plan xorsearch/examples/fox_mu4.toml
python -m xorsearch run  xorsearch/examples/fox_mu4.toml --out ~/runs/fox4 --seconds 2h --detach

python -m xorsearch status ~/runs/fox4               # frontier, pool, diversity, per-worker table
python -m xorsearch stop   ~/runs/fox4 --wait 120    # checkpoint and stop
python -m xorsearch resume ~/runs/fox4 --detach      # continue from the checkpoints
python -m xorsearch report ~/runs/fox4               # CSV tables + report.html
python -m xorsearch verify ~/runs/fox4               # re-verify every record independently
```

**Use `--detach` for anything you do not watch.** Without it, `run` and `resume` become the
coordinator in your terminal (Ctrl-C stops cleanly), and the campaign dies when that terminal or
shell session ends. This is how a benchmark launched as `python3 -m xorsearch run ... &` inside a
WSL shell call was lost. With `--detach` the coordinator starts in a new session, without a
controlling terminal, its output goes to `DIR/coordinator.log`, and it outlives the shell (and
the WSL session) that launched it. The launcher returns once the coordinator owns the run
directory and prints its pid and the status, stop and resume commands.

## 2. Commands

| Command | What it does |
|---|---|
| `run CAMPAIGN.toml --out DIR [--seconds N] [--detach] [--set k=v ...]` | Resolve the campaign file, freeze it into `DIR` (it must be missing or empty), then start the coordinator from the frozen copy. |
| `resume DIR [--seconds N] [--detach]` | Continue a stopped or crashed campaign. Workers with a checkpoint resume their exact chain; workers without one start fresh. Campaign time (`t` in every event) carries on. |
| `stop DIR [--reason R] [--wait S]` | Write a `STOP` request addressed to the live coordinator. `--wait` blocks until it has exited (exit 1 if it is still stopping or died). |
| `status DIR [--json]` | Phase, global frontier with the worker that found each point, pool sizes, fleet diversity, one row per worker. `--json` prints the raw `status.json`. |
| `plan CAMPAIGN.toml [--set ...] [--json] [--settings]` | Resolve and print the plan (targets, workers, caps, seeds, RNG seeds, settings hashes) without starting anything. `--settings` lists every non-default setting of every worker with its origin. |
| `report DIR` | CSV tables and a self-contained `DIR/report/report.html`. |
| `verify DIR` | Check the frozen source, plan and snapshots, then re-verify every record: file hash, binding to its worker, equivalence, depth cap, gate limit, verification sidecar and NCFF export. Exit 1 on any failure. |
| `verify CIRCUIT.json --target T [--cap N]` | Verify one circuit file against a target. |
| `config show [--profile P ...] [--set ...] [--non-default] [--prefix X] [--flat]` | The resolved settings as a commented TOML file, ready to save as a profile (section 4). `--flat` prints one `key = value  # origin` line per knob. |
| `config explain [KEY_OR_PREFIX]` | A knob's documentation, legal values and default; every knob under a prefix (`sharing`, `moves.walk`); or, without argument, the list of sections. |
| `targets list`, `targets show NAME` | The target catalog; one target's size, matrix hash and verified seeds. |
| `quick TARGET [--seconds N] [--seed S] [--objective O] [--depth-cap N] [--gate-limit N] [--seeds ...] [--profile P] [--set ...] [--out DIR]` | One worker in this process: no coordinator, no sharing, no source freeze (live code). Writes a small run directory (default `xorsearch-runs/quick-TARGET-TIME`) that `status`, `report` and `verify` understand. |

`--seconds` takes `3600`, `90m` or `2h30m`. Without it the `[campaign] duration` applies, and
without either the run lasts until stopped; `--seconds 0` (or `none`) means until stopped even
when the plan has a duration.

Exit codes: 0 success; 1 a reported error (the message starts with `error:`) or a failed
verification; 2 a usage error.

## 3. Campaign files

A campaign file is TOML with three kinds of tables: `[campaign]` (identity and duration), `[set]`
(campaign-wide knob values) and one `[[workers]]` table per worker group. Relative paths in the
file (targets, seeds, profile files) are relative to the file itself.

```toml
[campaign]
name = "fox_mu4"                 # default: the file name
description = "capped and uncapped workers"
seed = 20261024                  # worker i (counted across all groups) gets seed + i * 1000003
duration = "8h"                  # seconds or "90m"/"2h30m"; omit = until stopped; --seconds overrides
profiles = ["default"]           # built-in profile names or TOML paths, applied in order
sharing = "pull"                 # shorthand for sharing.mode; or a [campaign.sharing] table
# backend = "xorsearch"          # advanced: "module:Class" (section 10)

[set]                            # any knob, campaign-wide (dotted keys or nested tables)
"worker.checkpoint_seconds" = 120.0
"moves.walk.expand.weight" = 1.0

[[workers]]
name = "cap7"                    # group name; worker ids are <name>-00, <name>-01, ...
target = "fox_mu4"               # catalog name, target JSON / matrix file, or generator spec
count = 4                        # workers in this group (default 1)
objective = "gates"              # "gates" (gates, then depth) or "depth_then_gates"
depth_cap = 7                    # real cap for recorded circuits; a list cycles over the
                                 # group's workers: [7, 8, "none"]
gate_limit = 130                 # record only circuits with at most this many gates (optional)
seeds = ["target"]               # cycled over the workers; each entry is one of:
                                 #   "target"          the target's built-in seed circuits
                                 #   "root"            the engine's default fresh root
                                 #   "root:<name>"     a named constructor (root:paar, root:bp, ...)
                                 #   "path/to.json"    a circuit JSON file (verified at plan time)
profiles = ["depth"]             # extra profiles for this group only
per_worker = [{}, { "restart.stall_seconds" = 1200.0 }]   # cycles over the group's workers
[workers.set]                    # knob values for this group only
"sharing.sample_points" = 2
```

`objective`, `depth_cap` and `gate_limit` are shorthands for the knobs `objective.kind`,
`objective.depth_cap` and `objective.gate_limit`, applied as the group's layer (origin
`group:<name>`); a `[workers.set]` or `--set` value for the same knob wins. The real cap is what
records must meet; while searching, the engine may go `objective.soft_depth_slack` deeper and
repairs depth before it records anything.

`plan` (and `run`) reject mistakes before anything starts: unknown fields and knobs (with the
closest name), wrong types, out-of-range values, unknown targets, seeds that do not compute their
target, duplicate group names, objectives that cannot be built, and more workers than available
CPUs (unless `campaign.allow_oversubscription = true`). They print notes for legal but surprising
choices, such as a seed deeper than its worker's cap. Two targets with the same matrix share one
frontier and one pool.

Examples in [`examples/`](examples/):

| File | Shows |
|---|---|
| `fox_mu4.toml` | one target, a capped and an uncapped group |
| `fox_mu8.toml` | a 540-gate target with the `large` profile, caps cycled per worker, run for days detached |
| `three_targets.toml` | several targets; campaign, group and per-worker overrides; root constructors |
| `sharing_ab.toml` | A/B of `pull` sharing against independent workers (`off`) |
| `legacy_ab.toml` | A/B of the xorsearch defaults against the old framework's policies (`legacy-compat`) |

## 4. Configuration: change any knob without touching code

Every tunable value is a *knob*, declared next to the code that reads it with a type, a range or
choices, and a doc string (`python -m xorsearch config explain` lists all of them). Values are
layered from lowest to highest priority; each value remembers the layer that set it:

| Origin label | Where it comes from |
|---|---|
| `default` | the knob declaration in the code |
| `profile:<name>` | `[campaign] profiles`, then the group's `profiles` |
| `campaign` | `[campaign] sharing` / `[campaign.sharing]` |
| `campaign:set` | the top-level `[set]` table |
| `group:<name>` | the group's `objective` / `depth_cap` / `gate_limit` and `[workers.set]` |
| `worker:<id>` | `per_worker` |
| `cli` | `--set key=value` on `run`, `plan`, `quick` and `config show` |

How to change a value, from the broadest to the narrowest scope:

- **Every campaign**: edit `config/profiles/default.toml` (applied first everywhere).
- **A reusable bundle**: a profile file. `python -m xorsearch config show > mine.toml` writes
  every knob with its documentation and legal values; delete what you keep, edit the rest, then
  use `profiles = ["mine.toml"]` (relative to the campaign file) or `--profile mine.toml`.
- **One campaign**: its `[set]` table.
- **One group / one worker**: `[workers.set]` / `per_worker`.
- **One run, from the shell**: `--set sharing.mode=off --set moves.walk.expand.weight=0`.

Values use TOML syntax everywhere (a bare word on `--set` is a string). TOML has no null: write
`"none"` (`--set objective.depth_cap=none`). To check the result: `config show --non-default
--profile large` for a profile, `plan FILE --settings` for every planned worker.

`campaign.*` knobs and `sharing.pool_per_point` are read by the coordinator and have one value per
campaign. Set them in campaign profiles, `[campaign]`, `[set]` or `--set`; `[workers.set]` and
`per_worker` reject them, and a group profile that sets them is overruled by the campaign value
(with a plan note). The resolved settings of every worker, with origins, are frozen into
`settings/<worker>.json`: a run always records exactly what it ran with.

Built-in profiles (`config/profiles/`):

| Profile | Purpose |
|---|---|
| `default` | Empty. Change defaults for every campaign here. |
| `quick` | Seconds-to-minutes runs: status, pool, diversity and epochs update every 1-10 s. The search itself is unchanged. |
| `large` | 500+ gates (FOX Mu8) and multi-day runs: fewer, larger writes; a crashed worker restarts from its checkpoint (`campaign.on_worker_failure = "restart"`). |
| `depth` | `depth_then_gates` objectives, tight caps and gate limits: more depth-repair time, 2 gates of search slack over a gate limit. |
| `legacy-compat` | The old `search/` framework's policies that still exist here (fixed scheduler, no stall restarts), for A/B comparisons only. |

## 5. Long runs: detach, stop, resume, crashes

- **Detach** (`run --detach`, `resume --detach`): the coordinator is a session leader with stdin
  on `/dev/null` and stdout/stderr appended to `DIR/coordinator.log`; its workers live in its
  session. Closing the terminal, ending the WSL shell call or killing the launcher's process
  group does not touch it. `status` shows its pid; `stop` and `resume` work exactly as for an
  attached run.
- **Stopping is staged.** `stop`, Ctrl-C, SIGTERM, SIGHUP or the end of the duration writes
  `STOP`. Workers finish their current step, checkpoint and exit. A worker still running after
  `campaign.stop_grace_seconds` gets SIGTERM, after `campaign.terminate_grace_seconds` SIGKILL.
  Then a final collection, `status.json` with `phase = "stopped"` or `"failed"`, and the lock is
  released.
- **A worker never outlives its coordinator by more than `worker.owner_check_seconds`**: it
  stops when the lock no longer names its coordinator or that coordinator has died.
- **Ownership.** One coordinator owns a directory (`campaign.lock`: pid, host, kernel start tick,
  token). A dead owner's lock is reclaimed by the next `resume`; the start tick means a recycled
  pid is never mistaken for the owner.
- **Resume** re-checks the frozen source, plan and snapshots, refuses a checkpoint written for a
  different run, worker, settings or source, and runs the *frozen* code, so editing the live tree
  between sessions is safe. Records written after the last checkpoint are kept (they are verified
  circuits); at most `worker.checkpoint_seconds` of search is redone.
- **Worker failures** follow `campaign.on_worker_failure`: `stop` (default: fail fast, never run
  silently degraded), `continue` (keep the others running), or `restart` (restart the worker from
  its checkpoint, at most `campaign.max_worker_restarts` times per session; each restart is a
  `worker_restart` event and its `error.json` is kept under `errors/<session>/`). Read
  `workers/<id>/error.json` and `launch.log`, fix the cause, then `resume`.
- **Duplicate run directories**: `run --out DIR` refuses a non-empty `DIR`, and two `run`s started
  together on the same empty `DIR` cannot both freeze into it (an exclusive claim file). A failed
  freeze leaves no half-written directory.

## 6. Run directory layout

```
DIR/
  .xorsearch-run         exclusive claim taken before freezing (marks a run directory)
  plan.json              resolved plan: targets, seeds, workers (cap, objective, seed, rng seed, settings hash)
  freeze.json            hashes: plan, every snapshot below, source manifest + archive, git HEAD/dirty
  campaign.toml          the campaign file as given
  environment.json       python, OS, CPU model, logical/available CPUs, thread env, command line
  settings/<id>.json     resolved settings + origins per worker; settings/campaign.json for the coordinator
  targets/<key>.json     target snapshot (rows + matrix hash)
  seeds/<key>/<sha>.json seed circuits as verified at plan time
  source/xorsearch/...   frozen source copy: run and resume execute this, never the live tree
  source.tar.gz          byte-reproducible tarball of the same files
  campaign.lock          owner identity while running
  STOP                   last stop request (addressed to one coordinator token)
  status.json            coordinator summary: phase, workers, restarts, frontier, pool, diversity, errors
  campaign.jsonl         coordinator events (section 7)
  coordinator.log        stdout/stderr of detached coordinators, one header line per launch
  pool/<key>.json        campaign pool: distinct DAGs per frontier point, written atomically
  sessions/<token>.json  one per run/resume: start/end, worker pids/commands, stop reason, exit codes
  error.json             coordinator failure of the latest session
  errors/<token>/...     older error files (previous sessions, restarted workers)
  report/                `xorsearch report` output
  workers/<id>/
    status.json          phase, steps, steps/s, best, frontier, skipped-record counts, pool stats
    chain.json           best and current-chain value sets (input to fleet diversity)
    checkpoint.json      engine state in an envelope bound to run, worker, settings and source hashes
    records.jsonl        index of saved records
    records/g<G>-d<D>-<dag>.json               circuit JSON (xor-circuit-lab format) + metadata
    records/g<G>-d<D>-<dag>.verification.json independent verifier output
    records/g<G>-d<D>-<dag>.ncff               NIST circuit file format
    rejected.jsonl       circuits the verifier rejected (should never happen)
    launch.log           stdout/stderr of the process (import failures land here)
    error.json           the worker's failure, with traceback
    events.jsonl, dossiers/, recorder.json     telemetry (section 7)
```

Every JSON file is written atomically (temporary file, fsync, rename): a crash at any moment
leaves the old or the new version, never a torn one. (A running worker's `status.json` and
`chain.json`, rewritten every `worker.status_seconds`, skip the fsync: still atomic, only not
durable across a power loss.) JSONL files are append-only and repair a
torn last line on the next append. A record's circuit JSON is written after its sidecars and is
the commit marker; a committed record whose index line was lost is re-indexed when the worker
restarts.

## 7. Logs and how to read them

Every event line has the envelope `v`, `t` (seconds since campaign start, monotonic, continuing
across resumes), `utc`, `worker` (`"coord"` for the coordinator), `it`, `ev`. Scores are
`{"gates": G, "depth": D}`. Full field lists: [telemetry/schema.md](telemetry/schema.md).

**`campaign.jsonl`** (coordinator), the campaign-level story:

| `ev` | Meaning and key fields |
|---|---|
| `start` / `resume` / `stop` | Session lifecycle: `session`, `seconds`, `workers`, `run_id`, `source_hash`, `settings_digest`, `t_offset`, `env`; on `stop`: `reason`, `returncodes`, `restarts`, `forced`, `error` |
| `worker_start` / `worker_exit` / `worker_restart` | Which worker, when: `worker_id`, `pid`, `cpu`, `returncode`, `error`, `restart` count |
| `frontier` | A new nondominated point: `target`, `point`, `by` (worker), `group`, `kind` (`gates`/`depth`/`frontier`/`seed`), `improvement` (dossier id), `ref` (engine candidate id), `move`, `record`, `dag`, `found_t`, `removed` (points it dominates), `frontier` (all points after it) |
| `pool` | One point of a target's pool changed: `point`, `size`, `distinct`, `added`, `donor`, `evicted` |
| `fleet_diversity` | Per target and `scope` (`bests`: each worker's best record; `chains`: current chains): `n`, `distinct`, `modal_fraction`, `mean`/`min`/`max` pairwise Jaccard distance, `basins`, `workers`, `alarm` |
| `collapse_alarm` / `collapse_cleared` | Mean best-to-best distance crossed `campaign.collapse_distance`: the fleet piled onto too few DAGs |
| `record_rejected` | A worker's record (`by`, `record`) failed independent re-verification (`reason`); excluded from frontier and pool |

**`workers/<id>/events.jsonl`** (one per worker), the search itself: `start`/`resume`/`stop`;
`epoch` every `telemetry.epoch_seconds` (per-move proposals, valid, accepted, neutral, uphill,
improvements, work and CPU; acceptance state; scheduler weights; plateau and diversity metrics);
`improve` (a new worker best or frontier point: move, sub-operations, phase, plateau age, root);
`plateau` (a closed plateau: length, neutral accepts, distinct states, drift); `restart`
(reason, source fresh/elite/shared/best, root); `phase`; `pull` and `pool_sample` (the donor
worker, record and point of every shared elite); `record`; `followup`
(what happened 100 / 1,000 / 10,000 iterations after an improvement); `move` (at start, each
move left out and why: inapplicable to this target or cap, or zero weight); `warn`.

**`workers/<id>/dossiers/<id>.json`**, one per improvement: the full move trace, the state before
(plateau age and size, acceptance state, phase, scheduler weights, distance from chain best, root),
during (the last `telemetry.ring_size` proposals) and after (values, gates, shape), lineage
(parent improvement, chain, root), the RNG seed to replay the proposal, and the verification.

Records and dossiers join on the engine candidate `ref`: each `frontier` event carries `ref`, and
`improvement` (the dossier id) when the record was made for an improvement (`ref` =
`<worker>-NNNNNN`; sampled DAGs and seeds have `<worker>:...` refs and no dossier).

Useful one-liners (more in `telemetry/schema.md` section 7):

```bash
# Who found what, and when (hours)
jq -r 'select(.ev=="frontier") | "\(.t/3600|.*100|round/100)h \(.target) \(.point.gates)@\(.point.depth) \(.by) \(.move) \(.improvement)"' DIR/campaign.jsonl
# Which move and sub-operations made each improvement, in which phase, after how long flat
jq -c 'select(.ev=="improve") | [.worker,.id,.move,(.components|join("+")),.phase,.plateau_age_s]' DIR/workers/*/events*.jsonl
# Plateau shape: length and distinct states of every closed plateau of one worker
jq -c 'select(.ev=="plateau") | [.t, .level, .proposals, .distinct_states, .drift]' DIR/workers/fox-00/events*.jsonl
# Diversity of worker bests over time for one target
jq -c 'select(.ev=="fleet_diversity" and .target=="fox_mu4" and .scope=="bests") | [.t, .mean, .distinct, .n]' DIR/campaign.jsonl
# The state before, during and after one improvement
jq '{before:.state_before, during:.ring[-20:], after:.shape_after}' DIR/workers/fox-00/dossiers/fox-00-000017.json
# Any trouble?
jq -c 'select(.ev|test("record_rejected|worker_exit|worker_restart|collapse_alarm"))' DIR/campaign.jsonl
cat DIR/workers/*/error.json DIR/error.json 2>/dev/null
```

## 8. Reports

`python -m xorsearch report DIR` writes `DIR/report/`: CSV tables (`improvements.csv`,
`epochs.csv`, `moves.csv`, `combos.csv`, `plateaus.csv`, `restarts.csv`, `frontier.csv`,
`fleet_diversity.csv`) for your own plots, and a self-contained `report.html` with best-over-time,
frontier, per-move statistics, plateaus, lineage, restarts and sharing, linked to the dossiers.
It works on finished, stopped and running campaigns and on `quick` runs.

## 9. Sharing

Each worker gets the campaign pool as the engine's `pool` (DESIGN.md section 2). The coordinator
keeps up to `sharing.pool_per_point` distinct, re-verified DAGs per frontier point and worker
group in `pool/<target>.json`.

| `sharing.mode` | Behaviour |
|---|---|
| `pull` (default) | When the restart controller restarts a stalled chain from its "shared" source, it draws a *distinct* elite (not already in its archive) from the best `sharing.sample_points` feasible points. Nothing ever interrupts a running chain. |
| `off` | No sharing. |

`sharing.scope = "group"` restricts sharing to workers of the same group (lineage-only). Workers
never receive their own records (`sharing.exclude_own`); those are already in their archive.

## 10. Extending

**Add a target.** Anything `core.target.load_target` accepts works in `target = ...` without
code: a target JSON (`{"id", "input_count", "rows": [row bitmasks, bit j = input j], "seeds":
[circuit paths]}`, the `search/targets/*.json` format), a 0/1 matrix text file (NIST `.mat.txt`
or plain rows), or a generator spec such as `"circulant:m=8,poly=0x11b,coeffs=2/3/1/1"`,
`"random:n=16,m=16,density=0.4,seed=1"` or `"sparse:n=32,m=32,weight=3,seed=2"`. To give it a
catalog name, drop the JSON into `xorsearch/targets/` (seed paths there are relative to the
repository root; see `targets/mixcolumns.json`, which uses a generator instead of rows). Check it
with `targets show NAME`: it prints the matrix hash and verifies every seed.

**Add a move.** Read DESIGN.md section 4.3 (the move protocol) and section 5 (code rules), then:

1. Write a `Move` subclass in a `moves/` module: `name`, `family`, `knobs`, `propose(ctx)`, and
   `applicable(target, objective)` if it only works on some targets or caps. It edits
   `ctx.state` inside a journal and returns a `Proposal` with the journal and a trace.
2. Declare its knobs in that module's `KNOBS` section (always `weight`, usually `burst_weight`),
   register the class with `@register`, and add the module to `config/registry.py` and
   `moves/base.py:load_all` if it is new.
3. Write the positive-control test: a small circuit where the move must find a known one-gate
   improvement.
4. Try it without code changes elsewhere:
   `python -m xorsearch quick fox_mu4 --seconds 300 --set moves.<family>.<name>.weight=3`. Then
   run an A/B campaign with two groups that differ only in that weight (`[workers.set]`) and
   compare their `frontier` events and the per-move epoch counters in the report.

**Alternative backends.** The campaign runtime calls core, the engine and telemetry only through
`campaign/records.py:Backend`. `[campaign] backend = "module:Class"` (or `quick --backend`)
substitutes a subclass; the tests run the whole runtime on a stub engine this way
(`tests/test_campaign_stub.py`). The choice is frozen into the plan.

Worker processes run with `OMP_NUM_THREADS` and similar thread variables set to 1, and with
`PYTHONDONTWRITEBYTECODE=1` so the frozen copy stays byte-identical.
