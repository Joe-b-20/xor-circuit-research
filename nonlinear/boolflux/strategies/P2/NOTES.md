# P2: T02 (A28/AD4/G176/GD14) and T06 (A34/AD4/G139/GD13), depth-first

Agent P2, 2026-11-15 from 15:22 UTC, CPUs 12-13. Code here, data in
`~/xs-campaigns/2026-11-15-targets/P2/` (runs/, found/). Bars (archive at 15:20): T02 28/4/175/14,
T06 34/4/134/13.

## 1. Starting material and skeleton bounds (scan.py, F's skeldepth.py)

`scan.py` read every circuit in NIST pin, best-1400, results/aes, study and target found/ folders,
2026-11-13-aes found/, and all hub archives (`2026-11-14-hub/*/archive/*.bfx`); 206 distinct
circuits with AD <= 4, A <= 34, GD <= 17 (`runs/scan.jsonl`).
- [C] (skeleton bound = min gate depth of any circuit with the same AND functions as affine forms
  over inputs and earlier ANDs): every A <= 28 AD4 circuit in the archive has skeleton bound >= 14,
  every A <= 34 AD4 circuit has bound >= 13. So GD 13 at A28 and GD 12 at A34 need different AND
  functions, not better XOR layers; plain kernel/trb/XOR resynthesis cannot reach them.

## 2. T06 bottom as a bilinear tensor decomposition (bil.py, botanat.py, orbit.py)

Model M (as T4): x^-1 = u z with u = N^-1 = (x^17)^-1 in GF(16), z = x^16. Every AES output bit is
a bilinear form of rank 4 in (Tr16(alpha u), x) [C, bil.py checks all 8 on 256 inputs].
- [C] In 34/4/134/13 (and NIST 34/4/139/13 and the other A33-A39 AD4 GD13-15 circuits except
  A32 125/127 and A36 129) the 18 AND-level-4 gates are exactly rank-1 products
  Tr16(alpha_j u) * g_j(x), no affine part: the bottom is a rank-18 decomposition
  sum_j alpha_j (x) g_j (x) w_j of the tensor of (u, z) -> u z, w_j in GF(256) giving which outputs
  use product j (output k uses j iff bit k of A(w_j) is 1, A = AES affine linear part).
- Front = the 16 ANDs of AND level < 4 (9 stage-1 + 3 + 4 inversion). Y-form levels (ylev.py; as
  T4's ylevels.py): 134 front: alpha 12, 92, 176 at gate level 8, eight at 9, four at 10; NIST 139
  front: two at 8; T4's 48@11 front (also 16 ANDs): 12, 81, 92, 176 at 8, eight at 9, three at 10.
- GD 12 with a rank-1 bottom means: per output k, sum over its products of 2^(1+lev(alpha_j)-12) <= 1
  (Kraft, XOR tree over products; the AES constant is free via XNOR).
- [C] Exact symmetries (orbit.py, checked on 256 inputs): x -> b x (b in GF(256)*), u-scaling by
  a in GF(16)*, Frobenius; 30600 images per decomposition.
- orbsearch.py D=12, fronts 134 / 139 / 48@11 x 14 base bottoms (all AD4 A34-39 rank-1 bottoms
  in NIST + best-1400) x 30600 images: no feasible image; best has 4-6 outputs over budget, total
  Kraft >= 10.1 (budget 8 = 1 per output) [C for these images].
- fwalk.py (flip-graph walk, Kauers-Moosbauer flips, rank 18 kept, merges reported) on the 48 front:
  best total Kraft 10.0, excess 2.25 in 60 s; no rank drop seen [H].
- Counting (48 front levels): the four level-8 alphas form a basis; each u-direction contraction has
  rank 8, so the products must cover each basis coordinate >= 8 times; with 18 products this forces
  >= 7 products of weight >= 1/4; total Kraft = sum_j |c_j| W_j <= 8 then needs about 2 outputs
  per product on average (known decompositions: 3.1) [H, necessary conditions only].
- bsat.py (full Brent equations with Kraft cardinality, CaDiCaL): no answer in 9 min even for D 13.
  bsat2.py (alpha profile fixed): no answer in 2 min. Both are XOR-heavy for CDCL.
- bsat3.py: restricted model "an output uses at most one product per alpha class": linear XOR
  equations per output + Kraft + count of distinct (alpha, m) <= P. Running (see STATUS).

## 3. T06 gate count at GD 13 by bottom resynthesis (resyn.py, build.py)

build.py: front (kept, gates reused via T4's depthsynth parent mode) + any rank-1 decomposition
-> skeleton -> Huffman trees (meets the skeleton bound). Rebuilding 134 from its own decomposition:
G 193 without parent reuse, 134 with it (sanity). orbsearch D=13 on the 134 front: 5-13 feasible
images per base bottom; resyn.py builds them all (running).

## 4. T02

- [C] all A28 AD4 skeletons in the archive: bound >= 14 (section 1). The A28 bottom (13 ANDs) is not
  bilinear in model M (botanat.py), so section 2 does not apply.
- fdrive mix (gate/osc/trb) from 28/4/175/14, cap GD14 A28 AD4, seed 1, 2 h: running; osc relaxed
  stages reach 161-164 at GD15 but repair to 14 costs back to >= 175.

## 5. Results and further findings (16:45 UTC)

- **T02 strict: 28/4/174/14** (bar 175, NIST 176). fdrive mix seed 1 from best-1400 28/4/175/14
  (caps GD14 AD4 A28), stage 17, operator trb-bottom (timing-driven rebuild of the bottom linear
  region, then kernel), t = 2437 s. aes_check OK, new Pareto point.
  found/t02-a28-ad4-g174-gd14-t02mix1-s17.circ.txt (+ .json).
- [C] T02 stage 1 is rigid: in the 175 skeleton the stage-1 space Q = span(1, x, 9 products) holds
  exactly 9 classes of rank-1 products mod affine (27 products L*R, 3 per class); 7 classes have a
  member at gate level 3, two classes (operand pairs of 3-6 inputs) are at level >= 4 in every
  representation (cover28.py). The forms above stage 1 use stage 1 beyond N (outputs y0, y2-y4,
  y6, y7: swap.py), so no other cover is possible; GD 13 needs other middle/bottom AND functions.
- T06 depth, restricted model "one product per alpha class per output" (cp3.py, OR-tools CP-SAT,
  table constraints, 1 worker, 20 min) on the 48@11 front at D = 12: best 26 bottom products
  (A = 42), lower bound not proved. Built (build.py, depthsynth with parent): 42/4/229/12
  (runs/build/cp3-a42.circ.txt, unpolished; T4 has 42/4/230/12). Far from the 18 needed for A34 [H].
  bsat3.py (same model as CNF, CaDiCaL) gave no answer in 18 min (the pysat interrupt timer does not stop cd19;
  use an outer timeout).
- Caveat on the restricted model: BP-like decompositions (two GF(16) multiplications sharing the
  alpha set, like the 134 bottom: 9 classes x 2 products) have outputs that use both products of a
  class, so their product count in this model is higher than their true AND count. The 26 is an
  upper bound only in this model; it does not bound general rank-1 bottoms.

## 6. Skeleton pull and conjugates (17:00-18:00 UTC)

- sp.py (skeleton pull: kernel at cap+1, check the skeleton bound of the relaxed circuit, rebuild
  with P2 dsynth.py = T4 depthsynth whose parent ANDs/signals are reused only if fast enough,
  kernel at cap). T02 from the 174: relaxed states 160-169 at GD15 all have skeleton bound 14;
  rebuilt 283-298 at GD14, kernel (100k iterations) 181-194: worse than plain trb [H, 9 rounds].
  T06 from the 134: every relaxed state (126-129 at GD14) has skeleton bound 14, so no rebuild
  to 13 is possible from them [H, 26 rounds].
- GF(2^8) conjugates (coordinator tip from P3; copies of P3 conj.py/bottom.py/mkconj.py as
  conj_p3.py, bottom.py, mkconj_p3.py): conjskel.py computes the skeleton bound of all 2040
  conjugates. [C, these 2040 circuits] T02 174: bound 14 for 125 conjugates, 15 for 1438, 16 for
  477 (none below 14). T06 134: bound 13 only for the identity, 14 for 3, 15-16 for the rest. So
  conjugation cannot lower depth here; for T06 it cannot even keep GD 13, for T02 the 125
  bound-14 conjugates are new starts for G at GD14. rebuild.py (depth-optimal rebuild on its own
  skeleton) gives 302-328 at GD14 for six of them; mkconj (BP top) gives 191-202 at GD19-27.
  Pipelines queued (runs/q13e.sh).

## 7. Compliance (COMPLIANCE-1820)

- Kernel bfx-593fa798f5 (used until 18:15) has no repair_keep option. From 18:15 every new job uses
  strategies/P2/fdrive_p2.py (copy of P1 fdrive_p1.py: repair_keep 1, best only inside A/AD caps)
  with kernel bfx-94a75e2c18, via polish2.sh / conjpipe2.sh; save.py writes path_certified.
- The 174@14 (both found/ copies): path_certified true. Lineage: start 175@14 inside all caps was
  the job best until stage 17; stage 17 rebuilt the bottom linear region of that best (trb, linear
  only, result 175@14 inside caps) and ran one kernel under caps GD14 AD4 A28 from that feasible
  state; from a feasible start the kernel never leaves the caps.
- Stopped t06mix13 (mix mode with osc repairs, old kernel) at 18:15; nothing from it was used.
  t02trb5 (trb mode: every kernel call starts from a feasible state) continues on the old kernel.

## 8. Later runs (18:15-21:05 UTC)

- T02 polishing from the 174 (fdrive trb seeds 5 and 31, 45-60 min each; mix 32 running): no
  G < 174 [H].
- T02 conjugate pipelines (conjpipe2.sh, repair_keep 1): lam 81 k 2 (mkconj start 195@19): 166@17 at
  cap 17, 170@15 at cap 15, then the repair to cap 14 failed (stays 177-183 at GD15). lam 87 k 1
  (rebuild.py start 302@14): 192 -> 189@14 in 25 min. The conjugate landscape is worse than the
  original at GD14 [H, 2 conjugates].
- T06 bottom resynthesis (resyn.py starts = rank-1 decompositions from orbsearch D=13 on the 134
  front, built with depthsynth + parent reuse; fdrive_p2 trb at caps GD13 AD4 A34, 25-30 min):
  144 -> 136, 151 -> 136, 158 -> 137, 159 -> 135, 161 -> 135 (2-10 min each, then flat). These are
  distinct new 34/4/135-137/13 circuits (better than NIST 139/13, not better than the 134 bar),
  saved in found/ (path_certified true). Different decompositions give different basins, so a
  broad sweep is the overnight proposal (QUEUE.md P2-T06-resyn) [H].
- P7 bottom annealer (coordinator tip): copied to bopt.py/bbuild.py/bsel.py/s1lib.py/botclass.py.
  P2 changes: --calib starts from the own bottom, and --exact uses the exact front Y-form levels.
  In P7's sum-of-base level model the 134's own bottom violates Kraft at GD13 for 7 of 8 outputs;
  with exact levels all pass (model cost 65 = 18 products + 6 Y-sums + 10 x-forms + 31 output XORs).
  On CPU 15 (lent 21:35-23:45): boptjob.sh seeds 5 (6000 iterations) and 6 (3000): the annealing
  never improved on the own bottom (cost 65; a local optimum of this model [H]). bbuild gives
  34/4/144/14 (its Y-sums are slower than the front's own Y-forms, so GD 14). A gate polish at
  cap 13 could not repair it to GD 13 (best 134@14 and 135@14, saved because they beat their start,
  not relevant to T06).
- Resyn starts c0008 and c0018 (168, 167) -> 141@13. Ranking: the better the built G of a start,
  the better its basin (144-161 -> 135-137; 167-168 -> 141) [H, 9 starts].
- 22:40-23:40: final sweeps under `timeout 3600`: overnight_t06.sh on the 134 front (more resyn
  candidates, 15 min trb each) and on the NIST 139 front; overnight_t02.sh seeds 201-202.
