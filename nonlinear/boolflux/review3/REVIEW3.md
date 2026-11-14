# BoolFlux review 3: correctness of objectives, incumbents, selection, cleanup, BUF, timing, logs, benchmark numbers

Branch `boolflux-2026-11-13` at 7637b20, worktree `~/xcr-boolflux`, nothing modified outside
`review3/`, nothing committed. Every reproduction below was run (2 cores, `taskset -c 18,19`)
and its output is in `review3/tmp/*.out`. All commands are run from `~/xcr-boolflux`, as
`bash nonlinear/boolflux/review3/<script>` or `python3 nonlinear/boolflux/review3/<script>`.

Earlier reviews were not taken as given. One "found correct" claim of review 2 is wrong
(review2 m5: "no such case in v1/v2", see M3).

## Summary

| # | severity | area | where | finding | script |
|---|---|---|---|---|---|
| M1 | major | 1, 3 | bfx.c:788, cli.py:194, cli.py:256 | `run` ranks jobs by the kernel's `obj %.6f`; with 3 objective keys the third key (weight 1e-8) is rounded away and ties go to the lower seed: a worse circuit is saved as best | `m1_lex_third_key.sh` |
| M2 | major | 2, 3, CLI | cli.py:426-428, cli.py:411-423 | `pipe` from a start that violates the caps: crashes after round 0 (TypeError); with that fixed, every round restarts from the original start (repair progress discarded) | `m2_pipe_repair_lost.sh` |
| M3 | major | 7, 8 | bench.py:166-173, analyze.py:41-47 | improvements made by the rebuild stage (or the kernel's start clean-up) are never put in the trajectory; analyze.py's "reach target" counts are too low in two published table cells; review2's "no such case" is wrong | `check_bench_data.py` |
| M4 | major | 4, 7, 8 | bfx.c:734 (+ rebuild bfx.c:210) | the `skip_noop` filter misses most no-ops: 81-87 % of accepted moves leave the circuit unchanged up to renumbering; REPORT's "fix" and its trace statistics (15,710 moves "inserted" an AND: 15,131 re-created the same AND) | `m6_noop_filter.sh`, `m6b_trace_counts.sh` |
| M5 | major | 5 | cli.py:110-113 vs verify.py:494-499, core.py:269-271 | an output that is an input, or two equal outputs, is written as BUF; verify.py counts BUF, core does not, so a correct circuit gets `independent_ok False` / "VERIFICATION FAILED" (real case: `map:skinny`) | `m5_buf_counts.py`, `m5_skinny.sh` |
| M6 | major (claims) | 8 | REPORT.md:34, :171, LEDGER.md:157, :163 | REPORT/LEDGER statements that the raw data contradict (repair 1/35 vs 2/35, "~683 in about 2 s" vs 5.3-9.8 s, A41 vs A38) | `check_bench_data.py`, inline commands |
| m1 | minor | 3, 4 | cli.py:331 | `pipe` takes the cheapest synthesis variant by cost only and always replaces the input: caps and objective ignored | `m4_pipe_variant_choice.sh` |
| m2 | minor | 1, 2 | bench.py:141-145, :179 | v3 ranks infeasible variants by objective only; in repair a cheaper, deeper rebuild replaces the repair progress | `m7_rank_infeasible.py` |
| m3 | minor | 4, 7 | bfx.c:673-675; starts.py | the kernel strashes the start silently (AES ANF 1247 -> 1128, joltik naive 72 -> 65, PRINCE 35 -> 34); start metrics and trajectory point 0 are pre-clean-up | inline command |
| m4 | minor | 7 | bfx.c:620, :763-767 | tracemoves `.before` files carry zeroed metrics; before/after files are written on penalised (infeasible) "improvements" too | inline command |
| m5 | minor | 6 | bfx.c:698-699, :775; bench.py:160-166 | logged times are iteration-start times and exclude kernel start-up (5-50 ms); XORFlux times exclude its 0.4-1.5 s start-up | code reading |
| m6 | minor | 2 | bench.py:118-120 | a skeleton stage that runs into the end of the budget discards its rebuilt candidate without comparing it with the incumbent | code reading |
| m7 | minor | 2, 3 | cli.py:258-261, :406-410 | a failed job in round r aborts `run`/`pipe` before anything is written; the best of rounds < r is not saved | code reading |
| m8 | minor | 5 | core.py:159-160, cli.py:106 | `Model.load('nist')` reads the path `nist` if it exists in the cwd: `cli.py verify ... --model nist` run from `nonlinear/` crashes | inline command |
| m9 | minor | 1 | bfx.c:738, cli.py:148 | latent: a third key with fractional costs < 0.1 changes obj by < 1e-9 and is treated as neutral (no shipped model affected) | code reading |
| m10 | minor | 8 | analyze.py:51-59, :125-126 | "best-so-far" and "best" columns minimise cost whatever the objective (wrong for `a,cost` rows) | code reading |
| m11 | minor | 8 | REPORT.md:16, :166, :202, REPRODUCE.md | small wording/number mismatches; v3/v4 plans not in REPRODUCE, v4 not producible by make_plan.py | inline |
| m12 | minor | CLI | cli.py:314-316 | `--set skel.iters=N` is silently overwritten by `--skel-iters` | code reading |

No shipped result in `results/` is affected by M1 (all objectives there have at most two keys;
`results/MANIFEST.json`: `cost,gd` 50, `cost` 47, `a,cost` 5), and none by M2 (no `pipe` result
started outside its caps). M5 affects no AES result (none has a BUF).

---

## Major findings

### M1. Third objective key ignored when `run` picks the best job

- **Where.** The kernel prints `final ... obj %.6f` (`bfx.c:788`). `cli.parse_kernel_log`
  reads that string (`cli.py:194`). `cmd_run` sorts jobs by `(final obj, seed)` (`cli.py:256`)
  and keeps `results[0]` as the round's best and as `pool[0]` (`cli.py:263-271`).
- **What happens.** `objective_weights` gives weights 1, 1e-4, 1e-8 (`cli.py:142-149`). The
  third key moves obj by 1e-8 per unit. Six decimals cannot show that, so jobs that differ
  only in the third key tie. The tie goes to the smaller seed number, and the selection is
  then not lexicographic. The next round's pool order is wrong in the same way. The kernel's
  own comparisons use the full double and are correct. `pipe` and `bench.py` use Python
  objectives and are not affected.
- **Reproduction.** `m1_lex_third_key.sh` (`tmp/m1.out`):
  ```
  final cost 17.0000 G 17 A 4 GD 6 AD 2 obj 4.000600 ...    (seed 1)
  final cost 18.0000 G 18 A 4 GD 6 AD 2 obj 4.000600 ...    (seed 6)
  == cli's own ranking code on the two circuits with the seed labels swapped
     seed 1 obj 4.0006  A 4 GD 6 cost 18
     seed 2 obj 4.0006  A 4 GD 6 cost 17
     cli picks seed 1: cost 18 (the lexicographic best has cost 17)
  ```
  Step 1 is a real `cli.py run --objective a,gd,cost` run. Step 2 runs the real kernel
  (`iters 0`) on its two circuits and applies line 256 verbatim. The lower seed number is put
  on the worse circuit; that is the only change.
- **Fix.** Print obj with `%.17g` (or print the integer metrics and rank in Python by the key
  tuple, as `pipe` does).

### M2. `pipe` cannot repair a start that violates the caps

- **Where.** `cli.py:426-428` (crash) and `cli.py:411-423` (pool).
- **What happens.**
  - (a) When no job in a round is feasible, `best` is still `None`. The round report then
    evaluates `bm[k]` on `None` and raises `TypeError`. No round-1 job is started and no
    summary is written.
  - (b) With (a) patched, only feasible jobs enter `cands`. When there are none, `newpool` is
    empty and the pool stays `[start]`. Each round therefore restarts the repair from the
    original circuit.
  - `run` keeps the penalised best (`cli.py:256-268`). `bench.py` v3 keeps `cand`
    (`bench.py:179`).
  - Consequence: the depth-repair workflow behind the 124@GD14 result
    (`A-aes-gd14repair-rebuild-s4-v3`) cannot be run with `cli.py pipe`. REPORT section 5 lists
    this as fixed ("keep the last circuit while nothing is feasible (v3)"), but the fix is in
    `bench.py` only.
- **Reproduction.** `m2_pipe_repair_lost.sh` (`tmp/m2.out`): AES, NIST a33-ad4-g116-gd15,
  `--cap-gd 14`, 2 rounds, `--iters 2000`.
  ```
  == (a) pipe, unmodified
  TypeError: 'NoneType' object is not subscriptable
     round-1 files written: 0
  -- pipe-b (round report guarded in memory only):
     r0-s1 final cost 120 ... GD 15 ... obj 1910120.001500 feas 0
     r1-s1 start cost 116 ... GD 15 ... obj 1990116.001500
     r1-s1 start == original start: repair progress lost
  -- run:
     r1-s1 start cost 120 ... obj 1910120.001500   (progress kept)
  ```
- **Fix.** Guard the report. When nothing is feasible, rank the jobs by
  `(feasible, violation, objective)` (or by the kernel's penalised obj, printed exactly; see M1)
  and carry the least-violating results into the pool.

### M3. Rebuild-stage improvements missing from benchmark trajectories; table counts too low

- **Where.** `bench.py:166-173`. Trajectory rows come only from the gate kernel's `best` lines
  (`parse_bests`). The kernel prints no line for its start. So a rebuilt circuit (or a start
  the kernel's strash makes cheaper, m3) that is better than `best_m` is taken as `best_c` at
  line 172 without a row. `analyze.first_time` and `best_at` (`analyze.py:41-59`) read only the
  trajectory.
- **What happens.** The run's final circuit meets the target, but the table counts the run as
  not reaching it, or the time is too late. review2 m5 called this "conservative" and found "no
  such case in v1/v2". `check_bench_data.py` finds 4 runs: 2 in v2, 2 in v3.
- **Reproduction.** `python3 nonlinear/boolflux/review3/check_bench_data.py ~/xs-campaigns/2026-11-13-boolflux/bench/{v1,v2,v3,v4}`
  (`tmp/check_bench_data.out`):
  ```
  T1 (final better than last feasible trajectory point): 4
   F-gf16-mul-unseeded-s3-v2: final A9 G32, last trajectory point A10 G30 (t 14.7)
   N-gf16-mul-rebuild-s1-v2:  final G31,    trajectory = start only (G34)
   F-gf16-mul-unseeded-s2-v3: final A9 G31, last trajectory point A10 G30
   N-gf16-mul-rebuild-s1-v3:  final G31,    trajectory = start only
  reach-target count: analyze.py (trajectory) vs final verified circuit
   v2 F gf16-mul-unseeded v2: analyze reach 3/5, final meets target 4/5
   v3 F gf16-mul-unseeded v3: analyze reach 2/5, final meets target 3/5
  ```
  `tables-v2.md:117` and `tables-v3.md:56` print 3/5 and 2/5. The best-so-far curves of the two
  `N-gf16-mul-rebuild-s1` runs stay at 34 until 60 s, but the true value is 31.
  Other checks in the same script found no problem: no trajectory point is better than the
  final (no over-claim), trajectories are monotone, and no search exceeds its budget by more
  than 1 s.
- **Fix.** After every rebuild stage (and for the kernel's cleaned start), append a row when
  the candidate is feasible and better than `best_m`. Or let the kernel print a `best` line for
  its start. Then regenerate the tables.

### M4. `skip_noop` misses most no-op moves; report claims built on it

- **Where.** `bfx.c:734-735` compares the rebuilt candidate with `cur` by `memcmp` of the gate
  list. `rebuild()` renumbers gates: DFS post-order, with the operands of symmetric gates
  sorted by the *new* numbers (`bfx.c:210`). It is therefore not idempotent. A candidate that
  re-creates the current circuit comes back with a different numbering, passes the filter, and
  is accepted as a neutral move (`bfx.c:738`).
- **Reproduction.**
  - `m6_noop_filter.sh` (`tmp/m6.out`) uses `review3/kernel/bfx_instr`, which is `bfx.c` plus
    a structural hash that ignores renumbering, built by `review3/kernel/make_instr.py`. Its
    search is identical to `bfx`: same improvement sequence and same final circuit, checked in
    the script.
    ```
    maj3 (400 it):     skipped 1198; accepted moves that are the current circuit renumbered: 291 of 376
    present (3000 it): skipped 5692; ... 2183 of 2593
    aes a36 (3000 it): skipped 184;  ... 1809 of 2242
    ```
  - `m6b_trace_counts.sh` (`tmp/m6b.out`) replays REPORT section 2's AES trace (a36, seed 3,
    57644 iterations, `skip_noop 0`). It reproduces the reported 43,958 accepted moves, 10,850
    AND-targeting moves, 15,710 AND-inserting moves and the final 131:
    ```
    accepted 43958 (structurally unchanged 38099); targeted an AND 10850 (unchanged 10521);
    inserted an AND 15710 (unchanged 15131)
    ```
- **Effect on claims.** These are wrong claims; no saved circuit is wrong.
  - REPORT.md:70-71: the "10,850 targeted an AND gate and 15,710 inserted one" statistic
    suggests nonlinear activity. 15,131 of those insertions re-created the same AND and left
    the circuit unchanged; only 579 changed anything.
  - REPORT.md:243 and the summary say no-op neutral moves were fixed by `skip_noop`, with "no
    measurable quality effect". On AES the filter removes 184 no-op candidates, while 1,809 of
    2,242 accepted moves are still no-ops. The A/B (15 seeds each) did not test what it was
    meant to test.
- **Fix.** Decide "no-op" on a renumbering-invariant key: a structural hash plus an exact
  canonical comparison, or compare against `rebuild(cur)` iterated to a fixed point. Then
  repeat the skip_noop A/B and recount the trace statistics without no-ops.

### M5. BUF outputs make a correct circuit fail verification

- **Where.** `core.write_ncff` writes `BUF y x` for an output that is an input, or that is the
  same signal as an earlier output (`core.py:269-271`). `independent/verify.py` lists BUF in
  `counts` (`verify.py:494-499`, G excludes it). `core.metrics` has no BUF. `cli.verify_file`
  requires the count dictionaries to be equal (`cli.py:113`). So `metrics_agree` is False and
  `independent_ok` is False.
- **Effect.** `cli run`/`pipe` print "VERIFICATION FAILED" and exit nonzero. `bench.py` records
  `verified False`, so the run counts as failed in the tables. Both verifiers accept the
  function.
- **Reproduction.**
  - `m5_buf_counts.py` (`tmp/m5.out`): two 2-input functions registered in memory only.
    ```
    r3-wire: file has ['BUF y0 x0'] ... core counts {'AND': 1}, independent counts {'AND': 1, 'BUF': 1}
       -> metrics_agree False, independent_ok False
    r3-dup:  file has ['BUF y1 y0'] ... -> metrics_agree False, independent_ok False
    ```
  - `m5_skinny.sh` (`tmp/m5-skinny.out`): `map:skinny` is a repository target with 4
    weight-1 rows (the only one of the 58 loadable maps in `circuits/` with weight-1 or
    duplicate rows).
    ```
    best: {"cost": 12.0, "G": 12, ...}  core_ok=True independent_ok=False library_ok=True
    VERIFICATION FAILED ...
    BUF lines: 4
    core counts {'XOR': 12} independent counts {'BUF': 4, 'XOR': 12}
    ```
- **Fix.** Drop `BUF` from the independent counts before comparing (`cli.py:113`), or add the
  number of BUF lines `write_ncff` emits to core's counts.

### M6. REPORT / LEDGER statements contradicted by the run data

Each item was checked against the raw JSONs. The commands are in `check_bench_data.py`, plus
the one-liners given.

1. **REPORT.md:34 and LEDGER.md:163 say depth repair "succeeded in 1 of 35 runs".** Two of
   the 35 `aes-gd14repair` runs end feasible at GD 14:
   - `v1/A-aes-gd14repair-gate-s4-v1`: 129 G, A40, GD14, verified;
   - `v3/A-aes-gd14repair-rebuild-s4-v3`: 124 G.

   REPORT's own table (line 167, "v1: 1/5 feasible, at 129 gates") shows the first. Only the
   G <= 126 target was met 1/35 times.
2. **REPORT.md:171 says the rebuild takes the ANF circuit "to ~683 gates in about 2 s".** The
   first 683-gate trajectory points of `A-aes-anf-rebuild-s{1,2,3}` are at 7.1/9.5/9.8 s (v2)
   and 5.3/7.9/8.1 s (v3). `synth_s` is 8.3-13.3 s per run, most of it in the first rebuild.
   The table cells `5s:1247.0` in `tables-v2.md`/`tables-v3.md` agree with the data, not with
   the text.
3. **LEDGER.md:157 says the 14-level circuit "trades depth for ANDs (41)".** The circuit in
   the table (line 124) and in `results/aes/aes-nist-bench-rebuild-gd14-...` has A38. 41 was
   the older 126-gate circuit.

Fix: correct the three sentences.

---

## Minor findings

- **m1. `pipe` synthesis variant: by cost only, always replaces the input** (`cli.py:331`).
  - Caps and objective are ignored, and the variant is used even when it is worse than the
    job's input. `bench.py` v3 ranks by (feasible, objective) and keeps the input when it is
    better.
  - `m4_pipe_variant_choice.sh` (`tmp/m4.out`): GF(2^4) mult, xag, `--cap-gd 4`. The seeded
    variant (34 G, GD 4, feasible) is passed over for the Paar variant (31 G, GD 6). Here the
    gate stage happens to repair it to GD 4, so the result is not wrong. The gate stage just
    starts infeasible, or at a worse objective (`gd,cost`), for nothing.
  - Fix: use bench v3's rank and keep-if-better.
- **m2. bench v3 ranks infeasible circuits by objective only** (`bench.py:141-145`).
  - During repair, a cheaper but deeper rebuild counts as `synth_gain` and replaces the
    repair progress (`cand`, kept at line 179). It also keeps the skeleton share at 0.2.
  - `m7_rank_infeasible.py` (`tmp/m7.out`): PRESENT, cap GD 5, input 32 G / GD 6 (excess 1);
    the 25 G / GD 9 variant (excess 4) is chosen.
  - It cannot trigger on the AES repair runs, where forms-only rebuilds are 31-72 gates worse.
  - Fix: rank by `(feasible, total cap excess, objective)`.
- **m3. Start clean-up not accounted for** (`bfx.c:673-675`).
  - The kernel strashes and removes dead gates in the start before its clock starts. The naive
    ANF/XOR-tree starts contain duplicate XOR pairs. Measured with `bfx --stats`:
    - AES ANF: 1247 -> 1128;
    - joltik naive: 72 -> 65;
    - PRINCE: 35 -> 34.
  - bench's `traj[0]`, the tables and REPORT ("the 1247-gate ANF circuit") use the Python
    metrics from before the clean-up. In the linear-map pairs, XORFlux receives the 72-gate
    file and BoolFlux effectively starts at 65.
  - Command: `python3 -c` build of the ANF start, then `review3/tmp/k/bfx --stats FILE`. The
    outputs are in this review's log; the start files are in `tmp/k/`.
  - Fix: build starts with structural hashing, or report the cleaned start.
- **m4. tracemoves files.**
  - The `.before` circuit files carry `# cost 0 G 0 A 0 GD 0 AD 0 before` (`mprev_dummy`,
    `bfx.c:620,765`). Seen in `tmp/k/maj3.tm.it2.before`.
  - Before/after files are written whenever `mcur.obj < mbest.obj` (`bfx.c:763`), including
    penalised infeasible improvements that are not new bests (`bfx.c:771`).
  - Fix: write `before` with its own metrics, and use the best-update condition.
- **m5. Logged times** (`bfx.c:698,775`; `bench.py:160-166`).
  - `best t` is the time at the start of the iteration, measured from the kernel's own `t0`.
    That excludes process start, reading, simulation and the start clean-up (`kernel_startup_s`
    5-50 ms).
  - XORFlux trajectory times exclude its 0.4-1.5 s start-up (review2 noted this). It is
    documented, but it is not the same clock as BoolFlux's.
  - No run overruns its budget (check B1 = 0).
- **m6. Skeleton candidate discarded at the end of the budget** (`bench.py:118-120`).
  - The skeleton stage gets `min(R*share, budget-el)`. If it uses the rest of the budget, the
    loop breaks before the gate stage, and the rebuilt candidate is never compared with
    `best_c`. That is possible in the last round only; the logged runs are not affected.
  - Fix: evaluate the candidate as an incumbent right after synthesis.
- **m7. Failures lose earlier rounds.**
  - `run` raises `SystemExit` for any failed job (`cli.py:258-261`). In `pipe` an exception in
    a job propagates out of `ex.map` (`cli.py:406-407`). In both cases nothing is written,
    although a valid best of earlier rounds exists (only in the per-job `.best.bfx` files).
  - Fix: write `best.circ.txt` and `summary.json` after every round.
- **m8. Model name resolved as a path first** (`core.py:159-160`, also `cli.py:106`).
  - `cd ~/xcr-boolflux/nonlinear && python3 boolflux/cli.py verify ...g124...circ.txt --target aes --model nist`
    gives `IsADirectoryError: [Errno 21] Is a directory: 'nist'`.
  - A file named like a model in the cwd would be loaded silently as the model.
  - Fix: try `MODELS/<name>.json` first, or require a `.json` suffix for paths.
- **m9. Tolerance vs third-key weight (latent)** (`bfx.c:704,738,743,771`).
  - The absolute 1e-9 tolerance and the 1e-8 third-key weight make a third-key difference
    below 0.1 cost units count as neutral or "no improvement".
  - All shipped models have unit costs, so nothing is affected today.
  - In repair mode, obj is about 1e6-1e7 and the third key is near double resolution.
  - Fix: compare key tuples, or scale the tolerance to the weights.
- **m10. analyze.py columns.**
  - `best_at(..., key='cost')` and the "best" of "final cost/G (median, best)" minimise cost.
    For `a,cost` rows (gf16-mul) they mix circuits with different A, so they are not the
    best-so-far under the run's objective.
  - Fix: rank by the run's objective.
- **m11. Wording and reproducibility.**
  - REPORT.md:16 says PRINCE 16 "in 2-4 of 5 seeds"; v3 full is 1/5 (REPORT.md:158 says 1-4).
  - REPORT.md:166 says "15 more seeds"; there are 10 more (15 in total, v1/v2 s1-5 + v4 s6-15),
    and they mix code 19480fc (v1) with 154ded8 (v4).
  - REPORT.md:202 says "v1 and v2 agree", but GF(2^4) no-fraig is G 30 in v1 and 29 in v2.
  - REPRODUCE.md gives only the v1/v2 plan commands. v3 needs `make_plan.py --tag v3`, which
    regenerates `plan-v3.json` exactly (checked; v1 and v2 also regenerate exactly). v4
    (seeds 6-15, mixed v1/v2 labels) cannot be produced by `make_plan.py`.
- **m12. `--set skel.iters` overwritten** (`cli.py:314-316`).
  - `cfg.update(... 'iters': args.skel_iters ...)` comes after the `skel.*` settings.
    `--skel-iters 0` works; `--set skel.iters=0` is ignored silently.

---

## Can `cli.py` reproduce the benchmarked workflows?

| bench workflow | CLI equivalent | status |
|---|---|---|
| `gate` (one kernel run, wall budget) | `run --seeds S --rounds 1 --iters 1000000000000000 --seconds B --set skip_noop=1` | yes. For XOR-only models add `--set linear=1`; bench sets it automatically (`bench.py:75`) and cli does not. |
| ablations (`set`) | `run --set mv.resub3=0`, `--set neutral=0`, ... | yes |
| skeleton ablations `mv.merge 0`, seeded-only | `pipe --set skel.mv.merge=0`, `--set synth.unseeded=0` | yes |
| `unseeded` (no seeded variant) | none | missing (`run_skel` always builds the seeded variant) |
| `full`: time-sliced rounds (20 % skeleton, 80 % gate) on one job, alternating, incumbent kept | `pipe` is iteration-based. A fraction of jobs runs skeleton then gate; there is no per-round time slice, and `--seconds` caps each process | not reproducible |
| `rebuild` (skeleton iters 0) | `pipe --skel-iters 0 --skel-share 1` | partly: the variant is chosen by cost only and replaces the input (m1); there are no time slices |
| adaptive skeleton share (v3) | none | missing |
| variant choice by (feasible, objective), keep the input if better (v3) | none | missing (m1) |
| repair under caps across rounds | `run` keeps repair progress (`cli.py:256-268`) | `run`: yes. `pipe`: crashes / discards it (M2), so the 124@GD14 workflow (rebuild + repair) has no CLI path. |
| trajectory / time-to-target output | `run`/`pipe` record kernel `improvements` per job | partial: no merged per-run trajectory, and the same omission as M3 |

---

## Investigated and found correct

- **Kernel acceptance, feasibility first** (`bfx.c:731-778`). Improvements, neutral and uphill
  moves all require `m.feas >= mcur.feas` (or a repair start). The best is replaced only by a
  feasible state, or by a lower penalised obj while nothing is feasible. Stall restarts
  (`bfx.c:704`) restore the best only when it is strictly better. The final best is
  re-simulated from scratch (`bfx.c:785-787`). Checked by reading the code and by the M2 runs
  (`feas 0` progress written, never a worse circuit).
- **Lexicographic weights inside the kernel.** For the shipped models (unit costs; G <= 20000
  = GCAP), the second key can outweigh the first only with a difference above 10^4 units, and
  likewise the third over the second. The cap penalty is 1e6 per unit of excess plus 1e4 per
  unit of path excess. It dominates any objective difference below 1e4, so a feasible
  candidate always ranks before an infeasible one. The neutral tolerance 1e-9 is below the
  third-key step of 1e-8 (m9 is the latent exception).
- **Incumbent across rounds.**
  - `run`: job 0 of each round starts from `pool[0]`, and the kernel never returns a circuit
    worse than its (cleaned) start, so the best of the last round is the overall best (exact
    in the kernel's obj; M1 affects only ties).
  - `pipe`: the pool circuits re-enter `cands`, and `best` is replaced only by a strictly
    lower objective (`cli.py:412-424`). Correct when something is feasible.
- **bench incumbent.**
  - `best_c` is replaced only by feasible circuits with obj <= the best.
  - The reported final is the verified `best_c`.
  - Over all 1056 run JSONs: 0 trajectory points better than the final (T2), 0 non-monotone
    trajectories (T3), 0 budget overruns (B1).
  - The 33 unverified runs are exactly the repair runs that never became feasible.
- **Clean-up passes.**
  - `rebuild` drops candidates that become constant; it never folds them wrongly.
  - The f(x,x) simplifications are correct (x, or NOT when the library has it).
  - fraig merges only into signals that are never deeper in GD or AD, so feasibility is kept.
  - The cost in acceptance is the post-clean-up cost, and the trace "after" metrics are too.
- **Metrics agreement** (G, A, GD, AD, cost, counts) between kernel, `core`, and `verify.py`,
  including NOT written as `XNOR t a 0` (counted as XNOR on both sides). Checked on the
  124@GD14 file (`verify.py`: G=124, AND 38, XNOR 37, XOR 49, cost 124, the same in the bench
  JSON and `results/`). All 44 non-`xxn` `results/nist-format` names match `verify.py`'s A,
  AD, G, GD, XX. The BUF case (M5) is the exception.
- **Plans.** `make_plan.py --tag v1/v2/v3` regenerates `plan-v1/2/3.json` run for run.
- **REPORT tables against the data.** Section 4.1 equals `pooled.py` on v1+v2+v4 (rerun, the
  same as `pooled.md`). Sections 4.2, 4.3 and 4.5 match `tables-v1..v4.md` cell by cell,
  except the items in M6 and m11. The skeleton time "24 s -> 12 s" matches `skel_s`
  (24.0-24.1 in v1/v2, 11.4-11.8 in v3).
- **Skeleton kernel** (`skel.c`). Best tracking is strict and the final is re-analysed. The
  merge move skips the Metropolis test, but it cannot lose the best because the best is stored
  separately.

## Files

- `check_bench_data.py`: data checks T1/T2/T3/B1/V and reach-target vs final.
- `m1_lex_third_key.sh`, `m2_pipe_repair_lost.sh`, `m4_pipe_variant_choice.sh`,
  `m5_buf_counts.py`, `m5_skinny.sh`, `m6_noop_filter.sh`, `m6b_trace_counts.sh`,
  `m7_rank_infeasible.py`: reproductions.
- `kernel/make_instr.py`: builds `kernel/bfx_instr.c` (bfx.c plus a structural no-op counter;
  same search).
- `tmp/*.out`: the outputs quoted above. `tmp/*/`: run directories.


## Resolution (coordinator, 2026-11-14)

Regression tests: `tests/test_review3.py` (15 tests, ~1 min; `python3 -m unittest nonlinear/boolflux/tests/test_review3.py`).
The older suite (`tests/test_boolflux.py`, 10 tests) still passes.

| finding | fix | regression test / evidence |
|---|---|---|
| M1 third key lost in `run` job ranking | new `objective.py`: one ranking for kernel, cli, workflow, analyze = (feasible, total cap excess, summed path excess, keys in order); kernel compares the same way (`lex` config key, `mcmp`), weighted obj only sizes Metropolis steps; obj printed `%.17g`; `run`/`pipe`/`flow` rank by that tuple | `test_rank_lexicographic_third_key`, `test_kernel_lex_config_and_exact_obj`, `test_run_picks_lexicographic_best_job`, `test_kernel_unknown_lex_key` |
| M2 `pipe` crash / repair progress discarded | every verified job and pool circuit is ranked (infeasible ones by excess, then path excess); best is written every round; `CAPS NOT MET` marked in the file and exit code | `test_pipe_repairs_across_rounds` (round 1 starts from round 0's repair progress) |
| M3 rebuild gains missing from trajectories | the loop moved to `workflow.py` (bench.py and `cli.py flow` share it): a rebuilt candidate is compared with the incumbent at once and gets a trajectory row; the kernel's cleaned start is a row; analyze.py counts success from the final circuits; tables v1-v4 regenerated (`bench/data/tables-v*.md`: gf16-mul unseeded 3/5 -> 4/5 (v2), 2/5 -> 3/5 (v3), "(1: no time)") | `test_workflow_trajectory_has_every_feasible_incumbent` |
| M4 `skip_noop` missed renumbered no-ops | `same_structure()`: structural hash + exact pairing check, invariant under renumbering; review3/m6_noop_filter.sh now reports 0 renumbered no-ops accepted (maj3 0/213, present 0/1005, AES 0/750; search identical to the instrumented copy); trace statistics in REPORT §2 corrected (579 of 43,958 accepted moves changed AND structure); the A/B repeated (REPORT §7) | `test_noop_filter_structural`, `m6_noop_filter.sh` |
| M5 BUF lines fail verification | `verify_file` drops BUF from the independent counts (G already excludes it) and records `buf_lines` | `test_buf_outputs_verify` (`map:skinny`, 4 BUF lines, verified) |
| M6 wrong report/ledger sentences | corrected: 2 of 35 repairs reached GD 14 (129, 124); rebuild 5-10 s; A38 | REPORT.md, LEDGER.md |
| m1 `pipe` variant by cost only | ranked like everything else; the input is kept unless a variant is better | `test_pipe_variant_respects_caps` |
| m2 bench v3 ranks infeasible by objective | same ranking (excess first) in workflow.py | `test_rank_feasibility_then_excess` |
| m3 start clean-up silent | kernel prints `start_cleanup raw ...` when the clean-up changes the start; workflow puts the cleaned start in the trajectory; REPORT notes AES ANF 1247 -> 1128 | `test_start_cleanup_logged` |
| m4 trace `.before` zero metrics; written on penalised moves | `.before` carries the state's metrics; before/after written only on a new best | `test_trace_before_metrics` |
| m5 logged times exclude start-up | workflow shifts kernel times by the measured start-up (wall - kernel seconds); XORFlux start-up stays documented | code |
| m6 skeleton candidate lost at end of budget | incumbent check right after the rebuild | `test_workflow_trajectory_...` |
| m7 failure loses earlier rounds | failed jobs are recorded and skipped; best.circ.txt/summary.json written after every round; nonzero exit at the end | code (`run`, `pipe`) |
| m8 model name resolved as a path | `core.model_path`: stock name first, else an existing `.json` file | `test_model_name_not_shadowed_by_cwd` |
| m9 tolerance vs third key | per-key comparison with a relative tolerance (`dcmp`) | as M1 |
| m10 analyze "best" by cost | best by the run's objective (rank) | regenerated tables (gf16 `a,cost` rows changed) |
| m11 wording, v3/v4 reproduction | REPORT wording fixed; all plans in `bench/plans/`, REPRODUCE.md lists them | REPRODUCE.md |
| m12 `--set skel.iters` overridden | `skel.*` settings applied last | `test_skel_set_iters_wins` |
| CLI parity | `cli.py flow`: gate / full / rebuild-only (`--skel-set iters=0`) / adaptive / seeded-only / unseeded-only, pinned per seed, same code as bench.py; linear mode automatic for XOR-only models in run/pipe/flow; `pipe` repairs | `test_flow_rebuild_repair`; REPRODUCE.md |

Not changed: v1-v4 run data (produced by the earlier commits; only the tables were regenerated from them).
