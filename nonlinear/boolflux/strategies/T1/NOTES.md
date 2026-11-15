# T1: targeted search for goals B and C (2026-11-15, CPUs 0-2)

Goals (A/AD/G/GD): B = 28 / 4 / <=130 / <=22; C = 28 / 5 / <=127 / <=19.
Code: `strategies/T1/` (`survey.py`, `t1run.py`, `optest.py`). Data: `~/xs-campaigns/2026-11-15-study/T1/`.

## 1. Starting points (survey.py on the hub archive `2026-11-14-hub/long/archive`, 2311 records, ~01:35 UTC)
(G, GD) Pareto points per class [archive content, all verified on admission]:
- 28/4: (131,23) (132,22) (133,20) (135,18) (138,17) (141,16) (153,15) (175,14). 57 records with G <= 136.
  Closest to B: 132/22 (G -2), 131/23 (G -1, GD -1), 133/20 (G -3), 131/25.
- 28/5: (124,27) (125,25) (127,22) (128,20) (130,19) (133,18) (137,17) (150,15). 68 records with G <= 133.
  Closest to C: 128/20 (seed 688e861dabce; G -1, GD -1), 130/19 (G -3), 127/22 (GD -3).
- 29/4: 129/23, 130/22 (for the A-pull to 28).
Lineage: 28/5/127/22 = gen_skel(polish 130/19 <- pull <- seed 128/20); 28/4/131/23 = polish(trb(seed 131/25));
28/4/133/20 = polish(seed); 28/4/132/22 = seed (two structures) + polish/join copies.

## 2. Driver t1run.py (one process per CPU)
Local pool = archive A28 records in scope (A <= 28, AD <= goal AD, G <= Gt+12, GD <= GDt+10; for goal C this
includes the AD4 circuits) + every circuit any T1 worker admitted (DATA/shared/). Start chosen with weight
exp(-excess/2), excess = (G-Gt)^+ + (GD-GDt)^+. Operators (bandit on improvements per CPU-min, floor 0.15):
polish (kernel, caps 28/ADt/GDt, objective a,cost,gd, 30-120 s), osc (kernel at GDt+1..3 then at GDt),
trb (chained XOR-region rebuilds at GDt or GDt-1, then 30 s polish), join (pool partners, both roles, all cut
levels, best 6 + 30 s polish), skel (gen_skel kick, 8 s polish without GD cap, 40 s polish at caps), pullA
(A29 start, kernel with A cap 28 at GDt+2 then at GDt). Per kernel call T0 in {0.3,0.6,1.0}, max_excess in
{4,8,12}. Every candidate verified (hub common.verify) before admission; goal hits go through aes_check.py
into found/ with a JSON sidecar. Smoke test (optest.py, goal B): trb 133/20 -> 136/20; join 132/22 -> only
copies; skel 131/25 -> 134/22, 141/21. Works.

## 3. Runs
- run1 (01:39 - ~06:30 UTC): w0 goal B seed 101 (CPU 0), w1 goal C seed 202 (CPU 1), w2 goal B seed 303 (CPU 2).
- 01:40-01:46 UTC, CPU 2 (w2 stopped meanwhile): **alljoin1** (`alljoin.py`): every ordered pair of the 172 A28
  archive circuits with G <= 145 (+ T1 shared), hub join_all at every cut level: 29,412 pairs, 336 s.
  [C, within this case: hub join.py joins of these 172 circuits] no join result lies outside the existing
  A28 front: AD4 join front = (131,23) (132,22) (133,20) (135,18) (138,17) (141,16); AD5 = (124,27) (125,25)
  (127,24) (128,20) (130,19) (133,18) (137,17). 336 verified distinct near-goal joins (excess <= 4) saved in
  alljoin1/cand/ (e.g. 77 x 132/22, 20 x 131/23, 42 x 28/5/128/20, 26 x 130/19, 2 x 28/5/129/20) and fed to
  the workers as extra starts (new front/back mixes = new structures at the same cost).
- 01:46 UTC: all three workers restarted with v2 (op `deep` = 240-480 s polish; `--extra alljoin1/cand`),
  seeds 111/212/313, 4.7 h. Reason for deep: in the hub's polish/pull jobs the kernel's last improvement
  is spread uniformly over the budget (median at 50% of the budget, 693 jobs; hubpolish_stats.py), and the
  hub ran only 79 polish jobs on A28 inputs in total.
- 01:49-02:04 UTC, CPU 2: **crossjoin1** (`crossjoin.py`): 162 A28 circuits x 835 partners (A29-A33, AD <= 5,
  G <= 150), both roles, cut levels filtered by AND count (back ANDs <= 28, front+back <= 30): 270,540 pairs,
  607,446 joins, 23,363 results with A <= 28. [C, within this case] best A28 join results: AD4 (132,22) (135,21)
  (136,20); AD5 (124,27) (128,20) (135,19) ... - nothing new; 56 near-goal copies (16 x 132/22, 35 x 28/5/128/20).
  So the cheaper bottoms of the A29 4-level circuits (e.g. 29/4/130/22: linear gates per level 22|18|5|32|24 vs
  20|16|3|38|27 for 28/4/132/22, anatomy.py) are not reachable by the hub's join interface rebuild from the A28 fronts.
- 02:04 UTC coordinator note (L1): same-caps 90 s kernel jobs at the goal-near tuples gave 0 improvements
  (9-24 jobs each); what moved A <= 29 was pull with GD - 1 and the AD cap off on originals; 28/5/127/22
  (4d1642c45c7d) was never polished/pulled. Matches my first 25 min: 0 improvements in ~40 jobs.
- 02:07 UTC: **v3** (t1run.py; v2 kept as t1run_v2.py): op pullD (kernel at GD cap = start GD - 1 (p .75) / - 2,
  AD cap off with p .5 (C) / .3 (B), A cap 28, 60-90 s; then 45 s polish at goal caps if GD and AD already fit);
  pool keeps AD5 for both goals (excess +4 per AD above the goal); start = tuple chosen with weight
  exp(-excess/2)/(1 + tries of that tuple in this worker), then a structure (seed/ingest originals and
  first-of-tuple circuits x3); base op weights pullD .45, skel .12, osc .1, trb .1, polish .06, deep .06,
  pullA .06, join .05 (times the bandit factor). Restarted w0 B 121, w1 C 222, w2 B 323 (4.45 h, to ~06:34).

## 4. Results
- **28/4/132/20** (02:26 UTC, w1 job 13): pullD (GD cap 21, 60 s, T0 0.3) from alljoin1 candidate 6965f5d2759d
  (28/4/131/23 = hub join of front 89475138871e (L1) + back d33e25ba288c (28/4/131/23)). aes_check OK, new
  Pareto point on the pinned set; dominates the archive's 28/4/133/20 (best G at A28/AD4/GD<=20 was 133).
  Not goal B (G 132 > 130). Saved: found/front/aes-sbox-a28-ad4-g132-gd20-6dd93917c585.{bfx,check.json,json}.
  [H] the pull went 2 levels below the start (cap 21, result 20) and paid only +1 gate.
- v3 dominance bug: admit() compared (G, GD) across AD classes, so 28/4/132/20 was labelled dominated (by
  28/5/128/20) and the bandit gave pullD no credit. Fixed in v3.1 (full-tuple dominance); workers restarted
  02:30 UTC (seeds 131/232/333, 4.1 h).
- 02:57 UTC bottest.py (track F botsplice bottom transplant, 67 s on CPU 2): 47 A28/AD4 bases (G <= 135) x 138
  AD4 donors with A <= 30 (incl. the 29/4 and 30/4 circuits), all 6,486 transplants correct; [C, within this
  case] best A28 results = the existing tuples (131/23, 132/22, 133/20, 134/20 ...), nothing new.
- 03:04 UTC (coordinator request): w2 (goal B) stopped; CPU 2 runs **h3pol1** (`h3pol.py`, seed 41, 3.3 h) on H3's
  28/5/210/31 (H3/found/h3-d2-a29-ad5-g134-gd17-7-a28-ad5-g210.circ.txt, aes_check OK): phase G = kernel caps
  A28/AD5, no GD cap, 120 s runs chained until 4 stalls (<= 40% of time); phase D = GD descent toward C
  (GD cap = front GD - 1..2, AD off p .3, 90 s, then 60 s polish at that GD); joins of its front members with
  all A28 archive circuits after phase G and every 30 min. Coordinator correction 03:05: X1b showed [C] it has
  the same per-level AND spans as NIST 28/5/128/20 (only bracketing differs), so one CPU slot at most - as run.
- h3pol1 result (03:04-03:19, phase G only, 6 kernel runs of 120 s): 28/5/210/31 -> 143/25 -> 142/25 -> 140/27 -> 139/27
  (front also 28/5/142/25, 143/25). Stopped at 03:19 on the coordinator's priority change (H2's new AND space).
  Pool in h3pol1/pool/.
- 03:19 UTC: **h2pol** (`h2pol.py` = h3pol.py with AD free in phase G, pool AD <= 7, phase D = AD repair
  (AD cap = AD - 1) p .4/.2 mixed with GD descent) on H2's 9+5+14 circuits (new AND space per coordinator/X1b):
  s59 28/6/585/33 on CPU 2 (unit t1-h2s59, seed 59), s58 28/6/591/34 on CPU 1 (t1-h2s58, seed 58; w1 goal C
  stopped for it), 3.0 h each. w0 (goal B) continues on CPU 0.
- h2pol-s58 (03:19-03:25, 2 kernel runs): 28/6/591/34 -> 28/6/161/31. Stopped for the screening queue (coordinator 03:24).
- 03:26 UTC: **screen1** (`screen.py`, CPU 1, 3.0 h): new-AND-space builds (X1b 28/5/158/27 span-2cabef6153f4;
  H2 c8c7227f s76 s83 s103 s110 s114 s372 s467 s709, s58, s59; then whatever H2 appends to
  H2/builds-for-T1.txt): two chained 120 s kernel runs each, caps A 28 only; best -> found/newspace/ with
  aes_check + sidecar. h2pol-s59 continues on CPU 2, w0 (goal B) on CPU 0.
- h2pol-s59 phase G (03:19-03:43, 10 runs): 28/6/585/33 -> 157/31 (AD5) -> 155/28 -> 152/31 -> 152/27 -> 151/28; stall.
  Joincheck after G (hub join of its front members with all A28 archive circuits, 1110 joins, 20 s): front of s59 +
  back of AD4 archive circuits gives **A28/AD4** circuits 143/28, 145/26, 147/21, 153/20 (s59 shares the AD4 family's 9
  level-1 products, so these are presumably the AD4 AND space with s59's top linear layer - span not checked);
  back of s59: AD5 164/30 ... Phase D from 147/21 (GD cap 20): 138/20 -> polish 135/20.
- screen1 so far (2 x 120 s, caps A 28): X1b 28/5/158/27 -> 28/6/149/31 (152/29 after run 1); s76 576 -> 28/6/158/30;
  s83 583 -> 28/5/157/28; s103 592 -> 28/6/166/29. [H] the H2 builds all land at ~150-166 after 4 min.
- 03:44 UTC: w0 (goal B, hub pool) stopped after 0 improvements since 02:30 (75 min, ~45 jobs); CPU 0 now runs
  **w0ns** = t1run.py v3.2 (`--no-hub --admax 6 --gslack 40 --gdslack 15`, op gfree = 120 s kernel caps A 28,
  AD <= admax, no GD cap) on the new-space pools (found/newspace, h2pol-s58/59 pools, shared dir shared-ns),
  goal C, seed 404. First job: gfree on the joined 28/4/148/22 -> **28/4/132/24** (in 120 s).
- [C, X1/x1b_family.py span invariant] the joined AD4 circuits 28/4/132/24 (16d3a74a528b) and 28/4/135/20 have
  product span 70c8908eb0af = NIST 28/4/131/31's span: NOT a new AND space (new XOR layers on the AD4 family).
  s59 itself: span 12138d9cf3f6 (26 shared dims with AD4 g131, 16 with AD5 g124), as the coordinator said.
- h2pol-s59 phase D (03:43-03:55) worked only on the joined AD4-family circuits (they dominate the new-space AD5/6
  points): 147/21 -> 138/20 -> 135/20; 140/18 -> 139/18; 136/19; 135/19 (all dominated by the archive's AD4 front).
  Stopped 03:55; **h2pol-s59b** restarted from s59's best own-space circuit 28/5/152/27 (4bed23ed242b), 2.4 h,
  seed 591, with h2pol v2: join results go to h2pol-s59b/joins/ instead of the pool (env JOIN_TO_POOL=1 restores v1),
  so the pool stays in s59's AND space.
- **28/4/134/19** (04:00 UTC, w0ns job 4): deep (480 s, caps 28/5/19) from 28/4/132/24 (16d3a74a528b, the gfree
  polish of the s59-front x AD4-back join 059f19200fe1). aes_check OK, new Pareto point on the pinned set (between
  133/20 and 135/18). Saved found/front/aes-sbox-a28-ad4-g134-gd19-72bdecd812ee.*. R1 found the same tuple
  independently (r1-grind-28-4-134-19.bfx, different circuit 6e8e4bed95e7) by exact AND removal from an A29.
- 04:04 UTC screen1 stopped after 9 circuits (H2 had appended 69 builds; 4.3 min each would take 5 h; the rest
  goes to the overnight queue). Screen results (2 x 120 s): s372 -> 28/5/154/31, s467 -> 28/6/156/29, s110 ->
  28/5/156/29, s114 -> 28/6/157/31 (plus the ones above). [H] all H2 builds land at 154-166 after 4 min.
- 04:04-04:07 **hyb1** (`hybjoin.py`, CPU 1): 20 new-space circuits (found/newspace + h2pol pools) x 162 A28 archive
  circuits, both roles: 1,336 verified A28 joins saved (hyb1/). nsfront (new-space front + archive back) gives
  AD4 joins down to 141/25, 142/26, 145/21, 146/20, 148/19; nsback (archive front + new-space back) gives AD5/6 at
  164-191 only. Best raw joins are 10-15 gates above the AD4 front, but one of them polished to 134/19.
- 04:07 UTC: **w1ns** (CPU 1, goal B, seed 505, 2.25 h): t1run v3.2 `--no-hub --admax 5 --gslack 40 --gdslack 15`
  on hyb1 + h2pol-s59/pool + found/front (+ shared-ns, where R1's two new points 28/4/134/19 6e8e4bed95e7 and
  28/5/126/24 3572d6ef770c were copied for both ns workers).
- **Harvest failure (found by L1b, coordinator 04:29)**: w2's deep job (480 s kernel, caps 28/4/22, T0 0.3,
  max_excess 8, seed 166382251, start 28/4/132/24) was killed by `systemctl stop` at 03:04; its best.bfx
  **28/4/131/22** (aes_check OK, new on the pin, one gate from goal B) stayed in run1/scratch/w2/dp/ and was not
  logged. Fixes: (1) t1run.py **v3.3** harvests every scratch best.bfx at startup and on SIGTERM (admit + log
  event 'harvest'), and saves every admitted circuit not dominated by the hub archive / pinned NIST set to
  found/front/ with aes_check (event 'FRONT'); h2pol.py harvests on SIGTERM too. (2) `sweep.py` over all T1
  scratch/job dirs (116 kernel outputs): new-on-pin outputs = 28/4/131/22 (73d90cb694de, now in found/front/),
  plus same-tuple siblings 28/4/134/19 (01acad991012, w1ns osc) and 28/5/126/24 (19a2a6cf9d80, w0ns gfree from
  R1's 126/24; T1 polish of an R1 circuit). All A28 scratch outputs copied to T1/scratchpool/ as starts.
- 04:31 UTC restarts (v3.3): CPU 2 **bdeep** = t1run goal B, ops deep only, 480 s at caps 28/4/22, hub pool +
  bstarts (131/22, 132/20) + shared-ns + scratchpool, seed 606, 1.8 h; CPU 1 w1ns (goal B, seed 515, + found/front,
  bstarts, scratchpool); CPU 0 w0ns (goal C, seed 414). h2pol-s59b stopped (s59 space: 150/30, 150/35, 151/28,
  152/26 after 35 min; plateau ~150).

## 5. Final (06:04 UTC, all T1 jobs stopped; SIGTERM harvest worked: event 'harvest' in w0ns/w1ns/bdeep logs)
Goals: **B not met, C not met.**
New A28 frontier points (all aes_check OK and new on the pinned set; T1/found/front/, sidecars give the lineage):
| tuple | id | how |
|---|---|---|
| 28/4/131/22 | 73d90cb694de | deep (480 s, caps 28/4/22) from 28/4/132/24 (w2, 03:04; harvested late, see the harvest failure above) |
| 28/4/131/22 | a89756eb3f8b | gfree (120 s, caps A 28) from 73d90cb694de (w1ns) - same tuple, other circuit |
| 28/4/132/20 | 6dd93917c585 | pullD (GD cap 21, 60 s) from alljoin1 join 6965f5d2759d (28/4/131/23) |
| 28/4/134/19 | 72bdecd812ee | deep from 132/24 <- gfree <- join(s59 front, AD4 archive back); R1 found the tuple independently |
| 28/4/134/19 | 01acad991012 | osc from 134/19 (w1ns) |
| 28/4/132/21 | 2ecc6a26a598, 28073d63d808, b478daed07da | ns workers; dominated by 132/20 |
| 28/5/126/24 | 19a2a6cf9d80 | gfree from R1's 126/24 (same tuple as R1's point, so no new tuple from T1) |
A28 AD4 front now (archive + T1): 131/22, 132/20, 134/19, 135/18 (goal B needs 130/22: one gate from 131/22).
AD5 side: nothing new from T1; the best is still archive 127/22, 128/20, 130/19 plus R1's 126/24.

CPU use 01:39-06:04 (~13 CPU-h): hub-pool workers w0/w1/w2 (163 jobs, 4.1 CPU-h): 1 point (132/20) plus the
orphaned 131/22; alljoin1/crossjoin1/bottest (~0.4 CPU-h): nothing new [C within their cases]; h3pol/h2pol/screen
(~1.9 CPU-h): new-space circuits only to about 150 G; ns/hybrid workers w0ns/w1ns (131 jobs, 3.9 CPU-h): 134/19 and
the second 131/22 circuit; bdeep (10 x 480 s deep at caps 28/4/22 from 131/22, 132/20 and the hub pool, 1.4 CPU-h):
0 improvements (outputs 132/21, 132/22 again) [H].
[H] at these tuples a GD step costs about +1-2 gates. Same-caps polish at the goal-near tuples is dead (L1, and my
first 40 jobs). The things that moved were: GD pulls (pullD), long deep runs from a non-front start (132/24), and
new XOR layers brought in by joins with other circuits (alljoin copies, the s59-front hybrids).
Failures / pitfalls: the harvest bug (fixed in v3.3); the v3 cross-AD dominance bug (fixed in v3.1); one Monitor on
WSL files stayed silent while FRONT lines were written (I checked with grep instead); hub-pool workers stalled
after 02:30; the H2 builds plateau at 150-166 G with the kernel alone.
