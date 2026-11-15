# T4: target G (A <= 44, AD <= 4, G <= 140, GD <= 11)

Agent T4, 2026-11-15 from 01:33 UTC, CPUs 8-9. Code here, data in `~/xs-campaigns/2026-11-15-study/T4/`.
Start points: ours 48/4/151/11 (hub `4d335411443f`) and 43/4/141/12 (`20d6b396a934`).
Published at GD 11: 49/4/148 (NIST); nothing with A <= 48.

## Result summary

All verified with campaigns/aes_check.py (pin 3d80774), all new Pareto points; files in
`~/xs-campaigns/2026-11-15-study/T4/found/` with JSON sidecars. Before today: ours 48/4/151/11,
published 49/4/148/11 (nothing with A <= 48 at GD <= 11); ours 43/4/141/12, published 45/4/141/12.

| A | AD | G | GD | how |
|---:|---:|---:|---:|---|
| **42** | 4 | 301 | **11** | 48 front + shared-junk bottom with free x-forms + low d-junk AND (section 9), polished from 452 |
| 42 | 4 | 230 | 12 | same family (y0 at level 12), kernel-polished (from 458) |
| 43 | 4 | 278 | 11 | section 8, kernel-polished (from 417) |
| 44 | 4 | 254 | 11 | section 8, kernel-polished (from 380) |
| 46 | 4 | 203 | 11 | y1/y4 + y5/y6 coincidences (section 3), polished (from 275) |
| 47 | 4 | 186 | 11 | y1/y4 coincidence, polished (from 245) |

Goal G: A <= 44, AD <= 4, GD <= 11 are met (42/4/301/11); **G <= 140 is not** (best 254 at A44,
278 at A43, 301 at A42; polishing continues to 06:35 in queue/run-s42g21, run-s42t22). By counting, the shared-junk bottom costs about 100 XORs more than the 48's bottom
(section 8), so G <= 140 is not expected from this family [H].

## 1. Anatomy of the GD 11 / GD 12 circuits (anat.py, F's depth.py / skeldepth.py)

| circuit | AND levels (count @ gate level) | skeleton bound |
|---|---|---|
| ours 48@11 | 9 @2-3, 3 @6, 4 @7, 32 @9 | 11 |
| NIST 49@11 | 9 @2-3, 4 @6, 4 @7, 32 @9 | 11 |
| NIST 45@12 | 9, 4 @6, 4 @7, 13 @9 + 15 @10 | 12 |
| ours 43@12 | 9, 3 @6, 4 @7-8, 27 @9-11 | 12 |

All are "stage 1 (9 products, N = x^17 at gate level 5) -> depth-3 GF(16) inversion (AND @6,
AND @7, XOR @8: four Y-forms Y_i = Tr(alpha_i N^-1) + c at level 8) -> bottom". In the GD 11 circuits
every output is the XOR of exactly 4 level-9 products Y_i * w_i(x) (32 products, none shared).
- [C] swap.py: in 48@11, both 43@12, NIST 45@12 and 49@11 every use of stage 1 lies in
  span(1, x, N): stage 1 can be replaced by any 9-cover of N (depth permitting).
- [C] all critical paths of 43@12 run in, L0 x2, A1@3, L1 x2 (N at 5), ...: N at level 4 would make
  it GD 11. coverlev.py: no image of the 7 known cover classes (14280) has all 9 products at gate
  level <= 2 (best 3 at level 2) [C for these classes], so that route is closed.

## 2. GD 11 forces 4 products per output (model M; rank-1 bounds)

Model M: N at gate level >= 5, Y-forms (exact functions of N) at level >= 8, products at >= 9, so
with GD 11 every output is the XOR of <= 4 products (Kraft) plus cheap front terms.
- S_k = Tr16(Y R_k(x)), R_k(x) = theta_k x^16 + theta_k^16 x, has bilinear rank 4; a 4-product
  rank-1 output is an exact rank decomposition (basis A_k, x-forms = trace-dual basis on R_k).
- [C] cosets.py: exactly one pair of AES output functionals is GF(16)-proportional (bits 1, 2 =
  NIST y6, y5); [C] share.py: two outputs share at most 2 rank-1 products (all bases, all gamma).
- [C in M] inv6.py, depth-3 inversion (all affine functions of N at level 5; A2 = AND of affines;
  A3 = AND of level-6 signals; Y-form = A3 + {A3', A2 + A2', A2 + aff, aff}): Tr(alpha N^-1) is
  homogeneous cubic, so 4 independent Y-forms need 4 A3 gates and >= 2 A2 gates; with 2 A2 gates
  (182 orbits up to N -> c N^(2^i)) the direct Y-forms have rank <= 2 [C]; adding A3 + A3' forms gave
  no rank 4 (search truncated to 70 A3 candidates per orbit: [H]); 3 A2 gates: 3 of 7599 orbits reach
  rank 4 (the 48 uses one of them). So the inversion needs 7 ANDs (3 + 4) [C direct / H with pairs].
- [C] invdesign.py: with 3 + 4 ANDs, a 5th Y-form exists only as A3_x + A3_y with equal residuals;
  over all 150 design images the best rank-1 y5/y6 sharing is 1 product (bottom 31, A = 47), and no
  such design reaches Y-level 8 with any known cover (fast47.py, 97 covers with level-3 products) [H].
- So with RANK-1 bottom products, GD 11 needs >= 9 + 7 + 31 = 47 ANDs in M (and the 47 is not
  depth-feasible), i.e. 48 [C for the stated cases / H overall]. These bounds say nothing about
  rank-2 bottom products, which is where sections 3 and 8 get 43-47.

## 3. Rank-2 bottom products with shared junk (the mechanism behind 47 and 46)

(Y_a + w_b)(Y_b + w_a) = Y_a w_a + Y_b w_b + [Y_a Y_b + w_a w_b]: one AND carries two rank-1 terms,
leaving a d-junk Y_a Y_b (a quadratic function of N, often in the front span) and an x-junk w_a w_b
(a product of two x-linear forms of "subfield type", never in the stage-1 span on its own).
- [C] chain.py (48 front, exhaustive over all <= 3-product designs per output and all free x-forms):
  no output alone can drop a product when the junk must lie in the front span (no shared junk ANDs).
- But the x-junk of two DIFFERENT outputs can agree modulo the front span; then one set of junk ANDs
  serves both. pairscan.py / pair56.py on the 48 front:
  * y1, y4, pairing (0,2)(1,3): q1 = q4 mod stage-1 span (cover-dependent coincidence):
    8 products -> 4 + 2 shared x-junk ANDs + 1 shared d-junk AND(Y0, Y2): saves 1.
  * y5, y6 (the proportional pair), single pairs (1,3) / (0,3): x-junk equal mod span(1, x, N)
    (structural, any cover), d-junk free: 8 -> 6 + 1 shared x-junk AND: saves 1.
- Depth: y6 then had Kraft sum 1.004 > 1 at level 11. polpass.py: re-polarising a product used by
  one output only (AND(L^1, R) = AND(L, R) ^ R, free via XNOR when L has >= 2 terms) folds R into the
  output's junk and cancels front terms: Kraft 0.81, bound 11.
- Construction: build46.py (plans per output) -> polpass.py -> depthsynth.py (Huffman XOR tree per
  form; meets the skeleton bound) -> aes_check. 47 = y1/y4 only; 46 = y1/y4 + y5/y6.

## 4. Other GD 11 fronts (pairscan_all.sh over the 31 GD <= 11 AD4 archive circuits)

NIST 49@11 front: coincidences (y0, y5) p3 (0,1) and (y5, y6) p3 (1,3)/(0,3), both d-free but both
need y5: saves 1 -> 48. 51@11 / 53@11 fronts: 1 usable pair each. GD 10 fronts: none d-free.
GD 12 circuits (genscan.py, single merges of unshared products): no coincidences.

## 5. Joint search for more coincidences (coincov.py, coinscore.py, joint44.py, pipe43.py)

- coincov/coinscore (48 Y-basis, all 14281 cover images): estimated net savings up to 5 for some
  covers (A 43 at GD 11 if depth held), but pipe43.py (cover swap with polarity optimisation, exact
  skeleton bound) gives bound 12-13 for every one of the 600 best candidates: the 48's inversion
  operands are cheap only in its own cover. Cover-dependent coincidences and depth conflict.
- joint44.py (cover x inversion design x 4 Y-forms, fast47 depth model for Y-forms <= 8, junk classes
  mod S1, d-junk exact in the function-of-N world): best estimate 46, only for the 48's own cover [H].
  (A first run had a d-junk cost bug, kept as j44/cands-v1-dcostbug.jsonl.)

## 6. Search runs (fdrive, hub kernel bfx-593fa798f5)

| run | start | caps | result |
|---|---|---|---|
| b43 (mix) | 43/4/141/12 | GD11 AD4 A44 | 143/44/12 infeasible after 7 min (stopped) |
| b48 (gate, lex a,cost,gd) | 48/4/151/11 | GD11 AD4 A44 | no change in 40 min |
| r47s1/2 (gate) | 47 area synthesis (GD 25) | GD11 A47 | stopped after 5 min (replaced by depth-synth start) |
| p47s1 (gate) | 47/4/245/11 | GD11 AD4 A47 | 186 at 113 s, flat to 923 s |
| p47s4 (trb), p47s5 (osc) | 47/4/186/11 | same | no gain in ~3 min each (osc relaxed stage 160@GD12) |
| p46s1/2 (gate) | 46/4/275/11 | GD11 AD4 A46 | 203 at 300 s (s1); s2 stopped early |
| p44s1/s2 (gate) | 44/4/380/11, 44/4/376/11 | GD11 AD4 A44 | 254 at 716 s (s1); s2 264 at 90 s (stopped) |
| p43s1 (gate) | 43/4/417/11 | GD11 AD4 A43 | 284 at ~5 min (stopped for searches) |
| p43s2 (gate) | 43/4/284/11 | same | 278 at 434 s (stopped for searches) |
| p43s3 (osc) | 43/4/284/11 | same | relaxed stage 227@GD12, repair to 11 failed in 2 min (stopped) |
| p42s1 (gate) | 42/4/458/12 | GD12 AD4 A42 | 230 at 122 s (stopped: 42@11 found) |
| p42s2 (gate) | 42/4/452/11 | GD11 AD4 A42 | 301 at 433 s (stopped 03:33, saved) |
| p42s3 (gate) | 42/4/454/11 (basis y0,y1) | GD11 AD4 A42 | 314 at 86 s (stopped) |
| queue/run-s42g21 (gate), run-s42t22 (trb) | 42/4/301/11 | GD11 AD4 A42 | 03:34-06:35, verified into found/ at the end |

## 7. Failed / side experiments

- orbit_sat.py (C's stage1 encoding: is a subfield-type rank-2 form a member of a 9-cover?):
  orbit 85 and orbit 510 both > 1500 s without answer (inconclusive).
- absorb.py (same question, own encoding): > 6 min per target, stopped.
- greedy46.py: single-output moves never lower the AND count (savings need pairs); superseded by pairscan.
- coversearch.py: stage-1 replacement in 43@12 gives bounds 13-14 (own cover with polarity
  optimisation 12): no faster stage 1 among known classes.

## 8. Junk shared through linear dependencies: 44, 43 at GD 11 and 42 at GD 12

- Generalisation of section 3: an output's x-junk need not EQUAL another output's; it only has to lie
  in span(stage-1 products, G), G = the extra x-junk ANDs actually built. spanscore.py / spanfast.py
  (exact residues of alternating forms modulo the stage-1 span): on the 48 front, G = the 8
  constituents w0w2, w1w3 of y1, y2, y3, y5 (pairing (0,2)(1,3)) puts the x-junk of y4 and y7
  (p2) and y6 (p3 (0,3)) in the span: 13 products saved for 8 + 1 (AND(Y0, Y2)) junk ANDs:
  bottom 28, **A 44** (spanfast: best possible with p2/p3 designs on this front).
- 3-product designs with FREE x-forms (chain.py graphs; the x-forms on a Y-vertex used twice are a
  free split): chain44.py / cxplan.py: with the 44's span, y0 also has 3-product designs whose junk
  lies in the span: **A 43** (build46 'cx' plans, polpass, depthsynth: 43/4/417/11).
- search42.py: basis sets B (outputs whose constituents are built) x every other output's best
  design (2-product p2, 3-product incl. free x-forms, exact linear algebra; 2-parameter families by
  enumerating one parameter and solving the other): net 6 = **A 42** on the 48 front (B = {y4, y7}
  or {y0, y1}), but the 3-product outputs that need the level-9 d-junk AND exceed Kraft 1 at level
  11 (1.09-1.12 over all variants tried): 42/4/458/12. With the constraint "3-product outputs only
  with d-junk in the front span" the best is net 5 (A 43) for all three pairings [H: depth model is
  this constraint plus the polarity pass].
- Other GD-11 fronts (search42 on NIST 49@11, 51@11 x2, 53@11, light constraint): best A 44, 44,
  46, 46. A GD-10 front (60@10): products land at level 9, no GD-10 construction.
- G: per p2 output the 4 operands Y_a + w_b need their own XOR trees (the Y-form at level 8 has no
  slack for one more term) and the junk sum has 10-20 front terms; kernel polishing gives 380 -> 254
  (A44) and 417 -> 284 (A43) in minutes and then stalls. reqsynth.py (required-time synthesis with
  greedy reuse) and depthsynth with the 48 as parent do not beat the plain Huffman start by much.

## 9. 42 at GD 11: the d-junk AND at gate level 6-7

- The 42@12 of section 8 failed GD 11 only because output y0's junk contained AND(Y0, Y2) at level 9
  (Kraft 1.09). But Y_a Y_b = Tr(alpha_a N^-1) Tr(alpha_b N^-1) is a QUADRATIC function of N
  (exponents 14 (2^i + 2^j) mod 15 have weight 2), so modulo the front span it equals a product of two
  affine functions of N: one AND at gate level 6-7 (build46.py T4_DJLOW=1, dj_low()). Same AND count,
  Kraft weight 1/32-1/16 instead of 1/4. With it the search42 net-6 plan (basis y4, y7) has bound 11:
  **42/4/452/11** verified.
- search42 without the 3-product restriction, all three pairings, plus extra d-junk pairs: max net 6
  (A 42) on the 48 front [H in this design family]. onemore.py: no single extra x-junk AND upgrades two
  outputs at once (bases {1,2,3,5}, {0,1}, {4,7}, {0,4}).
- Mixed-pairing bases (|B| <= 2, runmix.sh) and extra d-junk pair sets: max net 6 (A 42).
- Other fronts with the full machinery (fronts2.sh): NIST 49@11 net 6 (A 43), 51@11 net 7 (A 44),
  53@11 net 7 (A 46). The 48 front stays best.

## Files
anat.py cosets.py share.py rank2.py xjunk.py chain.py absorb.py covers.py orbit_sat.py swap.py
coversearch.py coverlev.py inv6.py invdesign.py build47.py scan47.py scan47b.py fast47.py ownInv.py
dbg38.py build46.py greedy46.py pair56.py pairscan.py pairscan_all.sh vncheck.py coincov.py coinscore.py
pipe43.py joint44.py dbgj.py skterms.py depthsynth.py parsyn.py polpass.py genscan.py
spanscore.py spanmb.py spanfast.py chain44.py cxplan.py search42.py auto42.py fix42.py reqsynth.py
onemore.py
(queue job: ~/xs-campaigns/2026-11-15-study/T4/queue/polish_job.sh)

## 10. Coordinator request 03:50: goal G from the 43/4/141/12 side

- (a) [C] skeleton depth bound of 43/4/141/12 (both 43@12 files) = 12, all 8 outputs at 12
  (F's skeldepth.py: every AND operand and output built as its own optimal XOR tree over the given
  AND functions). So GD 11 is not reachable with its AND structure; (b) does not apply.
- Where it fails (ylevels.py): its front (16 ANDs, the same 9 + 3 + 4 shape as the 48's) has only
  3 Y-forms at level 8 (alpha 12, 176, 236, independent); every other Tr(alpha N^-1) is at 9-10.
  A rank-4 output needs 4 independent alphas, so every output of a bottom on this front has a
  product at level >= 10 (Kraft weight 1/2 at 11). The 48 front has 4 independent Y-forms at level 8
  (12, 81, 92, 176), which is what all the GD-11 constructions here use. So (c) on the 43 front
  would need the front changed until it is the 48 front's inversion (design 38 in inv/designs180);
  the 42/4/301/11 is that rebuild.
- CPU 8 trb run stopped at 42/4/300/11 (saved: found/t4-a42-ad4-g300-gd11-kernel-trb), replaced by
  a gate polish seed 23 (queue/run-s42g23, to 06:35).
