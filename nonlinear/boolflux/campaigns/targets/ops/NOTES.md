# ops/ and runner.py: notes (M2, phase 2, 2026-11-16)

Owner of `ops/common.py`, `ops/conjpull.py` and `../runner.py`: agent M2. Evidence labels: [C] computed
(exact within the stated case), [H] heuristic / one run. LOCAL ONLY (never committed or pushed by M2).

## Operator contract (BRIEF2.md)
`python3 nonlinear/boolflux/campaigns/targets/ops/<name>.py --in START --target Txx --seed S --seconds T --out DIR [--cpus 1] [flags]`
- limits from TARGETS.json (`common.limits`, re-read on every call); search states may exceed every cap
  (user 2026-11-15 23:50 UTC); only recorded circuits must be inside A <= ref A, AD <= ref AD.
- DIR gets `<name>-a..-ad..-g..-gd..-<hash>.circ.txt` + `<same>.json` (BRIEF.md sidecar fields: target, A AD G GD,
  start {path, sha256, tuple}, method, command, seed, elapsed_s, code {git, kernel, kernel_sha256,
  kernel_src_sha256, ops_sha256}, aes_check (OK line), utc; plus op, params, parent {path, sha256}, how,
  lineage, class (informational), path_certified (informational), aes_check_full, circuit_sha256).
- DIR/result.json: status (ok | error | timeout), wall_s, pareto_G_GD and pareto_A_AD_G_GD (tuple, file, how, t),
  rejected counts, notes, op-specific extras.  Exit within T + 60 s.

## common.py (shared helpers)
- `limits(tid)`, `target(tid)`, `reference_file(tid)`, `in_limits(tup, tid)`, `classify(tup, tid)` (copy of the
  ledger's rules, informational; the ledger decides), `pareto2` / `pareto4`, `check(path)` (aes_check.check +
  its printed OK line), `load`, `metrics`, `structure_key`, `kernel_bin()` (repo build
  `bfx-<sha1(kernel/bfx.c)[:10]>` in ~/xs-campaigns/2026-11-16-night/bin via hub.ops.kernel_bin), `code_info`.
- `Recorder(out, op, tid, start, seed, command, method, params, kernel)`: `offer(circuit, how, lineage,
  path_certified)` writes a candidate at once (so a killed job keeps its results) iff it is inside the hard
  limits and not weakly dominated in (A, AD, G, GD) by a point the job already wrote; the written file is
  checked with aes_check (two verifiers, all 256 inputs) and removed on failure; result.json is rewritten on
  every new point; `finish(status, extra)`.  `contract_args(ap)` adds the common flags.
- Kernel: bfx.c sha256 c8d293b6... (repair_keep support), build `bfx-94a75e2c18`, binary sha256
  e4f373f70f9698878db48476337876b68a02935d850117816faf0c561aa467a0 (identical bytes to
  ~/xs-campaigns/2026-11-14-hub/long/bin/bfx-94a75e2c18 used by P5/P6/P7).

## conjpull.py (conjugate + staged pull)
Method: P3 NOTES "Conjugates" and P6 NOTES s.12-13.  inv = H o inv o G for G(z) = lam z^(2^k): 2040
conjugates with the same AND structure (top linear layer f -> f o G, output layer Mout).
1. Conjugate selection `--conj` (comma list, processed in order until the time ends): `id`, `L:K`,
   `rank:R` / `top:N` / `all` by the conj3 score (BP top proxy + Paar bottom proxy, identity excluded).
   The screen of a start (2040 conjugates, ~144 s on one CPU [C, measured on 140@25]) is cached per start
   sha256 in NIGHT/cache/conj3 with a file lock (one job computes, concurrent jobs on the same start wait).
2. Build = P3 mkconj (naive conjugate, BP top resynthesis 12 runs, trb top/bottom passes), < 1 s.
3. Staged pulls `--schedule MODE:CAP:SECONDS[:rk0|rk1],...`: g = fdrive gate (kernel restarted from the
   stage best, 200k iterations per call), m = fdrive mix (gate / osc / trb rotation), o = osc, t = trb,
   k = one hub-style kernel run with objective cost,gd (P6 kern.py).  CAP may be relative (+N / -N to the
   stage input's GD).  Kernel caps: cap.gd = stage cap, cap.a / cap.ad = the target's A / AD; repair_keep
   from `--repair-keep` (default 1), per stage `:rk0` / `:rk1`, or per beam seed `--beam-rk 0,1`.
   `--beam B` seeds per stage; the best (feasible at the stage cap, then G, GD) goes on.
4. Every kernel output, osc-relaxed state and trb build (after hub.common.clean) is offered to the Recorder.
5. Start already a conjugate (file/dir name with conj or cj-, or a sidecar lineage/parent chain with
   'conj lam' / mkconj): non-identity conjugates are skipped (M1: do not re-conjugate) unless
   `--allow-reconj`.  [H] the name/sidecar test cannot see conjugate lineages without sidecars (e.g. P6's
   138@24, whose start is a stage file).
6. path_certified (informational): true iff every kernel call of the job so far started inside
   (A, AD, stage GD cap) or ran with repair_keep 1.
7. Added from M1's findings (00:00-00:15 UTC): `--beam-rk 0,1` (repair_keep per beam seed), `--repair-keep alt`
   (rk = seed % 2: matched rk 0 / 1 comparison across jobs without doubling job length), `--cap-a` / `--cap-ad`
   (search caps below the target's, e.g. T05 AD4 side `--cap-ad 4`; recorded results are still filtered by the
   target limits only), `--stall-stages N` (default 2: a lineage is dropped after N consecutive stages without
   a change in its own (A, AD, G, GD) set; M1 7.0), `--allow-reconj`.  The conj3 screen is split into 8
   k-slices with one lock each, so concurrent jobs on a new start share the 144 s screen.

## runner.py (sequential overnight runner)
See the docstring for the plan format.  Per block: CPUs assigned to operators in plan order; one job per
CPU through guard/xsrun (unit xs-P-<prefix>-<block>-<n>, XS_MEM per job), refilled every poll; job queue
per operator = rechained starts first, then rounds over (start x grid point) with a new seed per job;
results harvested while jobs run (sidecar present = complete) into ROOT/<Txx>/found/ after a second
aes_check, hard-limit filter, (A, AD, G, GD) weak-dominance filter against found/ and at most 2 structures
per tuple; new block-local (G, GD) frontier points become starts (max_starts); early stop by class
beyond the known frontier (LEDGER.json frontier + found/ at block start) + grace, or stall_minutes;
leftover minutes carried to the next block; `ledger.py run` after each block; hard stop at deadline_utc;
STATUS.md (blocks + frontier per target) every status_every_s; STATE.json for restart (resume = re-adopt
running units, keep the block end time, queue cursors, counters).  M1's drop rule as an operator option:
`"drop_start": {"within_gates": 1, "gd_slack": 2}` drops a start for that operator once all its round-0 grid
jobs are done and none recorded G <= start G + 1 at GD <= start GD + 2.
Added for the coordinator's night rules (00:05 UTC): early stop `first_minutes` / `stall_minutes` on points
"beyond known" ((A, AD, G, GD) weak dominance against LEDGER.json fronts + ROOT found/ + earlier beyond points
of the block); `"carry": "flagged"` + `"takes_carry": true` (leftover pool to T07, then T04, then T08);
per-operator `starts`; `tuple:A/AD/G/GD[:N]` start rule (ROOT found/, LEDGER.json, best-1400, hub archive);
.bfx starts converted to verified NCFF copies in ROOT/starts/; `max_per_start`; `rechain_gd_max`; the
ledger runs in the background after each block (the next block starts at once) and once more at the end.
The night plan is generated by ~/xs-campaigns/2026-11-16-night/mkplan.py -> plan.json (edit the script).

[H] Known limits: a job killed at a block end loses its unfinished stage (results already written stay);
the drop rule counts only round-0 jobs; `active_units` failing (systemctl error) keeps jobs "alive" until
the overdue stop (job seconds + 150 s).

## Tests and validation (UTC 2026-11-15/16)
- 23:54 smoke (T04, NIST 117@19, conj 188:0, g:26:25,m:21:25, 70 s budget): 126@26 conjugate (P3: 126@26)
  -> 116@23 -> 116@20 in 51 s; 4 files written, aes_check OK, sidecars complete.
- 23:55-00:41 validation from scratch on CPUs 0-7 (runs in ~/xs-campaigns/2026-11-16-night/m2/validate/, summary
  script m2/vsum.py; one job = one CPU; every listed circuit aes_check OK, sidecar complete):
  - **T04 32/4/114/19 reproduced** from NIST 117@19, conj 188:0 [C, 3 of 6 jobs]:
    schedule g:24:300,m:21:360,m:20:300,m:19:360 (M1-style): 114@19 at t = 879 s (seed 15, rk 1) and 1216 s
    (seed 16, rk 0; also 113@20 at 866 s); schedule g:30:300,m:26:400,m:21:360,m:20:300,m:19:360: 114@19 at
    1592 s + 113@20 at 1028 s (seed 13), 118@19 (seed 14); schedule g:26:300,m:21:360,m:19:360: 115@19 +
    114@20 + 113@21 (seed 12), 120@19 (seed 11).  Total 2.25 CPU-h for the 6 jobs, i.e. ~45 CPU-min per
    114@19 lineage [H, 6 jobs]; fastest 14.7 CPU-min.  Today: 114@19 first after 1.65 CPU-h of P3 lineage
    (M1 s.1), certified route P5 NIST -> 112@22 ~23 CPU-min + rkG1 3 mix stages x beam 2 (~36 CPU-min).
  - **T07**: random-seed lineages from 140@25 (250:4 x4, 97:0 x3, rank:6 = 250:4 via the screen x1): best
    140@23, 0 of 8 reach <= 139 [C, 8 jobs, ~2.3 CPU-h].  Replay with P6's own stage seeds (conj 250:4 ->
    k:31:200:s2004 -> k:27:200:s2011 -> k:27:200:s3011): 140@27 -> 140@24 -> **139@23 in 598 s**, the same
    tuples as P6's c3-140 run [C].  Polish of P6's 139@23 (k 240 s): **138@24** with P6's seeds 20378 (cap 27)
    and 17446 (cap 25), and with 1 of 3 random seeds [C, 5 jobs].  Polish of OUR replayed 139@23 (a different
    structure, kernel time limits are not deterministic): 138@26 once, 0 of 8 seeds 138@24.  So the k stage
    is P6-equivalent; the T07 lineage needs seed luck at the conjugate stage (P6: 1 of ~12 conjugate
    pipelines reached 139@23; M1 s.2) [H].
  - conj3 screen of 140@25: rank 6 = 250:4 score 39, identical to P6's c3-140 picks [C]; sliced screen: two
    jobs on one new start finish it in 72 s instead of 144 s [C, dry run].
- 00:16-00:27 mini runner tests (CPU 7, plans m2/mini-plan.json): launch through xsrun from inside the
  runner's own unit works; harvest, rechain, stall stop + carry (53 s carried to the next block, block end
  moved by exactly that), background ledger; stop of the runner unit mid-block and restart: the running job
  was re-adopted, the block kept its end time, counters continued [C].
- 00:41-00:52 dry run 1 (m2/dry1, 2 blocks x 5 min, CPUs 0-7, real ledger.py run after each block, 15 s):
  dryT04 early-stopped by the stall rule at 2.6 min (no point beyond the known front), 141 s carried to
  dryT07 (takes_carry), dryT07 clipped by the plan deadline; 84 jobs, 14 files in found/, every CPU busy.
  Found: the old next_job could launch an identical (start, grid) job twice while others waited -> replaced
  by a per-round "taken" set + in-flight check (dry run 2 tests it).
- 00:52-01:02 **dry run 2** (final code; m2/dry, log m2/dry-runner.log; runner = one unit xsrun P 0-7): dryT04
  every (start, grid) combo once per round (188:0 / rank:1 / rank:2 on 2 starts), M1 drop rule fired for both
  conjugate starts, stall stop at 2.5 min, 145 s carried to dryT07; runner unit stopped at +4 min while 8 jobs
  ran and restarted 15 s later: "BLOCK RESUME ... running jobs 8", jobs re-adopted and harvested, block end
  kept; dryT07 clipped to deadline - 60 s; background ledger after each block + final ledger run; 57 jobs,
  12 files in found/, no unit left behind [C].  Found and fixed: a rechained conjpull result given a non-id
  conjugate was skipped (no re-conjugation) and the job ended in 0 s; it now falls back to the identity pull.

- 01:03-01:10 smoke of the M3/M4 operators with the plan's flags, as the runner calls them (m2/opsmoke):
  satlns (T03, p1, side 0.6, gd 19) ok; rebase (T08 168@13, cap 13 --moves --relax 150) ok, 169@13;
  bottom (T09 41/136, cap 12, --amax 39) ok, **40/4/136/12 in 83 s** (new (A, AD, G, GD) Pareto point, aes_check
  OK; copied to ~/xs-campaigns/2026-11-16-night/m2/found/ for the ledger); bottom (T06 134@13) ok.
  rebase is **not-applicable** on the planned T06 (134@13 family, AD4, no --moves), T10 (NIST 59@10, cap 9),
  T09 (41/136, cap 11) and T02 (174@14) starts [C, operator exits 0-2 s] -> those CPUs were moved to bottom
  (T06, T09), conjpull (T10) and satlns (T02) in mkplan.py; the runner now also drops a start for an
  operator that answers not-applicable, or after 3 instant failures.

- 01:55-02:04 plan revision for M3's / M4's final findings (coordinator): runner gained block `pre_cmds` (+
  `refresh_every_s`, background) for the satlns span-index rebuild, `{GD}` / `{GD+n}` flag placeholders with
  `gd_room` / `g_any_gd` (grid points outside the tradeoff room are skipped; rechain obeys the same room), and
  `drop_if_result` (e.g. satlns.pool.n_pooled < 30 drops the start).  Mini test (m2/mini3, CPUs 6-7, 2.5 min):
  index rebuilt in 2 s at block start; 112/21 got only --gd 21 (22, 23 outside room 21), 114/19 got 19, 20, 21;
  satlns walks recorded 113/20 and 113/21 (known tuples) [C].  plan.json sha256 ed269b70... (675 min).

## Launch (night)
    python3 ~/xs-campaigns/2026-11-16-night/mkplan.py          # writes plan.json
    python3 nonlinear/boolflux/campaigns/targets/runner.py --plan ~/xs-campaigns/2026-11-16-night/plan.json --check
    XS_MEM=3G ~/xs-campaigns/guard/xsrun P 0-19 night-runner ~/xs-campaigns/2026-11-16-night/runner.log -- \
        python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/campaigns/targets/runner.py \
        --plan /home/joebachir20/xs-campaigns/2026-11-16-night/plan.json
Watch: ~/xs-campaigns/2026-11-16-night/STATUS.md, runner.events.log.  Stop: `systemctl --user stop
xs-P-night-runner`, then `runner.py --plan ... --stop-jobs` (jobs otherwise end by their own --seconds).
Restart: the same xsrun command (resumes from STATE.json).

## M3: ops/rebase.py and ops/bottom.py (agent M3, 2026-11-16 00:00-02:45 UTC)

Files (all M3): `ops/rebase.py`, `ops/bottom.py`, `ops/m3common.py` (adapter on `common.Recorder`: per-candidate
parent + method in the sidecar `lineage`/`how`; one capped kernel stage via hub.ops._kernel with repair_keep;
`--cpus K` = K-1 extra worker processes with seeds seed+1000 i, merged into DIR at the end), `ops/m3lib/`
(verbatim copies of strategies/P6 skelan, botbasis, hybrid, paarb, l3scan, rebase -> p6rebase; T3 pairs,
prodswap, gf4basis, gf4build, nbscan; P7 s1lib, bsel, bopt, bbuild; edits only: sys.path depth, `from p6rebase`,
bopt `CUT` (AND level of the bottom, was 4)) and `ops/m3lib/gbasis.py` (new: generalised class re-basing).
Runs and logs: `~/xs-campaigns/2026-11-15-targets/M3/runs/` (validation v-*, v2-*, screens screen/*).
Status values in result.json: ok | not-applicable (structure absent; exit 0 at once) | error.

### rebase.py (P6 method generalised)
- Classes (gbasis.py): "top" products = ANDs feeding no AND; grouped greedily by a common operand FUNCTION Q over
  the three trivial operand variants (L,R), (R,L), (L+R+1,R); class {Q R_i} -> {Q R'_t}, R'_t = sum_{i in v_t} R_i
  for any basis {v_t}: A unchanged, outputs stay expressible.  Depth bound = per-output Kraft at cap D over class
  products (re-based) + all other output terms at their Huffman arrivals; exact min-max over all class combos by a
  Pareto merge of partial sums [C in the botbasis case: non-class ANDs fixed at Huffman-earliest arrivals].  Bases:
  all for class size d <= 5, else identity + transvections + 3000 random (heuristic).  Reproduces botbasis exactly
  on NIST 183@13 / our 177@13 (cap 12: current 1.75, best 1.00, 51 feasible combos) and on the P6 variant 181@15
  (best 0.75) [C, 0.1 s each].
- Cap: `--cap D`; else `--goal depth` (default for T02 T06 T08 T09 T10) = lowest D in [GD-3, GD-1] with bound <= 1
  (else not-applicable unless --moves); `--goal gates` = min(target GD, start GD + 2).
- Per parent: (with `--moves`, AD3 GF(4) circuits only) T3 one-point coordinate moves priced by the bound, sharded
  over workers; variants with strictly more slack are processed first.  Then feasible combos -> P6 hybrid builds
  (`--builds 160`, --paar shared layer, `--slack3 0` = P6 setting of the 181 build) -> `--top 3` lowest-G distinct
  builds -> `--stages` kernel stages (caps A <= ref A, AD <= ref AD, GD <= D, objective cost,gd, repair_keep 1)
  -> optional `--relax S` stage at D+1 (result re-enters the pool).  Pool members (results) become parents again.
- Defaults changed after validation: builds 160 (builds cost ~0.1 s), slack3 0, move scan before the parent's own
  builds, scan time capped by the deadline (the first validation overran T by 237 s: fixed).

### bottom.py (P7 method generalised)
- Cut K = start's AND depth (`--cut`); 4 base Y-forms = independent degree>1 operands of the level-K products;
  outputs must be y_j = c_j + sum_i Y_i u_ij(x) without junk (else not-applicable); bopt SA (P7 code, 30k
  iterations, `--pw 0,3` alternating, exact per-output Kraft at `--cap`, A cap `--amax` default target A) ->
  bbuild -> kernel polish (caps A <= build A (`--polish-cap-a build`), AD, GD; 300 s).  `--plan-seeds` replays
  exact P7 bopt seeds; `--init own|mix` starts SA from the start circuit's own bottom when it fits the model.

### Validation (same starts as P6 / P7)
| op | start | result | CPU time | note |
|---|---|---|---|---|
| rebase | P6 coordinate variant [14,25,180,72] of 177@13 (181@15, P6 l3scan emit) | **35/3/181/12** | 258 s, 1 CPU | 159 combos, 159 builds in 17 s, build 198@12, one 240 s kernel stage; other builds 201 -> 185 [H] |
| rebase | archive 177@13, --moves (old ordering, 40 builds, slack3 1) | 182@12 | 2 CPU x 2040 s | the move scan found P6's 8 slack variants (765 scanned, 741 <= 1, 8 at 0.75) [C]; 181 not reached in that ordering |
| rebase | archive 177@13, --moves --stages 1 (fixed ordering, defaults) | **35/3/181/12** | 469 s, 1 CPU | scan 215 s -> variant [14,25,186,72] first -> 159 builds in 14 s (best 198) -> kernel 240 s; P6's 181 reproduced end to end [H for the kernel step] |
| bottom | NIST 45@12, --plan-seeds 7002 --pw 3 | build 41/4/138/12 (85 s, identical to P7's plan), polish -> **41/4/137/12** at 386 s; third plan 41/137 -> **41/4/136/12** at 880 s | 1 CPU x 880 s | P7's 136/137 reproduced [H for the kernel step] |
| bottom | NIST 45@12, random seeds | 42/4/138/12, 41/4/139/12 | 2 CPU x 1800 s | 9 + 10 plans; seed-dependent |

### Applicability screen (5-10 min per target and operator; [C] = structural fact, [H] = runs)
- T01, T03 (A28): both not-applicable [C]: the 13 top products have 13 distinct operand functions (no class, even
  with complements folded) and outputs carry level-1/3 AND terms, so they are not of the Y x form.
- T04: rebase applies (6 classes of 2) but the bound is not binding (Kraft 0.06 at 19); builds 127-129@19, kernel
  150 s -> 119@19 (ref 117) [H].  bottom: SA needs 21-22 bottom products (A 36-37 > 32) on 116@20 / 119@18 fronts
  [H, 1 plan each], own-bottom init impossible (complemented operands).  No use tonight.
- T05: bottom needs 22 products (A 36) [H].  rebase (9 classes of 2) gives depth-tight rebuilds of the 103: hybrid
  build 116@24 at AD7, kernel at cap 32 -> 106@28, 105@29 [H]; pulls at caps 31 / 29 (see below).
- T06: rebase bound at cap 12 is 1.875 (139: 2.0) -> no GD12 by re-basing [C, gbasis case]; at cap 13 builds 134-138,
  kernel 134-135 (no gain) [H].  bottom at cap 12: SA needs 29 products -> 45/4/151-154/12 (A > 34) in 5 plans [H];
  at cap 13 random SA 22-23 products (A 38-39), own-bottom init: plan stays at the own bottom (outputs not Kraft-
  feasible in the model), build 34/4/141/14.  No use tonight.
- T05 pulls (rebase --cap 31 / --cap 29, 2 x 270 s stages, 1080 s each): 105@30, 106@27 / 105@29, 106@27; no G <= 103 [H].
- T07: rebase bound not binding at 24-27.  From 138@24 (cap 24, 540 s): 141@22, 142@21, 144@20, 150@19 (all
  dominated by the known 140@22 / 141@19); from 137@28 at cap 27 with --moves (1200 s): 143@25, 144@23 [H].  No use.
- T08: rebase is the GD12 tool (validated) and, at the same cap, a gate move for GD13:
  - `--cap 13` from P6's 168@13 (seed 41): build 175 -> kernel 200 s -> **35/3/167/13** at 489 s; second seed (52):
    build 176 -> **35/3/165/13** at 414 s (new A35 AD3 GD13 best; P6's lineage ended at 168).  From 167@13 (seed 51,
    900 s): 168 x2; from 165@13 (seeds 81, 82, 900 s each): 165 x3, 166 x2, 168 [H]: plateau at 165.
  - GD12 pull from 165@13 (--moves, 1200 s): its bound at 12 is 0.75 (slack), but builds start at 210+ (relaxed lower
    levels), best 189@12 [H]; the 181@12 family stays the GD12 best.
- T09: bottom is the tool (validated); rebase bound at 11 is 1.75 -> no GD11 by re-basing [C, gbasis case].
  `--init own` (SA from the NIST 45's own bottom, all outputs Kraft-feasible at 12): first build 42/4/137/12 at 79 s,
  polish no gain (540 s); `--init mix` 1500 s: 42/4/139/12 best [H]: random-init P7 settings (`--pw 3`) did better.
- Copies of the new and reproduced circuits with sidecars: `~/xs-campaigns/2026-11-15-targets/M3/found/`.

### Recommended use in tonight's blocks
- T08 block: `rebase.py --in <best GD13> --target T08 --cap 13 --stages 1 --stage-seconds 200` (gate moves at
  GD13: 168 -> 167 -> 165 tonight), seeds in parallel on all CPUs, pool = the best GD13 circuits; plus
  `rebase.py --in <GD13 circuit> --target T08 --moves --stages 1` for GD12 (reaches 181 in ~8 CPU-min).
- T09 block: `bottom.py --in NIST 45@12 --target T09 --pw 3 --polish-seconds 300` (P7 settings; 136-137 in 15 min
  per CPU); then other operators on the 136/137.
- Not useful tonight (screens above): T01, T03 (not applicable), T04, T05, T06, T07, T10.

- T10: rebase at cap 10: exactly one feasible combo (identity) -> the 59@10 is rigid under re-basing [C, gbasis case],
  kernel 4 x 150 s stays 159; cap 9 bound 2.0 [C].  bottom: not-applicable (59@10 outputs carry linear / Y junk;
  the 48@11 front has no Kraft-feasible decomposition at GD10) [C].

## M4: ops/satlns.py, span-pooled SAT LNS (agent M4, 2026-11-16 00:00-02:45 UTC)

Owner: M4. `ops/satlns.py` is copied from strategies/P1/unionsat2.py v2.4 and generalised (P1's folder is
untouched). It records through M2's `common.Recorder`. Data, logs and scripts are in
`~/xs-campaigns/2026-11-15-targets/M4/` (runs/val, runs/screen, scripts/screen.sh = exact commands,
scripts/agg.py and scripts/qstats.py = log summaries). Labels [C] / [H] as above. LOCAL ONLY.

### What it does
- **Span index** (`--build-index`, file `M4/spanindex.json`). It covers every circuit file in best-1400, the hub
  long archive, results/aes, the NIST pin, every study `found/` (nested), every campaign `<agent>/found/`,
  P1/shared, and the `--pool-extra DIRS` (recursive). Each file is keyed by the canonical RREF of
  (1, x0..x7, AND truth tables). At 00:12 UTC: 4,827 files, 552 spans. The build is incremental (mtime + size)
  and takes 4-13 s.
  **Concurrency** [C, by construction]: the file is only ever replaced atomically (`<index>.tmp<pid>`, then
  `os.replace`), so a reader sees either the old or the new complete file. Concurrent writers each write a
  complete index; the last rename wins, and a file added in the meantime is picked up by the next build.
  Without `--no-index-update`, every job rescans (5-15 s) and writes. With it, the job reads only (it falls
  back to a build if the file is missing). Kernel scratch files go to the job's own `DIR/kernel/`.
- **Pool / model.** The pool is all indexed circuits with the start's span (at most `--maxcirc` 600, sorted
  by G, GD). From them the model takes their gate templates, a closure (at most 6000 extra templates) and a
  rotation closure of the current circuit. The SAT model (glucose4) encodes gate-level availability up to
  D (= `--gd`; default the target GD; raised to the start GD if the start is deeper), A <= target A
  (cardinality) and total templates <= K. AD is checked on decode: 0 rejections in 28 runs (76k queries).
- **Queries, fast profile v3**:
  - sideways (K = G, at least one freed template dropped): S1 (rl 1) .80, S2 (rl 2) .08, S0 (unrestricted) .04;
  - improving (K = G - 1): I1 .05, I2 .03;
  - focus: after every accepted sideways move, one K = G - 1 query on the templates that move changed plus
    1-2 hops, at most 60 templates;
  - time limit 2 s x a per-plan factor, enforced by a timer and a propagation budget (`--prop-rate` 1.2e7);
  - `--budget` caps each plan's share of SAT time (S0 .08, S2 .10, I1 .05, I2 .03);
  - in the last 90 s only rl-1 queries run (rl 0 / pull queries can overrun their limit: up to 162 s at
    an 8 s limit, even with the propagation budget [H, cause not found]; rl-1 queries never overran).
- **Options:**
  - `--polish-every N --polish-sec S --polish-share 0.25`: kernel bfx-94a75e2c18 with repair_keep 1 and
    caps A/AD/D on the walk state. The result is adopted if its (G, GD) is lexicographically better; this
    starts a new epoch, and the pool is re-selected if the span changed.
  - `--epoch S`: rebuild the model around the walk state every S s.
  - `--excursion N --exc-up 1 --exc-moves 12 --pull-tries 6 --pull-kernel 10`: walk at D + 1, then a kernel GD
    repair and SAT "pull" queries back to D; revert if all fail.
  - `--profile p1`: P1's v2.4 query mix with 20 s limits, for A/B.
  - `--save-walk N`: also keep every Nth walk state in DIR/walk/.
- **Recording.** A decoded or kernel circuit is offered to `Recorder.offer` (aes_check, sidecar) if it is
  inside the hard limits and Pareto-new in (G, GD) for the run (start included). This includes run-local
  points at GD above the target cap, e.g. during excursions; the runner / ledger filter them.
  `DIR/queries.jsonl` has one line per query (plan, kind, rl, side, free, allowed, K, result, seconds,
  propagations, conflicts, and G/GD for SAT answers). `result.json` -> `satlns` holds stats per plan x
  neighbourhood size, walk / excursion counts, pool and model sizes.

### P1 log analysis (the basis for the changes; 64 logs, 27.6k queries) [C counts, H reading]
- UNKNOWN answers took 18,500 of 44,000 SAT-seconds (42 %).
- Improving rl-1 queries with <= 40 freed templates: 1,411 queries, 0 SAT.
- The 8 G drops: 7 took <= 0.4 s (rl 1 / rl 2, 14-54 freed templates), 6 of them sideways. Only the 129/19
  came from an unrestricted query (6.2 s).

### Validation: P1's 28/5/129/19 from the hub 130/19 (T03, D 19, pool as of 17:03 UTC = 78 circuits)
| run (CPUs 13-16, 900 s each, 23:55 UTC) | queries | 129/19 reached at | by |
|---|---|---|---|
| fast v1, seed 1 | 4,338 | - | - |
| fast v1, seed 2 | 4,377 | **288 s** | focus query (48 freed, 0.25 s) |
| fast v1 + kernel polish every 25 accepted moves (15 s), seed 3 | 1,594 | **583 s** | kernel polish of a sideways walk state |
| P1 v2.4 mix (`--profile p1`), seed 1 | 1,023 | **780 s** | P1-style query (49 freed, 0.36 s) |

3 of 4 runs reproduced it in 15 min: 3,600 CPU-s for 3 hits, about 1,200 CPU-s per hit [H, 4 runs]. For
comparison, P1 found it once in its first 900 s run and never again in about 6 CPU-h from other starts.
All 3 hits passed aes_check.

### Applicability screen (00:14-01:52 UTC, CPUs 13-16, 780 s per job unless noted; kernel polish every 40 accepted moves for 10 s)
| target | start (pooled circuits in its span) | D | result |
|---|---|---|---|
| T01 | 131/22 L1 (139) | 22 | 0; with excursions: 0 (6 excursions, 3 pulled back, no gain) |
| T01 | 131/22 T1 (139), 1,500 s | 22 | 0 (polish took 44 % of the wall time, hence `--polish-share`) |
| T01 | 130/24 (139) | 24 | 0 |
| T02 | 174/14 P2 (10) | 14 | 0 in 5,189 queries. With excursions to D 15 the walk drops 174 -> 165 @15 in 4 min, but 19 of 20 pulls back to D 14 fail (and 165/15 is far above the archive 153/15) |
| T03 | 127/22 (188) | 22 | 0; with excursions: 0 |
| T03 | NIST 128/20 (188) | 20 | 0 |
| T03 | 129/19 (188) | 19 | 0 with excursions (9 excursions; the pulls only return 129/19) |
| T03 | 129/19 (188), 1,500 s | 20 | 128/20 by kernel polish (= the NIST tuple, not a gain) |
| T03 | NIST 124/27 (106) | 27 | 0 |
| T04 | 114/19 P3 (94) | 19 | 0; with excursions: 0 |
| T04 | 113/20 P3 rkG1 (94) | 21 | **32/4/112/21** at 584 s (focus query, 53 freed, 0.21 s) |
| T04 | 112/21 (above) (95) | 21 | 0 |
| T04 | 113/20 rkH1; rkG1 seed 61, 1,500 s; rkJ1, 1,500 s | 21 | 0, 0, 0 |
| T04 | 113/20 rkG1 (95) | 20 | 0 |
| T05 | NIST 103/32 (247) | 34 | 0 (walk stays at 103/32-34) |
| T05 | 104/29 AD5 (370) | 32 | 0 |
| T07 | 138/24 P6 (1) | 24 | 0 |
| T09 | 136/12 P7 (1) | 12 | 0 |

**New circuit:** `~/xs-campaigns/2026-11-15-targets/M4/found/satlns-a32-ad4-g112-gd21-efda23263f.circ.txt` with
its sidecar (a copy of runs/screen/r2-t04-d21/).
- aes_check OK, A AD G GD = 32 4 112 21.
- T04 tradeoff gates_for_depth (GD 21 <= 21, G 112 <= 114).
- Not dominated by the index (archive + every campaign found/ as of 00:43 UTC; the best points there were
  113/20 and 112/22) nor by the pin (aes_check: "new Pareto point on pinned set: YES").
- Reached from 113/20 by a sideways walk at D 21; not reproduced in 3 more runs (63 CPU-min).

### Totals and what the logs say (28 runs, 25,200 CPU-s wall, 76k queries, 16,800 SAT-s, 6,700 s kernel polish) [H]
- **Gains at the walk cap D:** 4 in total: 3 x 129/19 (validation) and 1 x 112/21. 2 came from focus
  queries, 1 from a P1-style query, 1 from a kernel polish. Focus queries: 28k queries, 22 % of SAT time.
- **No gains:** S0 (19 % of SAT time), S2 (12 %), I1 + I2 (14 %), pulls. S1 (17 %) is the cheap walk
  engine: 77 % SAT, about 0.08 s per query.
- **Excursions** (8 runs): the walk does move above the cap (T02 down to 165 @15), but pulls back to D
  returned the pre-excursion G or failed, 0 gains. Off by default.
- **Pool size matters.** Spans with 78-370 pooled circuits gave all the gains. Spans with 1-10 circuits
  (T02 P2 line, T07 P6 conjugate, T09 P7 rebuild) only reshuffle one circuit; there the operator walks
  fast but finds nothing.

### Recommendation for tonight
- **Role:** satlns is a plateau finisher on a fresh frontier point. It is not a gap-closer: in 13-25 min it
  never moved T01, T02, T05, T07 or T09.
  - Use it as a second stage (rechain) on new T04 and T03 points made by conjpull / rebase, at the point's
    own GD and at +1 / +2 (tradeoff room: T04 GD <= 21, T03 GD <= 22, or any GD for G <= 123).
  - Only use it when the point's span has >= ~50 pooled circuits. `result.json` -> satlns.pool.n_pooled
    shows this; a cheap runner rule would be to drop the job if it is under 30.
- **Flags:** `--gd <cap> --polish-every 40 --polish-sec 10 --no-index-update`, everything else at the
  defaults (profile fast v3, focus 1.0, qsec 2, budgets, prop-rate 1.2e7, polish-share 0.25, excursions off).
  - Job length 900-1,500 s; P1 data and the validation put a hit at 300-800 s when one exists.
  - XS_MEM 1500M (observed RSS 330-470 MB, D <= 34).
  - Seeds: vary per job. Several jobs on the same start are fine (independent walks).
- **Index:** once per block, `python3 nonlinear/boolflux/campaigns/targets/ops/satlns.py --build-index
  --pool-extra ~/xs-campaigns/2026-11-16-night` (adds the night's found/ circuits to the pools). Jobs then
  read it with `--no-index-update`.
