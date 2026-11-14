# BoolFlux review 4: objective selection, cost handling, hard constraints

Branch `boolflux-2026-11-13` at 417e449, worktree `~/xcr-boolflux`. Nothing outside `review4/`
was modified and nothing was committed. All runs used CPUs 18-19 (`taskset -c 18,19`, or `xsrun`
for runs longer than a minute). Commands are run from `~/xcr-boolflux`. The outputs quoted here
are in `review4/tmp/*.out`.

The review-3 fixes were checked against the code, not against the resolution table. Each one
holds (see "Verified correct"). The problems that remain are in **cost handling**: the
kernel's search constants are in absolute cost units, `--set` reaches only the kernel, and some
model combinations are not validated. A further problem is how the Metropolis step treats the
second objective key.

## Summary

| # | severity | where | finding | script |
|---|---|---|---|---|
| M1 | major | bfx.c:260, :790-791, :812, :818; workflow.py:31-33 | `T0`, `uphill`, `max_excess` are absolute cost units. A model with every gate at 10 (same ranking of circuits as bgc) turns the gate kernel into pure descent: PRESENT gives 14/18/17/14 gates where bgc gives 14 on all 4 seeds | `r4_scale.sh` |
| M2 | major (with `--set`) | cli.py:162+167, workflow.py:67+72, bfx.c:286-287; cli.py:305-317 | `--set cost.*` / `gdw.*` / `cap.*` / `lex` change only the kernel's objective. Python ranks and reports under the model. `run` never compares results with its start, so it saves a circuit worse than the start (bgc 16 vs start 14, exit 0). `cost.<op not in model>` widens the library, every job's cost becomes NaN, and the run fails only at the end | `r4_set_cost.sh`, `r4_twin.py` (3) |
| m1 | minor | bfx.c:809-818; objective.py:30-37 | when the first key is A or GD, a cost-only uphill step has d = 1e-4·Δcost and is accepted with p ≈ 0.9998 at any T in the schedule. `max_excess` 8 allows 8·10^4 cost units. The current state's cost drifts (median +4, max +13..17 above the best vs +0 / +4..6 cost-first). No measured effect on the final result | `r4_drift.sh` |
| m2 | minor | core.py:157-160, :274-275; verify.py:546; cli.py:126-127 | `not_as: XNOR0` with cost[NOT] ≠ cost[XNOR] is accepted. core costs a NOT at cost[NOT], but the file has `XNOR t a 0` and verify.py costs it at cost[XNOR], so a correct run ends in VERIFICATION FAILED. `Model.load` also does no other validation (negative/NaN costs, `BUF`, unknown names) | `r4_custom_models.sh` (b) |
| m3 | minor (latent) | bfx.c:767, :849; workflow.py:79-94 | the kernel prints `start`/`best` costs with `%.4f`. workflow trajectories (and analyze's time-to-target and best-so-far) use these rounded costs, while incumbents use exact Python costs. No effect with unit costs | code reading |
| m4 | minor | review3/m1_lex_third_key.sh, m4_*.sh (step 1), m7_rank_infeasible.py, m2 part (b) | these review-3 reproductions embed verbatim copies of the old code, so they no longer test the current code. m1's printed verdict is a hard-coded string, now false ("lexicographic best has cost 17"; the actual best is A4 GD5) | `review4/tmp/r3/all.out` |

No shipped result is affected. Every stock model (`models/*.json`) has unit costs, so M1 does not
apply to them, and no `results/` summary uses `cost.*`/`gdw.*`/`cap.*`/`lex` in `settings`.

---

## Major

### M1. Kernel search constants are absolute cost units; non-unit cost models get a different algorithm

- **Where.**
  - Defaults: `T0 0.6`, `uphill 1.0`, `max_excess 8` (`workflow.py:31-33`, used by cli and
    workflow; kernel defaults at `bfx.c:260`).
  - `budget = mffc_cost(s) + uphill` (`bfx.c:790-791`): the new gates may cost at most one
    unit more than the removed cone.
  - Uphill candidates need `m.obj <= mbest.obj + max_excess` (`bfx.c:812`) and are accepted
    with probability `exp(-d/T)` (`bfx.c:818`), with d in weighted cost units.
- **What happens.** None of these is scaled by the model's cost unit. Multiplying every cost by
  10 leaves the ranking of every circuit unchanged, but:
  - `budget` no longer allows even one extra gate;
  - `max_excess` 8 is below one gate, so the uphill list is always empty;
  - `T0` 0.6 against d = 10 gives p ≈ 6e-8.

  The kernel then runs as descent plus neutral moves. A model in other units (gate equivalents,
  ×100, areas such as 2.33) silently gets a much weaker search. Costs of 0.1 go the other way:
  10 extra gates per move, 80 gates of slack.
- **Reproduction.** `r4_scale.sh` (`tmp/scale.out`). Same PRESENT ANF start, `cost,gd`, 30000
  iterations, seeds 1-4. Each column is final cost per seed, then the current-state cost above
  the best's cost (median, max over accepted moves):
  ```
  bgc   (1 per gate)                 final 14 14 14 14            drift median 0 1 0 0, max 6 5 5 6
  bgc10 (10 per gate)                final 170 180 140 170        drift max 0 0 0 0   (never uphill)
  bgc01 (0.1 per gate)               final 1.4 1.4 1.4 1.4        drift max 1.7 1.8 1.6 1.8 (17-18 gates)
  bgc10 + T0=6 uphill=10 max_excess=80   final 140 140 140 140
  ```
  Under bgc10, 3 of 4 seeds save a circuit 3-4 gates worse than the unit-cost search finds
  (17/18/17 vs 14). Scaling the three constants by 10 restores 14 on every seed.
- **Fix.** Scale the three constants in Python where the config is written (`kernel_config`,
  `workflow.kernel_cfg`) by the model's cost unit. For example, use the smallest positive gate
  cost (or the median): `uphill·u`, `T0·u`, `max_excess·u`, with `u = 1` for every stock model.
  Alternatively, normalise `cost.*` by `u` in the config and report costs ×u. Then record `u` in
  `summary.json`. For objectives whose first key is A/GD, see m1.

### M2. `--set` keys that define the objective reach only the kernel

- **Where.**
  - `kernel_config` writes the model costs, then `cfg.update(extra)` (`cli.py:162`, `:167`). The
    same happens in `workflow.kernel_cfg` (`workflow.py:67`, `:72`) for `flow --set` and bench
    `set`.
  - In the kernel, `cost.K` both sets the cost and *adds op K to the library*
    (`bfx.c:286`). `gdw.K` sets a gate-depth weight (`bfx.c:287`) that core, `objective.path_excess`
    (`objective.py:68`) and verify.py do not know.
  - `cap.*` and `lex` can also be overridden this way.
  - The Python side ranks, chooses jobs and pools, and reports with the model's costs, unit depth
    and the CLI caps/objective (`objective.rank`, `core.metrics`).
  - `cmd_run` chooses the best only among job results, never against the start or pool
    (`cli.py:305-317`). Unlike `pipe` (`cli.py:445-447`) and workflow (`best_c = start`), it relies
    on "the kernel never returns worse than its start", which holds only when kernel and Python
    agree.
- **What happens.**
  - (a) The kernel minimises a different cost than the one reported. `run` saves a circuit worse
    than its start under the reported model and exits 0, with `verified` true.
  - (b) A `cost.*` key for an op outside the model widens the library. `core.metrics` gives
    `cost = NaN` (`core.py:93`) and the rank tuples contain NaN, so the sort and the pool order are
    arbitrary. The run fails only at the end ("VERIFICATION FAILED", library check), after the
    whole budget.
  - (c) With `gdw.3=0`, the kernel's GD and feasibility differ from Python's in 35 of 40 random
    circuits. The kernel then accepts or rejects against a cap that Python does not enforce in the
    same way, so a run can end in "CAPS NOT MET" for circuits the kernel considered feasible.
- **Reproduction.** `bash nonlinear/boolflux/review4/r4_set_cost.sh` (`tmp/set_cost.out`):
  ```
  == (a) start: results/present/present-bgc-cost-nocap-g14-...  cost 14
  round 0: best {"cost": 16.0, "G": 16, "A": 8, "GD": 9, "AD": 5} ...
  best: {"cost": 16.0, ...}  core_ok=True independent_ok=True library_ok=True      (exit 0)
  -- kernel's own final lines: final cost 34.0000 G 16 ... / final cost 36.0000 G 18 ...
  -- summary.json best cost 16.0, start_metrics cost 14.0, settings cost.6 = 4
  == (b) model xag + --set cost.14=1
  round 0: best {"cost": NaN, "G": 14, ...} {"AND": 2, "NOT": 1, "OR": 2, "XOR": 9}
  VERIFICATION FAILED ...;  per-job Python cost: [nan, nan]
  ```
  (c): `python3 nonlinear/boolflux/review4/r4_twin.py`, part (3):
  `gdw.3=0: kernel GD != Python GD in 35/40 circuits; kernel feasible != Python feasible in 35/40`.
- **Fix.**
  - Refuse `cost.*`, `gdw.*`, `cap.*`, `lex` and `w.*` in `--set`/`set`, with a message
    pointing to `--model` (a custom JSON), `--cap-*` and `--objective`. If cost overrides are
    wanted, apply them to a copy of the `Model` so that Python ranks and reports with the same
    costs, and refuse ops outside the model.
  - In `cmd_run`, add the round's pool circuits to the candidates, as `pipe` does. Then no run
    can save a result worse than its start.

---

## Minor

### m1. Metropolis step and `max_excess` when the first key is not cost

- **Where.** `objective.weights` gives weight 1 to the first key and 1e-4 to the second. The
  kernel uses `d = m.obj - mcur.obj` (`bfx.c:809`), `m.obj <= mbest.obj + max_excess`
  (`bfx.c:812`) and `exp(-d/T)` (`bfx.c:818`). T runs from T0 = 0.6 down towards 0 but never
  reaches 0 (`bfx.c:775-776`).
- **What happens.** For `a,cost` or `gd,cost`, a step that keeps the first key and adds Δ to the
  cost has d = 1e-4·Δ. It is accepted with p = exp(-1e-4·Δ/T), at least 0.99 down to T = 0.01.
  The cap on the cost of the current state is mbest.obj + 8, i.e. 8·10^4 cost units. So the
  temperature schedule has no effect on the second key, and the walk drifts uphill in cost. Only
  the per-move budget (`uphill` 1, in cost units, `bfx.c:791`) slows it. Neutral moves under
  `a,cost` need equal A *and* equal cost.
- **Reproduction.** `r4_drift.sh` (`tmp/firstkey.out`), 30000 iterations, seeds 1-4. The two
  drift numbers are the current-state cost above the best's cost (median, max over accepted
  moves):
  ```
  gf16-mul xag a,cost     final (A,cost) (15,30) (16,31) (16,31) (15,30)   drift median 4 4 4 4, max 13 14 13 15
     w.cost=1             final          (15,30) (16,31) (16,31) (16,31)   drift median 0 0 0 0, max 5 4 4 5
     uphill=4 / uphill=8  final          (15,30) (16,31) (15,30) (16,31)   (both)
  gf16-mul xag cost,a                                                       drift median 0,      max 4 5 4 5
  present bgc gd,cost     final (GD,cost) (5,16) (4,18) (4,18) (5,17)      drift median 2 2 1 2, max 10 11 8 11
     w.cost=1             final           (5,17) (4,19) (5,17) (5,17)      drift max 3 4 4 3
  present bgc cost,gd                                                       drift max 6 5 5 6
  ```
  The drift is measured, but these seeds show no consistent effect on the final circuits.
  Raising `uphill`, the cost budget for A-reducing rewrites, to 4 or 8 changed nothing on
  gf16-mul either, so the cost-unit budget did not visibly limit A-first search.
- **Fix (if wanted).** Make the step lexicographic as well. Let d be the difference in the
  first differing key, in that key's own units. Use a temperature and `max_excess` per key, or
  one temperature for keys scaled to a unit step. Then `a,cost` treats cost uphill steps at the
  same T as `cost,a` does.

### m2. Model files: `not_as: XNOR0` with cost[NOT] ≠ cost[XNOR]; no validation in `Model.load`

- **Where.**
  - `core.write_ncff` writes a NOT as `XNOR t a 0` when `not_as == 'XNOR0'` (`core.py:274-275`).
  - `core.metrics` costs it at cost[NOT].
  - verify.py costs the file's XNOR at cost[XNOR] (`verify.py:546`).
  - `verify_file` requires equal costs (`cli.py:126-127`).
  - `Model.load` (`core.py:157-160`) accepts any numbers and names. verify.py does check them
    (`validate_model`, verify.py:468-485): it rejects negative or non-finite costs and requires
    BUF to be 0. `Model.cost` raises KeyError for a `BUF` entry.
- **Reproduction.** `r4_custom_models.sh` (b) (`tmp/custom.out`), model
  `{AND 1, XOR 1, XNOR 5, NOT 0.5, not_as XNOR0}`:
  ```
  best: {"cost": 14.0, ...}  core_ok=True independent_ok=False library_ok=True
  VERIFICATION FAILED ...
  core cost 14.0 counts {'AND': 4, 'NOT': 2, 'XOR': 9} | verify.py cost 23.0 counts {'AND': 4, 'XNOR': 2, 'XOR': 9}
  ```
  NIST (all costs 1) is not affected.
- **Fix.** In `Model.load`, reject `not_as: XNOR0` unless cost[NOT] == cost[XNOR] (or have core
  cost the NOT at cost[XNOR]). Also run verify.py's `validate_model` rules there: finite and
  non-negative costs, known gate names, BUF only as 0.

### m3. Rounded costs in kernel log lines feed the trajectories

- **Where.** `start ... cost %.4f` and `best ... cost %.4f` (`bfx.c:767`, `:849`).
  `workflow.parse_kernel` (`workflow.py:79-94`) builds trajectory rows from them and offers them
  to `offer_traj`, ranking them against exact Python metrics (start, rebuilds).
- **What happens.** With a fractional model (e.g. a gate cost of 1/3), a kernel row of the same
  circuit can look cheaper than an exact rebuild point, so a duplicate row is added later. Also,
  analyze.py's thresholds (`cost <= 14`) are applied to rounded values. Selection is not affected,
  because incumbents use exact costs. Unit costs are not affected.
- **Fix.** Print `%.17g` for cost in `start`/`best` (as obj already is).

### m4. Review-3 reproduction scripts that no longer test the current code

- These copies were rerun with outputs under `review4/tmp/r3/` (`tmp/r3/all.out`; the paths were
  redirected so that `review3/tmp` stays untouched):
  - `m1_lex_third_key.sh` step 2 applies the *old* `cli.py:256` sort, and its verdict line is a
    fixed string ("the lexicographic best has cost 17"). With the current kernel the two circuits
    are A4 GD5 cost 18 and A4 GD6 cost 15. Under `a,gd,cost` the first one is the best, and it is
    what `cli run` saved (`summary.json`: A4 GD5 cost 18, seed 1).
  - `m2_pipe_repair_lost.sh` part (b) patches code that no longer exists (AssertionError).
    Part (a) now shows the fix: round-1 files are written, and the round-1 starts are the round-0
    results (125 G / VSUM-lower and 119 G), not the original 116.
  - `m4_pipe_variant_choice.sh` step 1 and `m7_rank_infeasible.py` reproduce the old selection
    lines verbatim. The `pipe` run in m4 now takes the feasible seeded variant (synth 34 G GD 4 ->
    32 G GD 4). Its last summary line fails with `KeyError: 'job'` (old summary format).
- Fix: delete or mark these as historical. The regression tests in `tests/test_review3.py` are
  the current checks.

---

## Verified correct (and how)

1. **Review-3 regression tests.** `python3 -m unittest nonlinear/boolflux/tests/test_review3.py
   nonlinear/boolflux/tests/test_boolflux.py`: 25 tests, OK, 50.5 s (`tmp/tests.out`).
2. **Kernel ranking.**
   - `mcmp` (`bfx.c:174-180`) orders by viol (sum of cap excesses, as `objective.excess`), then
     VSUM, then the `lex` keys. Every `cli`/`workflow` config sets `lex` (`objective.weights`).
   - Improvement (`:810`, `:816`), neutral (`:811`), uphill (`:812`), new best (`:834`) and stall
     restart (`:778`) all go through `mcmp` with `m.feas >= mcur.feas`. A feasible state is never
     left, and a feasible candidate always beats an infeasible current state, so a feasible circuit
     that has been seen is always taken as best.
   - Checked by reading the code, and by the m2 rerun (infeasible repair progress kept, `feas 0`
     lines only while nothing is feasible).
3. **Python twin of the kernel metrics** (`r4_twin.py`, `tmp/twin.out`).
   - 179 random circuits under three models: unit costs; fractional with a 0-cost NOT and
     ANDN 0.05; large/mixed with NAND 10000 and ORN 0.125. 134 of the circuits violate a GD cap,
     an AD cap or both.
   - The kernel's post-clean-up `start` metrics (cost, G, A, GD, AD) equal `core.metrics` and
     verify.py's `compute_metrics` (from the NCFF the CLI writes).
   - The kernel's VSUM (recovered from `obj = cost + 1e6·viol + 1e4·vsum`) equals
     `objective.path_excess`.
   - 0 mismatches in either check. AD uses the same nonlinear set in both
     (odd-popcount ops = `NONLINEAR_OPS`). The one exception is `gdw.*` (M2c).
4. **Cost end to end with a fractional/zero/large model.** `r4_custom_models.sh` (a): kernel
   `final cost 3.1970`, core 3.197, verify.py 3.1970000000000005, `independent_ok True`.
5. **Job, pool, round and variant selection.**
   - `cmd_run` (`cli.py:305-317`), `cmd_pipe` (`:444-456`, pool circuits re-ranked), `cmd_flow`
     (`:520-521`), `run_skel` (`:364-370`: variant by rank, input kept unless a variant is better)
     and `workflow.search` (`:158-190`: start, every rebuild, every kernel result) all use
     `objective.rank` on `objective.measure`, with exact metrics (no printed obj) and seed only as
     a tie-break between equal ranks.
   - Confirmed on the m1 rerun (saved best = minimum rank under `a,gd,cost`) and the m4 rerun.
   - Exception: `cmd_run` does not include the start (M2).
6. **Repair under caps across rounds.** `run` and `pipe` carry the least-violating results
   forward (m2 rerun: round-1 starts are round-0 results). `write_best` marks an infeasible
   incumbent. `finish` exits non-zero with "CAPS NOT MET" and never reports an infeasible circuit
   as success.
7. **Caps with any objective order.** The cap test sits before the keys in both `mcmp` and
   `rank`, so `a,cost`, `gd,cost` and `cost,gd` with GD/AD/A caps rank the same way. The
   required-level pruning (`bfx.c:789`) never allows a candidate deeper than the cap in a
   feasible state.
8. **`mffc_cost` / budget with unequal costs** (`bfx.c:421-432`, `:790-791`).
   - The MFFC is computed from reference counts that include output references. It sums
     `op_cost` (and correctly skips the b operand of NOT).
   - The budget is only a filter on generated candidates. Acceptance uses the metrics of the
     rebuilt, fraiged candidate, so a candidate that reuses MFFC gates or merges by strash cannot
     be mis-costed.
9. **NOT as XNOR0 and BUF** with the NIST model (equal costs). Counts and costs agree (m5 rerun:
   `independent_ok True` on `map:skinny`, 4 BUF lines; on the two in-memory BUF cases from
   `m5_buf_counts.py`; and in the 124 @ GD14 file via `aes_check.py`).
10. **`aes_check.py`.** It ran on `results/aes/...g124-a38-gd14-ad4`: verified, new Pareto point,
    and "best published G at GD<=14: 125 (gain +1)". `dominated_by` uses ≤ on all four of
    (A, AD, G, GD), so an equal tuple counts as not new.
11. **analyze.py.** Success is counted from the verified final circuit. `best_at` and the "best"
    column rank by the run's own objective and caps (`rank_key`). Trajectory rows are feasible
    points only, so the missing VSUM does not matter.

## Files

- `r4lib.py`: helper; runs `bfx` (private build in `tmp/bin/`) with `workflow.kernel_cfg`.
- `r4_twin.py`: kernel/core/verify.py metric and VSUM twins; gdw mismatch (M2c).
- `r4_set_cost.sh`: M2 (a), (b).
- `r4_scale.sh` (+ `r4_firstkey.py`): M1.
- `r4_drift.sh` (+ `r4_firstkey.py`): m1.
- `r4_custom_models.sh`: verified item 4, and m2.
- `tmp/r3/`: review-3 scripts with output paths redirected (m4); `tmp/r3/all.out`.
- `tmp/*.out`: outputs quoted above.


## Resolution (coordinator, 2026-11-14)

Regression tests: `tests/test_review4.py` (8 tests); full suite 33 tests pass.

| finding | fix | test |
|---|---|---|
| M1 T0 / uphill / max_excess in absolute cost units | kernel: after reading the config they are multiplied by the cheapest allowed gate cost when cost is the first objective key (else 1); `scale_abs 1` keeps the old behaviour; logged as `scale unit X`. Unit-cost models unchanged. | `test_bgc_times_ten_reaches_14` |
| M2 `--set` desynchronises kernel and Python | `workflow.check_sets`: `cost.*`, `gdw.*`, `cap.*`, `w.*`, `lex`, `in/out/seed/iters/seconds` refused in `--set` (run, pipe, flow, bench `set`); `run` keeps the start as a candidate, so a worse job never replaces it | `test_forbidden_keys`, `test_allowed_keys_still_work`, `test_run_never_worse_than_start` |
| m1 cost-only drift when A or GD is the first key | Metropolis step and `max_excess` measured on the first differing key (`ldelta`) when the first key is not cost; cost-first objectives keep the weighted difference (the measured behaviour of every campaign: secondary keys drift almost freely, which helps plateau walks) | code; full suite |
| m2 custom models: NOT-as-XNOR0 cost mismatch, unchecked costs/names | `Model.load` rejects unknown gates and BUF, negative/NaN/infinite costs, and `not_as XNOR0` with NOT cost != XNOR cost | `test_not_xnor_cost_mismatch_rejected`, `test_bad_costs_rejected`, `test_stock_models_load` |
| m3 costs printed with 4 decimals | kernel prints costs `%.10g` (start, best, final, stats, circuit headers) | `test_fractional_cost_in_log` |
| m4 stale review-3 scripts | left as the historical reproductions; review4/tmp/r3 holds the reruns against current code | - |
