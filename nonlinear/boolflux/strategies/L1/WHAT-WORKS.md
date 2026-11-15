# What worked and what did not in the hub era (L1, 2026-11-15)

Analysis only: no search was run. Every number is recomputed from the campaign directories under
`~/xs-campaigns/2026-11-14-hub/` by the scripts in this directory; the text tables they print are in
`~/xs-campaigns/2026-11-15-study/L1/q1.txt` .. `q7.txt` (named with each claim).

Labels: **[C]** = counted from the logs / archives named (a count, not a proof about the search space);
**[H]** = interpretation or recommendation. Every [C] covers only the runs listed in section 0.

## 0. Data, terms, value model

**Data [C].** Eight hub directories: `abhub` (1 h, 4 CPUs), `long` (18:41 - 01:30 UTC, five scheduler
starts: long1, long2, long3, a 2-minute false start, long4), and the six 1-CPU 1-hour arms `ab2base`,
`ab2gen`, `ab3gen`, `ab3lin`, `ab4base`, `ab4ad3`. Together 7,231 jobs, 65.90 CPU-h, 2,521 distinct
archived circuits. `main` holds only the 242 seeds; `abmem` is the memetic arm of the first A/B (no
operator log in the hub format; used only in 4.1). All jobs returned code 0; no `finish-error` or
`control-error` event exists; 36 job directories in `long` have no run record (jobs killed at restarts).
Worker utilisation was 98-100 % in every phase (`q2.txt` e2).

**Terms.**
- *Tuple* = (A, AD, G, GD). *Target* = the archive circuit a job is run on.
- *Front admission* = an admitted circuit that, at the moment of admission, was not dominated (equality
  counts as dominated) by anything already in that directory's archive or by the pinned NIST set
  3d80774. This is the model-free unit of progress. 80 in total: 75 made by hub jobs, 5 ingested from
  track F.
- *Cap box* of a tuple = everything with A <= its A, AD <= its AD, GD <= its GD (the comparison BEST.md
  prints as "published best within the same caps"). dG = best earlier G in the box minus the new G.
- *Goal-near* = inside a goal's A and AD caps, not dominated in (G, GD) inside that class, and within
  6 gates / 4 levels of the goal box.
- *Equal-tuple copy* = an admitted circuit whose tuple another, earlier circuit already had (the archive
  keeps up to 4 per cell).

**Value model [H].** V = tier(A, AD) x size. tier = 64 / 32 / 16 / 8 / 4 for A = 28 / 29 / 30 / 31 / 32,
2 for A 33-35, 1 above, 1000 for A <= 27 (never occurred); times 1.4 for AD 4, 1.96 for AD 3, 1 for AD 5,
0.7 for AD >= 6. size = min(dG, 6) / 2 for a gain inside an occupied cap box; 1.5 / 4 / 8 if the point
extended the reach of its class in GD / AD / A (never occurred, see finding 1 in section 1). Reason: the user's order is
lexicographic A > AD > G > GD, so one AND less must outweigh any gate gain (factor 2 per AND, more than
the size range of 6) and one AND-depth level must count for less than an AND (1.4 < 2). The model has
free constants; where a conclusion depends on them I say so, and every table also gives the plain count
of front admissions and the count with A <= 31. Code: `l1_lib.py` (`tier`, `improvement`).

## 1. Headline findings

1. **Every one of the 80 front admissions is "fewer gates under the same caps". [C]** None lowered the
   smallest A, the smallest AD at an A, or the smallest GD of a class. dG is 1 for 54 of them, 2 for 12, 3 or more for 14 (largest 9).
   The hub's own gain rule (`Archive.gain`) scored the 75 hub-made ones as 51 x "lowers A" (8), 22 x
   "lowers AD" (4), 2 x G (`chk_gain.py`). That rule asks only for some archived point that is no worse on
   the other three coordinates, and a circuit with more ANDs and fewer gates always exists. So the
   per-operator "gain per CPU-h" figures in E's notes, and the bandit's reward, are close to admission
   counts with a random 4-or-8 multiplier. **[H]** They should not be used to rank operators.
2. **No goal B-G was met and the best distance to each goal box is what the seed pool already had, or one
   step better. [C]** Lowest G per GD inside each goal class, seed pool (17:38 UTC) -> `long` at stop
   (`chk_stairs.py`): B 28/4: only 131@25 -> 131@23. C 28/5: new 133@18, 130@19, 127@22; 128@20 unchanged.
   D 32/4: 122@18 -> 119@18, new 121@17, 115@22, 114@26; 117@19 and 116@20 unchanged. E 32/<=6: nothing at
   G <= 110 changed. F 35/3: 141@24, 142@21 and GD 16-19 filled; 140@25 and 139@27 unchanged. G: 142@12 ->
   141@12. 19 hub-made goal-near admissions in 65.9 CPU-h, the last one that tightened a goal box at 22:20 UTC
   (35/3/142/21); 28/5/133/18 at 00:06 UTC is 6 away from C.
3. **The mature best circuits are fixed points of the kernel. [C]** For each of 28/4/131/23, 132/22,
   133/20, 28/5/128/20, 130/19, 32/4/116/20, 117/19, 119/18, 32/5/104/29, 105/26, 35/3/139/27, 140/25,
   141/24, 43/4/141/12: every polish / pull / osc job whose result stayed inside the tuple's own caps
   returned the same G or more (5-24 such jobs per tuple, 9 or more for all but 28/4/131/23 and 28/5/130/19; 0 with lower G; `q5.txt`). Polish on a seed
   circuit: 138 jobs, 3.8 CPU-h, 0 with lower G (`q7.txt` 1); the memetic control agrees (106 polishes,
   4 admissions).
4. **Value came from one skeleton family. [C]** 83 % of V and 26 of the 34 front admissions with A <= 31
   have the stage-1 space of the NIST A28 AD5 circuits (10 level-1 ANDs). One seed, NIST 28/5/128/20,
   is an ancestor of 14 of those 34 (61 % of all V). No new A28 AND space was created: all 230 archived
   A28 circuits lie in the 6 AND spans of the seeds (`q3.txt`, `q5.txt`).
5. **The valuable new structures were by-products of failed repairs. [C]** The 29/4 family (10|2|4|13,
   11 front admissions, the 129@23 / 130@22 / 131@20 / 132@19 / 133@18 / 135@17 / 138@16 / 146@15 points)
   and the 30/4 family (10|3|4|13, 6 front admissions) were first made by `pull` jobs that ended
   infeasible (the 30/4 one also once by osc, which has no A cap): asked to lower AD (A cap kept) or GD (AD cap off), the kernel ended one AND above the A cap
   with AD one lower (28/5 -> 29/4 twice, 29/5 -> 30/4 twice). All 11 front admissions of the A- and
   AD-lowering pulls came from jobs that ended infeasible (`q7.txt` 2, `chk_jump.py`).
6. **CPU did not follow value. [C]** Targets with A >= 33 took 35.5 CPU-h (54 %) and gave 31 front
   admissions, all with A >= 33, none goal-near except in the goal F / G windows; targets with A <= 29
   took 13.0 CPU-h (20 %) and gave 21, all with A <= 30. 22.6 CPU-h (34 %) went to targets with A >= 32
   outside every goal window: 11 front admissions, 0 goal-near (`q2.txt` b, `q5.txt`).
7. **A tuple is used up after about two polishes and three pulls. [C]** Front admissions per CPU-h by
   attempt number on the same tuple (all copies together): polish 2.31 / 0.92 / 0.00 / 0.56 / 0.26 (5+),
   pull 2.08 / 2.19 / 1.29 / 0.00 / 0.19. Attempts 4 and later: 475 jobs, 12.8 CPU-h, 3 front admissions.
   The scheduler counts attempts per circuit id and the archive keeps up to 4 ids per tuple (308 ids for
   85 front tuples at stop; 1,135 of the 1,526 join admissions are equal-tuple copies), so old tuples keep
   receiving kernel jobs while new ones wait: 28/5/127/22 (admitted 22:05 UTC) received no polish, pull,
   trb or osc job in the 3.4 h until stop; five A29/A30 AD4 points of the last hour received none either
   (`q4.txt` 2b, `q6.txt`).
8. **join in the hub era only re-arranged XOR logic and mostly repeated itself. [C]** 1,451 of 1,526 join
   admissions have the AND span of a parent, all have a parent's stage-1 space. First join on a target:
   1,083 jobs, 7 front admissions; later joins on the same target: 3,471 jobs, 4.65 CPU-h, 3 front
   admissions. `op_join` takes partners = (front ids + other cell minima)[:300]; the front has had
   283-311 ids since long3, so at most 18 and finally 0 partner slots went to non-front circuits:
   nursery circuits cannot be partners (`q6.txt` 1).
9. **osc did not pay. [C]** 347 jobs, 9.52 CPU-h (14 %), 4 front admissions, 2 of them in the single
   1-CPU-h arm that got it adopted; in `long` 299 jobs, 8.2 CPU-h, 2 front admissions (V 2). It runs
   without an A cap (31 results raised A).
10. **The A/B decisions rest on counts of 1 vs 2. [C]** Inside long3, twenty 1-CPU 1-hour blocks of the
    same configuration gave 0, 1, 2, 4 front admissions in 11, 5, 3, 1 blocks. **[H]** A one-hour
    one-CPU arm cannot separate the configurations tested; see section 5.

## 2. Operators and chains (question 1)

### 2.1 Per operator, all hub directories [C] (`q1.txt`; 65.90 CPU-h)

| op | jobs | CPU-h | share | admitted | front adm | with A <= 31 | goal-near | V | V / CPU-h | front adm / CPU-h |
|---|---|---|---|---|---|---|---|---|---|---|
| pull | 866 | 23.57 | 36 % | 126 | 33 | 18 | 8 | 811 | 34.4 | 1.40 |
| polish | 666 | 18.19 | 28 % | 109 | 21 | 7 | 4 | 224 | 12.3 | 1.15 |
| osc | 347 | 9.52 | 14 % | 29 | 4 | 2 | 1 | 40 | 4.2 | 0.42 |
| join | 4554 | 6.07 | 9 % | 1613 | 10 | 2 | 2 | 25 | 4.1 | 1.65 |
| gen_skel | 296 | 4.41 | 7 % | 219 | 3 | 3 | 1 | 40 | 9.1 | 0.68 |
| trb | 460 | 3.81 | 6 % | 251 | 4 | 2 | 3 | 164 | 43.0 | 1.05 |
| gen_joinplus | 5 | 0.13 | | 3 | 0 | 0 | 0 | 0 | | |
| gen_inv3 | 6 | 0.10 | | 0 | 0 | 0 | 0 | 0 | | |
| linres | 10 | 0.08 | | 8 | 0 | 0 | 0 | 0 | | |
| gen_bottom | 21 | 0.01 | | 0 | 0 | 0 | 0 | 0 | | |

Notes. trb's 4 front admissions were all first attempts, 3 of them on seed circuits (two A28 AD5 points:
28/5/131/19 in ab3lin, 28/5/127/24 in long3); its V rests on those two. gen_skel's direct points are
28/5/127/22 (goal C class) and two 31/5/115 points. The last four operators were sampled 5-21 times in
one arm; the logs say nothing about them either way.

By phase of `long` (V per CPU-h, front admissions): long2 (11.9 CPU-h) 40.9, 21; long3 (30.1 CPU-h) 9.3,
24; long4 (13.2 CPU-h) 21.8, 10. Per hour of `long`: front admissions 8, 10, 9, 8, 3, 12, 5; with
A <= 31: 3, 5, 5, 2, 0, 9, 5. **[H]** No steady decline: yield comes in bursts when a new family appears
(hours 5-6 are the 29/4 family).

### 2.2 Operator by maker of its target [C] (`q1.txt`; rows with >= 1 CPU-h)

| job | jobs | CPU-h | front adm | A <= 31 | V | V / CPU-h |
|---|---|---|---|---|---|---|
| pull on a join product | 344 | 9.37 | 11 | 3 | 122 | 13.0 |
| polish on a join product | 297 | 8.12 | 12 | 5 | 113 | 13.9 |
| osc on a join product | 190 | 5.21 | 2 | 1 | 17 | 3.3 |
| pull on a seed | 177 | 4.85 | 6 | 2 | 114 | 23.5 |
| polish on a seed | 138 | 3.79 | 1 | 0 | 7 | 1.8 |
| join on a join product | 2434 | 3.15 | 4 | 2 | 15 | 4.6 |
| pull on a gen_skel product | 94 | 2.54 | 2 | 2 | 67 | 26.5 |
| pull on a pull product | 85 | 2.29 | 8 | 7 | 324 | 141.1 |
| pull on a trb product | 83 | 2.27 | 1 | 1 | 96 | 42.3 |
| gen_skel on a join product | 152 | 2.26 | 1 | 1 | 4 | 1.8 |
| polish on a polish product | 79 | 2.13 | 2 | 0 | 5 | 2.5 |
| osc on a seed | 75 | 2.06 | 0 | 0 | 0 | 0 |
| pull on a polish product | 69 | 1.87 | 5 | 3 | 88 | 47.1 |
| trb on a join product | 202 | 1.68 | 1 | 0 | 2 | 1.2 |
| polish on a trb product | 56 | 1.53 | 3 | 1 | 51 | 33.0 |
| join on a seed | 1004 | 1.41 | 2 | 0 | 4 | 2.7 |
| polish on a pull product | 48 | 1.30 | 2 | 0 | 4 | 3.0 |
| osc on a trb product | 42 | 1.15 | 2 | 1 | 23 | 20.1 |
| polish on a gen_skel product | 41 | 1.12 | 1 | 1 | 45 | 40.0 |
| trb on a seed | 103 | 0.84 | 3 | 2 | 162 | 192.5 |

The strongest chain step is **pull on a circuit that a pull just made** (8 front admissions in 85 jobs,
7 with A <= 31): once a depth pull lands in a fresh spot, the next pull keeps paying. What the kernel does
to its target by maker (`q7.txt` 1, polish jobs only): gen_skel product: G lowered in 38 of 41 jobs, mean
-10 to -15 gates, 10 of the 38 still improving after 75 of 90 s; pull / polish product: 12-32 %, -1 to -2.5
gates; join product: 16 of 297; trb product: 3 of 56; seed: 0 of 138. **[H]** gen_skel hands over
circuits that are far from locally optimal (it only polishes for 8 s without a GD cap); the 90-s kernel
then recovers 10-15 gates and occasionally ends below the front. Everything else the kernel is given is
already at its local optimum.

### 2.3 Which operators the valuable points needed [C] (`q5.txt`)

For each front admission, an operator counts as *needed* if some step by it in the lineage changed the
tuple (a step that only produced an equal-tuple copy does not count):

| op | front adm with a tuple-changing step by op | V of those | only as equal-tuple copy | step that changed the AND span |
|---|---|---|---|---|
| pull | 51 | 1011 | 0 | 18 (V 637) |
| polish | 31 | 350 | 8 | 1 |
| join | 29 | 326 | 24 | 1 |
| gen_skel | 22 | 433 | 0 | 7 (V 82) |
| trb | 10 | 269 | 26 | 0 |
| osc | 10 | 111 | 0 | 9 (V 110) |

Per CPU-h spent on the operator (credit overlaps, so this is an upper bound for each): gen_skel 98,
trb 71, join 54, pull 43, polish 19, osc 12. **[H]** pull is the operator almost every valuable lineage
needs; gen_skel and trb are cheap enablers; polish and osc are the expensive ones for what they enable.
New AND spans were introduced 47 times by gen_skel, 19 by join, 13 by pull, 13 by polish, 11 by osc, but
the spans that carry value are the seeds' (V 677) and the ones pull introduced (V 560); gen_skel's 47
new spans carry V 4 (`q3.txt`). gen_skel's value is as a perturbation inside a span (147 of 217 of its
admissions keep the parent's AND span), not as a source of new product sets.

### 2.4 The chains behind the A28 / A29 / A30 points [C] (`q1.txt`, `q4.txt` 1)

- **A28 AD5** (span of NIST 128/20): 28/5/130/19 = pull GD-1 on the seed (improved after 4 s);
  28/5/131/19 = trb on the seed; 28/5/132/19 = pull GD-1 on a trb copy of the seed; 28/5/133/18 = pull GD-1
  on 130/19; 28/5/127/22 = gen_skel on a polish copy of 130/19; 28/5/127/24 = trb on E's 125/25. Six
  points, all within two steps of a seed.
- **A28 AD4**: one point, 28/4/131/23 = polish(trb(E's 131/25)). The class received 619 jobs and
  5.35 CPU-h.
- **A29 AD4** (new): 28/5/132/19 -> join copy -> pull GD-3 (ended infeasible on A) -> 29/4/140/16 -> pull
  GD-1 -> 148/15 -> polish, pull -> 146/15 -> gen_skel (148/19, worse) -> pull GD-1 -> **133/18**, pull AD
  -> **132/19**; gen_skel + polish on 140/16 -> **131/20**; join of 133/18 and 146/15 -> 30/4/144/17 ->
  polish -> **135/17**, pull -> **138/16**. Second line: E's 28/5/125/25 -> pull AD (infeasible) ->
  29/4/130/23 -> pull A -> **130/22** -> gen_skel, join, polish, pull -> **129/23**.
- **A30 AD4**: 29/5 circuits -> pull AD (infeasible on A) -> 30/4/130/20 (ab3gen), 30/4/132/21 (long3);
  osc and pull GD-3 on these -> 140/15, 144/15, 145/15.
- **A31**: 31/5/114/28 = join(seed, join(seed, gen_skel(join))); 115/24, 115/25, 115/26 = gen_skel or
  polish(join) within one G of it. V 4 each: one gate under an existing box.

The pattern that produced gains of more than 2 gates: push a circuit somewhere worse but different
(pull to a much lower GD, or a gen_skel kick), then pull / polish from there. The single biggest steps
were kernel jobs on fresh gen_skel or join products: 29/4/148/19 -> 133/18 (last improvement at 90 s of 90),
29/4/143/20 -> 131/20, 30/4/144/17 -> 29/4/135/17 (84 s).

## 3. Where CPU was wasted (question 2)

All [C]; categories overlap, so they do not add up.

| item | jobs | CPU-h | front adm | source |
|---|---|---|---|---|
| osc, all | 347 | 9.52 | 4 (2 in `long`) | q1 |
| kernel jobs (polish, pull) on a tuple's 4th or later attempt | 475 | 12.8 | 3 | q4 2b |
| polish, 3rd or later attempt on a tuple | 295 | 8.0 | 2 | q4 2b |
| join, 2nd or later job on the same target | 3471 | 4.65 | 3 | q2 a |
| polish on seed circuits | 138 | 3.79 | 1 (0 with lower G) | q7 1 |
| pull lowering A | 180 | 4.90 | 6, all from infeasible ends; feasible at end in 9 jobs | q7 2 |
| pull lowering AD | 168 | 4.58 | 5, all from infeasible ends; feasible in 4 jobs, 0 of 64 on AD3 targets | q7 2 |
| pull lowering GD that ended infeasible | 214 | 5.8 | 1 | q7 2 |
| any job on a target with A >= 33 | 3775 | 35.5 | 31 (0 with A <= 32) | q2 b |
| any job on a target with A >= 32 outside every goal window | 2239 | 22.6 | 11 (0 goal-near) | q5 |
| gen_skel on targets with A >= 32 | 217 | 3.2 | 0 | q2 b2 |
| trb, osc, gen_skel: 2nd or later job on the same target | 178 | 2.8 | 0 | q2 a |
| any job on an A28 AD4 target | 619 | 5.35 | 1 | q2 b |

- **Time-outs**: none. Kernel jobs use 98 s CPU for a 90-s budget; join uses 4.8 s of its 60-s budget;
  gen_skel 54 of 60 s; trb 30 of 30 s. 3,500 of 4,554 join jobs and 387 of 460 trb jobs produced no
  candidate at all.
- **Depth pulls are immediate or never**: when a GD pull ends feasible, the first feasible circuit
  appears after a median of 0 s (90 % within 2 s; up to 25 s on AD4 targets). 304 of 518 ended feasible.
  **[H]** A 20-30 s feasibility check would return most of the 5.8 CPU-h of the infeasible ones; the
  price would have been one front admission (29/4/140/16, the root of the 29/4 family, see finding 5), so the
  infeasible path is better kept as an explicit, separate move.
- **Nursery admissions**: of 217 gen_skel admissions, 98 were ever used as a target, 61 have a descendant,
  13 are, or have a descendant that is, a front admission. Polish + pull on targets carrying the nursery
  flag: 9.4 CPU-h, 14 front admissions (1.49 per CPU-h, V 40 per CPU-h); on other targets: 32.4 CPU-h, 40
  (1.23, V 20). **[H]** The nursery pays about as well per job as the front and better in value, because
  it is where the kernel still moves; 119 gen_skel products were never touched.
- **Repeated targets**: 281 targets were joined 10 or more times (nearly all in `long`); the most repeated got 16.

## 4. Productive ancestors (question 3)

### 4.1 Seeds [C] (`q3.txt`)

253 seed / ingested circuits; 110 have any descendant; 38 have a front admission among their descendants.

| seed | AND profile by level | V of descendants (share) | front adm below | with A <= 31 |
|---|---|---|---|---|
| NIST 28/5/128/20 | 10\|1\|2\|2\|13 | 803 (61 %) | 14 | 14 |
| E-low1 29/5/138/16 | 10\|2\|3\|4\|10 | 150 (11 %) | 7 | 7 |
| E-low1 28/5/125/25 | 10\|1\|2\|2\|13 | 122 (9 %) | 4 | 4 |
| NIST 28/5/124/27 | 10\|1\|2\|2\|13 | 90 (7 %) | 3 | 3 |
| E-low1 29/5/135/17 | 10\|2\|3\|4\|10 | 82 (6 %) | 4 | 4 |
| E-splice 35/3/144/20 | 11\|12\|12 | 71 (5 %) | 16 | 0 |
| E-low1 28/4/131/25 | 9\|2\|4\|13 | 45 (3 %) | 1 | 1 |
| E-splice 32/4/116/20 | 9\|2\|4\|17 | 28 (2 %) | 7 | 1 |
| NIST 32/4/117/19 | 9\|2\|4\|17 | 22 (2 %) | 6 | 2 |
| NIST 33/4/105/25 | 9\|2\|4\|18 | 18 (1 %) | 5 | 1 |

(A point with two seed ancestors counts for both.) The five most productive seeds share one stage-1
space (10 level-1 ANDs, the NIST A28 AD5 front); by stage-1 space the value splits 83 % (that space, 26
front admissions) / 6 % (AD3, 11 level-1 ANDs, 21 front admissions) / 4 % (the 9-AND space of the
A31-A33 Boyar-Peralta family, 15) / 3 % (NIST A28 AD4, 1) (`chk_stairs.py`). The seeds with the most
descendants of any kind are the A32-A33 ones (NIST 33/4/105/25: 878 descendants, 5 front admissions):
join breeds copies there.

### 4.2 Hub-made hubs [C]

28/5/132/19 (`dfb8f2eff43d`, pull(trb(seed))) and the trb copy of the seed above it: 10 front admissions
below each, all A <= 31. 29/4/140/16 (`70751e0f9ad4`): 9. 29/4/148/15 (`d45543784321`): 7.
29/4/146/15: 6. 35/3/149/19 (`a428384b90b5`, pull on the E-splice seed): 12, all AD3.

### 4.3 What the productive ones have in common

- **[C]** Same nonlinear skeleton: 10 level-1 ANDs spanning the A28 AD5 stage 1, then 5 (AD5) or 6 (AD4)
  middle ANDs and 13 final ANDs (10 final ANDs in E's 29/5 variant).
- **[C]** Room in the published staircase: the pin has A28 AD5 circuits only at GD 15, 20 and 27
  (150, 128, 124 gates) and nothing with A = 29 at AD 4. The hub's A <= 29 points are at GD 15-19 and
  22-24, between or beside those. In the A28 AD4 class the pin and E's seeds already hold points at
  GD 14, 15, 16, 17, 18, 20, 22, 25; the hub added one.
- **[H]** So "productive ancestor" here means "a skeleton whose gate-depth trade-off nobody had walked
  yet", not a circuit with a special property. The A28 AD5 skeleton had three published depths; the hub
  walked it with depth pulls and got six more. That supply is finite: on 28/5/128/20 and 130/19 the
  kernel now returns the same G (finding 3).
- **[C]** The A29 / A30 AD4 families are that skeleton plus one or two ANDs in the middle
  (1|2|2 -> 2|4 or 3|4). They are not a route to goal B as they stand: they keep the 10-AND stage 1,
  while the NIST 28/4 circuits have 9 level-1 ANDs and 6 in the middle. Depth pulls on 29/4 targets with
  the AD cap off fell back to 28/5 in 5 of 10 jobs (132@21, 135@19, 136@20: not better than the
  existing 28/5 points; `chk_jump.py`).

## 5. Settings (question 4)

Evidence is weak throughout: op seconds never varied; eps, nursery and operator set changed together;
arms are single 1-CPU-h runs.

- **How noisy one CPU-hour is [C]**: twenty 1-CPU 1-hour blocks inside long3 (same configuration, shared
  archive): 11 / 5 / 3 / 1 blocks with 0 / 1 / 2 / 4 front admissions; V per block 0 (11 times), 1-15
  (7 times), 32, 34. With a mean near 1, a second arm shows 2 or more in about a quarter of runs by chance.
- **The arms, recounted [C]** (`q4.txt` 3; front admissions / with A <= 31 / V): ab2base 1 / 0 / 2;
  ab2gen (+osc, generators never sampled) 2 / 2 / 38; ab3gen (+generators, eps 0.5, nursery 0.4)
  2 / 1 / 36; ab3lin (+linres) 2 / 1 / 130, both from trb, not linres; ab4base 1 / 1 / 4; ab4ad3
  (ad3_share 0.3) 2 / 0 / 3. **[H]** None of these differences means anything on its own. The ad3_share
  rule "adopt if test >= base" fired on 2 vs 1, and by value the base arm was ahead (one 31/5 point
  against a 35/3 and a 38/3 point).
- **hub vs memetic (first A/B) [C]**: 10 front admissions (my replay; E counted 8 against the seed pool)
  vs 2 at about 4 CPU-h each. **[H]** This one is unlikely to be chance (about 2 % if the rates were
  equal), but the arms differ in everything; and all 10 hub points have A >= 32.
- **ad3_share 0.3 [C]** (`q4.txt` 4): in long3+long4, AD3 targets took 18 % of CPU before it was set and
  44 % after. Front admissions per CPU-h on AD3 targets 0.75, on the others 0.77; V per CPU-h 1.9 vs 23.5.
  Nothing nearer goal F resulted (140@25 and the pin's 139@27 stand). **[H]** Set it to 0, or confine it
  to the goal F window (GD 22-27); the AD3 points it produced are at GD 14-21.
- **eps / bandit [C]**: explore jobs 30.65 CPU-h, 30 front admissions, V 18.4 per CPU-h; exploit jobs
  35.25 CPU-h, 45, V 21.1. Exploit chose join 4,222 times of 5,447 (long3: 2,669 join picks); in ab2gen it
  locked onto osc (32 of 38 jobs). **[H]** The bandit is not steering toward value: its reward is the
  gain discussed in finding 1, and the score (gain + 0.5) / (CPU-s + 120) favours 5-second jobs. Fixed shares would lose
  nothing.
- **Seconds [C]**: time of the last improvement in jobs that gave a front admission: polish median 21 s
  (24 % after 60 s), pull median 53 s (39 % after 60 s, 15 % after 80 s). Admitted jobs on nursery targets
  were still improving after 75 s in 28-29 % of cases, on other targets 14-20 %. **[H]** 90 s is enough
  for mature targets (they do not move at all) and too short for fresh structures; no run compared
  budgets, so this is a suggestion to test (90 vs 180 s on nursery targets), not a result.
- **nursery [C]**: see section 3; never tested alone. **near**: 0.0 in every run, no data.
- **Workers [C]**: 6 CPUs (long2) to 12-15 CPUs (long4): utilisation 98-99 %, no scheduler bottleneck.

## 6. Recommendations (question 5)

All [H]; each names the count it rests on. None of this has been tested as a configuration.

### 6.1 Scheduler (for hub long5 and for X2's goal scheduler)

| change | basis |
|---|---|
| Score progress by cap box (dG under A, AD, GD caps, weighted by class), not `Archive.gain` | finding 1 |
| Count attempts per (operator, tuple), not per id; stop at 2 polish, 3 pull, 1 trb, 1-2 gen_skel per tuple | finding 7, section 3 |
| New tuples with A <= 32 get their first polish and first GD pulls before anything else is scheduled | 28/5/127/22 waited 3.4 h; pull on a fresh pull product is the best chain step (2.2) |
| Choose targets by class, not uniformly over front ids. Suggested CPU shares: A28 30 %, A29-31 25 %, A32 (AD4 and AD <= 6) 25 %, goal F window 10 %, goal G window 10 % | finding 6. The split inside A <= 32 follows the user's order, not a measurement |
| Inside a class spend the kernel on fresh structures (gen_skel products, results of infeasible pulls, joins that changed the tuple), never on seeds or on tuples already polished twice | finding 3, section 2.2 |
| join: one pass per target and archive state; fill the partner list with non-front circuits first; do not keep its equal-tuple copies as targets | finding 8 |
| Drop osc | finding 9 |
| ad3_share 0 (or goal F window only) | section 5 |
| Fixed operator shares instead of the bandit. Suggested CPU: pull 45 %, gen_skel 20 %, polish 20 % (fresh structures only), trb 10 %, join 5 % | 2.1-2.3, section 5 |
| pull: make "GD-1, AD cap off" the default move (61 V per CPU-h, 11 front admissions in 272 jobs; GD-3: 8 in 131); stop A- and AD-lowering pulls on AD3 and AD4 targets (0-2 % feasible); keep the class jump as its own move with caps (A+1, AD-1, GD) on AD5 targets with A <= 31 | finding 5, section 3 |
| pull: check feasibility after 20-30 s and stop if still infeasible | section 3 |
| Seconds: keep 90 for polish / pull on front tuples; try 180 on nursery targets as an A/B; join 60 and trb 30 are not binding | section 5 |
| A/B arms: at least 8 CPU-h per arm and judged on front admissions with A <= 32 plus goal-near admissions (`eval_run.py`), not on the hub gain | finding 10 |

### 6.2 What to drop

osc; ad3_share; polish on seeds; repeat joins; A- and AD-lowering pulls outside AD5 targets; gen_skel on
targets with A >= 33 outside the goal F / G windows. linres, gen_inv3, gen_bottom and gen_joinplus had
0 front admissions in 5-21 jobs each: no reason to add them, too few jobs to call them useless.

### 6.3 Overnight from 07:00 UTC

- **Expectation.** The hub operators have not improved any goal-near tuple under its own caps (finding 3) and
  no goal box has tightened since 22:20 UTC. A 12-h hub run in the current configuration is likely to keep
  filling the A29 / A30 AD4 staircases and the AD3 staircase at GD 14-21 and unlikely to meet B-G. Most of
  the 20 CPUs are better spent on whichever new operator of tonight's agents (T1-T4, X1, R1, R2) shows
  goal-near admissions in its own A/B; I have not looked at their results.
- **What I queued** (`QUEUE.md`, entry L1): the existing scheduler with the configuration changes that
  need no code (no osc, no ad3_share, uniform operator choice with pull and gen_skel listed twice,
  nursery 0.5) on a fresh directory seeded only with the goal classes, one circuit per tuple
  (`mk_focus_seeds.py`: 425 seeds from the present archive), and optionally the baseline configuration
  beside it on the same number of CPUs so that the morning has one comparison with enough CPU-hours to
  mean something. The launch path was tested in pieces of under 2 minutes on CPU 12 (`smoke1`, `overnight/smoke2`:
  seeding, the operator list with repeats, a gen_skel and a trb job, harvest, evaluation); the
  configuration itself has never run for longer. The job script is `focus_job.sh`; `harvest.py` writes
  new non-dominated circuits to `found/` with sidecars and aes_check results.
- **For goal C and B** the logs point at what T1 is already doing (gen_skel kicks of the A28 circuits
  followed by longer polishes under the goal caps, depth pulls from 127/22 and 128/20). 28/5/127/22
  itself had never been polished or pulled when the hub stopped.
- **For goal D** the hub's depth pulls moved 31/5 circuits to 32/4 in 4 of 30 jobs (119@21, 122@18,
  123@17, 125@17), 3 or more gates above the 32/4 front; and 33/4/108/19 is one AND from the box. Neither
  route was ever run on purpose (caps 32 / 4 / 19-20 from 31/5 and 33/4 starts).

## 7. Limits

- Front admissions are judged inside each directory against its own archive; the six 1-CPU arms and
  `long` ran in parallel from shared snapshots, so the same tuple can count in two directories
  (29/5/134/17 does). The per-directory tables are exact; the all-directories totals count such
  repeats.
- Lineage credit follows the `parents` field. For join it names the two circuits joined; whether an
  equal-tuple copy in a lineage mattered (different XOR layout) cannot be read from the logs.
- "Same AND span" compares span(1, inputs, AND outputs) as truth tables; it says nothing about XOR cost.
- The value model's constants are mine. Findings 1-3 and 5-10 are counts and do not use it; finding 4
  and the V columns do.
- I did not re-verify circuits (the hub verified at admission) and did not run any search.

## 8. Files

`l1_load.py` (cache), `l1_lib.py` (replay, value model, lineage), `q1_ops.py`, `q2_waste.py`,
`q3_anc.py` (AND structure via `boolflux.core`), `q4_settings.py`, `q5_goals.py`, `q6_starve.py`,
`q7_kernel.py`, `chk_gain.py`, `chk_jump.py`, `chk_stairs.py`, `chk_delta.py`, `mk_focus_seeds.py`, `focus_job.sh`,
`harvest.py`, `eval_run.py`
(judge any hub directory with these measures: `L1_OUT=DIR python3 l1_load.py name=/abs/hubdir ...`, then
`L1_OUT=DIR python3 eval_run.py`). Outputs: `~/xs-campaigns/2026-11-15-study/L1/`.
