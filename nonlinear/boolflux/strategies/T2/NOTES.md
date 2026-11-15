# T2: targeted search for goals D and E (2026-11-15, CPUs 3-5)

Goals: D = A <= 32 / AD 4 / G <= 116 / GD <= 19; E = A <= 32 / AD <= 6 / G <= 102 / GD <= 31.
Data: `~/xs-campaigns/2026-11-15-study/T2/`.  Code here.  NIST pin 3d80774.

## Summary (05:30 UTC; final numbers in the last section)
- No circuit meets D or E; no circuit better than the starting points (E 32/5/104/29; D
  32/4/116/20, 117@19, 119@18).  Nothing in found/.
- E: about 70 kernel jobs in 7 walk variants: plain plateau walk, GD 36, unshare restarts, chains,
  depth release x3.  Plus all-pairs joins over 268 circuits (340k joins).  The lowest G at A 32 /
  AD <= 6 is 104 (at GD 29-42); 105@26 is the best fresh re-tightening.  Depth release reaches the
  104 level from 107@22, 106@24, 105@26 and 108@20 in one job each, never below it.  Census:
  L0+L1 = 33 and L4+L5 = 31 linear gates in all three AD5 104/105 structures (the layers trade
  gates, the sums stay), so a 102 needs a different structure, not a better layer [H].
- D: 32/4/19 always ends at 117@19 (= NIST): plain walk, unshare, AD-off alternation, front
  re-optimisation under exact per-output deadlines at cut levels 1, 2, 3 (45 / 50 / 70-gate
  fronts, 0 below).  [C] No single-layer linear rebuild of the 116@20 reaches GD 19 (Kraft test,
  all 5 layers).  [C] D is equivalent to a 9-AND front of <= 44 gates for 23 fixed functions with
  fixed deadlines (in front of the 117@19 back); in ~30 front jobs the kernel never found one [H].
- New tools: walk.py (caps / objective / elite / alt caps / unshare / chains), unshare.py, bfx_dl
  (per-output deadlines), front.py + frontwalk.py, join_pool.py, slp.py, bp.py, regions.py.

## Code
- `walk.py`: repeated gate-kernel jobs (kernel/bfx.c compiled into OUT/bin, same KDEFAULTS as hub/ops.py)
  under hard caps with a lexicographic objective (default `cost` only, so GD drifts freely under the
  GD cap); an elite pool keeps distinct circuits of equal objective; each job starts from the elite
  (p 0.75, mostly from the best class) or from an original start (p 0.25).  Goal-meeting results are
  checked with aes_check.py and written to found/ with a JSON sidecar.  Log: OUT/log.jsonl.
- `join_pool.py`: all ordered pairs of a pool through hub/join.py (`join_all`: every cut level),
  keeps every distinct product inside a metric box.
- `regions.py`: per-AND-level census (#AND, #linear gates per AND level).
- `slp.py`: exact SAT SLP re-synthesis of one linear region with gate-depth deadlines (pysat CaDiCaL;
  pair selectors, order-encoded levels, used-gate and colex symmetry breaking).
- `bp.py`: Boyar-Peralta SLP heuristic (exact distances over GF(2)^m, m <= 22) for one region.

## Structure of the starting points (regions.py) [C, counts]
AND / linear gates per AND level (linear gate level = max AND level of its operands):

| circuit | AND per level | linear per level |
|---|---|---|
| NIST 32/7/103/32 | 9,1,1,3,3,7,8 | 18,15,2,3,1,3,4,25 |
| NIST 32/5/104/30 | 9,1,2,8,12 | 18,15,4,4,6,25 |
| NIST 32/5/105/26 | 9,1,2,8,12 | 18,17,2,5,7,24 |
| ours 32/5/104/29 (617a1c3af391) | 9,1,2,8,12 | 17,16,4,4,7,24 |
| ours 32/6/104/31 (a882e2a69000) | 9,1,1,4,9,8 | 18,15,3,3,4,4,25 |
| NIST 32/4/117/19 | 9,2,4,17 | 18,18,3,16,30 |
| ours 32/4/116/20 (a43e1ae3d73f) | 9,2,4,17 | 18,17,3,16,30 |
| ours 32/4/119/18 (6e0debf39db2) | 9,2,4,17 | 20,18,3,16,30 |

- The NIST 103 is AD7 because its 5-AND GF(16) inverse is a chain at AND levels 2-6 and the 18
  final products start as soon as each inverse signal is ready (levels 4-7): the late products sit
  behind a sequential inverse.  No AD <= 6 circuit in the archive has fewer than 104 gates.
- D: at cap GD 19 the critical paths of the 116@20 run through every AND level (84 gates have no
  slack, from the top linear layer to the outputs): one level must be saved along every
  top-to-output path; the 116@20 saves one level-1 linear gate against the NIST 117@19 and pays one
  gate level.

## Runs and results (times UTC, 2026-11-15)
- 01:36 `ewalk1` (CPU 3): E walk, caps 32/6/31, objective cost, 600 s jobs, 47 archive circuits
  with A 32, G <= 104 (incl. AD7 103s as infeasible starts the kernel must repair).
- 01:36 `dwalk1` (CPU 4): D walk, caps 32/4/19, objective cost, 300 s jobs, 20 AD4 starts
  (116@20/21, 117@19, 119@18, 115@22).
- 01:38-01:45 `ejoin1` (CPU 5): all ordered pairs over 268 archive circuits (A <= 34, G <= 107,
  AD <= 7): 339,849 joins in 402 s, 4258 distinct products in 32/6/107/34.  Best per (AD, GD):
  AD5: 104@29-31, 105@26-28, 106@24-25, 107@22-23; AD6: 104@31-34, 105@28-30.  Nothing below 104 at
  AD <= 6 [H: this join operator on this pool].
- 01:50-01:52 `djoin1` (CPU 5): 109 AD4 circuits (A <= 33): 47,835 joins, 331 products in
  32/4/121/21; best 121@17, 119@18, 117@19, 116@20.  Nothing new.
- 01:53 `ewalk2` (CPU 5): E walk with a looser GD cap (32/6/36, objective cost) from 80 of the 490
  AD<=6 G=104 join products: aims at G <= 103 at any GD <= 36, to be pulled to GD 31 afterwards.

- 01:53-02:02 `ewalk2` (CPU 5, caps 32/6/36) stopped after 0 completed jobs for the unshare run
  (below); 01:36-01:56 `dwalk1` (4 jobs: 116@21 -> 117@19 in the first job, then 117@19 plateau) and
  01:56-02:02 `dwalk2` (+ AD-off alternation, 1 job, 117@19) replaced by dwalk3.

## D: why single-layer XOR rebuilds cannot give GD 19 from the 116@20
- trb's per-target Kraft test with cap 19 fails in every AND layer of a43e1ae3d73f (layers 0-4:
  30/30 'infeasible start'): [C, for re-synthesis of ONE layer's linear gates with its leaves treated
  as independent and the rest of the circuit unchanged] no such rebuild reaches GD 19.  The saved
  level has to come from changes in several layers (or changed AND operands).
- Depth with every linear signal rebuilt as an unshared depth-optimal XOR tree over its atoms
  (inputs and AND outputs), AND structure fixed: GD 16 for all five D starts (116@20, 117@19,
  119@18, 115@22, 33e0003e3b49), 17 for the 104@29 family, 19 for the AD6 104 [C, computed].  So the
  AND structure leaves 3 levels of room at GD 19; the question is purely the gate cost of sharing.

## New restart: unshare (unshare.py, walk.py --p-unshare)
Keep the AND gates; rebuild every AND operand and output as a depth-optimal (Huffman on arrival)
XOR tree over its atoms, hash-consed; random tie-breaks give different rebuilds.  116@20 -> 233@16,
104@29 -> 211@17.  One 100 s kernel job (objective cost) from there: 233@16 -> 118@19 under caps
32/4/19, 211@17 -> 105@31 under 32/6/31 [H, one seed each].  So the kernel descends from the
shallow side to within 1 gate of the best known points in 100 s, from a start that shares nothing
with the plateau except the AND gates: a restart that keeps the AND structure but escapes the XOR
local optimum.
- 02:02 `ewalk3` (CPU 5): E walk, caps 32/6/31, p-unshare 0.4, p-start 0.3, 300 s jobs, same 47 starts.
- 02:02 `dwalk3` (CPU 4): D walk, caps 32/4/19, p-unshare 0.35, AD-off alternation (alt caps
  32/-/19, p-alt 0.25, p-from-alt 0.25), 300 s jobs, 20 archive starts + dwalk1's three 117@19.

- 02:04 `ewalk1` stopped (2 jobs x 600 s, both 104 -> 104: the plain walk at 32/6/31 from the
  104 plateau did not move in 20 CPU-min).  Replaced by `ewalk4` (CPU 3): **depth release** after
  L2/WHAT-WORKED-BEFORE.md (the 104@29 was found by a kernel run from N:107@22 with the GD cap free:
  107@22 -> 106@36 -> 105@28 -> 104@29): 63 archive cell minima with A 32, AD <= 6, GD <= 24 plus
  NIST 107@22, 109@20, 110@22, 110@23, 122@16, 105@26; half the jobs with GD free (alt caps 32/6/-),
  their results kept in a side pool and re-tightened to 32/6/31 by later jobs (p-from-alt 0.4);
  p-unshare 0.15; 300 s jobs.

- 02:02-02:36 first measurements [H, few jobs]:
  - ewalk3 (6 jobs): elite jobs on the 104 plateau 4/4 unchanged (104 -> 104, as L1 counted for the
    hub); unshare 210@19 -> 107@31 in 300 s; AD7 103 start -> 32/6/107/31 (AD repair costs 4 gates).
  - dwalk3 (6 jobs): unshare 253/237/233@16 -> 121/118/119@19 (300 s each); 115@22 -> 118@19;
    117@19 starts unchanged.
  - ewalk4 (5 jobs): GD-free jobs go deep (121@22 -> 110@39 at AD5, 126@16 -> 113@39), re-tightening
    to GD 31 gives 109@31 (2 of 2); unshare 220@15 -> 118@32.
  - Reading: an unshare restart reaches 1-4 gates above the plateau in one job but then competes
    with the plateau members for elite picks and is never continued.  Added `--chain K` (continue an
    unshare result for K more jobs) and `--partial-share` (unshare only the operands of a random
    subset of AND levels / the outputs: unshare_partial, a smaller kick: 116@20 -> 116-156@20).
    Smoke test (6 s jobs): 236@16 -> 133 -> 126 -> 124@19 along one chain.
- 02:37 ewalk3, dwalk3 stopped; `ewalk5` (CPU 5, E, caps 32/6/31, p-unshare 0.6, partial 0.3,
  chain 3, 300 s) and `dwalk4` (CPU 4, D, caps 32/4/19, same plus AD-off alternation 0.2/0.2).

- 02:37-03:07: chains do not help [H]: ewalk5 unshare 216@17 -> 105@31, then 3 chain jobs 105 ->
  105 -> 105 -> 105; dwalk4 partial unshare 128@19 -> 117@19, then 3 chain jobs unchanged.  The
  kernel converges inside one 300 s job; continuing the same lineage adds nothing.
  ewalk4 (11 jobs by 03:07): GD-free jobs: 107@22 -> 32/5/104/42, 116@21 -> 32/4/115/36,
  108@20 -> 106@30; re-tightened 109@31 (x2), 105@26 unchanged; unshare 252@16 -> 110@31,
  238@16 -> 115@29.  Depth release reproduces the 104 level (at GD 42) from a 107@22 start in one
  job, matching L2's account of how the 104@29 was found, but not below it.
- 03:07 ewalk5, dwalk4 stopped.  `ewalk6` (CPU 5): second depth-release arm, same pool as ewalk4,
  p-alt 0.6, kernel T0 1.2 and max_excess 12 (hotter walk).  `dwalk5` (CPU 4): D walk adding the
  23 AD4 A32 cell minima at GD 15-18 (125@15, 126@16, 121@17, 119@18) as shallow-side starts
  (p-start 0.45), unshare 0.25 (half partial), AD-off alternation 0.2.

- E depth release, 03:55 [H]: in ewalk4 (20 jobs) and ewalk6 (8 jobs) the GD-free jobs found
  32/5/104/42, 104/39, 104/37 (from NIST 107@22 twice and from 105@26), 105/44, 106/39-40; their
  last improvement came late (t = 128-212 s of 300; others at 234-292 s), so the 300 s jobs end
  while still improving.  Re-tightening the deep 104s to GD 31 gave 106@30 (1 of 1).  Nothing below
  104 at any GD.  03:55 ewalk6 stopped, `ewalk7` (CPU 5): GD-free jobs of 900 s (alt-job-s), 300 s
  re-tightening, starts = 32 AD5 GD 19-26 cell minima + NIST 107@22, 109@20, 110@22/23, 105@26.

## D as a front subproblem with per-output deadlines (front.py, bfx_dl, frontwalk.py)
- [C, computed] The NIST 117@19 (073a719e1bc5) cut at AND level 1: front = 9 ANDs + 36 linear = 45
  gates, 23 cut signals (stage-1 products' sums and the x-forms the final products read); back = 72.
  Required times of the cut signals for GD 19 (backward pass through the back): [8,8,8,8,10,10,1,3,
  5,4,5,3,2,2,5,5,5,5,2,3,6,4,6]; arrivals in the 117@19 [7,7,8,8,9,9,1,3,3,4,3,1,2,2,5,5,5,4,2,3,
  4,4,5]: slack 1-2 on 9 of the 23 signals.  The 116@20 has the same back (L2: join with 0
  interface gates) and a 44-gate front that misses these deadlines by 2 levels.
  => **D is equivalent to: a 9-AND front of <= 44 gates computing these 23 functions within these
  deadlines** (then join -> 32/4/116/19).
- bfx_dl.c (made by mk_bfx_dl.py from kernel/bfx.c, shared kernel untouched): config `outoff`
  gives per-output offsets o_k = D - deadline_k, used in the GD metric, the repair penalty and
  the required times.  frontwalk.py runs it on the front (caps A 9, AD 1, GD max deadline,
  objective cost), joins each result in front of the 117@19 back, measures, aes_check on goal.
  Smoke test (15 s jobs): the 116@20's 44-gate front is repaired to 45 feasible -> joined 117@19.
- 03:41 `dfront1` (CPU 4, replacing dwalk5, which had 6 jobs: 117@19 plateau, unshare 232@16 ->
  119@19): 120 s jobs, starts = the fronts of ten 116@20/116@21/117@19 circuits, 80 min.
- dfront1 03:41-03:54: 6 jobs of 120 s, every result a 45-gate front (44-gate starts repaired to
  45) -> 117@19.  [H] the 45-gate level-1 front is tight under these deadlines.  03:55 `dfront23`
  (CPU 4): same at cut level 3 (front 15 ANDs + 55 linear = 70 gates, 27 cut signals, back = 17
  final products + 30) for 45 min, then cut level 2 for 40 min.
- dfront3 (cut level 3) 03:55-04:40: 11+ jobs of 180 s, every result a 70-gate feasible front
  -> 117@19; the 69-gate fronts taken from the 116@20s (deadline excess > 0) are repaired to 70.
  Bug found 04:33: frontwalk ranked its elite by gate count only, so the infeasible 69-gate starts
  were re-picked; fixed (feasible first) before the level-2 phase started.  The level-3 numbers
  are still valid repairs, but they are not a drift test of the 70-gate plateau.
- E analogue (617a1c3af391 cut at level 4: front 20 ANDs + 48 linear, 21 cut signals, back 12 ANDs
  + 24 linear; deadlines for GD 31): 3 x 30 s smoke jobs 68 -> 68.  Not run further.

## Failures / negative results
- Exact SLP (slp.py) is too slow at region sizes that matter: top region of 617a1c3af391 (17 XOR,
  8 leaves, 15 targets): k=17 SAT in 33 s without symmetry breaking, k=16 unknown after 300k
  conflicts; with symmetry breaking k=17 itself unknown after 400k conflicts (52 s).  Level-1 region
  of the 116@20 (17 XOR, 14 leaves) with cap-19 deadlines: no answer in 115 s.  Not pursued.
- BP heuristic (bp.py) does not beat the kernel's linear layers: top region of 617a1c3af391 17-18
  gates (current 17), bottom region 27 gates (current 24).  [H] The linear regions of these circuits
  are already better than the classic SLP heuristic finds from their target forms.

## Final numbers (05:58 UTC; the last three units stop on their own by 06:21)
| run | caps | jobs | best feasible | lowest G at any GD |
|---|---|---|---|---|
| ewalk1 plain | 32/6/31 | 2 | 104@31 | 104 |
| ewalk3 unshare 0.4 | 32/6/31 | 6 | 104@31 | 104 |
| ewalk4 depth release (300 s) | 32/6/31 (+GD free) | 43 | 32/5/104/31 | 32/5/104/42 |
| ewalk5 unshare + chains | 32/6/31 | 5 | 105@31 | 105 |
| ewalk6 depth release, T0 1.2 | 32/6/31 (+GD free) | 8 | 105@26 | 105@44 |
| ewalk7 depth release (900 s GD-free) | 32/6/31 (+GD free) | 10 | 105@26 | 32/6/104/42, 104/47 |
| dwalk1-5 (plain, AD-off, unshare, chains, shallow starts) | 32/4/19 | 21 | 117@19 | 117 |
| dfront1 / dfront3 / dfront2 (117@19 front, cut 1/3/2) | per-output deadlines GD 19 | 6 / 11 / 15 | front 45 / 70 / 50 -> 117@19 | - |
| dfront18 (119@18 front, cut 1) | deadlines GD 18 | 17 | front 47 -> 119@18 | - |
| ejoin1 / djoin1 | box 32/6/107/34, 32/4/121/21 | 340k / 48k joins | 104@29 / 116@20, 117@19 | - |
Every walk-run row is [H] (time-budgeted kernel runs, the seeds are in the logs).  found/ is empty:
no result met a goal box, so aes_check was never triggered.  The candidate-saving path was checked
by hand on ewalk3/cands/a32-ad5-g104-gd31-1f7c7565dc4d.bfx: aes_check OK (both verifiers), dominated
by NIST 104@30.
