# Z1: 27 ANDs via the output staircase (2026-11-15, track Z)

Labels: [P] proved here (argument given), [C] computed exactly / exhaustive within the stated case,
[H] heuristic or empirical, [V] verified circuit (aes_check). Code: this directory. Data:
`~/xs-campaigns/2026-11-15-targets/Z1/` (runs/, found/). Code version: worktree HEAD 8922cac
(+ untracked strategy dirs); H2 binaries gen13 = gen13c sha256 fbc526c7f7d3574c... (read-only use).

## 1. What the staircase is, exactly [P]

Setting (staircase NOTES): ANDs g_1..g_A independent of {1, x} and each other; every output
combination c has a unique AND support; m_k = fewest ANDs (dependency-closed) whose span holds k
independent output components; waste = m_8 - m_1 - 7.

Define the core E = ANDs in the closure of EVERY nonzero output combination, and L = the rest
(K = |L|). Call L a *sink layer* if no AND of L is an ancestor of another AND of L. Let M be the
8 x K output-usage matrix (column j = which outputs read g_j, for g_j in L) and Code = row space
of M, a binary [K, 8] code (rank 8 because the outputs are independent mod the core).

**Lemma 1 [P].** If L is a sink layer, m_k = |E| + d_k(Code) for k = 1..8, where d_k is the k-th
generalized Hamming weight (Wei 1991). *Proof.* For a k-dim set C of output combinations the
closure of their supports is E (every nonzero c needs all of E, and E is closed) plus the L-members
read, which are sinks and so add nothing else; the L-part of the support of the subspace C is the
support of the subcode {cM : c in C}. Minimising over C is d_k. []

Consequences [P]: m_1 = |E| + d_1 (d_1 = minimum distance), m_8 = |E| + K when every L member is
read, so **waste = K - d_1 - 7** and A = |E| + K. With Wei duality (d_r(C) and K + 1 - d_s(C^perp)
partition 1..K) the staircase is equivalent to the arrangement of the K columns of a parity-check
matrix H (D = K - 8 rows). For three-stage circuits H is exactly the matrix of the last products'
images in H2's quotient V / (T_full + free) (H2 NOTES 5): c is an output combination iff
sum c_i img_i = 0. So
  d_k = k + min{ rho : f(rho) >= k + rho },  f(rho) = max number of images in a rank-rho flat,
i.e. a 1-step = one more product whose image is already in the span used so far, a 2-step = one
product opening a new image dimension and one closing it.

**So for sink-layer circuits the staircase is not an independent lever [P]:** (m_1, waste) =
(|E| + d_1, K - d_1 - 7). The targets (16, 4) and (17, 3) are, with d_1 = 2: |E| = 14, K = 13
(9 + 5 + 13) or |E| = 15, K = 12 (10 + 5 + 12, 9 + 6 + 12); with d_1 = 3: |E| = 14, K = 13 again.
Every 27 with a sink last layer and a common core is |E| + K = 27; the staircase adds only the
shape constraint on the image arrangement, which gen13 (H2) enumerates anyway.
A builder filter "waste <= 4" is therefore just "K <= d_1 + 11" in that class (useless as pruning);
it says something new only for non-sink layers or circuits whose components do not share one core.

**Lemma 2 [P, three-stage model: prefix of x-quadratics and functions of N, one parallel layer
with operands in aff(x) + V0; uses X3 NOTES 4.1].** d_1 >= 2, hence m_1 >= |E| + 2. *Proof.* X3's
projection onto the classes 127, 15, 47, 111 kills the prefix and maps a product to a tensor of
rank <= 2, while every nonzero output combination maps to a rank-4 tensor; so no output
combination reads only one layer product. [] With track C's stage 1 >= 9 [C, one level, x-linear
operands] and inversion = 5 [C], m_1 >= 16 in that model: **X1b's first component (16) is optimal
there**, and d_1 = 2 means two products whose tensors add up to a rank-4 output tensor. A 27 in
that model is then exactly a layer with waste K - 9 = 4, i.e. K = 13 over a 9 + 5 prefix.

## 2. The families [C, staircode.py on all 111 staircase files; identity m_k = E + d_k checked]

All 111 files: sink last layer, common core, and m_k = E + d_k exactly (`runs/staircode-all.jsonl`,
`runs/staircode-summary.txt`). d_perp = Wei-dual hierarchy = flats of the K images in V/(T + free).

| A | AND levels | E | K | d_k (code) | d_perp (images) | waste | files |
|---|---|---|---|---|---|---|---|
| 28 | 9-1-2-2-14 (X1b) | 14 | 14 | 2,4,6,7,9,11,12,14 | 2,5,7,10,12,14 | 5 | 14 (+1 with levels 10-1-2-2-13) |
| 28 | 9-2-4-13 (AD4) | 15 | 13 | 2,4,6,7,9,11,12,13 | 4,6,9,11,13 | 4 | 19 |
| 28 | 10-1-2-2-13 (AD5) | 15 | 13 | 2,4,5,7,8,10,11,13 | 2,5,8,11,13 | 4 | 26 (+1 10-1-2-3-12) |
| 28 | 10-1-2-2-13 (g150 type) | 15 | 13 | 2,4,6,7,9,10,12,13 | 3,6,9,11,13 | 4 | 1 |
| 28 | 10-1-2-2-13 (AD4-type code) | 15 | 13 | 2,4,6,7,9,11,12,13 | 4,6,9,11,13 | 4 | 2 |
| 29 | 9-1-2-2-15 (umizame) | 14 | 15 | 4,6,8,9,11,12,14,15 | 3,6,9,11,13,14,15 | 4 | 4 |
| 29/30 | 10-2-4-13, 10-2-3-4-10, 10-3-4-13 (hub) | 16/17 | 13 | AD5 code | 2,5,8,11,13 | 4 | 7 |
| 30 | 9-2-4-15 | 15 | 15 | umizame code | | 4 | 2 |
| 31 | 9-1-2-6-13 | 14 | 17 | 4,6,9,11,12,14,16,17 (+1 variant) | | 6 | 7 |
| 32 | BP family | 14-15 | 17-18 | d_1 = 4 | | 6-7 | 27 |

So every family is "E + K" with d_1 = 2 (all A28, hub A29/A30 with an AD5 layer) or d_1 = 4
(umizame, BP, A31): waste = K - d_1 - 7 everywhere [C]. The hub A29/A30 differ from A28 AD5 only
in E (extra middle ANDs), the layer code is identical.

Observations [C on these files]:
- every file has a sink last layer and a common core = the whole prefix (stage 1 + middle);
- A28 (all): d_1 = 2 (two last products with equal image mod T + free, e.g. g124 {15, 21} and
  {23, 27}); umizame A29/A30: d_1 = 4 (no repeated image: its first component needs 4 late ANDs,
  m_1 = 14 + 4 = 18).
- the "2,1,2,1" pattern (AD5 A28) = image flats f(rho) = 0, 2, 5, 8, 11, 13: each new image
  dimension carries 3 more images (one opens it, two close two output directions); the AD4
  pattern 2,2,1,2,2,1,1 = f = 0, 2, 4, 7, 9, 13; X1b 2,2,1,2,2,1,2 = f = 0, 2, 4, 7, 9, 12, 14:
  the AD4 arrangement with one more junk dimension.
- **Where X1b's m_1 = 16 comes from [C]:** not from a cheaper last-layer part (d_1 = 2 as in all
  A28) but from the core: |E| = 9 + 5 = 14 instead of 10 + 5 or 9 + 6. Its first component is
  E + members {16, 26} (g158; both GF(4)-norm members of tower gamma 7). The extra AND is in the
  layer (K = 14), so waste = 14 - 2 - 7 = 5. In g158 the layer is 12 members (tower gamma 7) +
  the non-member pair {18, 19} (= H3's dependent pair; parallel columns of M, the last 2-step).
- Junk accounting behind the 28s (H1/H2/C facts, reread in staircase terms): AD5 pays the extra
  AND for x-junk (10-product stage 1), AD4 for N-junk (6-AND middle), X1b in the layer.

## 2b. One stage-1 span behind all A28 families [C, `spaneq.py`, field maps x -> c x^(2^i)]

span = span(1, x, stage-L products) (H2 stages), compared under all 2040 maps x -> c x^(2^i):
- X1b prefix Pb (g158) = image of AD4 g131's span (x -> 24 x^64 and two GF(4)* multiples);
  X1b prefix Pa (g169) = image of AD4 g131, g141 AND g176 spans (3 maps each). So the three AD4
  9-spans and both X1b 9-spans are ONE span class, S9.
- Each NIST AD5 10-span contains an image of S9 (6 maps each); g124 = g128 (identity), g150 = image
  of g124. So the AD5 spans are one class S10 = S9 + one product.
- Hence X1b's "new family" 9 + 5 + 14 is H2's AD4-span 9 | 5 | 14 family up to a field symmetry
  (gen13 over Pb / Pa at K = 14 gives exactly H2's AD4 numbers: 4676 candidate subspaces,
  69 covering 14-member layers, gamma 7 <-> AD4 gamma 1), and all three A28 designs share S9.
  Every exact result over one member of a class holds for the class (gammas permuted by the map).

## 3. Constructive runs (gen13 = exact dense-subspace search, H2's real model) - see section 6

Pipeline (`g13case.sh`): H2 rprep.py (read-only) -> gen13 -> H2 fastrank.py -> `rvd_z1.py` (copy of H2
rvd.py writing to Z1 found/; re-verifies covering sets on the 256 inputs, minimises, builds and
aes_checks). Log: `runs/g13/cases.log`. Positive controls [C]: AD4 g131 span gamma 1 K = 14 ->
4676 candidates, 69 covering 14-member layers (= H2), two rebuilt and aes_check OK
(found/z1g13-ctl-ad4a-g1-*); AD4 span + its own 6-AND middle gamma 1 K = 13 -> 1 covering layer
(AD4 itself), rebuilt OK (found/z1g13-m6-131-g1-*).

Results (1275-member model, single gamma unless stated, stage 1 and middle fixed as stated):
- **(16, 4) route: X1b prefixes Pa and Pb (= class S9) + their own 5-AND middle, K = 13, all 16
  gamma: no covering layer** [C, member model; batch1, 15:46-15:53 UTC]. (K = 14 at gamma 7 gives
  the 69 layers; gamma 7/9/14 leave 3 non-covering candidates at K = 13.) Consistent with H2's
  AD4-span result via the S9 symmetry.
- **(17, 3) route in the AD4 family: S9 (g131, g141, g176) + each file's OWN 6-AND middle (E = 15),
  K = 12, all 16 gamma: none** [C, member model; batch2, 15:54-16:02 UTC; this middle had only been
  run at K = 13 by H2]. So 9 + 6 + 12 = 27 has no GF(4)-norm member layer over these prefixes.
- **Mixed gammas: S9 (Pb) + 5-AND middle, K = 13, members of any TWO gammas (all 120 pairs, 2550
  candidates, quotient dim 41): none** [C, two-gamma member model; 16:07-16:52 UTC]. All 16
  gammas at once (20400 candidates) was OOM-killed at the 4 GB cap (gen13 pair table) - not run.
- **Pair -> 1 AND sweep, prefix operands [C, `pairsweep.py` + H3 r1enum_v5, 17:38-17:49 UTC]:**
  all 517 known A28 files (hub archive A28, NIST, best/study files, H2 AD5 builds) -> 150 distinct
  AND spans with a parallel last-layer pair (136 of type 9+5+14, 14 of type 15+13). For each: kept
  ANDs fixed, one new AND with both operands in span(x, every kept AND that has a consumer = stage 1
  and middle; nv 22-23, exhaustive 2^21-2^22): **UNSAT for all 150**. (g124's pair {17, 26}
  agrees with H3's nosinks result.) Positive control of the input generator: window {26} of g124 ->
  r1enum finds AND 26's own operand at its Gray index (pairctl.py).
- **Semi-member layers, member-seeded (all 108,375 rank <= 2 tensor products: 1275 members +
  107,100 semi-members, one gamma, BMP middle unless stated), 19:05-21:04 UTC: none** [C, this pool,
  complete for layers whose member images have >= 9 (K = 13) / >= 7 (K = 12) distinct points]:
  S10 (g124) K = 12 (= 10 + 5 + 12): gamma 0 1 4 5 6 7 (candidate subspaces 0-15, none covering);
  S9 + AD4 6-AND middle K = 12 (= 9 + 6 + 12): gamma 0 1 4 5 6 7 (0 candidates);
  S9 (g131) K = 13 (= 9 + 5 + 13): gamma 0 4 5 7 (9,384-30,600 candidates, none covering; H2 had
  done gamma 1 and 6). Gamma reps cover all 16 gamma by H2's x -> w x symmetry for the BMP-middle
  cases (S9, S10 spans invariant, H2 inv4.py) and, via 2b, every A28 stage-1 span; for the 6-AND
  middle case the symmetry of the middle was NOT checked, so there only the 6 reps are covered. These were H2's queued-but-never-run "tier 2" cases.
- **Full-operand pair -> 1 AND, the (17, 3) step of the AD5 family [C, 17:52-23:09 UTC, CPUs 1, 4, 5]:**
  NIST a28-ad5-g124 pair {17, 26} and a28-ad5-g128 pair {20, 27} (the parallel pairs = the last
  2-step of their staircases): kept 26 ANDs fixed, ONE new AND with operands anywhere in
  span(x, all 26 kept ANDs) (nv 34; any chain depth, stage mixing allowed), r1enum_v5 over the whole
  Gray range [1, 2^33) in contiguous pieces: **hits 0 for both** (runs/pair/g124-17-26.q*.out,
  g128-20-27.q*.out). This was H3's "SKIP nv 34" case. Total ~12.5 CPU-h.
- Class-seeded semi (gen13c), capped, [H] only: S10 K = 12 gamma 7: 110,751 candidates in 83 min,
  none covering; S9 + 6-mid K = 12 gamma 1: 57,158 in 45 min, none.
- s9-semi-g1 class-seeded (gen13c), K = 13: stopped by hand after 32 min, 450,925 candidate
  subspaces, none covering [H, incomplete].
- Semi pool control attempt: S9 (g131) gamma 1, members + 107,100 semi, member-seeded, K = 14
  (where 69 member layers exist): stopped by hand after 13 min (147,687 candidate subspaces, none
  covering yet) - INCONCLUSIVE as a control (the member layers were not reached in that time).
  Replaced by the cheaper control S9 + 6-AND middle, gamma 1, K = 13 (1 member layer known):
  **semi pipeline control PASSED** [C]: 108,375 candidates (members + semi), member-seeded gen13
  complete in 17 min, 89,320 candidate subspaces, exactly 1 covering = AD4's own layer, rebuilt
  28/4/528/27, aes_check OK (found/z1g13-ctl-s9m6-semi-g1-*).
- Archive scan [C, `arch_scan.py`, hub archive A <= 30, 765 parsed + 17 with dependent ANDs]: every
  circuit has a sink last layer and a common core; (A, E, K, d_1, waste) in {(28,14,14,2,5) x203,
  (28,15,13,2,4) x247, (29,14,15,4,4) x23, (29,16,13,2,4) x242, (30,15,15,4,4) x4, (30,17,13,2,4) x46};
  no circuit with m_1 < 16 or waste < 4.

## 2c. Which last-layer ANDs serve which direction [C, `chainstair.py`, runs/chainstair.txt]

Every file tested has a NESTED optimal chain C_1 < ... < C_8 (|supp C_k| = d_k), so the staircase
can be read as "add these ANDs, gain this output direction":
- g124 (AD5): {15,21} {23,27} {20} {18,19} {25} {16,24} {22} {17,26}: costs 2,2,1,2,1,2,1,2.
  The last step is the parallel pair {17, 26} (identical output usage; H3's dependent sink pair):
  its 2 images are the only ones outside the largest image hyperplane (d_perp_1 = 2).
- g131 (AD4): 2,2,2,1,2,2,1,1 - the 4 images outside the largest hyperplane (d_perp_1 = 4) are
  spread over steps; the last two directions cost one AND each.
- g158 (X1b): {16,26} {13,23} {15,17} {20} {24,25} {21,22} {27} {18,19}: the AD4 pattern, but the
  last direction costs the non-member pair {18, 19} (parallel; H3 showed pair -> 1 AND impossible
  with the full operand space [C, kept ANDs fixed]). That pair is X1b's whole extra waste.
- umizame g137: first direction costs 4 ({16,20,21,26}), then 2,2,1,2,1,2,1.
- g150 (AD5 span, other layer): 2,2,2,1,2,1,2,1 (no parallel pair; 3 images outside the hyperplane).
Image arrangements [C, `images.py`, columns of a parity-check matrix = images mod T + free]:
g124: 11 distinct images in F2^5, repeats {15,21} {23,27}, 13 three-term relations;
g131: 11 distinct, repeats {21,22} {24,25}, 10 three-term relations; g158 (X1b): 13 distinct in
F2^6, repeat {16,26}, 9 relations; g150: 12 distinct, repeat {16,17}, 10 relations; umizame g137:
15 distinct images in F2^7 and NO three-term relation. So d_1 = size of the smallest dependent set of
images: 2 when two products have the same image (all A28), 4 for umizame (no repeat, no 3-term
relation). The "2, 1, 2, 1" alternation is the many 3-term relations: a 2-step opens one new
image dimension with a product and closes it with a second; a 1-step adds a product whose image
lies in the span of those already used (in these layers mostly via a 3-term relation). [P for the reading, C for the counts]

Reading [P]: a 27 from one of these 28s by changing only the last step needs the final 2-step to
become one AND, i.e. the parallel pair window (pair -> 1 product), which for g124 / g128 with the
full operand space (all 26 kept ANDs + x) had not been run (H3: "SKIP nv 34") - queued here.

## 4. Tools (this directory)
- staircode.py: staircase via the output-usage code (E, K, d_k, identity check vs staircase.py), stair_summary.py.
- arch_scan.py: fast (E, K, sink, d_1, m_1, waste) scan of .bfx / .circ.txt (ms per file; the builder filter).
- chainstair.py: nested optimal staircase chain (which ANDs give which direction); images.py: image arrangement.
- spaneq.py: stage-1 span equality / containment under x -> c x^(2^i).
- members.py: which last products are GF(4)-norm members of which tower gamma.
- g13case.sh + rvd_z1.py + sidecar.py: one gen13 case end to end (H2 code read-only), full sidecars.
- pairgen.py / pairctl.py / pairjob.sh / pairsweep.py / pairlist.py: pair -> 1 AND windows (H3 r1enum read-only).
- qrun.sh: per-CPU sequential queue runner.

## 5. Failures and pitfalls
- gen13 with all 16 gammas at once (20,400 candidates) was OOM-killed at the 4 GB cap (pair table).
- Semi K = 14 control (S9, 69 member layers exist) did not reach them in 13 min: K = 14 semi runs are
  too slow to be controls; K = 13 with the 6-AND middle is the working control.
- r1enum costs ~43 s per 2^24 operands here (6.1 CPU-h per 2^33 window), twice H3s
  estimate.
- Heredocs inside bash -lc single quotes break on apostrophes; write files with the editor tools.
- The WSL clock / timeout drift made the night units end about 30 min after their nominal 705 min.
