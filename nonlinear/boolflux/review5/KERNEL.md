# Review 5: gate kernel (`nonlinear/boolflux/kernel/bfx.c`), agent C1, 2026-11-15

Scope: every line of `kernel/bfx.c` (896 lines at f9fe6f7, 1127 now) and how it is built and called
(`cli.py`, `workflow.py`, `hub/ops.py`). Not redone: what reviews 3 and 4 fixed (lexicographic
ranking, structural no-op filter, start clean-up line, cost scale, exact cost printing, first-key
Metropolis step).

Labels: [C] = proved by a test, or exhaustive within the case stated next to it; [H] = measured on
the stated runs, or judgement.

Tests: `tests/test_review5_kernel.py` (15 tests; they drive the kernel binary with hand-written
configs). Kernel commits on `boolflux-review5`: 695a90b (K1-K3), 764ac97 (P1-P3), d221d2b (K4, S1,
S2, sweep), 162953b (S3, bench script), and the commit that adds this file.

Campaign directory (scripts, logs, scan results): `~/xs-campaigns/2026-11-15-study/C1/`.

## Summary

| # | kind | severity | finding | default behaviour |
|---|---|---|---|---|
| K1 | bug | medium | config reader: a one-word comment line swallowed the next line; `cost.N` / `gdw.N` with N outside 0..15 wrote past the op tables; unknown `mv.*` names were ignored; `--stats` without a file crashed | fixed; valid configs read the same |
| K2 | bug | low (latent) | with `cand_cap` > 1024 only the first 1024 kept candidates were evaluated | fixed; no effect at the shipped `cand_cap 40` |
| K3 | bug | low | `trace` printed costs with 4 decimals and `tracemoves` with 2 (review 4 m3 fixed only the log lines) | fixed |
| K4 | missed clean-up | low | fraig merges a signal only into an EARLIER equal signal that is not deeper; when the earlier one is the deeper one nothing is merged (0.2-2 % of candidate evaluations) | old rule kept; `fraig 2` merges into the shallower one |
| P1-P3 | speed | - | pair table, structure comparison, fraig levels | same trajectories; about 15-20 % less CPU per iteration [H, noisy CPU] |
| S1 | new move | - | `xspan`: exact test whether a signal is, on its care set, the XOR of any number of other signals; removes the AND of the target cone | off (`mv.xspan 0`) |
| S2 | repair | medium (design) | the violation is the sum of the cap excesses, so a gate-depth repair can end one AND above `cap.a` | old rule kept; `repair_keep 1` forbids raising any single excess |
| S3 | proposals | - | two of three sampled two-gate roots repeat XOR/XNOR roots that were already enumerated exactly | old sampling kept; `nl_root 1` / `2` |

Every option added here is off by default, and `TestTrajectory` checks that the default search is
bit-identical to f9fe6f7 for fixed seeds and iteration counts (four workloads). The same test ran
clean under `-fsanitize=address,undefined` (whole test file, 14 tests at the time).

## Method

- Read `bfx.c` line by line; findings below carry file:line of the current file.
- Fixed workloads with fixed seeds and a fixed iteration count (`iters`, `Tperiod_it`, `stall_it`:
  no wall-clock dependence), so two kernels can be compared on the exact sequence of `best` lines,
  move counters and the result circuit. Workloads (NIST pin 3d80774 starts, hub polish settings):
  a29 polish under its own A/AD caps, a32 cost-first without caps, a32 depth repair
  (GD 30 -> cap 24), a28/AD4 descent, PRESENT from the ANF start (4 inputs, bgc library).
- Timing: all CPUs were busy during this phase (the coordinator confirmed that there was no quiet
  slot); CPU 12 was shared by about five processes. User times for the SAME binary varied by up to
  2x between calls, so the numbers below are minimum-of-N user seconds from interleaved runs on
  CPU 12 and are rough. `review5/bench_kernel.sh` repeats the comparison properly (f9fe6f7 against
  every kernel commit, fixed seeds, one pinned CPU per (workload, seed) group, up to 8 CPUs, 3-5
  minutes) and writes `review5/bench_kernel_results.md`; the coordinator runs it on idle CPUs.
- No hardware counters in this WSL kernel (`perf_event_open` fails), no perf, no valgrind; profile
  by gprof on an `-O2 -pg -fno-inline` build (inflates small functions).

## Bugs

### K1. Config reader (medium)

- **Where.** `parse_config`, `bfx.c:315-384`; `cfg_op`, `bfx.c:310`.
- **What happened.**
  1. The reader took tokens in pairs. For a comment of ONE word (`#note`) the "value" was the first
     word of the next line, and the rest of that line was then skipped as comment text, so
     `#note` / `iters 0` silently dropped `iters 0`. Comments of two or more words worked. The
     Python side writes no comments, so no recorded run is affected [C: code reading; all configs
     are written by `workflow.kernel_cfg`, `cli.kernel_config`, `hub/ops._kernel`].
  2. `cost.99 1` or `gdw.-3 1` indexed `op_ok[]`, `op_cost[]`, `op_gdw[]` outside 0..15 (memory
     overwrite, no message). `--set` cannot reach these keys since review 4, a hand-written config can.
  3. `mv.resub9 1` (unknown move name) was ignored; every other unknown key is an error.
  4. `bfx --stats` without a file name copied a NULL pointer.
  5. A path containing a space was cut at the space.
- **Fix.** One `key value` per line (`fgets`); blank lines and `#` lines skipped; a key without a
  value, an op number outside 0..15, an unknown move, `cand_cap` < 1 and a missing `in`/`out` are
  errors (exit 2); path values are the rest of the line.
- **Tests.** `TestConfigParsing` (6 tests).

### K2. Candidates past the first 1024 were never evaluated (low, latent)

- **Where.** main loop, `bfx.c:1049-1056` (was `static int order[1024], neu[1024], up[1024]`).
- **What happened.** `CAND` is sized by `cand_cap`, the evaluation arrays were fixed at 1024 and
  the loop bound was clamped to 1024, so with `cand_cap` > 1024 the reservoir kept candidates that
  were never looked at. No shipped setting does this (40 everywhere).
- **Fix.** Arrays sized by `cand_cap`. **Test.** `test_cand_cap_bounds`.

### K3. Trace costs rounded (low)

- **Where.** `trace` line `bfx.c:1112`, `tracemoves` lines `bfx.c:1079-1095`.
- **Fix.** `%.10g`, as review 4 did for `start` / `best` / `final`. **Test.** `test_trace_costs_exact`
  (costs 1.5 and 0.123456789).

### K4. fraig misses the merge when the earlier of two equal signals is the deeper one (low)

- **Where.** `fraig`, `bfx.c:826-859`.
- **What happens.** Signals are visited in index order and hashed on their complete truth table.
  A signal `v` equal to an earlier `u` is merged into `u` only if `u` is not deeper (gate depth and
  AND depth). Otherwise nothing happens: `u` is not merged into `v`, and `v` is not entered in the
  table, so a third equal signal is compared with `u` only. The candidate then keeps two gates
  with the same function. Counted on the 2000-iteration workloads: 67-457 of 21,000-39,000
  candidate evaluations (0.2-2 %) [C: counter in a debug build, `C1/dbg1.py`].
- **Why the reverse merge is safe.** If `u` is strictly deeper than `v` in gate depth or in AND
  depth, `v` cannot depend on `u` (both depths never decrease along a path), so replacing `u` by
  `v` cannot make a cycle; `rebuild` checks for cycles anyway. It is done only when `v` is not
  deeper than `u` in BOTH measures, so no depth grows.
- **Fix.** `fraig 2`: merge into whichever is not deeper in both; signals with incomparable depths
  are all kept as representatives. `fraig 1` (default) is the old rule, because the effect on
  results is not clear (E2 below) and the default trajectories are kept.
- **Test.** `test_fraig2_reverse_merge`.

## Investigated and found correct [C: code reading plus the tests named]

- **Acceptance and feasibility** (`bfx.c:1057-1073`). A feasible state is never left for an
  infeasible one (improvement, neutral and uphill branches all require it); in repair mode the
  comparison is violation, then summed path excess, then the keys (`mcmp`, `bfx.c:185`).
- **Incumbent.** `best` is replaced only on a strict `mcmp` improvement and is re-simulated before
  the final write; the output file is written through a temporary file and `rename`, so a killed
  run leaves the last complete best.
- **Care sets** (`tfo_care`, `bfx.c:461`). Exact single-signal observability on all 2^n patterns;
  an unobservable signal gets the empty care set (any divisor replaces it). Every candidate is
  re-simulated and compared with the target (`eval_cand`); none failed in any run of this review,
  including the sanitizer build.
- **0-3 gate resubstitution** (`find_cands`, `bfx.c:614-731`). Level and budget tests are applied to
  the root and to the inner gates; the masked-equality cases of the sampled roots (X free on a lane /
  X forced) are right for both operand orders.
- **Depth and cost** (`levels`, `metrics`, `bfx.c:122-168`). Same numbers as `core.Circuit.metrics`
  and `objective.path_excess` (review 3 checked the agreement; unchanged here).
- **Clean-up** (`rebuild`, `bfx.c:211`). Dead gates dropped, f(x,x) folded (constant -> candidate
  rejected, identity -> wire, complement -> NOT when the library has it), symmetric operands sorted,
  structural hashing. The start clean-up merges structurally duplicate gates: see "Other components".
- **`same_structure`** (`bfx.c:878`). A hash collision cannot produce a false "same" (exact check of
  op and mapped operands after pairing).
- **RNG.** xoshiro256** seeded by splitmix64 from `seed`; seed 0 is fine; the only uses of wall time
  are the stop test and, when `Tperiod_it` / `stall_it` are not set, the schedule.
- **Degenerate circuits.** No gates, outputs that are inputs or repeat, a single NOT, a start that
  simplifies to fewer gates, `g -1`: `test_degenerate_circuits`.
- **Small n.** n < 6 uses one masked word; n = 6 one full word.

Left as it is, with a note:

- **Stall restart** (`bfx.c:1025`). After a stall the search returns to `best`, which is the FIRST
  circuit with the best metrics; plateau moves made since are dropped. Design choice, not changed.
- **Uphill step when the first key is not cost** (review 4 m1). One more AND and one more XOR have the
  same acceptance probability when A is the first key and no `cap.a` is set. The hub always sets
  `cap.a`, so its runs are not affected.
- **Reservoir** (`add_cand`, `bfx.c:547`). Candidates of all levels share one uniform reservoir of
  `cand_cap`, so a zero-gate candidate can be displaced by a three-gate one when more than
  `cand_cap` are found. Not measured.

## Speed (P1-P3): same trajectories

Profile of the f9fe6f7 kernel on the a29 polish workload (gprof): `build_pairs` + `find_cands` and
their helpers (`hval`, `eqc`, `lookup`) about 65 %, candidate evaluation (`rebuild`, `fraig`, `sim`,
`levels`, `metrics`, `same_structure`) about 25-30 %.

- **P1. Pair table** (`bfx.c:504-611`).
  - Each entry keeps a 64-bit digest of its masked value that is GF(2)-linear
    (`ldig(x ^ y) = ldig(x) ^ ldig(y)`, `bfx.c:517`). At level 3 the wanted partner of entry X is
    `GT ^ X`, so its digest is one XOR of stored digests: the 2 x (number of pairs) lookups per
    resub3 move no longer build and hash a 256-bit value each. Probes compare digests before words.
  - Slots carry a build stamp, so the table (64k slots for the AES settings) is not cleared for
    every move; resub1 moves build no table at all.
  - Level-1 matches are found while the table is built (digest of GT, then words), not by a second
    pass over all pairs.
  - The op is chosen once per entry, not once per word (`pair_val`).
  - The sampled-root scan tests the first word from a dense array before touching the entry.
  - Entries with equal values share a digest and so a probe sequence, in which they stay in
    insertion order for any table size; lookups therefore return the same entries in the same order
    as before, which is why the trajectory is unchanged.
- **P2. `same_structure`** (`bfx.c:874-906`). The current circuit's gate hashes, their sum and their
  sorted order are cached until it changes; a candidate with different metrics, a different hash
  sum or a different output hash is "different" before anything is sorted (two `qsort`s per
  candidate before).
- **P3. fraig** computes levels only when two signals have the same function (`bfx.c:841`).

Measured [H] (min of 3-4 interleaved runs, 1000 iterations, CPU 12 under load, `-O3 -march=native`):

| workload | f9fe6f7 user s | 764ac97 user s | ratio |
|---|---|---|---|
| a29 polish | 1.06-1.07 | 0.84-0.95 | 0.79-0.89 |
| a32 cost-first | 1.12 | 0.75-0.94 | 0.67-0.84 |
| a28/AD4 descent | 0.84 | 0.77 | 0.92 |

`-O2` (what `cli.py` builds) and `-O3 -march=native` (what the hub builds) did not differ beyond
the noise for either kernel. Trajectories: identical hashes for all five workloads x 2 seeds at
2000 iterations, plus the golden test.

What is left: `build_pairs` (about 12,000 pair values per move for 90 pair divisors and the NIST
library) and the 20 full candidate evaluations per move (rebuild, simulate, fraig, metrics each).
A larger gain needs incremental evaluation of candidates, which is a redesign and was not tried.

## Search options (all off by default)

None of the options below showed a clear gain as a default, so every one stays off. All runs:
fixed iteration counts, hub polish settings, kernel 162953b, logs in `C1/logs/<tag>/`.

### S1. `xspan`: exact linear-span resubstitution (`mv.xspan W`, `xspan_tries`, `xspan_any`, `sweep`)

- **Where.** `xspan_solve` / `xspan_cands`, `bfx.c:734-815`; chosen like the other moves by weight.
- **What it does.** For the target signal s with care set C: Gaussian elimination over GF(2) on the
  tables (masked by C) of all signals outside the fanout cone and outside the fanout-free cone of
  s, plus the constant, decides exactly whether s = d1 ^ d2 ^ ... ^ dk (^ 1) on C for ANY k. A
  solution replaces s by an XOR tree (smallest arrival first, XNOR or NOT for the constant), so
  every AND of the fanout-free cone of s goes; the move is tried only when that cone holds an AND.
  resub1-3 reach k <= 4 and only inside the cost budget (cone cost + `uphill`), so a 1-AND cone
  never gets a 3-gate XOR replacement from them directly. Divisors respect the AND-depth
  requirement at s; the usual evaluation and acceptance do the rest. `sweep 1` takes the targets
  in index order, so `iters` = number of gates is one exact pass over an unchanged circuit.
- **Tests.** `test_xspan_removes_all_ands_of_a_parity` (18 ANDs -> 0 with xspan alone),
  `test_xspan_complemented_and_caps`, `test_sweep_tests_every_gate_once`.
- **Result 1, exact scan [C].** Case: one signal replaced by an affine combination of signals
  outside its fanout cone and its fanout-free cone, the rest of the circuit unchanged. Within this
  case, no AND can be removed from any of the 194 archive circuits with 28 ANDs
  (`~/xs-campaigns/2026-11-14-hub/long/archive`, after the start clean-up), from the 10 A28
  circuits in `2026-11-14-hub/best/`, or from the 14 NIST A28 circuits (every gate tested, no AD or
  GD restriction; `C1/archscan.py`, `C1/xscan.py`). This says nothing about replacements that
  change more than one signal or add an AND. Fanout-free cones in these circuits hold at most one
  AND (one cone with two in 28/5/127/22; `C1/mffc.py`), so a single-signal replacement with one
  AND instead of two has no target there.
- **Result 2, archive scan [C for the counts].** All 2310 archive circuits, every gate once:

  | mode | circuits that lose >= 1 AND | by start A (hits/scanned) | not dominated by the archive |
  |---|---|---|---|
  | no caps | 242 (1 AND: 168, 2: 58, 3: 14, 4: 2) | 29: 32/133, 33: 38/231, 34: 71/119, 35: 39/264, 36-39: 41/342, 41-60: 21/92; 28, 30, 31, 32, 40: 0 | 0 |
  | AD cap = own AD | 206 | 29: 1/133 (29/4/176/14 -> 28/4/176/15), 33: 38/231, 34: 71/119, 35: 39/264, 36-39: 36/342, 41-60: 21/92 | 0 |

  Three results were checked with `aes_check.py` (OK; none is a new point). Results:
  `C1/scan-free.jsonl`, `C1/scan-ad.jsonl`, circuits in `C1/found/`.
- **Result 3, as a polish move [H].** `mv.xspan 0.3` against the default, 2500 iterations:

  | starts | runs | default: sum of mean final A | with xspan |
  |---|---|---|---|
  | 4 circuits, cap AD only (X1-X4; three have xspan solutions) | 4 seeds each | 127.75 | 127.50 |
  | 6 archive circuits with AD-preserving solutions, own A and AD caps (Y1-Y6) | 3 seeds each | 196.33 | 197.00 |

  The default moves remove the same ANDs within 2500 iterations: the archive circuits with
  solutions are unpolished `join` outputs, not circuits where resub is stuck. So xspan is an exact
  test and a scan tool; as a polish move it shows no gain here and stays off.

### S2. `repair_keep 1`: a repair may not raise the excess of any single cap

- **Where.** `metrics` (`xgd`, `xad`, `xa`, `bfx.c:140-143`), filter in the main loop `bfx.c:1064`.
- **Problem.** `viol` is the sum of the excesses over `cap.gd`, `cap.ad`, `cap.a`, and a smaller
  sum is always "better". A gate-depth repair can therefore pay for one level with one AND above
  `cap.a` and then stay at violation 1, in the cap that is hardest to repair.
- **Measured [H]** (2500 iterations, 6 seeds, runs that end feasible):

  | workload | default | `repair_keep 1` |
  |---|---|---|
  | a32 GD 30 -> cap 24 | 4/6 (the other two end at A 33), mean G 112.3 | 6/6, mean G 112.2 |
  | a28/AD4 GD 31 -> cap 25 | 5/6 (one ends at A 29), mean G 141.4 | 6/6, mean G 141.5 |
  | a29 GD 32 -> cap 24 | 4/6 (two end at A 30), mean G 147.5 | 6/6, mean G 148.0 |
  | a32 AD 7 -> cap 5 (cap A 32) | 1/6 (five end at A 33, AD 5) | 0/6 (all stay at AD 7) |

  First feasible state after 93-294 iterations (default) and 101-317 (`repair_keep`). So it makes
  gate-depth repairs reliable at no cost in G, and it blocks the AND-depth repair, which needs the
  extra AND on the way. Off by default; worth setting for jobs that tighten GD only.
- **Test.** `test_repair_keep_never_raises_a_cap_excess` (also shows the default going to A 33).

### S3. `nl_root`: root op of the sampled two-gate candidates

- **Where.** `find_cands`, `bfx.c:651-663`.
- **Observation.** The block "s = op2(X, d3), sampled" draws op2 uniformly from the binary library.
  XOR and XNOR roots were enumerated exactly just before (all divisors, up to 4 pair matches
  each), so with the NIST library 8 of the 12 samples per move repeat that work and 4 try an AND
  root. `nl_root 1` samples AND-like roots only; `nl_root 2` tries every divisor with every
  AND-like op and orientation (most fail the one-pass feasibility test before the pair scan).
- **Measured [H]** (2000 iterations, 6 seeds, mean final G; all runs feasible, A unchanged):

  | workload | default | `nl_root 1` | `nl_root 2` | `fraig 2` (K4) |
  |---|---|---|---|---|
  | a29 from G 182, caps A29 AD5 GD20 | 177.0 | 178.8 | 178.8 | 177.8 |
  | a30 from G 205, caps A30 AD4 GD20 | 171.3 | 171.2 | 170.3 | 168.5 |
  | a28 from G 177, caps A28 AD4 GD18 | 171.2 | 169.5 | 169.5 | 169.3 |
  | a32 cost-first (NIST 103) | 103.0 | 103.0 | 103.0 | 103.0 |

  Differences of 1-3 gates in both directions with 6 seeds: no clear effect for any of the three.
  All stay off.
- **Test.** `test_nl_root_modes`.

### Not built

- A replacement with ONE new AND for a cone with two or more (s = L ^ (d_i & d_j), products added
  to the span): cones with two ANDs do not occur in the A28-A35 circuits (see Result 1), only in
  the shallow A43-A60 ones.
- Incremental candidate evaluation (see Speed).

## Other components (not edited; for C2, C3 and the coordinator)

- **Archive circuits with a duplicate AND gate** [C]. 172 of the 2310 circuits in
  `~/xs-campaigns/2026-11-14-hub/long/archive` contain two structurally identical AND gates (same
  operands); the kernel's start clean-up merges them, so their true AND count is one below the
  recorded one (for example `1b706c348e80`: recorded 30/4/144/17, cleaned 29/4/143/17). None of the
  cleaned circuits is outside what the archive already dominates. They come from `join` and `trb`
  outputs that are archived without structural hashing (list: `C1/scan-free.jsonl`, records with
  `cleaned[0] < from[0]`).
- **Kernel build.** `cli.build_kernel` (`cli.py:43-47`) compiles in place when the binary is older
  than the source; two processes starting at once both run `gcc -o kernel/bfx`, and one can execute
  a half-written file. `hub/ops.kernel_bin` writes `bfx-<hash>.tmp` and renames, but all builders
  share the one `.tmp` name. A per-process temporary name (`.tmp.<pid>`) and `os.replace` fixes both.
  `cli.py` builds with `-O2`, the hub with `-O3 -march=native`: no measurable difference here, but
  two binaries of one source exist; a `-march=native` binary kept in an archive directory is only
  valid on the same CPU type.
- **Kernel seeds.** `cli.py` uses `seed + 1000 * round`, `workflow.py` `seed * 1000 + round`; with
  the first, (seed 1, round 1) and (seed 1001, round 0) are the same kernel run.

## Files

- `kernel/bfx.c`, `tests/test_review5_kernel.py`, `review5/bench_kernel.sh`, this file.
- `~/xs-campaigns/2026-11-15-study/C1/`: `setup.py` (workloads), `bench.sh`, `tbench.sh`, `eb.sh`,
  `summ.py` (experiments), `golden.py`, `xscan.py`, `archscan.py`, `scansum.py`, `mffc.py`,
  `scan-free.jsonl`, `scan-ad.jsonl`, `found/` (xspan results of the archive scan, kernel format),
  `logs/`, `p1.py` ... `p10.py` (the edits as scripts), `bfx-f9fe6f7.c`.
