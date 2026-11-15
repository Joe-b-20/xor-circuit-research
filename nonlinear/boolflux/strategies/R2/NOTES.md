# R2: affine-slack window redesign (hub operator `aslack`), 2026-11-15

Code: `aslack.py` (window, span algebra, product search, re-synthesis), `op_aslack.py` (hub operator,
common CLI + `--npolish`, `--hunt`), `calib.py` (per-window calibration). `aslack_v1.py` = first
version (used by calib1). Frozen copy used in the A/B: `frozen-ab/` (md5 in data dir).
Data: `~/xs-campaigns/2026-11-15-study/R2/`.

## Method

Representation: all functions are 256-bit truth tables (Python ints); spans are GF(2) row echelon
dicts (leading-bit pivots), one elimination per test.

1. **Window**: S = k ANDs at one AND level L (2-5; "hunt" mode up to 8), seed AND plus ANDs with the
   most shared operand-cone leaves / downstream readers (25%: random). Same level => antichain. D =
   linear gates reachable from S through linear gates only, optionally limited to depth dd (0-3) or
   full. Targets T = signals of S u D read outside S u D, or outputs.
2. **Requirement.** Each target's affine form over D's leaves and S is split into a fixed part (leaves
   that depend on S or have AND level > L; kept as is) and g_t over (1, C, S), where C = slack signals:
   independent of S (not in TFO(S)), AND level <= L ("wide": every such signal; "local": D's leaves +
   S's operand cones), deduplicated by table. V = span(1, C), R = span{g_t mod V}, r = dim R.
   New products q_j = a_j * b_j with a_j, b_j affine over O = slack signals of AND level <= L-1.
   Requirement: R subset of span{q_j mod V}. Hence m >= r, and an A reduction needs r < k.
   AND depth cannot increase (new ANDs at level <= L, targets use signals of level <= their own).
3. **Search.** For a fixed operand a, b -> a*b mod V is GF(2)-linear in b, so one elimination of
   {a*o_i} against W = V + R (R pivots tagged with R coordinates) gives every b in span(O) with
   a*b in V + R, and its R tag. Operand candidates a: all single signals (both polarities), random
   pairs, original operands first; when dim span(O) <= 10 (AND level 1: affine functions of x)
   EVERY non-constant affine a is enumerated (then the search for m = r products is exhaustive for
   that window). Pick: greedy spanning set of tags, cheapest-first with noise (3 picks per window);
   operands re-decoded sparsely over O (shallow signals first).
   Hunt extension (heuristic): when k - r >= 2, add e random "free" products z to R (m = r + e < k),
   so products may leave V + R.
4. **Re-synthesis** of only the window's linear logic: per target, new form = fixed part + q's +
   V-part, the V-part decoded sparsely over C (random elimination orders, half shallow-first; fewest
   terms, then lowest gate level) both directly and as "old V-part + correction", the smaller kept.
   Operand rows + target rows -> shared pair merging (Paar, count >= 2) -> each row combined
   lowest-level-first. Kept gates are re-emitted lazily (topological), dead gates removed (live()).
   Every rebuilt circuit is checked on all 256 inputs inside the operator; the hub verifies again.
5. **Operator** (`--seconds T`): 45% of T on windows (30% chaining: next window from the best raw
   result), then the best `--npolish` (3) raw results (lexicographic objective under the caps, at most
   2 per (A, G)) polished with the gate kernel (hub `ops._kernel`, same settings as op_polish).
   Candidates: raw + polished circuits the archive would place, highest hub gain first.

## Results

### Calibration 1 (aslack_v1, 14 front circuits of the long archive, 392 windows, 00:14 UTC) [H]
`calib1.jsonl` (stopped early at 392 of 750 windows to free CPU 19 before 00:20).
- 366/392 windows spanned (m = r products found), 366/366 rebuilt circuits correct on 256 inputs.
- Time per window: mean 0.34 s, median 0.26 s, max 3.9 s (wide C at level 4-5: 100-120 signals).
- r < k in 26/392 windows (dimP = k always: no product is redundant mod V). (k, r, L): (5,4,1) x12,
  (3,2,1) x5, (4,3,1) x4, (5,3,1) x2, (5,4,4) x2, (4,3,4) x1. None of these had a spanning set of r
  products, i.e. no A reduction.
- r = k in the other windows: then an A reduction inside the window is impossible for ANY products
  (R in span(q) mod V needs m >= r) [C, within the window model of item 2: fixed S, D, targets, C].
- New intermediate nonlinear values: in 231/366 spanned windows at least one new product differs from
  every old product of S (1 new: 149, 2: 62, 3: 18, 4-5: 2).
- Raw G change (before polish): dd 0: mean +1.6, 23/57 equal; dd 1: +2.1, 21/75 equal; dd 2: +3.6,
  2 lower; dd 3: +4.9; full D: +11.3 (re-synthesising large linear layers is worse than the polished
  original). GD rose in 226/366 (v1 decoding ignored levels; v2 decodes shallow-first).

### A-hunt (exhaustive at level 1) [C within the window model, per window]
Tests on 8e7cd56e3482 (32/4/125/15), windows up to k = 8: r < k is easy to reach with larger windows
(e.g. (8,6,1), (7,5,1), (5,4,1)), but for every level-1 window tested (exhaustive over all affine
operands a, all b by elimination) no set of r products spans R: no A reduction with m = r. The free-
product extension (m = r + e < k, random z) found nothing in 16 tries [H].

### Operator tests (30 s, snapshot) [H]
- 1b0f3813aa19-like 28/5/124/27 (test1): 51 correct rebuilds, best raw = input metrics; candidates
  are dominated near-front points (G +2..6, GD +2..4).
- 8e7cd56e3482 32/4/125/15 (test2): 91 distinct raw circuits, best raw ties the input (125/15) with a
  different structure; candidates 125/16, 126/16.
All candidates pass hub.common.verify.

### A/B (hub style, 1 CPU, arms one after the other, same snapshot `snap` (long @ 00:15 UTC), seed 8)
- First base run 00:18-00:24 ABORTED (kept as `abbase-aborted-0018`): CPU 19 was shared with hub jobs
  placed on CPUs 17-19 by mistake (00:19-00:25, coordinator) and with my operator tests.
- base arm `abbase`: restarted 00:24 UTC from a fresh copy of `snap`; polish,pull,join,trb,osc,gen_skel,
  nursery 0.3, ad3_share 0.3; 1 h.
- test arm `abtest`: same + aslack (60 s, frozen copy), launched by `ab_test.sh`, which waits (sleep
  loop, ~0 CPU) until the base unit has ended. The two units are both "active" during the base arm, but
  only the base arm computes: the arms run ONE AFTER THE OTHER at ~1 CPU each (coordinator asked
  00:23; checked: the abtest unit held only bash + sleep, 60 ms CPU). No operator tests of mine on
  CPU 19 while an arm runs.
- Results (compare2.py --check, `ab_compare.json`; L1 eval_run in `l1eval/`) [H, one pair of 1-CPU-hour
  blocks; L1 found 0/1/2/4 front admissions in 11/5/3/1 of twenty blocks of ONE configuration, so a
  front count of 1 vs 0 alone does not separate the arms]:
  | arm | CPU-h | jobs | admissions | new frontier points | V (L1) | goal-near / met |
  |---|---|---|---|---|---|---|
  | base | 1.01 | 143 | 16 | 0 | 0 | 0 / 0 |
  | test | 1.01 | 83 | 33 | 1 (39/3/172/13, aes_check OK-new) | 2 | 0 / 0 |
  aslack in the test arm: 29 jobs, 0.47 CPU-h, 23 admissions, gain 8.22 (17.7 / CPU-h; next best
  operator in either arm 0.92 / CPU-h). The bandit gave it half the CPU after its first gain.
  The frontier point is an **A reduction**: parent 40/3/172/13 (join-made) -> 39/3/172/13 directly by the
  window move (raw, before polish; window k = 3 ANDs at level 3, r = 2, 2 new products, same G and GD).
- Per-job view of the 29 aslack jobs: windows found A reductions (raw) on A >= 36 circuits only:
  40/3/172/13 (21 raw), 37/4/121/14 (69 raw, all with GD +1..+2 so none was kept by v1), 48/4/151/11 (6),
  37/3/155/15 (9; 36/3/155/16 admitted), 39/3/172/13 (6). On A <= 35 front circuits: 0 A reductions;
  admissions there are same-cell ties with new structure (28/5/127/22 x3, 29/5/134/17 x3, 28/5/128/21 x4).

### v2 (after the A/B, 02:30 UTC; `code-v2/` md5 43d2f0d0 op, 0baabd7b aslack)
The A/B showed A-reduced raw circuits were discarded when their GD rose (lexicographic key put the cap
violation first). v2: chains into A reductions (least cap violation first), polishes the best two A
reductions with A cap = their A (kernel repairs GD), returns all of them. Tests (60 s):
37/4/121/14 -> 34/4/119/15 (A -3, G -2, GD +1); 48/4/151/11 -> 44/4/149/14 (A -4, G -2, GD +3).

### (a) Per-job improvement on fixed goal-near targets under their own caps (v2, 60 s jobs) [H]
`fixed/fixed.jsonl`: 13 tuples x 3 jobs = 39 jobs: **0/39 improved** (28/4/131/23, 28/4/133/20,
29/4/130/22, 28/5/127/22, 28/5/130/19, 32/4/116/20, 32/4/119/18, 33/4/108/19, 32/5/104/29, 35/3/140/25,
35/3/141/24, 43/4/141/12, 48/4/151/11). Each job did produce 4-40 feasible same-metric circuits with new
structure (the hub keeps up to 4 per cell). A reductions (raw) appeared only on 43/4/141/12 (2-3 per
job) and 48/4/151/11 (3-12), always with GD above the cap, which the 60-s polish did not repair.

### Kernel control for the A reductions (op_polish, A cap = what aslack reached, 2 seeds x 90 s) [H]
`kctl.log`:
- 40/3/172/13, caps 39,3,13: kernel stays at A 40 (2/2). aslack: 39/3/172/13 (raw window move).
- 37/4/121/14, caps 34,4,15: kernel reaches 34/4/117/15 and 34/4/115/15 (better than aslack's 34/4/119/15).
- 48/4/151/11, caps 44,4,14: kernel stays at A 48 (48/4/139/14, 48/4/141/14). aslack: 44/4/149/14.
So in 2 of 3 cases aslack finds A reductions that the kernel's repair mode does not find within 90 s.
These are all on redundant A >= 37 circuits, not near the A28-A32 goals.

### (b) Goal-directed run, goals B-G (goal_run.py, v2, 90 s jobs, 03:10-04:03 UTC, stopped early) [H]
`goal/log.jsonl`: 30 jobs over goals F,G,F,G,B,C,D,E (pool = 12 closest archive circuits per goal, A
allowed up to cap + 8). No pool improved: F 35/3/140/25, G 43/4/141/12, B 28/4/132/22, C 28/5/128/20,
D 32/4/117/19, E 32/5/104/29 at the end, the same as at the start. 0 goal hits. Stopped to free the CPU for
the cap-respecting descents below.

### Cap-respecting A descent (cap_descent.py: window moves accepted only with AD, GD within the goal caps
and (A, G) lexicographically lower; then kernel 60 s with caps (A reached, AD cap, GD cap)) [H]
- Goal G caps (44, 4, 140, 11), 240 s windows each: 48/4/151/11, 49/4/148/11 unchanged (raw: no A
  reduction keeps GD <= 11); 51/4/151/11 -> 50/4/148/11 and 53/4/152/11 -> 52/4/153/11 (both by the
  kernel; the raw window results kept A); 59/4/159/10 -> raw 57/4/165/11 -> 56/4/162/11. Under GD <= 11
  the window move's A reductions mostly disappear (they came with GD +1..+3).
- Goal F caps (35, 3, 138, 26): every start reached A 35 by RAW window moves, GD within the cap:
  36/3/144/23 -> 35/3/143/22 (aes_check OK, new vs pin; dominated in our archive by 35/3/142/22),
  36/3/146/22 -> 35/3/145/23, 37/3/148/21 -> 35/3/150/23, 38/3/148/18 -> 35/3/148/24, 39/3/148/22 ->
  35/3/153/25 (A -1..-4 at AD 3). None reaches G <= 138. Files: descF/found/*.bfx (+ .json).
- Second F descent from the F front (35/3/140/25, 141/24, 142/21) and two of the above, 240 s + 120 s
  kernel (descF2/descent.jsonl): no A reduction at A 35, no G <= 138. 35/3/140/25 -> 140/26,
  141/24 -> 141/25, 142/21 -> 140/26, 143/22 unchanged, 145/23 -> 144/22. Nothing better than the archive.

## Conclusion (05:30 UTC)
- Move works as designed. Over 10,000 rebuilt circuits were checked inside the operator and every one
  was correct on 256 inputs (func_bad = 0 in every calibration, test and job record). Typical time is about 0.3 s per
  window. It often creates new intermediate products: at least one new product in 63% of windows.
- Value: **A reductions on redundant circuits** (made by join/gen, A >= 36). In the A/B it produced the
  only new frontier point, 40/3/172/13 -> 39/3/172/13. Under F caps it took 36-39/3 circuits to 35/3 within
  the GD cap. On 48/4/151/11 it reached 44/4/149/14, where the kernel's repair mode with the same A cap
  stayed at A 48 (and also at A 40 for 40/3/172/13).
- No value near the A28-A35 fronts: 0/39 fixed-target jobs improved, the goal run made no progress, no
  goal B-G met. Exhaustive at level 1: no A reduction for any level-1 window subset of 8 A28/A29 circuits
  [C, window model].
- AND depth never increases by construction. AD reduction by the same move needs the targets' degree to
  be at most 2^(L-1) (an AND depth d function has degree <= 2^d). The one exhaustive test (the single
  level-2 AND of a NIST A28/AD5) found nothing. Not pursued further.

### Exhaustive level-1 scan [C, within the window model]
`scan_l1.jsonl` (scan_l1.py). 8 front circuits: 28/4/131/23, 28/4/133/20, 28/5/127/22, 28/5/130/19,
28/5/124/27, 29/4/130/22, 28/4/141/16, 28/5/137/17. For EVERY subset S (|S| >= 2) of the level-1 ANDs
(9 ANDs: 502 subsets; 10 ANDs: 1013 subsets): full downstream linear closure, wide slack (all signals
independent of S with AND level <= 1), new products with operands ranging over ALL non-constant affine
functions of x (both operands complete: a enumerated, b by elimination). r < k in 98 (9-AND) / 142
(10-AND) subsets, of which 85 / 127 have r = k - 1. **No subset admits m = r products** (0 spanned in all
8 circuits). For the r = k - 1 subsets, m = r is the only A-reducing size, so for them no A reduction
exists in this model. Case covered: replacing a set of level-1 ANDs by new level-1 ANDs, with targets =
the functions read outside the window's downstream linear closure, slack = level <= 1 signals. It says
nothing about moves that also change level-2+ ANDs, nor about m strictly between r and k - 1 for
k - r >= 2 (13 / 15 subsets per circuit). Identical counts across circuits with the same number of
level-1 ANDs suggest a shared stage-1 structure (not checked further).

## Failures / limits
- A reduction: never found. Necessary condition r < k holds in ~7% of 2-5-AND windows (level 1 mostly).
- Full-D windows re-synthesise whole linear layers and lose 5-20 gates vs the polished original.
