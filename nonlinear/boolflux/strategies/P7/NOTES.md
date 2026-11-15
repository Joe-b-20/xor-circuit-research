# P7: T09 (A45/AD4/G141/GD12) and T10 (A59/AD4/G159/GD10)

Agent P7, 2026-11-15 from 15:23 UTC, CPUs 18-19. Code here, data in
`~/xs-campaigns/2026-11-15-targets/P7/` (found/ with JSON sidecars, runs/ with logs and plans).
Labels: [C] = exhaustive or proved within the stated case, [H] = heuristic / empirical.

## 0. Baselines (kernel only) — failed
- T10: fdrive mix (gate/osc/trb) from NIST 59/4/159/10, caps GD10 AD4 A59, 13 min: no change
  (osc relaxed stages reach 154-157 at GD11, A57-59; never repaired below 159 at GD10).
  runs/t10-mix1. The hub had already polished this cell (36 jobs at cap.gd 10, 90 s each, objective a-first).
- T09: fdrive mix from our 43/4/141/12, 10 min: no change (runs/t09-mix1, stopped).
- T09: polish of T4's 44/4/254/11 with the GD12 slack (cap GD12, A45): 254 -> 194 in 10 min (A45),
  far from 141 (runs/t09-a44g1, stopped). T4-style rank-2 junk-sharing builds are too XOR-heavy.

## 1. Anatomy (s1lib.py, T4/anat.py, F/depth.py, botclass.py)
- NIST 59@10: 17 level-1 products (four N-coordinate groups of 4-5 products, all products at gate
  level <= 2, each N-coordinate at gate level 4), inversion 6 A2 (GL5) + 3 A3 (GL6) + 1 AND at GL7,
  four Y-forms at GL7, 32 rank-1 bottom products at GL8, outputs = XOR of exactly 4 products (GL10).
  Regions: L0 51, L1 17, L2 5, L3 3, L4 24. Front (cone of the 4 Y-forms) 77 gates, bottom 82.
- NIST 45@12: front 17 ANDs (65 gates), 4 base Y-forms at GL8 + 5 Y-sums at GL9; bottom = 28
  RANK-1 products (13 at GL9, 15 at GL10), 5 of them shared between outputs (y0, y4 use 5 products).
- Our 43@12: front 16 ANDs (63 gates), base Y levels 8,8,8,9; bottom 27.  48@11: front 16 ANDs (67 gates).

## 2. The bottom as a tensor problem (bsel.py, bopt.py)
Output j = c_j + sum_i Y_i u_ij(x) (Y_i base Y-forms, u_ij linear): a 4x8 GF(2) matrix B_j of rank 4.
A rank-1 product (alpha, w) = AND(Y_alpha, w), Y_alpha a sum of base Y-forms.  Choosing products and
per-output subsets with sum B_j is a simultaneous rank-1 decomposition; depth enters as Kraft per
output (base Y at Lb -> product Lb+1; 2-sums Lb+2; 3/4-sums Lb+3).
- [C] Minimal 4-product decompositions of different outputs can share products only for the
  GF(16)-proportional pair (y5, y6): the x-forms of output j lie in the GF(16)-line of R_j, two
  distinct lines meet in 0 (bsel.py found the same: 30 products minimum with 4-product
  decompositions on the 48 front at GD12).  NIST 45@12 shares more because some outputs use 5
  products (over-complete decompositions).
- bopt.py: simulated annealing over per-output decompositions (random bases of the remainder
  after subtracting 1-3 products already used by other outputs), exact Kraft per output, cost =
  products + Y-sum XORs + new x-forms + output XORs - shared pairs.  Calibration: NIST 45@12's own
  bottom scores 80 (true bottom 76 gates); bopt finds 74-77 with 24-26 products.
- bbuild.py: front cone + Y-sums + x-forms (Boyar-Peralta distance heuristic, polarity aware) +
  products + depth-aware shared pairs + Huffman output trees; verified on 256 inputs.

## 3. T09 results (all verified with aes_check, files in found/ with sidecars, all path_certified)
| A | AD | G | GD | how | class |
|---:|---:|---:|---:|---|---|
| 41 | 4 | **137** | 12 | loop LC seed 7002 (NIST 45 front, bopt --pw 3) build 41/138 + 300 s gate polish cap A41 (repair_keep 1); also reached from our 137 front (LA s1011) | strict, best G |
| 39 | 4 | **138** | 12 | loop LC seed 7001 (NIST 45 front, bopt pw 0, 22 products), build, no kernel | strict, fewest ANDs |
| 42 | 4 | 137 | 12 | bopt seed 12 (n45q-s12), build 143 (v1) / 138 (v3) + gate polish | strict (dominated) |
| 39 | 4 | 139 | 12 | 48@11 front (A48 donor, front only) + bopt --pw 4 (23 products) build 39/141 + gate polish cap A39 | strict (dominated) |
| 40 | 4 | 139 | 12 | bopt seed 60 (t45-s60) build | strict (dominated) |
Pareto in (A, G) at GD12 within A<=45: 39/138, 41/137.
- Builder versions: v1 reused every old top-layer gate as "free" (hidden cost), v2 added a
  Boyar-Peralta x-form synthesis and depth-aware shared pairs, v3 restricted reuse to the front cone
  and made x-form availability polarity-aware.  v3 builds land within 0-2 gates of front + model cost.
- Polish (fdrive gate, caps GD12 AD4 A45) gains 0-6 gates on builds and stalls at 137-140 [H].
- bopt --refine (exhaustive single-output re-decomposition against all <=2-subsets of other
  outputs' products) found nothing after SA: SA end states are single-output optimal.
- With 4-product decompositions only (bsel.py) the 48 front needs 30 products (A46): illegal for T09.
- amax 39 (bottom <= 22 on the 17-AND front): SA did not get below 23 products [H].
- 43@12 front (base Y levels 8,8,8,9): model costs 80+, builds 144-148: worse.
- 48@11 front: model 72, build 143 (v3), polish 140.

## 4. T10 (GD10): why G is pinned in the 59@10 architecture
- [C] Stage 1: for each of the four N-coordinates, all sums of products of <= 2-variable affine
  operands that are Kraft-feasible at gate level 4 (4 GL2 products, or 3 GL2 + <= 2 GL1 monomials, or
  2 GL2 + <= 4 GL1), with operand constants solved exactly: 33 / 1 / 2 / 3 decompositions
  (s1pol.py).  All 198 combinations built into the circuit (rgscan.py): best G 159 (two
  combinations equal the reference), none lower.  No two coordinates can share a product with these
  decompositions.  So stage 1 cannot be made cheaper in this model.
- [C] Top layer: all 51 L0 gates are distinct (form, polarity) targets (each needs >= 1 gate).
- [C] Bottom at GD10 with Y-forms at GL7: every output needs 4 products at GL8 (Kraft 4 x 1/4), so
  only the 4 base Y-forms can be used, the decomposition is unique, and 32 products + 24 output XORs
  are forced.  Over all 840 Y-bases the new x-forms the bottom needs range 25-32; the circuit's own
  basis needs 26 (xcount.py).  So a different inversion could save at most 1 x-form gate there.
- Remaining freedom: the inversion (22 gates: 10 AND + 2 twins + 2 pair sums + 8 XOR).  Kernel on the
  4-input sub-problem (invsub.py, NOT depth weight 0): no move from 22.  SAT exact synthesis
  (invsat.py): in progress.
- [C] Reachable Y-forms (yreach.py): of the 15 Y-forms only the 4 base forms are available at GL7 as
  an XOR (<= 5 terms, Kraft at 7) of the inversion's existing GL4-6 signals, so per-output bases or
  y5/y6 product sharing cannot be had without new inversion gates.
- Inversion as a 4-input problem: kernel (invsub.py) no move from 22 gates; SAT exact synthesis
  (invsat.py generic layered, invsat2.py layer 1 as candidate subset): neither found even the known
  22-gate solution within 10 / 15 min (runs/inv/): too slow as encoded [failed experiment].
- Conjugates (coordinator tip; conj_circuit copied from strategies/P3/conj.py into t10conj.py):
  screen of all 2040 (lam, k) (runs/conj/screen59.jsonl): 4-product decompositions (<= 2-variable
  operands) exist for 3 of the 4 N-coordinates only in 34 conjugates, all with lam in the norm-1
  group and k in {0, 4}; these fix N, hence give the same stage 1, the same Y-forms and the same
  bottom (identical cost) [C for the 4-product shape].  782 conjugates have no decomposable
  coordinate, 918 one, 306 two.  Full-shape check (3+2, 2+4 shapes) of representatives of the
  two-coordinate classes (9 distinct coordinate sets, s1pol all shapes): none has all four
  coordinates decomposable (runs/conj/job2.log) [C for those classes].  One-coordinate classes
  (27 distinct coordinate sets): none has all four (best: three, lam 10 k 3) (runs/conj/job3.log) [C].  Zero-coordinate classes (23 distinct coordinate sets): at most one
  coordinate decomposes (runs/conj/job4.log).  So [C, model: every N-coordinate of the conjugate is a
  Kraft-feasible GL4 sum of products of <= 2-variable affine operands (shapes 4, 3 + <= 2 monomials,
  2 + <= 4 monomials), the 59's inversion and N-coordinate system kept]: only the 34 N-fixing
  conjugates (identical circuits) admit such a stage 1; conjugation gives T10 nothing new.
  Simpler reason: N(lam x^(2^k)) = N(lam) N(x)^(2^k), so the span of the four N-coordinates is the same
  4-dim space of quadratic functions for every conjugate; decomposability of a function of x does not
  depend on the conjugate.  span15.py (quadratic condition only, an upper bound): of the 15 non-zero
  combinations only 1, 2, 4 (4-product shape) and 3, 8, 14 (3 + <= 2 monomials; 3 also 2 + <= 4) can be
  such GL4 sums.  So other coordinate systems with all four at GL4 exist ({1,2,4,8} is the 59's; e.g.
  {1,3,4,8}, {1,2,4,14}), but using them needs a redesigned inversion, and the 59 already uses A = 59 =
  the cap, so any extra coordinate products must be paid by inversion ANDs [open lever, not built].
- T09 conjugates (P3 mkconj.py, read-only use) of 42/137 and 40/139: GD 22-25 starts; fdrive gate
  cap 14 could not repair 25 -> 14 in 240 s (runs/cj-188-0-*); stopped [failed: GD12 too tight].
- GD9 [H, partly C]: with Y at GL7 at best (N-coordinates have rank-8 quadratic parts, so N needs
  >= 4 products per coordinate -> GL >= 4; Y is cubic in N and not a single product -> GL >= N+3),
  bottom products are at GL >= 8 and a rank-4 output needs 4 of them: GD >= 10 in this architecture.

## 5. Safety of the retained states
All fdrive runs used --cap-a/--cap-ad; every logged stage state of the mix/osc runs was checked for
A > cap or AD > 4 (none, runs/*/log.jsonl), and every recorded circuit is cap-checked by p7job.record
before it enters found/.
- 18:20 COMPLIANCE-1820: all found/ sidecars got path_certified (certify.py): every kernel result in
  found/ came from fdrive gate mode started inside all caps (GD12, AD4, cap A) -> true; builds have no
  kernel -> true.  From 18:20 every kernel call runs with repair_keep 1: strategies/P7/fdrive_p7.py (copy of
  P1's fdrive_p1.py) with kernel bfx-94a75e2c18 (copied to P7/bin, sha256 e4f373f7...; the hub kernel
  bfx-593fa798f5 does not know the key).  Sidecars with the A48 donor (hub 48@11 front) carry
  donor_outside_limits + donor_note (donor.py): bbuild holds only the donor as read and its one output.
- bopt --refine2 (pairwise joint re-decomposition, top-40 candidates per output, single shared
  product subsets): plan 73 -> 72 on LC-s7002, build 140, polish 137 (no new point).  bbuild --tries
  (randomised BP / pair tie-breaks): no gain.  Long SA (150k it, T0 1.5-3): worse than 30k-it seeds.
- T09 GD11 (equal-priority objective) [C in the tower model]: with base Y-forms at GL8 every GD11
  output needs 4 base-Y products at GL9 -> 32 products (A >= 48); with Y at GL7 (59@10 front, 27 ANDs)
  bopt's best bottom has 23-24 products (A 50-51) [H].  T4's rank-2 junk-sharing circuits (A42-47 at
  GD11, G >= 186) remain the only A<=45 GD11 points; no tradeoff (G <= 149) found.
