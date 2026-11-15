# What produced value before the hub, and what failed (agent L2, 2026-11-15)

Scope: everything up to the hub's first run (2026-11-14 17:38 UTC), plus track F's AD3 runs and
tracks C and G, which ran beside the hub without using it. Hub-era operators are agent L1's.
Sources: `~/xs-campaigns/2026-11-13-aes/` (tracks C, D, E, F, main), `~/xs-campaigns/2026-11-13-boolflux/`
(first study), `results/MANIFEST.json`, the NOTES of each track. Every number marked [C] was
recounted from the run records by the scripts in this directory (`e2.py` lineage, `e3.py` job
yields, `s1.py` join sweep, `m3.py` / `m4.py` manifest, `p1.py` pinned set); their outputs are in
`~/xs-campaigns/2026-11-15-study/L2/`. [H] marks an interpretation.

Value order used throughout (the user's): #AND, then AND depth, then #gates, then gate depth.
Tuples are A/AD/G/GD. "N:" = a pinned NIST circuit (pin 3d80774), "R:" = a `results/aes` circuit.

## 0. Summary

1. [C] **No pre-hub mechanism ever lowered the AND count below its start's family minimum.** All
   A28 points are published A28 circuits re-timed by the gate kernel. All A29 points are A28
   circuits where a depth repair broke the A cap (the result has a 10-AND last layer, section
   1.0). All A31 points are joins of two A32 circuits.
   Nothing reached 27, and nothing was aimed at it except tracks C and G (exact and algebraic
   work, no circuit).
2. [C] **The kernel was never asked to remove an AND from an A28 circuit.** No run record has an
   A cap below 28 or an AND-first objective on AES (216 `cost,gd`, 104 `cost`, 23 `gd,cost`
   summaries; the 33 `a,cost` runs are all small functions). Track D's windows and track E's
   chains minimised gates. This is the largest gap in the pre-hub record for goal A.
3. [C] What paid, in value order: depth pulls at fixed A on the A28 line (7 admitted points from
   53 jobs, 1.9 CPU-h); joins at the stage interface (first A31 circuits, 20 new points in 200
   CPU-s); kernel polish of fresh join or pull products (not of published circuits); the
   timing-driven regional rebuild under AD <= 3; one constructive depth-3 inversion block that
   then served as a join donor in 5 of long1's 17 frontier points.
4. [C] What did not pay: kernel polish of published circuits at their own caps (0 changes in 52
   jobs on A28 circuits, 9 of 10 starts unchanged after 1 CPU-h each); SAT windows; ejection
   chains; skeleton kicks; per-layer linear resynthesis; AND distribution; union-graph mapping.
5. [C] Two frontier points came from kernel runs whose A cap was never met (32/5/104/29 and
   29/5/135/17). The records do not flag this. For 32/5/104/29 the unmet cap is incidental: a
   paired probe (section 6) shows the gain comes from releasing the depth cap, not from the
   unreachable A cap.

## 1. Recipes for the valuable results

Common settings. Kernel `bfx_new` = `kernel/bfx.c` at 0659eb9 (track E copy), `lex cost,gd`,
kernel defaults of `strategies/E/erun.py` (`T0 0.6, Tperiod_it 20000, stall_it 60000, uphill 1.0,
max_excess 8, mv.resub1/2/3 = 1/2/1, dmax 220, pdiv 90, nl_samples 12, cand_cap 40, fraig 1`).
In `memetic.py` the kernel seed of a job is the member's polish counter (1, 2, ...), not a random
number. "polish" = caps equal to the circuit's own A, AD, GD. "pull" = cap GD lowered by 1-3,
cap A = the circuit's A, **AD free**. All jobs 120 s unless stated.

Run records: `E/low1/run/` and `E/long1/splice/` hold `log.jsonl`, `admitted/<hash>.bfx|json`
(the json nests the complete origin chain), and `polish/<hash>-p<seed>[-gdN].cfg|log|start.bfx|best.bfx`.
The full lineage of all 61 admissions is in `~/xs-campaigns/2026-11-15-study/L2/e2.out`.

### 1.0 AND-level profiles of the pre-hub low-AND results [C, `strategies/E/analyze_stages.py`]

| result | ANDs per AND level | explicit N^-1 signals |
|---|---|---|
| all 13 A28 results (AD4 / AD5) | 9 2 4 13 / 10 1 2 2 13, the published profiles | no |
| 29/5/135/17, 29/5/138/16 | **10 2 3 4 10** | no |
| all six A31 results | **9 1 2 6 13** | yes, after 14-19 ANDs |
| published for comparison | A29: 9 1 2 2 15 and 9 1 2 1 6 10; A30: 9 2 4 15; A32: 9 2 4 17 and 9 1 2 8 12 | A32: yes |

The A29 circuits are not the published A29 design. Under depth pressure the kernel took the
A28 AD5 circuit (last layer 13) to a last layer of 10 ANDs with 9 ANDs on levels 2-4. The A31
circuits are a Boyar-Peralta front and middle (9 + 9 ANDs, N^-1 explicit) under a 13-AND last
layer, where the A32 parents have 17 or 12 + 8.
[H] Both are structures outside the published families that nobody has analysed for goal A.
H1 may want them: `results/aes/aes-nist-E-pull-g135-a29-gd17-ad5.circ.txt` and
`results/aes/aes-nist-E-join-g116-a31-gd22-ad5.circ.txt`.

### 1.1 A = 28 (all keep the published per-level AND counts, 9|2|4|13 or 10|1|2|2|13 [C])

| point | chain (seed, time to result) | start | record | reproducible |
|---|---|---|---|---|
| 28/4/133/20 | `cli.py run --objective cost,gd --cap-a 28 --cap-ad 4 --cap-gd 20 --iters 100000 --seeds 1-8 --jobs 8`; seed 5 only, iteration 56529, 25.7 s | N:a28-ad4-g134-gd20-xx106-41 | `2026-11-13-boolflux/frontier-fwd-3/aes-sbox-a28-ad4-g134-gd20-xx106-41/` (src, bin, cfg, logs), code b0e56ecb18fe | yes with the run's own binary, and with today's code plus `--set skip_noop=0` (both re-run 2026-11-15, identical gate list); no with today's defaults (section 6) |
| 28/4/135/18 | pull GD19 (s1, 9.7 s) -> 136@19; polish (s2, 104 s) -> 135@19; pull GD18 (s3, 117 s) -> 136@18; polish (s4, 0.02 s) -> 135@18 | R: the 133@20 above | `E/low1/run`, admitted `edd3dc86b19d72d8` | one-off, time-budgeted |
| 28/4/138/17 | ... 135@19; pull GD17 (s1, 92 s) -> 140@17; polish (s2, 41 s) -> 139; polish (s2, 67 s) -> 138 | same | `384b7a8e2dee96a0` | one-off |
| 28/4/131/25 | polish caps 28/4/26 (s5, 87 s) | R: 131@26 (deterministic `cli.py run` from N:a28-ad4-g131-gd36) | `b28fe8246a5ee92f` | one-off (1 of 7 polishes of the two 131@26 circuits) |
| 28/4/175/14 | `cli.py flow --config gate --seconds 900 --seeds 1-4`, caps 28/4/14; seed 4 | N:a28-ad4-g176-gd14-xx148-25 | `main/conv/a28-ad4-g176-gd14`, code 7b3ff8a72682 | one-off, 1 of 4 seeds; manifest time 960 s exceeds the 900 s budget |
| 28/5/137/17 | pull cap A28 GD17 (s1, 95 s) -> 138@17; polish (s1, 30 s) -> 137 | N:a28-ad5-g128-gd20-xx100-27 | `7bb7e13f3d598b9a` | one-off |
| 28/5/125/25 | pull cap A28 GD26 (s4, 58 s) | N:a28-ad5-g124-gd27-xx96-26 | `dbd43170e14b9544` | one-off (1 of 4 pulls of this start; the others gave 129@23, 130@25 and 128@25 at AD 6) |

[C] low1 on the A28 line: 55 polishes (2.0 CPU-h) changed 6 circuits. Five of the six were
products of a pull made earlier in the same run and one was a result of the 11-13 kernel run;
no published circuit changed. 53 pulls (1.9 CPU-h) changed 53, 21 of them without meeting the
caps, 7 admitted. Pulls that never met their cap: 176@14 -> GD 11-13 (0 of 6), 153@15 -> GD 13-14
(0 of 5), 141@16 -> GD 15 (0 of 1), 138@17 / 137@17 -> GD 14-15 (0 of 3). GD 16 from the 17s was
met twice: at 146 gates (dominated by the published 141@16) and at A29.

### 1.2 A = 29 (low value: both are A28 circuits plus one AND)

| point | chain | record |
|---|---|---|
| 29/5/135/17 | pull of N:a28-ad5-g128-gd20 with **cap A28**, GD17 (s3); the repair went to A29 within the first 1.5 s and stayed there; 135 at 57.2 s. Seed 1 of the same job gave the feasible 28/5/138/17 | `E/low1/run/polish/688e861dabceaeab-p3-gd17.*`, admitted `0bbd82012fd62271` |
| 29/5/138/16 | pull cap A29 GD16 (s1, 115.5 s) of the 135@17 | `492089d26ec188ef` |

[H] In the user's order 28/5/137/17 beats 29/5/135/17. The A29 points only matter as G records.

### 1.3 A = 31 (joins of two A32 circuits; no kernel run removed the AND)

| point | chain | record | reproducible |
|---|---|---|---|
| 31/5/119/20 (first A31) | join: front N:a32-ad5-g107-gd22-xx75-4 kept up to AND level 4, back N:a32-ad4-g117-gd19-xx85-6 above AND level 3, 9 interface gates | `E/sp1` (`python3 strategies/E/splice2.py OUT --shard i/4 files.list`, 4 shards about 50 s each), `E/found/E-splice-a31-ad5-g119-gd20.json` | deterministic construction |
| 31/5/117/20 | `erun.py --seed 1 --seconds 240 --cap-a 31 --cap-gd 20` from the 119@20 (30.8 s; seed 2 also 117, 6.3 s) | `E/polish1/A31gd20-splice-s1.*` | one-off, 2 of 2 seeds |
| 31/5/115/28 | `erun.py --seed 1 --seconds 240 --cap-a 31` (GD free) from the 119@20 (238.6 s; seed 2: 115@34) | `E/polish1/A31-splice-s1.*` | one-off |
| 31/5/116/22 | join(front N:a32-ad5-g105-gd26 LX1, back 31/5/117/20), the back being a 3-deep join chain over R:108@20 (a32 ad5), N:a33-ad4-g106-gd22 and N:a32-ad4-g117-gd19; 4.4 min into long1 | `E/long1/splice/admitted/87e6dd3d8b251fe7.json` | deterministic given the pool |
| 31/5/118/19 | pull GD19 (s4, 28 s) of the 117@20 -> 119@19; join(front R:108@20 LX1, back it LY1, 1 interface gate) | `E/low1/run`, `67ddf01dc0753d1a` | pull one-off, join deterministic |
| 31/5/124/17 | pull cap A31 GD17 (s5, 96 s) of the 118@19 | `d20ee139e5eb68d9` | one-off |
| 31/5/123/18 | polish (s1) of 31/5/127/18, a 6-deep join chain whose root donors are F's `invsplice-116-g122-a37-gd14` and N:a32-ad4-g127-gd15, N:a32-ad5-g110-gd22, R:122@18 | `E/long1/splice`, `5f88c32686d51ca6`; long1 logged no within-job time | one-off |

[C] Why 31: in the sp1 sweep (150 circuits, 24,443 distinct join results) 489 results have fewer
ANDs than both parents, and the only ones below 32 are 18 results "A32 x A32 -> A31" with the
front cut at AND level 4 (or 6) and the back at level 3. No join gave fewer than 28. Joins with
one A28 parent and one non-A28 parent gave A >= 32 (3,818 results). Not one valid join exists
between an AD4 A28 circuit and an AD5 A28 circuit (0 results) - the same fact track G states as
"AD4 level 1 + AD5 inversion + AD4 layer misses one output dimension".
[C] Kernel alone: `erun.py` with cap A31 from the two A32 parents, 240 s, 2 seeds, with and
without cap GD20: 0 of 8 runs reached A31.

### 1.4 Goal-near points at A >= 32

| goal | point | chain | record |
|---|---|---|---|
| E | 32/5/104/29 | `erun.py --start N:a32-ad5-g107-gd22-xx75-4 --seed 1 --seconds 240 --cap-a 31` (GD, AD free). **The cap was never met**: the kernel stayed in repair mode (objective 1000104, excess 1) and walked 107@22 -> 106@36 (42 s) -> 105@33 -> 105@28 (196 s) -> 104@29 (236.6 s). Seed 2 of the same job reached 32/7/103/32, the published record tuple. The effective ingredient is the released GD cap (section 6) | `E/polish1/A31-parent1-s1.*`, one-off |
| D | 32/4/116/20 | join(front 31/5/116/22 LX1, back N:a32-ad4-g117-gd19 LY1, 0 interface gates); also directly in sp1 | `E/long1/splice/admitted/a43e1ae3d73fd6ce.json`, deterministic |
| D | 32/4/122/18 | `cli.py run`, caps 32/4/18, iters 100000, seeds 1-8 (seeds 6 and 8), 34.6 s | `frontier-fwd-3/aes-sbox-a32-ad4-g137-gd18-xx105-7`, deterministic command |
| D | 33/4/108/19, 33/4/110/18 | `cli.py run`, caps 33/4/20, seeds 1-8 (seed 7; seed 6) | `frontier-fwd-2/aes-sbox-a33-ad4-g108-gd20-xx75-5`, `...-g110-gd20-xx77-4`, deterministic |
| D | 33/4/115/15 | join(front N:a32-ad4-g127-gd15 LX3, back D's 37/4/121/14 LY3, 0 interface gates), 18.9 min into low1 | `E/low1/run`, `7e7b5cfa5ba7bf49`, deterministic |
| F | 35/3/140/25 | join(front R:35/3/139/27 LX2, back N:a35-ad3-g147-gd20 LY2) -> 140@26; polish (s2) -> 140@25 | `E/long1/splice`, `6ca48240265ce766` |
| F | 35/3/143/23 | join(front R:35/3/144/20 LX2, back R:35/3/139/27 LY2) | sp1 and long1, deterministic |
| F | 35/3/177/13, 35/3/162/14, 35/3/142/22 | `fdrive.py --mode fresh|trb --cap GD --cap-ad 3 --cap-a 35 --seconds 2700`, seeds 812 (fresh), 801 (trb), 808 (trb) | `F/ad3b/a35-f13`, `a35-t14`, `a35-t23`; sidecars in `F/found/camp-ad3b-*`; one-off |
| G | 43/4/142/12 | joins over N:a45-ad4-g141-gd12, N:a45-ad4-g147-gd12, R:36/4/134/13, R:45/4/146/12 -> 148@12; two polishes (s1, s1) -> 142 | `E/long1/splice`, `c9c8e998c9959b3e` |
| GD14 | 37/4/121/14 (two circuits) | D: kernel stage of a breathe cycle, 120 s, kernel seed 999975904, from R:38/4/124/14. F: `fdrive.py --mode trb --seed 2 --seconds 3600` from F's 122@14, at 1407 s | `D/fair/B124/c001`; `F/ab/r2-trb` |

The other Pareto points of the pre-hub set (41 tuples, 42 circuits) are in MANIFEST.json with the
same record types. [C] By mechanism: 20 polishes, 7 joins, 4 pulls, 6 `cli.py run`, 3 trb,
1 track D kernel stage, 1 main queue.

### 1.5 The two hidden enablers

* [C] **The 2026-11-13 deterministic sweep.** `cli.py run --iters 100000 --seeds 1-8` under each
  NIST circuit's own caps (78 starts, 37-68 s wall on 8 CPUs each, about 8 CPU-h in all). Six of
  its results are still on the pre-hub front, and its results are parents in most later joins
  (R:108@20 A32, R:122@18, R:131/133/134@13 A36, R:139@27 and 144@20 AD3, R:146@12 A45).
* [C] **F's constructive depth-3 inversion block.** `invbatch.py --only 0^2,1^3 --seeds 2-2
  --iters 200000; invsplice.py 116 inv-0x2_1x3-s2.txt` (7 s, no gate search) gave 37/4/122/14,
  which is itself dominated by the 121s. As a join donor it is in the lineage of 5 of long1's
  17 frontier points (31/5/123/18, 32/5/112/18, 33/4/112/17, 33/4/113/16, 35/4/123/14).
  [H] A new stage design is worth more as a donor than as a circuit.

## 2. What worked, ranked by value, with CPU cost

| rank | mechanism | value it produced | CPU cost [C] |
|---|---|---|---|
| 1 | depth pull at fixed A, then polish of the pulled circuit (low1) | all new A28 points at GD 17-19 and 25: goals B and C territory | 3.9 CPU-h on the A28 line; first point after 9 min |
| 2 | deterministic kernel run under own caps on every NIST circuit | 28/4/133/20; six front points; the parent pool | about 8 CPU-h for 78 starts (5-9 CPU-min each) |
| 3 | join at the stage interface (splice2) | first A31 circuits; 20 new points in sp1; 33/4/115/15, 32/4/116/20, 33/4/107/21 | sp1: 200 CPU-s. long1: 26 admissions, all in the first 8.6 min; 1,484 s of join time in 2.3 h |
| 4 | polish of join products (long1 splice arm) | 11 of its 17 frontier points; 3.63 points per CPU-h against 0.64 for polish alone | 4.7 CPU-h per arm |
| 5 | trb (timing-driven regional rebuild + kernel) under AD <= 3 | 40/3/174/13 and 38/3/161/14 in 2 min each; later 35/3/162/14 and 35/3/142/22 (35/3/177/13 came from fdrive's `fresh` mode: short independent kernel restarts) | 2 CPU-min for the first two; ad3b 14 jobs x 45 min |
| 6 | constructive depth-3 inversion block | 122@14 with no search; donor for 5 frontier points | seconds |
| 7 | depth release: kernel from a low-depth circuit with the GD cap removed (found by accident, in a job whose A31 cap was never met) | 32/5/104/29 and a 103@32 from N:107@22, where 4 x 900 s of polish at GD <= 22 gave nothing | 2 x 240 s |
| 8 | plain kernel from an unconverged result | 124@14 -> 122@14 in 4 of 4 seeds (25-123 s); 121 in one 120 s stage | minutes |
| - | exact work of tracks C and G | no circuit; the facts that explain why both A28 designs cost 28 in the three-stage model | C: 21.3 CPU-h in the 30 recorded zdfs runs, plus 1.9 h for stage 1 k = 8; G: 2 CPUs for about 9 h |

[H] Rows 1-4 are one pattern: the kernel is a good finisher and a poor explorer. It needs a start
that is new (another cap, another stage combination). Published circuits and its own converged
outputs are fixed points for it at their caps.

## 3. Failed approaches

"Decisive" = the evidence closes the idea as designed. "Under-tested" = small n, short budget or
the wrong objective for the question we now care about.

| # | approach | evidence [C unless marked] | verdict | retry? |
|---|---|---|---|---|
| 1 | Track D SAT windows, mode g (fewer gates at the same caps) | Surviving logs: 3,062 windows, 3,337 SAT calls, 0 SAT, 2,399 UNSAT (72 %), 938 over the 30k-conflict budget (28 %). Starts: N 116, 124 (A28), 127, 133; R 108@19, 124@14, 131@13. Windows of 4-9 gates (5-12 in the cut variant), <= 12 cut inputs. STATUS says "about 3,900" and lists NIST 103; no log supports either | decisive for small gate-saving windows at the caps; **not a test of AND removal**: the encoding asks for k-1 gates, or k gates with one AND fewer | yes, under another design: allow more gates for one AND fewer, larger windows aligned with a stage. H3 and R1 are doing this now; do not repeat mode g |
| 2 | D depth mode (GD - 1) | 115 windows on 4 starts, 0 accepted; runs cut at 64 s of 400 by the outage | under-tested (n and time) | low priority; pulls do this job |
| 3 | D breathe (windows at GD+1, kernel repair, windows polish) | fair test, 4 starts x about 1,100 s: 4 window accepts at GD+1, all undone by the repair; both gains came from the kernel stage | decisive | no |
| 4 | D incremental (CEGIS) encoding | k = 7: 14 of 15 decided against 15 of 15; k = 9: 1 of 12 against 5 of 12 | decisive at this size | no |
| 5 | E M1 ejection chains | a36, 60 s, 5 seeds: median 135 against 133 (control); variant without neutral acceptance 133; p = 0.05: 134. N:104 uncapped: 104 in every arm. A28 124 with A cap 30 or 31, 300 s: n = 1, no change. asmall1 (A29 starts) killed by the outage, no results | decisive for gate count on A36; **under-tested on A28** (n = 1) and never run with an AND-first objective | only as an AND-removal move (kick = merge two ANDs, repair by XOR), which is X1's task |
| 6 | E M2 skeleton kicks | single moves cost +12..+42 gates (A28 124) and +0..+19 (N:104) after the seeded rebuild; a36, 60 s, 5 seeds: median 135 | decisive as a gate-count move | no; see 9 for the AND-count question |
| 7 | E M3 exact-match splice | superseded by the linear interface (M3b) | - | no |
| 8 | kernel polish of published circuits at their own caps | main queue: 9 of 10 starts unchanged after 4 x 900 s each (one -1 at A28 GD14). long1: 52 polishes of A28 circuits, 0 changes; control arm 3 frontier points in 4.7 CPU-h | decisive | no. Give the kernel a new start instead |
| 9 | skeleton level on AES (bench) | output = input skeleton in 11 of 12 cases; full configuration 739-758 gates against 633 for rebuild only (naive start) | decisive for gate count. [H] not a test of K - 1 on an A28 skeleton: the objective was K + 0.02 E inside 120 s runs from A32-A36 circuits | under-tested for goal A, but track G's calibration predicts failure (its basis search cannot find 9-product covers that SAT finds in 33 s) |
| 10 | kernel removes an AND (cap A - 1) | 0 of 8 runs from the A32 parents (240 s, objective cost,gd) | under-tested: 2 starts, cost-first objective; no A28 start at all | hub `pull` now lowers A by 1 (L1 has the numbers) |
| 11 | raising the A cap to buy gates (A28 124 with cap 30 / 31) | n = 1 per arm, 300 s, no change | under-tested | low value by the user's order |
| 12 | F AND distribution transforms | no single transform lowers any output of N:116's skeleton below 15; beam of 8 lowers the Kraft excess 2.35 -> 1.26, not the bound | decisive | no |
| 13 | F union-graph area-flow mapping | only 169-176-gate covers at GD about 10 from 141 pool circuits | decisive | no |
| 14 | F direct splices on equal functions | 116 front + 133 back = 130@15; 133 + 116's inversion outputs = 127@14 | decisive; the linear-interface join replaced it | no |
| 15 | F inversion block into other bases; relaxed inversion specs; bottom transplants | 133-143 at GD14; complete designs 28-29 gates against 27; 143@14, 150@13 | decisive for GD14 ("122 is the floor of this route") | no |
| 16 | F search arms from 122@14 | 1 CPU-h jobs: gate-old 0 of 3, gate-new 0 of 3, osc 0 of 3, mix 0 of 1, trb 1 of 3 | under-tested (n = 3); trb's 1 of 3 is not significant | trb is in the hub |
| 17 | cap repair by the rebuild workflow | GD14 -> 13: 2 of 35 (136, 137 gates); GD13 -> 12: 0 of 10; 116@15 -> 14: 2 of 35 runs of 120 s | decisive: repair works when the skeleton depth bound already meets the cap | no |
| 18 | linres (XORFlux per linear layer) | N:35/3/139/27: each layer returns at its size (41, 20, 28, 15). Hub A/B 3: 10 jobs, 8 cell admissions, 0 frontier points | decisive per layer; cross-layer forms were not tried | no |
| 19 | F: A <= 34 under AD <= 3 by the kernel | one job, 10 stages, 1,204 s, seed 1, from N:35/3/139/27: unchanged. The log shows cap GD 40 and no A cap | under-tested, and possibly not the test it was meant to be | H4 is searching 34 at AD3 by construction |
| 20 | C: annealing over GF(4)-norm member subsets | best cost 20-23 against 16 for A28 from random starts | decisive (needle-like); replaced by exact enumeration | no |
| 21 | C: generic SAT of the last layer (13 free products) | not solved in 10 min; with 8 fixed > 170 s | decisive for that encoding | H3 has other encodings |
| 22 | C: two retracted results | "k = 7 UNSAT" with a fixed target basis (unsound); `nblock.py` k = 10 UNSAT contradicted by a verified construction | lesson: validate every exact model on a known positive first | - |
| 23 | G: generic basis local search (nlb) | solves 4-bit MC in under 2 s; 0 of 7 on 8-bit 9-product covers in 60-240 s | decisive; not used as evidence | no |
| 24 | G: last-layer walks with exact middle and exact cover test | 2,516 layers evaluated by the 23:10 UTC summary (1,702 K = 13 with junk 3, dim U = 7; 814 K = 12 with junk 5-6): every cover UNSAT, 0 circuits | [H] strong negative inside the three-stage model with operands in span(x, N, N^-1); says nothing outside it | not in this model |
| 25 | joins across the two A28 families | 0 valid joins between AD4 and AD5 A28 circuits; A28 x BP joins give A >= 32 | decisive for the linear interface | `gen_joinplus` adds products (hub era) |
| 26 | no-op filter | v5: median 133 in both arms, sign test p = 1 | decisive: no effect | no |
| 27 | Berkeley ABC flows | worse on every target (AES from N:104: 110) | decisive | no |

Not finished, and not failures: track C's gamma sweep (k = 12, dim Z = rank = 4) completed 10 of
16 values for the AD5 prefix and 11 of 16 for the AD4 prefix, all with 0 hits
(`C/logs/zdfs_r4_k12_*.json`); gammas 170-238 (and 34 for AD5) were never run. `C/STATUS.md`
and `C/NOTES.md` do not record the completed ones.

## 4. Reproducibility gaps (question 5)

1. [C] Of the 86 AES manifest entries, 47 are deterministic commands, 2 were re-run and
   reproduced (108@20 and 126@14), 7 are deterministic joins that were never re-run, and 30 are
   one-off time-budgeted jobs. **Every A <= 31 point of the AES push except the joins is one-off.**
2. [C] 28/4/133/20 has a deterministic command and a complete run folder (`src/`, `bin/`), but
   the code is b0e56ecb18fe, before review 3's ranking change. Tested for this report
   (section 6): its own binary reproduces it byte for byte, and so does today's code with
   `--set skip_noop=0`; with today's default no-op filter the same command stays at 134. The
   manifest does not say that the flag is needed. Presumably the same holds for the other 46
   "deterministic command" entries (not tested).
3. [C] All 36 curated AES-push entries give the strategy scripts' sha256 "at curation time"
   (17:54 UTC), not what ran. 377b03f committed the scripts 14 minutes later, so a commit now
   exists but the manifest does not cite it. Track E's kernel is a copy (`bfx_new`) with no hash
   recorded per job; track F's is a snapshot named only by a hash prefix (7c53f2e4).
4. [C] long1 logged no within-job time and no caps for its polishes (10 Pareto entries have
   `time_to_result_s: null`). low1 logged both.
5. [C] The kernel seed of a memetic polish is the member's polish counter. Two different jobs can
   therefore share (start, seed) only by accident, and the "seed" in a sidecar is meaningful only
   together with the start hash. F's two AD3 entries give the seed as "see cmd".
6. [C] Two entries are circuits that violate the caps of the job that made them (job_caps A31 ->
   A32 circuit; A28 -> A29). The manifest's `caps` field is empty for them and the mechanism text
   does not say so.
7. [C] Track D's window counts cannot be rebuilt: t2 and t3 runs died in the outage with only a
   first checkpoint, the breathe logs do not store window statistics, and no log exists for
   NIST 103.
8. [C] `E/long1/splice.log`, `control.log`, `low1/run.log`, `D/fair-q1x.log` are empty (the
   xsrun units wrote nothing to them); the jsonl logs are the only record.
9. [H] CPUs 12-19 of this machine are probably the efficiency cores (i7-13700H: 6 P-cores with
   two threads, 8 E-cores; WSL reports "10 cores x 2 threads"). Time-budgeted jobs on those CPUs
   do fewer iterations. low1 (CPUs 11-13), D's fair test (11-13), the main queue (0, 17-19) and
   tracks C and G are affected. No record stores iterations per job for the memetic polishes,
   so this cannot be corrected afterwards.

## 5. What this says for tonight [H]

* For goals B and C the measured recipe is the pull-then-polish ladder on the A28 line with AD
  free in the pull. It moved 133@20 to 135@18 and 138@17 in 30 minutes on 3 CPUs and stalled
  below GD 17. Pulls of more than 2 levels at once never met the cap.
* For goal E the only pre-hub gain came from releasing the depth cap on a GD22 circuit
  (section 6). T2's walk under caps 32/6/31 is the same idea with the caps set on purpose.
* For goal A nothing pre-hub is a recipe. What the record does supply is the list of things not
  to repeat (section 3, rows 1, 3, 8, 23, 24, 25) and three untested questions: an AND-first
  kernel on A28 starts, an AND-removing window with free gate budget, and a K - 1 skeleton
  search on the A28 skeletons.

## 6. Checks run for this report (CPU 12, each job under 2 minutes)

**Is the unmet A cap what produced 32/5/104/29?** [C, n = 3 per arm] Paired runs from
N:a32-ad5-g107-gd22 with `erun.py`, 100 s, seeds 1-3, caps AD <= 6 and GD <= 31, objective
`cost,gd`, kernel `bfx_new`; arm 1 with cap A31 (unreachable), arm 2 with cap A32 (feasible).

| seed | cap A31 | cap A32 |
|---|---|---|
| 1 | 32/5/106/29 (21.5 s) | 32/5/106/29 (21.2 s) |
| 2 | 32/5/106/26 (97.9 s) | 32/5/106/27 (81.2 s) |
| 3 | 32/5/106/28 (31.2 s) | 32/5/106/28 (26.7 s) |

Both arms leave 107 in every run and seeds 1 and 3 follow the same path. The unreachable cap
changes nothing. What the 2026-11-14 job had and the main queue's 4 x 900 s at GD <= 22 lacked
was the released depth cap. None of the 100 s runs reached 104; the original needed 236 s.
Data: `~/xs-campaigns/2026-11-15-study/L2/probeE/`.

**Are the recorded joins reproducible?** [C] `rejoin.py` re-ran the first A31 join and all 29
join admissions of long1 and low1 from their recorded parents and cut levels: 30 of 30 give the
identical kernel text. Output: `~/xs-campaigns/2026-11-15-study/L2/rejoin.out`.

**Does the "deterministic command" behind 28/4/133/20 reproduce it?** [C] With its own binary
snapshot (code b0e56ecb18fe, kept in the run folder) and a copy of its cfg: yes, 133 at iteration
56,529 again and a byte-identical best circuit. With today's code (f9fe6f7), same command and seed 5: yes with `--set skip_noop=0` (identical
gate list, 133 at iteration 56,529), no with the default settings (134, no improvement). The
no-op filter, on by default since 7ae20c8, changes the random trajectory; the ranking changes of
reviews 3 and 4 did not change this one. Details: `NOTES.md`.
