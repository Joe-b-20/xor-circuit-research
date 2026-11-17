# Using BoolFlux

How to run BoolFlux, check a circuit and read its output. How it works is in
[HOW-IT-WORKS.md](HOW-IT-WORKS.md).

**Run every command from the repository root.** `OUT` is any output folder. Times are wall times
on one CPU of the machine in [HISTORY.md](HISTORY.md#compute).

## Requirements

| Needed | For | Without it |
|---|---|---|
| Python ≥ 3.11 (standard library) | everything | — |
| gcc | the C kernels, compiled on first use (each `run`/`pipe`/`flow` compiles a private copy into its output folder) | nothing runs a search |
| GNU time (`time -v` on `PATH`) | wall time and peak RSS of each kernel process in `flow`, `bench/bench.py` | Python measures both (wall clock, `os.wait4` `ru_maxrss`); the run record says which |
| `taskset` (util-linux) | pinning: `flow --cpus`, the hub's workers | pinned with `os.sched_setaffinity` (unpinned, with a warning, where that is missing too) |
| `numpy` and `python-sat` | `ops/conjpull.py`, and `ops/transport.py` (its builds and pulls) | that script stops (their tests are skipped) |
| `numpy` | `ops/selbuild.py`; refitting the hub's learned model | that script stops at import (its tests are skipped) |
| `python-sat` | `ops/satlns.py`; `ops/winsat.py` SAT windows (its AND removal and the hub's `andrm` need neither) | `satlns.py` stops at import, `winsat.py` at the first SAT query |

`python3 search/nonlinear/boolflux/cli.py tools` prints what this machine has; `run`, `pipe`,
`flow` and the hub print the same line on stderr when they start.

## Quick start

```bash
python3 search/nonlinear/boolflux/cli.py list                                  # targets, models, objective keys
python3 search/nonlinear/boolflux/cli.py run --target maj3 --model xag --objective a,cost \
    --iters 3000 --seeds 1 --jobs 1 --out OUT/maj3                           # 2 s: 4 gates, 1 AND
python3 search/nonlinear/boolflux/cli.py verify OUT/maj3/best.circ.txt --target maj3 --model xag

python3 -m unittest discover -s search/nonlinear/boolflux/tests -t search/nonlinear       # 143 tests, 6 minutes
python3 -m unittest discover -s search/nonlinear/boolflux/independent                     # 36 tests, 4 s
python3 -m unittest discover -s search/nonlinear/boolflux/hub/tests -t search/nonlinear   # 68 tests, 40 s
```

## Commands

| Command | Does |
|---|---|
| `run` | gate kernel: one job per seed, in rounds of a fixed iteration count; the best distinct circuits of a round start the next |
| `pipe` | rounds of AND-skeleton search, synthesis back to gates, and gate search; a share of the jobs skips the skeleton stage |
| `flow` | time-sliced workflows: `gate`, `full` (skeleton, rebuild variants, gate stage), rebuild-only, adaptive |
| `verify FILE ...` | both verifiers, the library check and metric agreement for each file |
| `start` | write the starting circuit (naive ANF, or a checked copy of a file) |
| `list` | the targets, stock models and objective keys |
| `tools` | Python, gcc, GNU time, taskset, numpy and python-sat on this machine |

Every command has `-h`. The ranking is the same everywhere: feasible first, then cap excess, then
the objective keys in order.

```bash
# small S-box from its naive ANF, gate-depth cap 6 (3 s): 16 gates at GD 6
python3 search/nonlinear/boolflux/cli.py run --target present --model bgc --start anf --objective cost,gd \
    --cap-gd 6 --iters 20000 --seeds 1-2 --jobs 1 --out OUT/present
# AES from a NIST circuit under its own caps (6 s): 109 -> 108 gates
python3 search/nonlinear/boolflux/cli.py run --target aes --model nist \
    --start search/nonlinear/seeds/aes-sbox/aes-sbox-a32-ad5-g109-gd20-xx77-4.circ.txt \
    --objective cost,gd --cap-a 32 --cap-ad 5 --cap-gd 20 --iters 20000 --seeds 7 --jobs 1 \
    --set skip_noop=0 --out OUT/aes-g109
# GF(2^4) multiplication, ANDs first (16 s): 33 gates with 10 ANDs
python3 search/nonlinear/boolflux/cli.py pipe --target gf16-mul --model xag --start anf --objective a,cost \
    --iters 20000 --skel-iters 2000 --seeds 1-2 --rounds 2 --jobs 1 --out OUT/gf16mul
# the gate kernel for a wall budget, pinned to CPU 0 (7 s)
python3 search/nonlinear/boolflux/cli.py flow --target present --model bgc --objective cost --config gate \
    --seconds 5 --seeds 1 --cpus 0 --out OUT/flow-gate
python3 search/nonlinear/boolflux/cli.py verify search/nonlinear/seeds/aes-sbox/aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt \
    --target aes --model nist --cap-gd 19
```

- `--start` takes `anf` or a NIST `.circ.txt` / `.slp` / NCFF file; a start that breaks the caps
  is repaired first. `--seeds 1-8` or `1,3,5`; `--jobs N` runs N kernels at a time (default: all
  CPUs); `--rounds R --pool P` runs R rounds, each from the P best distinct circuits of the last.
- A `run` or `pipe` that its `--iters` budget ends is deterministic for its seed, settings and
  code version (the kernel seed of seed S in round R is S + R·2³²). `flow` is time-budgeted and is
  not. `--seconds` is a safety cap per process in `run` and `pipe`, the budget per seed in `flow`.
- `pipe` with `--iters 100000 --skel-iters 2000 --seeds 1-8 --rounds 3` reaches 9 ANDs on
  GF(2⁴) multiplication. `--skel-share` (default 0.5) is the share of jobs that run the skeleton
  search first; `--skel-iters 0` makes it a rebuild only.
- A run exits nonzero with `CAPS NOT MET` when no feasible circuit was found (the best repair is
  still written) and with `VERIFICATION FAILED` if a verifier rejects the best circuit. `verify`
  prints `ok` or `FAIL` per file and exits 1 if any fails; with `--cap-*` a circuit outside a cap
  fails too.

## Targets, models, objectives, caps

- **Targets**: `aes` and `aes-inv` (computed from FIPS-197); `maj3`, `fulladd`, `gf16-mul`,
  `gf16-inv`; every S-box with a table in
  [boolflux/benchmarks/sboxes.json](boolflux/benchmarks/sboxes.json) (present, gift, skinny64,
  prince, midori_sb0, piccolo, rectangle, serpent_s0..s7, ascon, keccak_chi5, sm4, camellia_s1,
  ...); `aes-sbox-sel`, NIST's S-box with a direction bit (inputs `c x0..x7`: the S-box for
  `c = 0`, its inverse for `c = 1`); and `map:<name>`, a linear map of
  [circuits/](../../circuits/README.md) with at most 16 inputs. To add a function, add
  `{"name", "n", "m", "table", "source"}` to `sboxes.json`. Bit order is msb/msb: `x0` is the
  most significant input bit, `y0` the most significant output bit.
- **Models** ([boolflux/models/](boolflux/models/)): `nist` (AND, XOR, XNOR, NOT; NIST's
  counting), `bgc` (AND, OR, XOR, NOT), `gc6` (AND, OR, XOR, XNOR, NAND, NOR, NOT), `gc` (every
  two-input gate and NOT), `xag` (AND, XOR, NOT), `xor` (XOR only; the exact linear mode). A model
  is a JSON file `{"name", "gates": {"AND": 1, ...}}`; fractional costs work; `--model PATH.json`
  loads your own.
- **Objective**: up to three of `cost`, `g`, `a`, `gd`, `ad`, compared in order (`cost,gd`,
  `a,cost`, ...).
- **Caps**: `--cap-gd`, `--cap-ad`, `--cap-a`. They are hard: an infeasible circuit never
  replaces a feasible best.

`--set key=value` changes a gate-kernel setting; every key and default is in
[boolflux/DESIGN.md](boolflux/DESIGN.md#43-gate-kernel-kernelbfxc). The ones that matter most:

| Setting | What it does |
|---|---|
| `T0`, `Tperiod_it`, `max_excess` | the sawtooth temperature (`T0=0`: no uphill steps, a plateau walk only) and the largest step above the best |
| `stall_it` | iterations without a new best before the chain returns to it |
| `stop_stall_it` | N > 0: the job stops N iterations after its last new best (default 0, off) |
| `clock` | clock of `seconds`: `real` (default since 2026-11-16), `cpu` (CPU time, for paired comparisons), `mono` (the old clock, 3-6 % fast on WSL) |
| `skip_noop` | skip structural no-ops (default 1); runs recorded before it was the default replay with `skip_noop=0` |
| `tracemoves=FILE` | every accepted move, with circuits before and after each improvement; `search/nonlinear/boolflux/bench/show_trace.py FILE` prints it |

## Checking and placing AES circuits

```bash
python3 search/nonlinear/boolflux/aes_check.py FILE [FILE ...] [--json OUT.json]   # under 1 s per file
python3 search/nonlinear/boolflux/aes_check.py FILE --function aes-invsbox         # the inverse S-box
python3 search/nonlinear/boolflux/independent/verify.py FILE --aes --model search/nonlinear/boolflux/models/nist.json
python3 circuits/check.py                                                          # every circuit in circuits/ and seeds/
```

`aes_check.py` runs both verifiers with the NIST library, then compares the circuit's
`(A, AD, G, GD)` with every circuit of the same function in the pinned NIST set in
[seeds/](seeds/): it lists those with all four metrics ≤ (equality counts as dominated, so a
circuit equal to NIST's is not new) and the published best G at the circuit's caps.
`--function` is `aes-sbox` (the default, 91 NIST circuits: `seeds/aes-sbox/`, `old-2020/*-fwd-*`,
`sbox/*-fwd-*`), `aes-invsbox` (91: `seeds/aes-invsbox/`, `old-2020/*-rev-*`, `sbox/*-inv-*`) or
`auto` (the function each file computes). The same choice is `$BOOLFLUX_FUNCTION` for the hub and
the method scripts ([boolflux/aesfn.py](boolflux/aesfn.py)).

`aes_check.py` does not place `aes-sbox-sel` circuits. Check them with
`cli.py verify FILE --target aes-sbox-sel --model nist` (both verifiers, all 512 inputs) and
`circuits/check.py`, and compare them with NIST's 9 in
[seeds/aes-sbox-sel/](seeds/aes-sbox-sel/).

## The hub

```bash
ls search/nonlinear/seeds/aes-sbox/*.circ.txt circuits/aes-sbox/*.circ.txt > OUT/seeds.list
python3 search/nonlinear/boolflux/hub/scheduler.py --dir OUT/hub --cpus 2,3 --hours 1 \
    --seed-list OUT/seeds.list --ops polish,pull,join,trb \
    --seconds polish=90,pull=90,join=60,trb=30 --seed 1
```

One worker per CPU in `--cpus`. `OUT/hub/archive/` holds every admitted circuit (`<id>.bfx` and
`<id>.json` with its parents, operator, seed and code version), `front.json` the front,
`runs/<run_id>.json` and `stats.jsonl` one record per job; `control.json` is re-read while the
scheduler runs. `--function aes-invsbox` runs the hub on the inverse S-box (seed it with
`seeds/aes-invsbox/*.circ.txt`); the function is kept in `OUT/hub/campaign.json`, and the
operators inherit it. Each operator is also a program (`hub/op_polish.py --archive OUT/hub --in ID
--caps A,AD,GD --objective KEYS --seed S --seconds T --out JOBDIR`; more in `hub/ops/`). Judge a
run by its frontier admissions per AND count, not by the scheduler's gain figures. `--policy priority`
(default) fills each free CPU from the first non-empty level: join (front circuits with archive members
they have not met, `--join-batch 8` targets per job, `--join-cpus 1`, at most `--join-share 0.10` of the
CPU time of the last 10 minutes), fresh (first polish, then first pull, of a front tuple), the repeats under
`--tuple-caps` (second polish, second and third pull; `--variants-first` moves them after "other"), variant and near
(first polish / pull of each structure of a front tuple, then of each member of a cell within `--near-gap`
gates of the front), other (one job of every other operator per front tuple: `trb` once), repeat (fewest
jobs per tuple over the caps, `--repeat-max` to stop); `--policy bandit --eps 0.25` is the
rule used until 2026-11-16 (`--near`, `--nursery` and `ad3_share` apply to it only). Each job's decision
(level, level sizes, rule) is in `runs/<run_id>.json`. `control.json` `"ingest"` globs are read every
`--ingest-every 60` s (was 1800). polish and pull also return up to `--bests 8` of the kernel's intermediate
bests (placeable, non-dominated); pull lowers GD by default (`--lower GD,GD,GD,AD,A` is the old draw), trb
keeps the input's GD (`--gd-offsets 0,0,1` the old). `hub/status.py OUT/hub` prints
the operators' jobs, admissions and CPU time and the front points the run produced.

Opt-in (2026-11-17; the defaults above are unchanged):

| Option | What it does |
|---|---|
| `--ops ...,andrm` | operator `andrm` (`hub/ops/op_andrm.py`, 120 s, once per front tuple): exact window AND removal, a kernel polish of the hit with one AND fewer at its own caps, then a pull back to the source's GD |
| `--policy learned` | join as in `priority`; otherwise the (operator, target) with the most predicted front additions per CPU second (`hub/learned.py`, model `hub/learned_model.json` fitted on logged hub campaigns), weighted by `--learned-a-decay 0.7` per AND above the front's lowest A, with online calibration (`--learned-k 2`), exploration noise (`--learned-noise 0.3`) and at most `--learned-max-att 3` jobs per (operator, tuple); operators the model does not know (`andrm`) are not launched |
| `--kopt 'polish,pull:KEY=VAL,...'` | kernel settings for every job of those operators (keys `pair_xor`, `tgt_w.mffc1`, `tgt_w.and`, `tgt_w.viol`, `stop_stall_it`, `T0`) |
| `--kopt-first 'polish:KEY=VAL,...'` | the same for first jobs only (levels `--kopt-first-levels fresh,variant,near,other`), over `--kopt` |

## Method scripts

The methods of [HOW-IT-WORKS.md](HOW-IT-WORKS.md#moves-around-the-kernel) are scripts in
[boolflux/ops/](boolflux/ops/). All but `selbuild.py` share one interface:
`--in START --target REF --seed S --seconds T --out DIR [--cpus N] [--function F]`. `--target` is a
reference circuit (a path, or a file name in `seeds/aes-sbox/` or `seeds/aes-invsbox/`): its A and
AD are hard limits on every circuit written, its G and GD the point to beat. Search states may pass
above the limits. `--function` (default `auto`: the function the `--in` circuit computes; for
`transport.py` the other one) selects the AES S-box or its inverse for every check and for the NIST
set. Every script runs on inverse circuits too: `conjpull.py` builds the inverse's conjugates
(S⁻¹(y) = G′(S⁻¹(Lin y + c_L)), Lin = A G A⁻¹), `rebase.py --moves` uses GF(4) tables over the
inversion input z = S⁻¹(y)²⁵⁴ (`rebase_lib/gf4fn.py`), and `satlns.py` pools `circuits/aes-invsbox/`
and `seeds/aes-invsbox/`.

```bash
S=search/nonlinear/seeds/aes-sbox
python3 search/nonlinear/boolflux/ops/rebase.py --in $S/aes-sbox-a35-ad3-g183-gd13-xx148-29.circ.txt \
    --target aes-sbox-a35-ad3-g183-gd13-xx148-29.circ.txt --cap 13 --seed 1 --seconds 120 --out OUT/rebase
python3 search/nonlinear/boolflux/ops/bottom.py --in $S/aes-sbox-a45-ad4-g141-gd12-xx96-25.circ.txt \
    --target aes-sbox-a45-ad4-g141-gd12-xx96-25.circ.txt --seed 1 --seconds 120 --out OUT/bottom
python3 search/nonlinear/boolflux/ops/conjpull.py --in $S/aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt \
    --target aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt --seed 1 --seconds 120 --out OUT/conj
python3 search/nonlinear/boolflux/ops/satlns.py --in $S/aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt \
    --target aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt --gd 20 --seed 1 --seconds 120 --out OUT/satlns
```

On one CPU these two-minute runs wrote 35/3/180/13 (re-basing, from NIST's 35/3/183/13) and
41/4/136/12 (shared bottom, from NIST's 45/4/141/12); conjugation and the SAT LNS need longer
lineages. `OUT` gets only circuits that pass both verifiers inside the limits, each with a
sidecar `.json` (start and its sha256, method, command, seed, time, code, function and the run
record's main fields), `result.json` (best per (G, GD), wall time, status), and the run record
`run.json` + `events.jsonl.gz` ([Run logs](#run-logs)). Kernel builds and caches go to
`$BOOLFLUX_CACHE` (default `~/.cache/boolflux`).

| Script | Main options (defaults) |
|---|---|
| `conjpull.py` | `--conj` items in order: `id`, `L:K`, `rank:R` (default `rank:1`), `top:N`, `all`; opt-in `sh:K`, successive halving: K conjugates (188:0, 189:0 and those that keep the level-1 AND span first) run the first stage, the best `--sh-keep 2` by (A, AD, G + max(0, GD − d), GD) the rest, or with `--sh-probe S` a probe of S seconds instead of the first stage. `--schedule MODE:CAP:SECONDS,...` (default `g:31:200,m:27:200,m:25:200`; CAP `N`, `+N`/`-N` from the stage input, `d+N` from the start's GD); opt-in `--caps lineage` makes every later stage pull, at most `--max-pull 2` levels. A schedule longer than `--seconds` is scaled (`--overrun refuse` refuses it); `--registry FILE` never repeats a (start, conjugate, schedule); conjugates of a conjugate are refused (status `refused`) unless `--allow-reconj` |
| `transport.py` | `--maps` (default `id,188:0,189:0,screen:3`; also `L:K`, `depth:N`), the GD caps of the build `--ladder -1,0,1,2` relative to the start's GD, then staged pulls of the best `--pull-n 2` builds by `conjpull --conj id` (`--pull g:+0:150,m:+0:150,m:-1:170`; builds deeper than the start's GD + 1 `--pull-deep g:+0:120,m:s+2:150,m:s:200`, `s±N` relative to the start's GD) |
| `rebase.py` | `--cap D` or `--goal depth\|gates`; `--moves` (`--descend`: moves that lower a bound above 1, step by step); opt-in `--price gates` (`--pool 3000` combinations priced, `--builds 160` built), with it `--deep` and `--patch` |
| `bottom.py` | `--cut K` (AND level of the kept front; default the start's AD), `--cap D` (default the lower of the target's and the start's GD), `--amax A` (ANDs of a plan, default the target's A), `--pw 0,3` (weight per AND in the annealer's cost, one value per plan in turn; `--pw 8` gave the inverse 39/4/140/12, `--pw 6` 45/4/143/11), `--junk` (`absorb5` on the inverse, `terms` on the forward S-box; also `absorb`, and `reject`: not applicable), `--polish-seconds 90` (builds equal to the start or to a build already polished are not polished again unless `--polish-dup`) |
| `satlns.py` | `--gd D`, `--profile fast\|tuned\|basic` (default `fast`); it pools the circuits in `circuits/aes-sbox/`, `seeds/aes-sbox/` and `$BOOLFLUX_POOL_DIRS` |
| `winsat.py` | SAT resynthesis of windows (`--modes cost:0.6,gd:0.25,slack:0.15`, `--K 8` inputs, `--maxg 10` gates, `--budget 20000` conflicts per call); `--modes andrm:1` is exact AND removal alone, whose hits become the walk state when their AD is at most the current AD + `--andrm-ad 1` |

```bash
# 4 s: eight builds, 40/6/219/23 to 40/6/224/22, from our forward 32/4/125/15
python3 search/nonlinear/boolflux/ops/selbuild.py --in circuits/aes-sbox/aes-sbox-a32-ad4-g125-gd15-xx93-37.circ.txt \
    --top-mode xdelta --bottom-mode leafg --seed 2 --out OUT/sel
# 23 s: 40/6/224/22 -> 40/6/169/22
python3 search/nonlinear/boolflux/cli.py run --target aes-sbox-sel --model nist \
    --start OUT/sel/aes-sbox-sel-a40-ad6-g224-gd22-xx184-38.circ.txt --objective a,ad,cost,gd \
    --cap-a 40 --cap-ad 6 --cap-gd 22 --iters 100000 --seeds 1 --jobs 1 --out OUT/sel-polish
```

`selbuild.py --in F` turns a forward or inverse circuit F into an `aes-sbox-sel` circuit
([HOW-IT-WORKS.md](HOW-IT-WORKS.md#moves-around-the-kernel)) for each map of `--maps` (default
`best`: the 3 maps whose muxes need 4 + 4 ANDs; or `L:K,...`). It scores every basis of each side
with one build and builds the `--top 3` best of each side with `--runs 8` Boyar–Peralta runs per
region. `--top-mode` is `bp` (default; F's top forms re-synthesised over x, c and the products with
c), `wrap` (the muxed inputs first, then F's own top), `flat` (one balanced tree per form) or
`xdelta` (F's own top, plus one XOR per changed form); `--bottom-mode` is `wrap` (default), `flat`
or `leafg` (F's own bottom kept, the muxes in parallel over its leaves). `flat`, `xdelta` and `leafg`
are depth-aware and scored by (GD, G); the others by G. It writes the distinct
(A, AD, G, GD) builds that compute `aes-sbox-sel` on all 512 inputs and `result.json`, and no run
record; the builds are then polished by `cli.py run` under GD caps. From inverse circuits it gave
builds about 8 levels deeper and 100 gates larger than from forward ones.

## Output

```
OUT/
  run.json, events.jsonl.gz   the run record (next section)
  summary.json          command, settings, caps, seeds, code hash, every job (seed, kernel seed,
                        improvements with time and iteration, moves, wall time), best (verifier verdicts)
  best.circ.txt         the best circuit (header: command, code hash, origin; CAPS NOT MET if infeasible)
  src/, bin/            the sources this run used and the kernels built from them
  r<R>-s<S>.cfg/.log    kernel configuration and log of round R, seed S
  r<R>-s<S>.start.bfx / .best.bfx   start and best of that job (kernel text format)
  s<S>/                 (flow) per-seed working folder
```

Circuit files carry a `% Tally:` comment (`G A GD AD` and counts by type). In `nist` files a NOT
is written `XNOR t a 0`, as in NIST's own files.

## Run logs

Every search run writes a run record, from which it can be replayed: `cli.py run`, `pipe` and
`flow` into `OUT/`; each method script into its `--out` folder; each hub job into
`OUT/hub/jobs/<run_id>/`, and each start of the scheduler into `OUT/hub/sessions/<UTC>-<pid>/`;
`bench/bench.py` into each run's work folder. The code is
[boolflux/runlog.py](boolflux/runlog.py). Worked replays of published circuits are in
[circuits/REPRODUCE.md](../../circuits/REPRODUCE.md).

| File | Content |
|---|---|
| `run.json` | written at the start and at the end (`status` is `running` until then) |
| `events.jsonl.gz` | one JSON line per event: `t` (seconds since the start), `ev`, and its fields |
| `git-<sha256>.diff.gz` | when the tree had uncommitted changes: `git diff HEAD` plus every untracked file under `search/` (the hub keeps one copy per campaign in `OUT/hub/runlog/`) |

| `run.json` field | Content |
|---|---|
| `kind` | `cli.run`, `cli.pipe`, `cli.flow`, `hub.scheduler`, `hub.op.<name>`, `ops.<name>`, `bench.<tool>` |
| `argv`, `cwd`, `command` | the exact command line (Python first), the folder it ran in, a shell-quoted line that replays it from there |
| `git` | `commit`, `branch`, `dirty`, `untracked`, and when dirty `diff` (the saved file) and `diff_sha256` |
| `sources_sha256` | sha256 over every `.py`, `.c` and `.json` file of `search/nonlinear/boolflux/` (paths and bytes) |
| `function` | `aes-sbox` or `aes-invsbox` (AES runs) |
| `seeds` | every seed: the job seeds, the kernel seed of every job (`run`, `pipe`), and how derived seeds are formed (each derived seed is also an event) |
| `config` | the resolved settings, caps and kernel defaults |
| `starts` | start circuits (seed files of the hub): path, sha256, metrics |
| `budget_s` | the wall-time budget (`null`: an iteration budget) |
| `kernels` | each kernel binary: path, sha256, source and its sha256, the gcc command that built it, the gcc version on `PATH` |
| `host`, `tools` | CPU count and affinity, OS, Python; GNU time and taskset (path or `null`) and how times, RSS and pinning were done |
| `env` | the `BOOLFLUX_*` variables |
| `t_start_utc`, `t_end_utc`, `wall_s`, `cpu_s`, `max_rss_kb`, `status`, `result` | timing (CPU time of the process and its children; RSS of the largest child), exit status, outcome |

Events: `improvement` (`metrics`, `operator`; every new best of a kernel job, every trajectory
point of `flow` with its source, every circuit a method script records, every hub admission),
`kernel` (round, kernel seed, caps, wall time, RSS, exit code), `stage` and `conjugate`
(conjpull), `job` (hub: run id, operator, target, seed, CPU), `candidate` (hub operators). Read
them with `zcat events.jsonl.gz` or `runlog.read_events(path)`. A killed run keeps every event
written before it was killed.

To replay a run: check out `git.commit`; if `git.dirty`, apply the diff
(`zcat git-….diff.gz | git apply`); check that `sources_sha256` matches
(`python3 -c "import sys; sys.path.insert(0, 'search/nonlinear'); from boolflux import runlog; print(runlog.sources_sha256())"`);
then run `command` from `cwd`. Iteration-budgeted runs (`run`, `pipe` without a `--seconds` stop)
give the same circuits; time-budgeted runs (`flow`, the hub, the method scripts) repeat the same
seeds and settings, not the same trajectory.
