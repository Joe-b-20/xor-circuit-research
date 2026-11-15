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
