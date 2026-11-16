# Using BoolFlux

How to run BoolFlux, check a circuit, and read its output. How it works is in
[HOW-IT-WORKS.md](HOW-IT-WORKS.md), and how results are verified is in
[VERIFICATION.md](VERIFICATION.md).

BoolFlux needs Python 3.11 or newer (standard library only) and gcc. The kernels are compiled
on first use, and each run compiles a private copy into its output folder. **Run every command
from the repository root.** `OUT` stands for any output folder, preferably outside the
repository ([runs/README.md](runs/README.md)). Every example below was run on 2026-11-14 pinned
to one CPU (`taskset -c 0`), on the commit `417e449` working tree. The times given are wall
times on that machine.

## Quick start

```bash
python3 nonlinear/boolflux/cli.py run --target maj3 --model xag --objective a,cost \
    --iters 3000 --seeds 1 --jobs 1 --out OUT/maj3                     # 5 s: 4 gates, 1 AND
python3 nonlinear/boolflux/cli.py verify OUT/maj3/best.circ.txt --target maj3 --model xag
python3 nonlinear/boolflux/campaigns/verify_all.py                     # re-verify everything, ~70 s
```

## Commands

| command | does |
|---|---|
| `run` | gate kernel (`kernel/bfx.c`): one job per seed, in rounds of a fixed iteration count; a pool of distinct best circuits carries over between rounds |
| `pipe` | rounds of AND-skeleton search (`kernel/skel.c`), synthesis back to gates, and gate search; a share of the jobs skips the skeleton stage |
| `flow` | the benchmark driver's time-sliced workflows (`workflow.py`): `gate`, `full`, rebuild-only, adaptive; one process per seed, optionally pinned |
| `verify FILE ...` | both verifiers, the library check, and metric agreement for each file |
| `start` | write the starting circuit (naive ANF, or a checked copy of a file) as NCFF |

Every command has `-h`. The ranking is the same everywhere: feasible first, then total cap
excess, then the objective keys in order (`objective.py`).

### run

```bash
# small S-box from its naive ANF, gate-depth cap 6 (7 s, 2 seeds): 16 gates, GD 6
python3 nonlinear/boolflux/cli.py run --target present --model bgc --start anf --objective cost,gd \
    --cap-gd 6 --iters 20000 --seeds 1-2 --jobs 1 --out OUT/present

# AES: deterministic replay of a recorded result (11 s). NIST a32-ad5-g109-gd20 -> 108 gates at
# iteration 19189, the same gate list as results/aes/aes-nist-cost_gd-gd20-ad5-a32-g108-a32-gd20-ad5
python3 nonlinear/boolflux/cli.py run --target aes --model nist \
    --start nonlinear/nist/aes-sbox/aes-sbox-a32-ad5-g109-gd20-xx77-4.circ.txt \
    --objective cost,gd --cap-a 32 --cap-ad 5 --cap-gd 20 --iters 20000 --seeds 7 --jobs 1 \
    --set skip_noop=0 --out OUT/aes-g109
```

`--start` takes `anf` or an NCFF / NIST `.circ.txt` / `.slp` file. A start that breaks the caps is
repaired first. `--seeds 1-8` or `1,3,5`. `--jobs N` runs N kernels at a time (default: all
CPUs). `--rounds R --pool P` runs R rounds, each starting from the P best distinct circuits of
the previous round. `--seconds` is a safety cap per process. A run that its `--iters` budget ends
is deterministic for a given seed, settings and code version. The kernel seed of seed S in
round R is S + R x 2^32 (`workflow.kernel_seed`, the same in `run`, `pipe`, `flow` and the
benchmark; round 0 gives S). Before review 5, `run` and `pipe` used S + 1000 R and `flow`
S x 1000 + R, which collide ((1, 1) = (1001, 0)); a command recorded with them is replayed with
`--seed-scheme legacy` (bench plans: `"seed_scheme": "legacy-flow"`). `summary.json` records
the kernel seed of every job.

The replay above needs `--set skip_noop=0`, because the default no-op filter (on since 7ae20c8)
changes the random trajectory. Without it the same command gives 109 at 20,000 iterations. The
same holds for every result recorded before 7ae20c8, which includes all 2026-11-13 `cli.py run`
results in the manifest: add `--set skip_noop=0` to the recorded command, or use the `src/` and
`bin/` snapshot in the run folder. Checked on 2026-11-15 for 28/4/133/20 (seed 5, 100,000
iterations): identical gate list both ways, 134 instead of 133 with the default filter
([VERIFICATION.md](VERIFICATION.md) section 6). Multi-round recorded commands also need
`--seed-scheme legacy`.

The command exits nonzero with `CAPS NOT MET` when no feasible circuit was found (the best
repair so far is still written), and with `VERIFICATION FAILED` if a verifier rejects the
best circuit.

### pipe

```bash
# GF(2^4) multiplication from its schoolbook ANF, AND count first (37 s, 2 seeds x 2 rounds)
python3 nonlinear/boolflux/cli.py pipe --target gf16-mul --model xag --start anf --objective a,cost \
    --iters 20000 --skel-iters 2000 --seeds 1-2 --rounds 2 --jobs 1 --out OUT/gf16mul
```

That short run ends at 33 gates with 10 ANDs. The ledger's 9 ANDs (32 gates) took
`--iters 100000 --skel-iters 2000 --seeds 1-8 --rounds 3` ([LEDGER.md](LEDGER.md) section 1,
82 s). `--skel-share` (default 0.5) is the fraction of jobs that run the skeleton search first.
`--skel-iters 0` makes the skeleton stage a rebuild only.

### flow

```bash
# gate kernel alone for a wall budget (12 s including start-up)
python3 nonlinear/boolflux/cli.py flow --target present --model bgc --objective cost --config gate \
    --seconds 5 --seeds 1 --cpus 0 --out OUT/flow-gate
# full configuration: skeleton stage + rebuild variants + gate stage in 2 s rounds
python3 nonlinear/boolflux/cli.py flow --target present --model bgc --objective cost --config full \
    --round-s 2 --seconds 6 --seeds 1 --cpus 0 --out OUT/flow-full
# rebuild only (skeleton kernel with 0 iterations), adaptive share: the workflow of the 124@GD14 run
python3 nonlinear/boolflux/cli.py flow --target present --model bgc --objective cost --config full \
    --skel-set iters=0 --adaptive --round-s 2 --seconds 6 --seeds 1 --cpus 0 --out OUT/flow-rebuild
```

`--seconds` is the wall budget per seed, rebuild included. `--cpus 0,2,4` pins seed i to CPU
`cpus[i % len]`. `--no-seeded` / `--no-unseeded` drop rebuild variants. `--set` changes gate
kernel settings and `--skel-set` changes skeleton kernel settings. Flow runs are time-budgeted,
so they are not bit-reproducible. The exact benchmark plans are in
[bench/REPRODUCE.md](bench/REPRODUCE.md).

### verify and start

```bash
python3 nonlinear/boolflux/cli.py start --target present --model bgc --out OUT/present-anf.circ.txt
python3 nonlinear/boolflux/cli.py verify OUT/present-anf.circ.txt OUT/present/best.circ.txt --target present --model bgc
python3 nonlinear/boolflux/cli.py verify nonlinear/boolflux/results/aes/aes-nist-D-kernel-g121-a37-gd14-ad4.circ.txt \
    --target aes --model nist
```

`verify` prints `ok` or `FAIL` per file, with metrics, and exits with 1 if any file fails; a
failing file gets a second line that says why. With `--cap-gd N`, `--cap-ad N` or `--cap-a N` a
circuit outside the cap fails too (`caps=NOT MET`). Kernel `.bfx` files are accepted (converted
in a temporary folder). `cli.py list` prints the targets, the stock models and the objective
keys, and `cli.py CMD -h` explains every option of a command.

## Targets, models, objectives, caps

- **Targets**: `aes` and `aes-inv` (computed from FIPS-197); `maj3`, `fulladd`, `gf16-mul`,
  `gf16-inv`; and every S-box in [benchmarks/sboxes.json](benchmarks/sboxes.json): present,
  led, gift, skinny64, prince, midori_sb0, midori_sb1, piccolo, rectangle, klein, noekeon, pride,
  serpent_s0..s7, printcipher, chi3, ascon, keccak_chi5, skinny128, sm4, camellia_s1.
  `map:<name>` is a linear map from `circuits/`. Bit order is msb/msb: `x0` is the most
  significant input bit and `y0` the most significant output bit.
- **Models** ([models/](models/)): `nist` (AND, XOR, XNOR, NOT; NIST's accounting), `bgc` (AND,
  OR, XOR, NOT), `gc6` (AND, OR, XOR, XNOR, NAND, NOR, NOT), `gc` (every two-input gate and NOT),
  `xag` (AND, XOR, NOT), `xor` (XOR only; switches on the exact linear mode). A model is a JSON
  file `{"name", "gates": {"AND": 1, ...}}`, and fractional costs work. `--model PATH.json` loads
  your own.
- **Objective**: up to three of `cost`, `g`, `a`, `gd`, `ad`, compared lexicographically (for
  example `cost,gd` or `a,cost`).
- **Caps**: `--cap-gd`, `--cap-ad`, `--cap-a`. They are hard: an infeasible circuit never
  replaces a feasible best.

## Kernel settings (`--set key=value`)

Defaults are in `workflow.DEFAULTS`: `T0 0.6`, `Tperiod_it 20000` (sawtooth temperature),
`stall_it 60000` (restart from the best), `uphill 1.0`, `max_excess 8`, move weights
`mv.resub1 1`, `mv.resub2 2`, `mv.resub3 1`, `dmax 220` (divisors considered), `pdiv 90` (divisors
paired at level 1), `nl_samples 12`, `cand_cap 40`, `fraig 1`. Other switches read by
`kernel/bfx.c`: `skip_noop` (default 1), `neutral`, `odc`, `linear`, `tracemoves=FILE` (every
accepted move, with circuits before and after each improvement):

```bash
python3 nonlinear/boolflux/cli.py run --target maj3 --model xag --objective a,cost --iters 3000 \
    --seeds 1 --jobs 1 --out OUT/maj3t --set tracemoves=OUT/maj3t/moves.txt --set skip_noop=0
python3 nonlinear/boolflux/bench/show_trace.py OUT/maj3t/moves.txt
```

## Checking and placing AES circuits

```bash
python3 nonlinear/boolflux/campaigns/aes_check.py FILE [FILE ...] [--json OUT.json]   # under 1 s per file
python3 nonlinear/boolflux/independent/verify.py FILE --aes --model nonlinear/boolflux/models/nist.json --max-GD 14
python3 nonlinear/boolflux/campaigns/pareto_audit.py [--json OUT.json]    # results/aes vs the pinned set, 10 s
python3 nonlinear/boolflux/campaigns/best_table.py --out DIR [--clean]    # NIST-style tables of all candidates (12 s CPU)
python3 nonlinear/boolflux/campaigns/curate_aes.py --dry-run              # new Pareto points not yet in results/aes
python3 nonlinear/boolflux/campaigns/manifest.py                          # MANIFEST.json + nist-format/ (47 s)
python3 nonlinear/boolflux/campaigns/verify_all.py [--json OUT.json]      # everything (68 s)
```

`best_table.py` without `--out` writes into `~/xs-campaigns/2026-11-13-aes/best/`. It has one
row per (A, AD, G, GD) tuple; the column `other` counts further distinct circuits at that tuple
and `DIR/BEST.json` lists them with their source files, together with candidate files that could
not be read. Circuit files of earlier runs that are no longer in the table are listed, and
removed with `--clean`. `aes_check.py` keeps the metrics of the pinned NIST set in
`~/.cache/boolflux/` (keyed by the bytes of the pinned files and of `independent/verify.py`;
`BOOLFLUX_NO_CACHE=1` recomputes them, which takes about 10 s; `verify_all.py` always does).

## The hub (shared archive and scheduler)

These lines are the command forms used in the 2026-11-14 campaigns, copied from the scripts'
help text and the campaign records. They were not re-run for this page. The design and what was
measured are in [hub/SPEC.md](hub/SPEC.md) and [DESIGN.md](DESIGN.md).

```bash
bash nonlinear/boolflux/hub/seedlist.sh SEEDS.list                     # every verified circuit file we have
python3 nonlinear/boolflux/hub/scheduler.py --dir CAMPAIGN --cpus 4,5,6,7 --hours 1 \
    --seed-list SEEDS.list --ops polish,pull,join,trb \
    --seconds polish=90,pull=90,join=60,trb=30 --eps 0.25 --seed 1     # options also: --nursery P, --near P, --seed-only
python3 nonlinear/boolflux/hub/op_polish.py --archive CAMPAIGN --in ID --caps A,AD,GD \
    --objective KEYS --seed S --seconds T --out JOBDIR                 # one operator job; op_pull, op_join (--in2), op_trb alike
```

`CAMPAIGN/archive/` holds every admitted circuit (`<id>.bfx`, `<id>.json`), `front.json` the
current front, `runs/<run_id>.json` one record per job, `stats.jsonl` one line per job, and
`control.json` is re-read while the scheduler runs (operator list, registered operator
scripts, shares). Launch long runs through `~/xs-campaigns/guard/xsrun`, one busy process per
CPU. To judge a hub directory use `strategies/L1/eval_run.py` (frontier admissions by AND
class and goal-near admissions), not the scheduler's own gain figures
(`strategies/L1/WHAT-WORKS.md` finding 1).

## Targeted campaigns: ledger, operators, runner, morning check

The tools of the targeted campaigns of 2026-11-15/16
([results/targets/TARGETS.md](results/targets/TARGETS.md)). They read the target definitions
from a `TARGETS.json` (the campaign's copy is
[results/targets/TARGETS.json](results/targets/TARGETS.json); the live one is
`~/xs-campaigns/2026-11-15-targets/TARGETS.json`).

### The ledger

```bash
python3 nonlinear/boolflux/campaigns/targets/ledger.py baseline        # once: freeze the archive; refuses to overwrite (--force)
python3 nonlinear/boolflux/campaigns/targets/ledger.py run             # any time, idempotent: LEDGER.md + LEDGER.json
python3 nonlinear/boolflux/campaigns/targets/ledger.py curate          # dry run: what would be copied to results/targets/<ID>/
python3 nonlinear/boolflux/campaigns/targets/ledger.py curate --apply  # copy circuits, sidecars and logs/<name>/; never overwrites
python3 nonlinear/boolflux/campaigns/targets/ledger.py snapshot        # once (done 23:56 UTC): the "known-by-23:50" snapshot
```

`LEDGER_OUT=DIR` writes the ledger to DIR instead of the campaign folder; `run --strict` exits 1
when an issue has level FAIL. Night runs in `~/xs-campaigns/2026-11-16-night/<run>/found/` are
scanned as campaign files.

`run` verifies every new or changed file (cached by sha256), classifies each circuit per target,
and prints a `CHANGE` line for every strict or tradeoff Pareto point that is new since the last
run. The 2026-11-15 23:17 UTC run over 4,560 files took 3.6 s with a warm cache. A run with an
empty cache verifies every file (under 1 s each); run it on one CPU (`taskset -c N`, or `~/xs-campaigns/2026-11-15-targets/L0/run_ledger.sh run`
under the memory guard). Output: `LEDGER.md` (summary, per-target frontiers, sidecar audit) and
`LEDGER.json` next to TARGETS.json, plus a copy in `L0/history/`. What every column means is in
[campaigns/targets/README.md](campaigns/targets/README.md). Since the user's rules of 23:50 UTC
the ledger also prints "notable" lines (T03 any G <= 123, T05 any G <= 102, at any GD inside the
hard limits) and shows path certification for information only.

Every circuit an agent saves goes to `~/xs-campaigns/2026-11-15-targets/<agent>/found/<name>.circ.txt`
with a sidecar `<name>.json` in the form of
[campaigns/targets/SIDECAR-TEMPLATE.json](campaigns/targets/SIDECAR-TEMPLATE.json).

### Operators

From 2026-11-16 the campaign methods are operators in `campaigns/targets/ops/`, one file each,
with one contract so that the runner can mix them:

```bash
python3 nonlinear/boolflux/campaigns/targets/ops/<name>.py --in START.circ.txt --target Txx \
    --seed S --seconds T --out DIR [--cpus 1] [operator flags]
```

- the target's limits are read from TARGETS.json; the operator may exceed the caps internally;
- only circuits that pass `aes_check` and are inside the target's hard limits (A, AD) are
  written to DIR, as `<name>-a..-ad..-g..-gd..-<hash>.circ.txt` with a full sidecar (plus `op`,
  `params`, and the parent file with its sha256);
- `DIR/result.json` holds the best per (G, GD), the wall time and the exit status; the process
  exits within T + 60 s, uses one CPU unless `--cpus`, and stays under 2 GB (run it under
  `~/xs-campaigns/guard/xsrun` with `XS_MEM`).

The operators and their own flags, from their help text at 2026-11-16 00:10 UTC (method
descriptions in [HOW-IT-WORKS.md](HOW-IT-WORKS.md), "Methods added in the targeted campaigns";
design notes in `campaigns/targets/ops/NOTES.md`):

| operator | method | own flags | agent |
|---|---|---|---|
| `ops/conjpull.py` | GF(2^8) conjugate + staged pulls | `--conj id\|L:K\|rank:R\|top:N\|all` (list, in order), `--schedule MODE:CAPGD:SECONDS[:rk0\|rk1],...` (modes g gate, m mix, o osc, t trb, k one kernel run; CAPGD may be +N / -N), `--beam B`, `--repair-keep 0\|1`, `--kcfg KEY=VAL` | M2 |
| `ops/rebase.py` | exact re-basing of the last-level product classes, hybrid build at a GD cap, kernel | `--cap D` or `--goal depth\|gates`, `--builds`, `--top`, `--stage-seconds`, `--stages`, `--moves` (GF(4) coordinate variants, AD3), `--relax S` | M3 |
| `ops/bottom.py` | shared rank-1 bottom rebuild under the kept front, A-capped polish | `--cut K`, `--cap D`, `--amax A`, `--iters`, `--pw`, `--T0`, `--polish-seconds`, `--polish-cap-a build\|target` | M3 |
| `ops/satlns.py` | span-pooled SAT LNS (sideways, improving and focus queries) | `--gd D`, `--profile fast\|p1`, `--build-index` (span index of the archive) | M4 |

`rebase.py` and `bottom.py` exit 0 with status `not-applicable` in `result.json` when the start
has no re-basable classes, or no bottom of the required form.
Tested commands from the night (the runner wrote each into the sidecar of every circuit it saved; START, DIR and the seed are per job). Wall time = the job's `wall_s` in the runner log:

- `conjpull` (T05, job conjpull-54, `--seconds 1000`, ran 958 s, wrote 32/7/103/29 at 02:43 UTC):

  ```bash
  python3 nonlinear/boolflux/campaigns/targets/ops/conjpull.py --in ~/xs-campaigns/2026-11-15-targets/P4/found/p4-conj236-a32-ad7-g104-gd28.circ.txt --target T05 --seed 17104 --seconds 1000 --out ~/xs-campaigns/2026-11-16-night/T05/runs/T05/conjpull-54 --schedule g:34:300,t:32:300,m:32:360 --repair-keep alt --conj rank:6
  ```
- `bottom` (T09, job bottom-792, `--seconds 900`, ran 885 s, wrote 39/4/136/12 at 09:37 UTC):

  ```bash
  python3 nonlinear/boolflux/campaigns/targets/ops/bottom.py --in nonlinear/nist/aes-sbox/aes-sbox-a45-ad4-g141-gd12-xx96-25.circ.txt --target T09 --seed 750849 --seconds 900 --out ~/xs-campaigns/2026-11-16-night/T09/runs/T09/bottom-792 --pw 3 --polish-seconds 300
  ```
- `rebase` (T08, job rebase-732, `--seconds 900`, ran 877 s, wrote 35/3/166/13 at 08:56 UTC):

  ```bash
  python3 nonlinear/boolflux/campaigns/targets/ops/rebase.py --in ~/xs-campaigns/2026-11-15-targets/M3/found/rebase-a35-ad3-g167-gd13-6e861fc3c8.circ.txt --target T08 --seed 505694 --seconds 900 --out ~/xs-campaigns/2026-11-16-night/T08/runs/T08/rebase-732 --cap 13 --stages 1 --stage-seconds 200
  ```
- `satlns` (T03, job satlns-151, `--seconds 1200`, ran 1199 s, wrote 28/5/127/22 at 03:54 UTC):

  ```bash
  python3 nonlinear/boolflux/campaigns/targets/ops/satlns.py --in ~/xs-campaigns/2026-11-16-night/T03/found/conjpull-a28-ad5-g128-gd21-d20fd9235a.circ.txt --target T03 --seed 725371 --seconds 1200 --out ~/xs-campaigns/2026-11-16-night/T03/runs/T03/satlns-151 --polish-every 40 --polish-sec 10 --no-index-update --gd 22
  ```

Validation before the night (ops/NOTES.md): conjpull T04 smoke 70 s (126@26 -> 116@20); rebase 35/3/181/12 in 258 s from P6's coordinate variant; bottom 41/4/136/12 at 880 s from NIST 45@12; satlns 28/5/129/19 in 3 of 4 runs of 900 s.

### The overnight runner

`campaigns/targets/runner.py` (agent M2) runs a plan of sequential blocks, one target per block
on all listed CPUs, one job per CPU, each job through `guard/xsrun`:

```bash
python3 nonlinear/boolflux/campaigns/targets/runner.py --plan PLAN.json --check          # validate the plan
~/xs-campaigns/guard/xsrun P 0-19 night-runner ~/xs-campaigns/2026-11-16-night/runner.log -- \
    python3 nonlinear/boolflux/campaigns/targets/runner.py --plan PLAN.json              # unattended, one unit
systemctl --user stop xs-P-night-runner                                                  # stop; jobs end by their --seconds
python3 nonlinear/boolflux/campaigns/targets/runner.py --plan PLAN.json --stop-jobs      # stop the jobs at once
```

A block names its target, minutes, starts (`ref`, `ledger:frontier_G_GD:N`, `found:N`, files or
globs) and operators (CPUs, job seconds, flags, a grid of alternatives, rechaining of new frontier
points), plus early-stop rules; the plan has a hard `deadline_utc`. Results go to
`ROOT/<Txx>/found/` after a second `aes_check` and the hard-limit filter; the runner keeps
`ROOT/STATUS.md` and `ROOT/STATE.json` (a restart resumes from it, `--fresh` ignores it) and
runs `ledger.py run` after each block. The full plan format is the runner's docstring.

The plans run on 2026-11-16:

`~/xs-campaigns/2026-11-16-night/plan.json` (night-2026-11-16, deadline 2026-11-16T13:30:00Z, CPUs 0-19, carry `flagged`, at most 2 jobs per start; copied by morning.sh to `results/targets/night-2026-11-16/`):

| block | target | minutes | early stop (first / stall min) | operators: CPUs x job seconds |
|---|---|---|---|---|
| T05 | T05 | 90 | 45 / 40 | conjpull 8 x 1500 s, conjpull 6 x 1100 s, conjpull 6 x 1000 s |
| T03 | T03 | 120 | 45 / 40 | conjpull 5 x 1700 s, conjpull 4 x 960 s, conjpull 4 x 1300 s, conjpull 3 x 1000 s, satlns 4 x 1200 s |
| T01 | T01 | 60 | 45 / 40 | conjpull 8 x 1500 s, conjpull 2 x 660 s, conjpull 6 x 1300 s, conjpull 4 x 1100 s |
| T06 | T06 | 60 | 45 / 40 | conjpull 20 x 660 s |
| T10 | T10 | 15 | 45 / 40 | conjpull 20 x 450 s |
| T07 | T07 | 110 | 30 / 40 | conjpull 14 x 640 s, conjpull 6 x 280 s |
| T04 | T04 | 75 | 30 / 40 | conjpull 8 x 1260 s, conjpull 8 x 1000 s, satlns 4 x 1200 s |
| T08 | T08 | 70 | 30 / 40 | rebase 20 x 900 s |
| T09 | T09 | 45 | 30 / 40 | bottom 16 x 900 s, conjpull 4 x 450 s |
| T02 | T02 | 30 | 30 / 40 | conjpull 12 x 1300 s, conjpull 8 x 900 s |

`~/xs-campaigns/2026-11-16-night/plan2.json` (night-2026-11-16-pass2, deadline 2026-11-16T13:20:00Z, CPUs 0-19, carry `next`, at most 2 jobs per start; copied by morning.sh to `results/targets/night-2026-11-16/`):

| block | target | minutes | early stop (first / stall min) | operators: CPUs x job seconds |
|---|---|---|---|---|
| p2-T05 | T05 | 55 | 30 / 40 | conjpull 8 x 1000 s, conjpull 6 x 1300 s, conjpull 6 x 1100 s |
| p2-T07 | T07 | 42 | 30 / 40 | conjpull 8 x 640 s, conjpull 12 x 280 s |
| p2-T06 | T06 | 32 | 45 / 40 | conjpull 12 x 900 s, conjpull 8 x 700 s |
| p2-T04 | T04 | 28 | 30 / 40 | conjpull 12 x 1000 s, conjpull 4 x 280 s, satlns 4 x 1200 s |
| p2-T03 | T03 | 15 | 45 / 40 | conjpull 20 x 900 s |

Generator scripts: `~/xs-campaigns/2026-11-16-night/mkplan.py` and `mkplan2.py`; the second pass was started by `chain2.sh` when the first runner unit exited.

### The morning check

One command (agent L1) after all runs have stopped; it never commits or pushes:

```bash
bash nonlinear/boolflux/campaigns/targets/morning.sh              # in this worktree
bash nonlinear/boolflux/campaigns/targets/morning.sh --dry-run    # the same on a copy; nothing here changes
```

Steps, each logged and timed: `ledger.py run`; `ledger.py curate --apply`; copy the campaign
record (LEDGER.md/json, briefs, TARGETS.json, the request, the night folder's summaries) into
`results/targets/`; `curate_aes.py` and `manifest.py` (target and night circuits enter
`results/aes/` as `aes-nist-targets-<agent>-t<NN>-...` / `aes-nist-night-<run>-t<NN>-...`, with
the target's A and AD as caps); `best_table.py --md results/BEST.md`; `verify_all.py`;
`aes_check.py results/targets/*/*.circ.txt`; the unit tests. Exit status 0 only if every step
passed. Environment: `MORNING_CPU` (default 18), `XS_MEM` (default 4G), `MORNING_TESTS=0` skips
the tests. Morning run 2026-11-16 13:23 UTC: all steps OK, 199 s in total (log `~/xs-campaigns/2026-11-15-targets/L1/morning-20261116T131944Z/`). Steps: a-ledger 4 s, b-curate 4 s, c-record 0 s, e1-curate-aes 9 s, e2-manifest 31 s, d-best-table 8 s, f1-verify-all 62 s, f2-best-vs-manifest 0 s, f3-tests 81 s.

## Output

```
OUT/
  summary.json          command, settings, caps, seeds, code_sha256_12, every job (seed, kernel_seed,
                        improvements with time and iteration, moves, wall time), best (verifier verdicts)
  best.circ.txt         the best circuit (NCFF; header: command, code hash, origin; CAPS NOT MET if infeasible)
  src/, bin/            the sources this run used and the kernels built from them
  r<R>-s<S>.cfg/.log    kernel configuration and log of round R, seed S
  r<R>-s<S>.start.bfx / .best.bfx   start and best of that job (kernel text format)
  s<S>/                 (flow) per-seed working folder, incumbent.bfx
```

NCFF files carry a `% Tally:` comment (`G A GD AD` and counts by type). In `nist` files a NOT is
written `XNOR t a 0`. The NIST-format copies in `results/nist-format/` write it as `NOT`.

## Tests

```bash
python3 -m unittest discover -s nonlinear/boolflux/tests -t nonlinear      # 33 tests, ~110 s on one CPU
python3 -m unittest discover -s nonlinear/boolflux/independent             # 36 tests, 6 s
```
