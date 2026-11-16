# Using BoolFlux

How to run BoolFlux, check a circuit and read its output. How it works is in
[HOW-IT-WORKS.md](HOW-IT-WORKS.md).

It needs Python 3.11 or newer (standard library only) and gcc; two method scripts also need
`numpy` or `python-sat`. The C kernels are compiled on first use, and each run compiles a private
copy into its output folder. **Run every command from the repository root.** `OUT` is any output
folder. Times are wall times on one CPU of the machine in [HISTORY.md](HISTORY.md#compute).

## Quick start

```bash
python3 search/nonlinear/boolflux/cli.py list                                  # targets, models, objective keys
python3 search/nonlinear/boolflux/cli.py run --target maj3 --model xag --objective a,cost \
    --iters 3000 --seeds 1 --jobs 1 --out OUT/maj3                           # 2 s: 4 gates, 1 AND
python3 search/nonlinear/boolflux/cli.py verify OUT/maj3/best.circ.txt --target maj3 --model xag

python3 -m unittest discover -s search/nonlinear/boolflux/tests -t search/nonlinear       # 75 tests, 2 minutes
python3 -m unittest discover -s search/nonlinear/boolflux/independent                     # 36 tests, 4 s
python3 -m unittest discover -s search/nonlinear/boolflux/hub/tests -t search/nonlinear   # 20 s
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
  ...); and `map:<name>`, a linear map of [circuits/](../../circuits/README.md) with at most 16
  inputs. To add a function, add `{"name", "n", "m", "table", "source"}` to `sboxes.json`. Bit
  order is msb/msb: `x0` is the most significant input bit, `y0` the most significant output bit.
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
| `T0`, `Tperiod_it`, `max_excess` | the sawtooth temperature and the largest step above the best |
| `stall_it` | iterations without a new best before the chain returns to it |
| `skip_noop` | skip structural no-ops (default 1); runs recorded before it was the default replay with `skip_noop=0` |
| `tracemoves=FILE` | every accepted move, with circuits before and after each improvement; `search/nonlinear/boolflux/bench/show_trace.py FILE` prints it |

## Checking and placing AES circuits

```bash
python3 search/nonlinear/boolflux/aes_check.py FILE [FILE ...] [--json OUT.json]   # under 1 s per file
python3 search/nonlinear/boolflux/independent/verify.py FILE --aes --model search/nonlinear/boolflux/models/nist.json
python3 circuits/check.py                                                          # every circuit in circuits/ and seeds/
```

`aes_check.py` runs both verifiers with the NIST library, then compares the circuit's
`(A, AD, G, GD)` with every forward AES S-box circuit of the pinned NIST set in [seeds/](seeds/):
it lists those with all four metrics ≤ (equality counts as dominated, so a circuit equal to
NIST's is not new) and the published best G at the circuit's caps.

## The hub

```bash
ls search/nonlinear/seeds/aes-sbox/*.circ.txt circuits/aes-sbox/*.circ.txt > OUT/seeds.list
python3 search/nonlinear/boolflux/hub/scheduler.py --dir OUT/hub --cpus 2,3 --hours 1 \
    --seed-list OUT/seeds.list --ops polish,pull,join,trb \
    --seconds polish=90,pull=90,join=60,trb=30 --eps 0.25 --seed 1
```

One worker per CPU in `--cpus`. `OUT/hub/archive/` holds every admitted circuit (`<id>.bfx` and
`<id>.json` with its parents, operator, seed and code version), `front.json` the front,
`runs/<run_id>.json` and `stats.jsonl` one record per job; `control.json` is re-read while the
scheduler runs. Each operator is also a program (`hub/op_polish.py --archive OUT/hub --in ID
--caps A,AD,GD --objective KEYS --seed S --seconds T --out JOBDIR`; more in `hub/ops/`). Judge a
run by its frontier admissions per AND count, not by the scheduler's gain figures. `hub/status.py OUT/hub` prints
the operators' jobs, admissions and CPU time and the front points the run produced.

## Method scripts

The four methods of [HOW-IT-WORKS.md](HOW-IT-WORKS.md#moves-around-the-kernel) are scripts in
[boolflux/ops/](boolflux/ops/) with one interface. `--target` is a reference circuit (a path, or a
file name in `seeds/aes-sbox/`): its A and AD are hard limits on every circuit written, its G and
GD the point to beat. Search states may pass above the limits.

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
sidecar `.json` (start and its sha256, method, command, seed, time, code), and `result.json`
(best per (G, GD), wall time, status). Main options: `conjpull.py --conj` (which of the 2,040
conjugates) and `--schedule MODE:CAPGD:SECONDS,...` (the kernel stages); `rebase.py --cap D`
and `--moves`; `bottom.py --cut K` (AND level of the kept front); `satlns.py --gd D` (it pools
the circuits in `circuits/aes-sbox/`, `seeds/aes-sbox/` and `$BOOLFLUX_POOL_DIRS`). Kernel
builds and caches go to `$BOOLFLUX_CACHE` (default `~/.cache/boolflux`).

## Output

```
OUT/
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
