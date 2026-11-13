# BoolFlux review 2: commits 3a71f0f..ccb323f, MECHANICS.md, traces, rebuild penalty (2026-11-13)

Scope: `git diff 9f4c8df ccb323f -- nonlinear/boolflux` on branch `boolflux-2026-11-13` (HEAD
`ccb323f`, clean tree), `bench/MECHANICS.md`, the traces in
`~/xs-campaigns/2026-11-13-boolflux/traces/`, `bench/rebuild_penalty.py` and its data, and the
benchmark data in `~/xs-campaigns/2026-11-13-boolflux/bench/{v1,v2}` (v2 was still running).
Nothing outside `review2/` was modified; no commits. Every process ran pinned to CPUs 16-19, with
at most 4 at a time. The test scripts and their logs are in `review2/` and `review2/tmp/`.

**Bottom line.** I found no path that produces or reports a wrong circuit. The exact linear mode
is exact: on 116 affine cases it makes the same decisions as full simulation. The seeded rebuild
never produced a wrong circuit, an exception or an out-of-library gate (1,694 cases). The
incremental Paar is byte-identical to the old one (5,082 cases). The bit-order rewrites,
`anf_coeffs` and `map:` targets are correct. A deterministic replay reproduces the recorded AES
run exactly, but only with `skip_noop 0`: the shipped default is not unchanged. The findings that
matter are about how the benchmark reports performance: the peak-RSS comparison, the
full-configuration round policy on repair targets, and medians taken only over the runs that
succeeded. There are also several smaller inaccuracies in MECHANICS.md.

## Findings

### Critical (misleading performance claim)

**C1. The peak-RSS column compares XORFlux's whole Python process with BoolFlux's C kernel
alone.** `bench/bench.py:42-47,131-132,150-151,184`, `analyze.py:96,129`.
- For BoolFlux, `rss` collects `/usr/bin/time -v` only for the `bfx`/`skel` subprocesses.
- The Python side is never measured. That includes the start construction, the skeleton
  extraction and the seeded/unseeded synthesis of the full configuration, which run inside the
  bench worker. That side is what `cli.py` is in real use.
- For XORFlux, the measured process is the complete tool, interpreter included.
- `tables-v1.md` therefore prints 2.3-2.5 MB (BoolFlux) against 25.5-27.2 MB (XORFlux) on every
  linear row. That reads as a 10x memory advantage, but it is mostly the Python interpreter's
  baseline.
- Reproduction: `/usr/bin/time -v` of a Python process that imports `bench`/`boolflux` and builds
  the joltik ANF start peaks at 23.4 MB. Doing the AES extraction and the four synthesis variants
  peaks at 20.5 MB.
- Fix: label the column "search-kernel RSS" and add the driver's RSS
  (`resource.getrusage(RUSAGE_SELF).ru_maxrss` in the worker), or drop the column from the
  cross-tool table.

### Major

**M1. In the full configuration, progress on a start that breaks a cap is thrown away every
round.** `bench/bench.py:102-103,159-162,168`.
- `best_c` starts as the start circuit. It is replaced only by a *feasible* kernel result
  (line 161), and every round restarts from `cur = best_c` (line 168).
- On a repair target (AES `gd14repair`: start GD 15, cap 14), each round's 0.8·R seconds of
  penalised depth repair are therefore discarded until one round happens to finish feasible
  inside its own slice. The gate configuration repairs for the whole budget.
- v1 result: `gd14repair full` has 5/5 runs without a circuit inside the cap; `gate` has 4/5.
- This is a property of the driver, not of the skeleton stage, but it makes the skeleton look
  harmful on depth repair.
- Fix: while no feasible circuit exists, carry the kernel's best by penalised objective (the
  `g.out` file) as `cur`. Or report repair targets for the gate configuration only.

**M2. Medians are taken only over the runs that succeeded, and the tables do not say so.**
`analyze.py:62-64` (`med` drops `None`), `51-59`, `87`, `118`, `121`.
- "best-so-far median at checkpoints" and "final cost/G (median, best)" ignore every run that has
  no feasible point yet, or no verified final.
- Example: `aes-gd14repair | gate v1` reports `120s:129.0` and final `129.0, 129.0`. That is one
  run out of five; the other four have nothing inside the cap.
- The runs column does say "(4 failed)", but the checkpoint curve and the median look like
  five-run statistics.
- Fix: count a run without a feasible point as +inf, or print "k/n" next to every median.

**M3. On the AES benchmark starts, the full configuration's skeleton slice does nothing.**
Mechanism: `cli.SKEL_DEFAULTS` has no `emit_current`, `bench.py:124-144`, and the seeded rebuild.
- I ran the skeleton kernel exactly as `bench.py` does: SKEL_DEFAULTS, `cap.ad`, 6 s (= 0.2 · 30
  s), 4 seeds × 3 starts (`review2/test_fullconfig.py`).
- In 11 of 12 cases it returned the input skeleton unchanged, after 800-1000 iterations with
  88-177 accepted moves.
- The seeded rebuild then reproduces the parent gate for gate, and `bench.py` picks it.
- In the one changed case (gd14repair, seed 3) the result was worse (G 116→121, GD 15→17).
- So on `A-aes-*` and `F-aes-*`, "full vs gate" measures 20 % less gate time plus a kernel restart
  every round, not the value of skeleton search. MECHANICS.md section 5 hints at this ("usually
  the start"), but the benchmark tables do not.
- With `adaptive` (v3) the slice drops to 0.5 s after the first round and never recovers. The
  gate slice stays at 0.8·R, so a round gets shorter (more restarts) rather than giving its time
  to the gate kernel.
- The `rebuild` control (`skel_set iters 0`) is not round-matched either. Its skeleton stage
  returns at once, so its rounds last about 0.8·R and it runs about 25 % more rounds than `full`.
- Fix: say this in the report. Compare `full` with `rebuild` rather than with `gate`, and give the
  control an idle slice (or `seconds` with zero moves) so that round counts match.

### Minor

**m1. The kernel default changed with `skip_noop = 1`; the "defaults unchanged" claim only holds
at 3a71f0f.** `kernel/bfx.c:244`.
- The 3a71f0f commit message says the kernel defaults are unchanged. That was true at 3a71f0f:
  `neutral`, `odc` and `linear` keep the old behaviour by default.
- 7ae20c8 added `skip_noop`, on by default. A skipped no-op is never an improvement or an uphill
  move; it only leaves the neutral list. That changes which neutral move is drawn and when
  `rnd01()` is consumed.
- `review2/test_defaults.py` ran 8 cases × 3 seeds on iteration budgets:
  - old kernel (9f4c8df) vs new kernel with `skip_noop 0`: byte-identical (24/24);
  - new kernel with `skip_noop 0` vs the same plus `tracemoves`: identical (24/24);
  - old vs the new default: different in 24/24.
- REPRODUCE.md says this for the AES replay, but its **maj3 command (lines 10-11) has no
  `--set skip_noop=0`** and does not reproduce the recorded maj3 trace. Rerun with the default,
  the improving moves land at it 25 and 99 instead of 7 and 227. With `skip_noop 0` the moves
  file is identical.
- Fix: add `--set skip_noop=0` to the maj3 command, and state the default change wherever
  results from the old kernel are compared with new runs.

**m2. The cheapest synthesis variant is chosen by cost alone, ignoring the caps.**
`cli.py:331`, `bench.py:141`.
- A cheaper variant that breaks GD/AD wins over a feasible one, and the gate kernel then starts in
  repair mode.
- The full configuration also always feeds the synthesised circuit to the gate kernel, even when
  it is worse than the circuit that went in. In the gd14repair seed-3 case above, the round
  starts from 121@GD17 instead of 116@GD15.
- On the benchmark starts the seeded variant was the cheapest and, where the parent was feasible,
  feasible. So this did not matter here.
- Fix: choose by (feasible, objective), and keep the incoming circuit when it is better.

**m3. `bench.py:144` guards the synthesised circuit with `assert`, which `python -O` strips.**
- The gate kernel takes its target from its start circuit (`bfx.c:668-670`), so a wrong synthesis
  would be optimised silently. Only the final `verify_file` would catch it.
- `cli.py:332` uses an explicit `raise`; use one here too.

**m4. The comments on the adaptive share disagree with the code.** `bench.py:111-112`.
- The comment says the slice halves when the skeleton candidate "did not end the round better
  than the incoming best".
- The code (lines 142 and 166) tests the *synthesised* circuit straight after synthesis, before
  the gate stage, and ignores feasibility.

**m5. A synthesis improvement that the gate kernel does not beat never enters the trajectory.**
`bench.py:155-162`.
- The kernel prints no `best` line for its start, so a synthesised circuit better than `best_m`
  updates `best_c`/`best_m` (line 161) without a trajectory row.
- This is conservative: it delays, never advances, time-to-target. `review2/audit_bench.py` found
  no such case in v1/v2 (final = best feasible trajectory point in all 440 verified runs).

**m6. show_trace.py labels and keys.** `bench/show_trace.py:34-36,66-76`.
- "removed" means "this AND *output function* no longer exists", not "fewer ANDs". The aes142
  summary says "moves that removed ANDs 2", yet A is 36 in every aes142 move. Those two moves
  *replaced* an AND function. Suggest "AND functions replaced / added / rewired".
- `by_function` keys gates by `sorted({operand tables})`. That merges ANDN(x,y) with ANDN(y,x),
  and ORN likewise, in libraries that have them. No effect on the three traces (xag/nist have
  only symmetric binary ops).
- The hex tables are printed without zero padding (`'%x'`), so their lengths vary.
- `maj3-trace.txt` and `aes109-trace.txt` were made by an older show_trace.py. They lack the
  "AND gates: …" lines and the summary that the current script prints; aes142 matches the
  current script. Regenerate them.

**m7. The `tracemoves` `.before` files carry a zero metrics comment.** `bfx.c:620,765`.
- They are written with `mprev_dummy`, so they read `# cost 0.0000 G 0 A 0 …`. Write `mcur`'s
  pre-move metrics instead.

**m8. `odc 0` is not "exact equality" for unobservable signals.** `bfx.c:383-385`.
- When `s` is unobservable, `CARE` stays empty, so any replacement is still accepted. The
  ablation is "no ODCs for observable signals". Only the description needs adjusting.

**m9. `skip_noop` compares `Gate` structs with `memcmp`, padding included.** `bfx.c:734`.
- `Gate` is `{unsigned char op; int a, b;}`, with 3 padding bytes. Today they are zero (fresh
  mmap'd buffers), so this works.
- If they ever differ, a no-op is just not skipped (old behaviour); results are never wrong.
  Compare fields, or `memset` the gate buffers at allocation.

**m10. `targets.linear_map` ignores the optional affine constant line of a `.mat.txt`.**
`targets.py:83-90`.
- XORFlux documents that line as y = Ax + c. One repository map has it (`aes-sbox-bottom`), but
  it has 18 inputs and is refused (> 16). Raise when extra tokens are present.

**m11. The incremental Paar speed-up depends on the input.**
- The 1fc02c3 commit message claims about 3x.
- Measured old vs new `synthesize` wall time (`review2/time_paar*.py`):
  - 1.2x on 26 NIST AES skeletons;
  - 2.6x for `paar_outputs` on the AES ANF skeleton (K 246);
  - 0.9x for per-level Paar on the same skeleton.

**m12. A stale comment.** `cli.py:324` still says "three synthesis variants", but the seeded
variant is now added.

### MECHANICS.md inaccuracies (all minor)

Line references (bfx.c l.82, 93, 123, 167, 334, 362, 389, 432, 479, 580, 608; skel.c l.119, 210,
254, 275, 310, 330) are all correct. bfx.c is unchanged from 19480fc to HEAD. Every XORFlux file
named in the section 1 table exists and has the role described: phases burst/plateau/repair,
restart sources fresh/elite/shared/worker best, pull sharing, `walk.py`, `lns.py`,
`acceptance.py` slack, `dossier.py`. The defaults quoted (dmax 220, pdiv 90, cand_cap 40, 1:2:1,
stall_it 60000, K + 0.02 E, 1/1e-4/1e-8) match `cli.DEFAULTS`/`SKEL_DEFAULTS`; the kernel's own
built-in defaults differ (dmax 200, w.lin 0.001, seconds-based schedules).

1. Section 1: "grep for `xorflux`/`search/` … finds nothing" is out of date. `bench/bench.py`,
   `analyze.py` and `make_plan.py` mention it, by running XORFlux as a subprocess. The claim
   "imports no XORFlux code" is still true.
2. Section 2: "`linear 1`, set automatically for XOR-only libraries" is only true in `bench.py`
   (`kernel_cfg`, l.75). `cli.py run --model xor` never sets it: correct, just slower.
3. Section 2: "Every candidate circuit is re-simulated on all patterns" means the n+1 patterns in
   linear mode. That is exact, but the wording, and the header comment `bfx.c:7-9` ("all 2^n
   inputs"), should say so.
4. Section 3, step 4: "so a candidate never breaks a cap" holds for the depth caps (pruning).
   `cap.a` is enforced only by the acceptance rule (feasible states are never left), not by
   pruning.
5. Section 3, step 5, level 2b: "`op2` nonlinear" is wrong. `op2` is sampled from every binary
   library op (`lib2` includes XOR/XNOR, `bfx.c:519`).
6. Section 3, step 6: the order is wrong. `eval_cand` re-simulates and checks *before* `fraig`
   (`bfx.c:609-614`). The post-fraig circuit is checked again only when it is accepted
   (`state_refresh`, `bfx.c:336`). Exact either way, but the description says the check comes
   after fraig.
7. Section 4: the neutral move is also taken whenever `T <= 0`, not only "with probability 0.75 or
   when no uphill candidate exists" (`bfx.c:744`).
8. Section 4, determinism: "with an iteration budget a run is reproducible exactly" also needs
   iteration-based schedules (`Tperiod_it`, `stall_it`, as `cli.DEFAULTS` sets). The kernel's own
   defaults (`Tperiod 30`, `stall 60` seconds) are wall-clock based. Verified true under
   cli.DEFAULTS, and with `tracemoves` on (m1).
9. Section 5: the data path `bench/data/rebuild_penalty.json` does not exist in the repository.
   It is the bundle path (`make_bundle.sh`); the file is
   `~/xs-campaigns/2026-11-13-boolflux/bench/rebuild_penalty.json`.
10. Section 5: "On AES the skeleton kernel's best skeleton is usually the start". The cited data
    cannot show this, because every rebuild_penalty run uses `emit_current 1`. It is true, though
    (M3: 11/12 under the bench settings). Cite that measurement instead.
11. Section 6: "pipe alternates per job" is inaccurate. A fraction `--skel-share` (default 0.5,
    golden-ratio sequence, `cli.py:387`) of the jobs run skeleton + rebuild before the gate
    kernel; the rest run the gate kernel only.

## What I checked and found correct

**Exact linear mode (`bfx.c:651-665`).**
- Argument: every op with an even-weight 4-bit table (`!op_nl`) is affine, and an affine function
  is fixed by its values at 0, e_0, …, e_{n-1}. `INV[i] = 1 << (i+1)` puts input i to 1 exactly
  at pattern i+1. The target comes from the start circuit on the same patterns, and every check
  (`outputs_ok`, `eqc`, the pair hash, `fraig`, the final guard) is masked by `LASTMASK`.
- Care sets: an output of an affine circuit is affine in s's value, with coefficient the parity
  of the s→o paths. So flipping s changes o on all inputs or on none, and the n+1-pattern care
  set is exact.
- Nonlinear ops: the guard rejects any nonlinear library op (`bfx.c:656`). The start circuit must
  use library ops only (`bfx.c:672`). New gates come only from `lib2`, op 3 (only when NOT is in
  the library) or XOR/XNOR roots (only when in the library), and `rebuild` only turns f(x,x) into
  op 3 when it is allowed. So a nonlinear gate can never appear. XNOR, NOT and the constant/buffer
  ops are affine and handled exactly.
- Empirical test (`review2/test_linear.py`): `linear 1` vs `linear 0`, same seed, iteration
  budget, on random linear and affine maps (n = 3..16; libraries {XOR}, {XOR,XNOR,NOT},
  {XOR,XNOR}, {XOR,NOT}; starts with XNOR/NOT chains and complemented outputs). Identical
  decisions should be expected, because hash probe order among equal values is insertion order
  in both modes. Result: identical stdout and output circuit in 116/116 cases, every final
  re-verified on all 2^n inputs by an independent evaluator.
- Both guards fire: "linear mode needs a linear library" for AND in the library, and "start
  circuit uses op 8 outside the library".
- Not tested: n ≥ 14 with two binary ops, where `PCAP` truncates the pair table differently at
  W ≥ 256.

**Switches and `tracemoves`.**
- `neutral`, `odc` and `linear` default to the old behaviour. `use_neutral &&` short-circuits
  before `rnd01()`. The `observable` scan consumes no randomness.
- `tracemoves` adds only `circ_copy`/`fprintf`. It does not perturb a run on an iteration budget
  (24/24, and the AES replay below).
- A no-op candidate has d = 0. It can only be in `neu[]`, never be the improvement or uphill
  choice, so `skip_noop` cannot affect correctness.

**Deterministic replay.**
- The REPRODUCE.md AES command (seed 3, 57644 iterations, `skip_noop 0`) on HEAD gives a `best`
  sequence identical to the original `frontier-fwd-3/…/r0-s3.log` (131 at it 57644).
- Its `moves.txt` is identical to the recorded `traces/aes142/moves.txt` once timestamps are
  removed, and all ten `.before`/`.after` files are byte-identical.
- The same run with the default `skip_noop 1` ends at 134.

**Seeded rebuild (`skeleton.parent_forms`, `synthesize(parent=…)`).**
- By construction:
  - A parent nonlinear gate ((a^p)&(b^q))^r gets the form `AND_k ^ r` only when its truth table
    with r removed equals new AND k's table.
  - Linear gates combine operand forms exactly.
  - So every non-None form denotes exactly the parent signal's function.
  - `psig[x]` is always a signal with x's truth table: an inserted gate, a `have[f]` entry with
    the same form, or the new AND k for r = 0 parents.
- So the seeded `AND(psig[a], psig[b])` computes the parent AND's table, which is AND k's table,
  whatever the skeleton's (L, R) for k. The operands "carried over" are functionally exact.
- Parents with r = 1 (NAND/OR/ORN) are never given a `psig`. They and their fanout are rebuilt
  from forms, which is conservative.
- Complemented `have` keys (from `absorb`/`materialize`) are now skipped as greedy terms
  (`skeleton.py:164`). In the old code such a term could leave the constant bit in `rest` and hit
  `pos_sig[0]`.
- Every use of the result is checked against the full table: `cli.py:332` (raise),
  `bench.py:144` (assert, m3), `rebuild_penalty.py:51` (assert), then `verify_file` on the
  reported circuit.
- Fuzz (`review2/test_synth.py`): 121 parents, namely the 101 `results/` circuits (nist, bgc,
  gc, gc6, xag; gc includes NAND/NOR/OR/ANDN/ORN) and every 4th NIST AES circuit, plus an
  equivalence-mutated copy of each (AND→NOR(¬,¬)/ANDN(·,¬)/¬NAND, XOR→XNOR(¬a,b) and double
  NOTs). Skeletons came after 0-300 skeleton-kernel iterations (`emit_current 1`, `cap.ad` =
  parent AD). Result: 1,694 seeded rebuilds; wrong 0, exceptions 0, out-of-library gates 0, AD
  above the parent's 0.
- For information: the seeded rebuild was cheaper than the best unseeded one in 913 cases, equal
  in 449 and *worse* in 332 (20 %, mostly small S-boxes). Keeping both, as `cli.py` and `bench.py`
  do by default, is justified, and the `seeded-only` ablation should show this.
- The theoretical exception paths (`materialize`'s "need a constant operand for XNOR-NOT", when a
  carried-over XNOR has a constant-free form) need a library with XNOR but no NOT. No shipped
  model has one.

**Incremental Paar (1fc02c3).**
- The heap of (-count, a, b) pops the largest count, then the smallest a, then the smallest b.
  The old `max(…, key=(c, -a, -b))` makes the same choice.
- Stale entries are skipped by comparing with `cnt`. `where[(a,b)]` is exactly the rows holding
  both. The new term t is larger than every id, so the pairs (x, t) are keyed in order. A row
  reduced to {t} contributes no pairs, as in the old filter.
- Empirically, new vs old (9f4c8df) `synthesize` for all three unseeded variants:
  byte-identical in 5,082 of 5,082 cases (skeletons above), and in 6 large ANF-start
  cases.
- I also compared against an old copy with only the `fm & 1` line added, to separate that change
  from Paar. That copy is identical too, so on these inputs the `fm & 1` fix never fired.

**Truth-table and start rewrites.**
- `core.value_table` and `tables_from_values` (msb/msb; checked for t ≥ 2^N too), and
  `starts.anf_coeffs` (bitset Möbius transform): equal to the old code in 3000 random trials
  (n ≤ 10, m ≤ 12), including round trips.
- `starts.anf` starts are byte-identical to the old ones for present/bgc, gf16-mul/xag, aes/nist,
  ascon/gc and maj3/xag (`review2/test_tables.py`).

**`targets.load('map:…')`.**
- Equal to a direct row-times-x evaluation on all 18 repository maps with ≤ 16 inputs. Row j is
  output j at bit m-1-j; column i is input i at bit n-1-i, the same convention as XORFlux.
- All nine repository circuits for joltik, small-scale-aes and klsw17 compute the BoolFlux target.
- `LIN_BEST` (44/42, 44/42, 36/32) matches the best repository circuit at each cap.

**Traces (`review2/check_traces.py`).**
- All 13 before/after pairs (maj3: 2, aes142: 10, aes109: 1) compute the target. I checked them
  with my own evaluator, against a separately written AES S-box (x^254 plus the affine map).
- The G/A/GD/AD on each trace line match the files.
- My own multiset classification of AND changes (by output function; operands ordered for
  asymmetric ops, sorted for symmetric) agrees with show_trace.py on every move: (removed, new,
  rewired) = (2,1,0) twice for maj3; (1,1,1) at it 6014 and (1,1,0) at it 57644 for aes142,
  otherwise (0,0,0).
- There are no duplicate nonlinear gates that the dict could have merged.

**Benchmark driver (`review2/audit_bench.py`, code reading).**
- Pinning: one worker per CPU (`sched_setaffinity`), with every subprocess on the same CPU via
  `taskset`. The bench uses CPUs 0,2,…,14, one per physical core (siblings are (2k, 2k+1)), so
  there is no SMT contention.
- Each linear pair runs back to back on one CPU with the same start, the same seed and 120 s.
- Start construction is outside the budget for both tools. Skeleton kernel, synthesis and kernel
  launches are inside it for BoolFlux.
- Trajectory times: BoolFlux uses kernel time + launch offset from the driver's T0. XORFlux uses
  its worker clock, which excludes 0.4-0.9 s of its own start-up; that is in XORFlux's favour, by
  under a second.
- XORFlux records deeper than the cap are dropped before choosing the best, which is correct: an
  out-of-cap record can never dominate an in-cap point.
- The final circuits of both tools are verified by both verifiers with the caps.
  `verified = False` exactly for the 9 v1 runs without a feasible circuit.
- In v1/v2: no trajectory point better than the verified final (no over-claim), no final better
  than the trajectory, times monotone, no trajectory point or search wall time beyond the budget
  (+1 s / +2 s).

**`rebuild_penalty.py`.**
- It measures what section 5 says: extract, run the skeleton kernel for k iterations with
  `emit_current 1`, rebuild unseeded (best of 3) and seeded, assert both against the table.
  `accepted_moves` is the sum of the `acc` column of the `move` lines (field 5, correct).
- Numbers in the data (`review2/analyze_penalty.py`):
  - unchanged skeleton: 104→152, 131→203, 142→173 (+48, +72, +31), seeded +0 in all 9 runs;
  - exactly 1 accepted move: seeded +0, +2, +2, +11, +19, +19;
  - 25-90 accepted moves: +45 … +98;
  - K never changed (0/72), and seeded was never worse than unseeded.
- Caveat: "accepted moves" counts accepted proposals, including neutral and reverting ones.
  `K - ands_kept` (the number of parent AND functions lost) would track "number of AND functions
  changed" more directly, and the data already has it.

## Files

- `review2/common.py`: helpers (pinned runs, independent evaluator)
- `review2/test_defaults.py`: old vs new kernel, `skip_noop`, `tracemoves` (`tmp/test_defaults.json`)
- `review2/test_linear.py`: linear 0 vs 1 and the guards (`tmp/test_linear.log`, `.json`)
- `review2/test_synth.py`: Paar identity and seeded-rebuild fuzz (`tmp/test_synth.log`, `.json`)
- `review2/test_tables.py`: bit order, `anf_coeffs`, ANF starts, `map:` targets
- `review2/test_fullconfig.py`: what the bench's skeleton slice returns on the AES starts
- `review2/check_traces.py`: trace re-verification and AND classification
- `review2/audit_bench.py`, `review2/analyze_penalty.py`, `review2/time_paar.py`, `review2/time_paar2.py`
- `review2/old/`: the 9f4c8df / 3a71f0f sources used for the comparisons; `review2/bin/`: binaries built from them and from HEAD
- `review2/tmp/replay/`: the AES and maj3 replays
