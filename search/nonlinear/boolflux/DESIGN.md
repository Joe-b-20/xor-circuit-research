# BoolFlux design

One search method for small circuits of complete multi-output Boolean functions (S-boxes and
other functions of up to about 16 inputs) over a configurable gate library, cost model,
objective and hard caps. This file is the developer reference: what each part does and the
contract it follows. Read it before editing code; the user guide is
[USAGE.md](../USAGE.md) and the method overview [HOW-IT-WORKS.md](../HOW-IT-WORKS.md).

## 1. What the evidence says

The decisions below rest on the benchmark study, the AES runs and the hub runs of 2026-11-13 to
11-16 ([HISTORY.md](../HISTORY.md)). Tuples are A/AD/G/GD for the AES S-box, NIST model.

| Finding | Number | Decision |
|---|---|---|
| an approximate state can hide a wrong circuit | no saved circuit was ever wrong with complete truth tables | complete truth tables, exact care sets |
| a non-lexicographic cap penalty let an infeasible best replace a feasible one | review 1 | one rank, feasibility first, used by kernel, CLI and workflows |
| rebuilding from a skeleton cost gates even when unchanged | +31 to +72 gates | rebuild seeded with the parent circuit (+0) |
| skeleton moves on good AES circuits | input returned in 11 of 12 cases; one move costs +12 to +42 gates | skeleton search only for AND reduction (small functions) |
| mature circuits are fixed points of the kernel | 0 of 138 polishes of seeds improved | operators that hand the kernel new starts (pull, join, conjugate, re-base, rebuilt bottom) |
| joins pay in new starts, not steady yield | 17 against 3 frontier points in 4.7 CPU-h; all 26 join admissions in the first 8.6 min | join is an operator; repeat joins on one target are not scheduled heavily |
| the hub's gain is not a value signal | 51 of 75 admissions scored "lowers A", none lowered a class minimum | judge runs by frontier admissions per AND class |
| an old command does not replay under a new default | the no-op filter changes the trajectory | every run folder keeps settings, sources and binaries |

## 2. The method

Each job runs one **chain** in the gate kernel: a correct circuit that every move edits. A move
replaces one signal by 0 to 3 new gates equal to it on its care set; the result is rebuilt,
ranked and kept or undone ([HOW-IT-WORKS.md](../HOW-IT-WORKS.md)).

```
start (anf | NIST | own) ─► repair if a cap is broken ─► chain
                                                          │
             ┌──── pick gate s, care set, divisors ◄──────┤
             ▼                                            │
      candidates (levels 0-3, depth-feasible) ─► rebuild ─► rank ─► accept? ─ no ─► undo
                                                                     │ yes
                                                                     ▼
                                               new best? ─► write best; stall ─► back to best
```

Around the kernel: `pipe` alternates skeleton search, seeded synthesis and gate search; `flow`
runs time-sliced workflows; the hub keeps a shared archive and schedules operators; the method
scripts (conjugation, re-basing, shared bottom, SAT LNS) build new starts and call the kernel.

## 3. Package layout

Targets come from `targets.py` (built-in functions, `benchmarks/sboxes.json`, and linear maps
of `circuits/`). Next to the package, in `search/nonlinear/`: `seeds/` (NIST's AES S-box circuits,
verbatim, with `MANIFEST.json`, `PIN.md`, `import_nist.py` and `refresh.py`) and `campaigns/`
(the small-S-box and depth campaign scripts).

```
boolflux/
  cli.py                      commands: run, pipe, flow, verify, start, list
  core.py                     Circuit, Model, bitsliced evaluation, metrics, NCFF and .bfx formats (verifier 1)
  objective.py                objective keys, the shared rank, cap and path excess
  workflow.py                 kernel configs, kernel seeds, the time-sliced workflows of `flow` and bench/
  skeleton.py                 AND skeleton: extraction, kernel format, synthesis back to gates
  starts.py                   naive starts from a value table (anf, anf-or)
  targets.py                  targets: AES and its inverse from FIPS-197, small S-boxes, GF(2^4), maj3, fulladd, map:<name>
  aes_check.py                both verifiers, then placement against the pinned NIST set (S-box or inverse)
  aesfn.py                    the AES function of the AES tools: aes-sbox or aes-invsbox ($BOOLFLUX_FUNCTION), its NIST set
  runlog.py                   run records (run.json, events.jsonl.gz), kernel build records, GNU time / taskset fallbacks
  kernel/bfx.c, skel.c        the gate kernel and the skeleton kernel (C, built on first use)
  models/*.json               nist, bgc, gc6, gc, xag, xor
  benchmarks/                 sboxes.json (S-box tables with sources); LITERATURE.md (published sizes, by gate library)
  independent/                verify.py, the second verifier (no shared code), and its tests
  hub/                        archive, function bank, operators, scheduler, A/B tools, tests
  hub/ops/                    further hub operators (osc, gen_skel, gen_inv3, gen_bottom, gen_joinplus, linres, and_merge, gf4move) and their libraries (depth_lib/, and_merge_lib/, gf4_lib/)
  ops/                        method scripts: conjpull, rebase, bottom, satlns; common.py (the shared contract), rebuild_common.py (rebase and bottom); conj_lib/, rebase_lib/, bottom_lib/ (their libraries)
  bench/                      the 2026-11-13 benchmark study: driver, plans, analysis, ABC comparison, REPORT.md
  tests/                      tests: core and skeleton, kernel, formats and CLI, costs and models, objectives and workflows, every Boolean circuit of circuits/
```

## 4. Interfaces

### 4.1 Circuits and formats (`core.py`)

`Circuit(n, m, gates, outputs)`: `gates` is a list of `(op, a, b)` with `op` the 4-bit truth table
(`f(a,b) = (op >> ((a<<1)|b)) & 1`: AND 8, OR 14, XOR 6, XNOR 9, NAND 7, NOR 1, ANDN 4 (a & ~b),
ORN 13 (a | ~b), NOT 3 (unary, `b == a`)); signals `0..n-1` are inputs, `n+j` is gate `j`, and
operands are smaller signal numbers. Bit order is msb/msb: input `i` is bit `n-1-i` of the input
integer, output `j` bit `m-1-j` of the output.

| Function | Meaning |
|---|---|
| `tables()`, `output_tables()`, `value_table()` | bitsliced evaluation: one integer of `2^n` bits per signal |
| `metrics(model)` | G, A, GD, AD, cost, counts by type |
| `live()` | the circuit without dead gates |
| `read_ncff(path)`, `write_ncff(c, model, comments)` | NIST circuit format (`.circ.txt`); in `nist` files a NOT is written `XNOR t a 0` |
| `to_kernel(c)`, `from_kernel(text)` | the kernel's text format `.bfx`: `n N` / `m M` / `g G` / G lines `op a b` / `o s_0 ... s_{M-1}` |
| `Model.load(name_or_path)` | a model from `models/<name>.json` or a path |

A **model** is `{"name", "gates": {"AND": 1, "XOR": 1, ...}, "description"}`; fractional costs
work; `"not_as": "XNOR0"` makes NOT count and print as `XNOR t a 0` (the `nist` model).

### 4.2 Objective and rank (`objective.py`)

An objective is up to three of `cost, g, a, gd, ad`. Every component ranks a circuit as

```
(0 if every cap holds else 1, total cap excess, summed path excess, key 1, key 2, key 3)
```

The kernel gets the same order as `lex`; the weighted sum of the keys (weights 1, 1e-4, 1e-8)
only sizes a Metropolis step. `excess(metrics, caps)` and `measure()` compute the excess terms
exactly as the kernel does, so a repair that shortens too-deep paths before the maximum drops
counts as progress everywhere.

### 4.3 Gate kernel (`kernel/bfx.c`)

`bfx CONFIG` reads `key value` lines; `bfx --stats FILE` prints a circuit's metrics. The kernel
state is always a correct circuit. A move picks a gate `s`, computes its exact care set from one
re-simulation of its fanout cone, collects divisors (signals outside that cone), and searches:

| Level | Form | Search |
|---|---|---|
| 0 | an existing divisor | scan |
| 1 | `op(d1, d2)`, `NOT d` | all pairs of up to `pdiv` divisors, every library op and orientation |
| 2 | `XOR/XNOR(op(d1, d2), d3)` | hash table of the level-1 values, one lookup per `d3` |
| 2 | `op2(op(d1, d2), d3)`, op2 nonlinear | sampled `d3` and op2; the target for `op(d1, d2)` is derived lane by lane |
| 3 | `XOR/XNOR(op(d1, d2), op'(d3, d4))` | hash lookups over the level-1 table |

Candidates respect the depth caps exactly. Each is rebuilt (dead-gate sweep, structural hashing,
merge of gates with equal complete functions) and ranked; acceptance is the best strict
improvement, else a random equal candidate, else a Metropolis step on a sawtooth temperature
bounded by `max_excess`. After `stall_it` iterations without a new best the chain returns to it.
Every accepted circuit is re-simulated on all inputs; a mismatch aborts the kernel.

| Key | Default | Meaning |
|---|---|---|
| `T0`, `Tperiod_it` | 0.6, 20000 | sawtooth temperature: start value and period in iterations |
| `stall_it` | 60000 | iterations without a new best before returning to it |
| `uphill`, `max_excess` | 1.0, 8 | Metropolis scale; largest step above the best |
| `mv.resub1`, `mv.resub2`, `mv.resub3` | 1, 2, 1 | weights of the level-1, -2, -3 searches |
| `dmax`, `pdiv`, `nl_samples`, `cand_cap` | 220, 90, 12, 40 | divisors considered, paired at level 1, nonlinear samples, candidates kept |
| `fraig` | 1 | merge gates with identical complete functions |
| `skip_noop` | 1 | skip moves that leave the circuit structurally unchanged |
| `repair_keep` | 0 | 1: during a repair, no move may raise the excess of any single cap |
| `neutral`, `odc`, `linear` | | ablation switches; `linear` is the exact mode for XOR-only libraries |
| `tracemoves` | | file: every accepted move, with circuits before and after each improvement |
| `stats_every_it`, `stats_every_s` | 0 | a `kstat periodic` line every N iterations / S seconds |
| `kstat_time` | 0 | 1: `kstat time` lines, seconds per phase of a move |
| `keep_bests` | | directory: every new best also written to `best-<k>.bfx` (the hub's polish / pull pass `JOBDIR/bests`) |

After its old end lines the kernel always prints `kstat` lines (counters only; the search is identical with
or without them, `tests/test_instrumentation.py`): stop reason and timing, acceptance branches, candidate forms
and fates per move kind, target strata, nominal vs actual cost change, plateau walk size, three clocks.
`runlog.kernel_stats()` / `kernel_summary()` read them; the full list is in the 2026-11-16 instrumentation notes
(`INSTRUMENTATION.md` of that campaign) and in the comments above each counter in `bfx.c`.
| `cap.gd`, `cap.ad`, `cap.a`, `cost.<op>`, `w.*`, `lex` | | caps, model costs and the objective (written by `workflow.py`) |

The defaults are `workflow.DEFAULTS`; `--set key=value` changes them.

### 4.4 Skeleton kernel (`kernel/skel.c`, `skeleton.py`)

A skeleton is K products `g_k = L_k * R_k` of affine forms over `(1, x, g_<k)` with every output
in the GF(2) span of `(1, x, g)`. Every nonlinear two-input gate is `((a^p) & (b^q)) ^ r`, so any
circuit maps to a skeleton with K = A (`skeleton.extract`). Moves: *swap* a leaf product for one
equal to it modulo the span of the rest, *merge* two leaves into one product (K − 1), *split*
(K + 1, a kick), *perturb*; each is checked by Gaussian elimination over complete truth tables.
The objective is `K + w.lin * E`, E an unshared XOR count. `skeleton.synthesize` turns a
skeleton back into gates (Paar-style greedy, incremental), seeded with the parent circuit so an
unchanged skeleton rebuilds to exactly the parent. Defaults: `workflow.SKEL_DEFAULTS`
(`w.lin 0.02`, `T0 0.3`, `Tperiod_it 4000`, `mv.swap 4`, `mv.merge 3`, `mv.split 1`,
`mv.perturb 1`); `--skel-set` changes them.

### 4.5 Run folders (`cli.py`, `workflow.py`)

Every `run`, `pipe` and `flow` writes `summary.json` (command, settings, caps, seeds, code hash
`code_sha256_12`, every job's improvements with time and iteration), `best.circ.txt`, `src/` and
`bin/` (the sources used and the kernels built from them), and per job `r<R>-s<S>.cfg`, `.log`,
`.start.bfx`, `.best.bfx`. The kernel seed of seed S in round R is `S + R·2^32`
(`workflow.kernel_seed`). A run that its iteration budget ends is deterministic for its seed,
settings and code version; time-budgeted runs are not.

### 4.5a Run records (`runlog.py`)

Every entry point (`cli.py run/pipe/flow`, the hub scheduler and each operator job, the method
scripts through `ops/common.Recorder`, `bench/bench.py`) makes one `RunLog`: `run.json` (command
line, git commit and dirty state with the diff saved, `sources_sha256`, seeds, resolved config,
starts with sha256, budget, kernel binaries with sha256 and compiler, host, tools, timing, status)
and `events.jsonl.gz` (every improvement with time, metrics and operator; kernel calls with their
seeds). Each event is one gzip member written by one `O_APPEND` write, so forked workers share
the file and a killed run keeps what it wrote. Overhead: about 0.3 s per process (`git diff`, a hash of the
package sources, tool versions), one write per event. `runlog.measured` and `runlog.pin` replace GNU time
(`os.wait4` `ru_maxrss`) and taskset (`os.sched_setaffinity`) when they are missing; the record
says which was used. Fields: [USAGE.md](../USAGE.md#run-logs).

Decision logs (2026-11-16): the scheduler records every launch decision (bandit state, epsilon draw, target
pool sizes after each filter), idle CPUs with the reason, admission reasons, process timing from `os.wait4`,
5-minute summaries and `host.jsonl`; operators record kernel summaries, join / trb outcome counters, the archive
state they loaded and monotonic timing; conjpull records the screen, every stage with its improvements and AND
profile, and why loops ended. `$BOOLFLUX_LINEAGE` (a file) turns on a shared lineage log with NIST roots;
`$BOOLFLUX_FILTER_AUDIT=1` compares the operators' raw placement filter with the cleaned circuits.

### 4.6 Hub (`hub/`)

| Part | File | Contract |
|---|---|---|
| archive | `archive.py` | `archive/<id>.bfx` and `<id>.json` (id, metrics, counts, parents, operator, settings, seed, run id, code version, CPU and wall time, admission time); kept per cell (A, AD, GD) with the fewest G, up to 4 distinct circuits; `cells.json`, `front.json`. A dominated circuit enters its cell only within 6 gates of a dominating front point (40 for a generator's product) |
| admission | `common.py` | both verifiers on all inputs, model library, metrics agree; nothing unverified enters |
| function bank | `funcbank.py` | every distinct signal truth table with its cheapest known levels and cone AND count, tagged with interface functions (N, N^-1, N + N^-1, the outputs) |
| operators | `op_*.py`, `ops.py`, `join.py`, `trb_impl.py`, `ops/` | separate programs: `--archive --in ID [--in2 ID] --caps A,AD,GD --objective KEYS --seed S --seconds T --out DIR`; they write candidates and `record.json` and never admit |
| scheduler | `scheduler.py` | one pinned worker per CPU; epsilon-greedy choice of operator on recent frontier gain per CPU second; `control.json` re-read while running, every change logged in `events.jsonl` |
| records | `runs/<run_id>.json`, `stats.jsonl` | one record per job: code version, kernel hash, seed, settings, parents, timing, outcome, the job's run record (`jobs/<run_id>/run.json`); `sessions/<UTC>-<pid>/run.json` per scheduler start |
| function | `--function`, `campaign.json` | `aes-sbox` or `aes-invsbox` (aesfn.py), inherited by the operators through `$BOOLFLUX_FUNCTION` |

### 4.7 Method scripts

`ops/<name>.py --in START --target REF --seed S --seconds T --out DIR [--cpus N] [flags]`.
`REF` is a reference circuit (a path, or a file name in `seeds/aes-sbox/` or `seeds/aes-invsbox/`) or an id in
`$BOOLFLUX_TARGETS_JSON`; its A and AD are hard limits on what is written, its G and GD the point to
beat (`common.target`, `common.limits`). Search states may pass above every cap. `common.Recorder`
writes a circuit only after `aes_check.check` accepts it and it is inside the limits, with a
sidecar (start and sha256, method, command, seed, elapsed time, code version), and keeps
`DIR/result.json` (best per (G, GD), wall time, status) up to date; a script exits within
T + 60 s.

| Script | Method | Libraries |
|---|---|---|
| `conjpull.py` | screen the 2,040 conjugates `x -> λ x^(2^k)` by a proxy cost (heuristic top, Paar bottom), build the chosen ones (Boyar–Peralta top, timing-driven bottom), then a schedule of kernel stages at loosening-then-tightening GD caps; for the inverse S-box the input map is `Lin y + c_L` (Lin = A G A⁻¹) and the output map G′ (`conj.maps`) | `conj_lib/` (conj, conj3, bottom, bp, slp, trb) |
| `rebase.py` | enumerate the 840 bases of each last-level product class, price each output by its Kraft sum, keep the per-output Pareto sets, pick the best combination exactly, build a depth-feasible hybrid circuit, polish under the cap | `rebase_lib/` (botbasis, gbasis, hybrid, ...), `hub/ops/gf4_lib/` for `--moves` |
| `bottom.py` | anneal per-output rank-1 decompositions of the last AND level with an exact depth check, build (kept front, Y-sums, x-forms, products, shared pairs, Huffman output trees), polish under cap A | `bottom_lib/` (bopt, bbuild, bsel, botclass) |
| `satlns.py` | pool the gates of every indexed circuit with the start's AND span as templates, encode availability by level in SAT (glucose4), LNS with sideways (K = G), improving (K = G − 1) and focus queries | `python-sat` |

## 5. Verification

| Check | Where | What |
|---|---|---|
| kernel guard | `kernel/bfx.c` | every accepted circuit re-simulated on all inputs; a mismatch aborts (a bug guard, not a verifier) |
| verifier 1 | `core.py` | bitsliced evaluation against `targets.py` (AES from FIPS-197, small S-boxes from `benchmarks/sboxes.json`) |
| verifier 2 | `independent/verify.py` | one input at a time, its own parser, its own FIPS-197 table, library and cap checks; imports nothing from BoolFlux |
| agreement | `cli.verify_file` | both accept, the library holds, the caps hold, and G, A, GD, AD, cost and counts are equal |
| placement | `aes_check.py` | both verifiers, then dominance against every circuit of the same function (S-box or inverse, `aesfn.py`) in the pinned NIST set, by recomputed metrics |

`cli.py verify`, the hub's admission and every method script use `cli.verify_file` or
`aes_check.check`.

## 6. Code rules

- Python ≥ 3.11, standard library only (`ops/conjpull.py` also needs `numpy` and `python-sat`,
  `ops/satlns.py` `python-sat`); the C kernels are built with gcc on first use, one private copy
  per run folder. GNU time and taskset are optional (`runlog.measured`, `runlog.pin`).
- Every search run writes a run record (`runlog.RunLog`); a new entry point makes one too.
- Correctness is exact: complete truth tables everywhere; nothing is admitted, written as a
  result or compared before both verifiers accept it.
- One rank (`objective.py`) for every component; a new objective key goes there first.
- Iteration budgets bound kernel runs by default so they replay; anything time-budgeted is a
  one-off and says so.
- A default that changes the random trajectory is a change of the record: say so in
  `summary.json` and keep the old behaviour behind a setting.
- Every change to the kernel is checked against the regression tests in `tests/`.
