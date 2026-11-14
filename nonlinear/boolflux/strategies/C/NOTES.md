# Track C: AES S-box with fewer than 28 AND gates -- notes

Evidence tags: **[P]** proved (argument written here), **[C]** computed (exhaustive or exact SAT,
solver named), **[V]** verified on the 256 points by a script, **[H]** heuristic / observation.

Notation. F = GF(2^8) (poly 0x11B), K = GF(16) = {y : y^16 = y} in F, Q = GF(4) = {0,1,w,w^2},
w = g^85 with g = 3 a generator of F*. x the input byte; N = x^17 in K (norm F -> K),
n = N^-1 (0 -> 0). Truth tables: 256-bit ints, wire U_i = bit 7-i of x (core.py).
S(x) = Aff(x^-1), so MC(S) = MC(x -> x^-1); targets below are the 8 bits of x^-1.

## 0. One-layer cover problem (every stage is an instance)

If E is the span of what is available (constants, x, earlier ANDs) and the next layer computes
products l_j m_j with l_j, m_j in E, the layer succeeds iff each target t has
t + sum_j c_j l_j m_j in E. When operands come from O with O + <1> in E,
(l, m) -> l m mod E is GF(2)-bilinear and alternating (l*l = l in E), so a product is the
image of the rank-2 tensor l ^ m under a linear Phi : Lambda^2(O) -> F_2^256/E **[P]**.
Constants in operands are irrelevant; a product depends only on <l, m>. `qmc.py` is the exact
SAT model of this (operand bits, wedge bits, output combination c).

## 1. Structure of the published A28 circuits **[V]** (`structure.py`, `show_stage3.py`)

* a28-ad5-g124: ANDs per AND level 10 | 1 | 2 | 2 | 13.
  a1..a10 products of affine forms in x; N's 4 coordinates are in span(1, x, a1..a10) and no
  9-subset suffices. a11..a15: all operands are functions of N (GF(16) inversion, depth 3).
  a16..a28: operands in span(1, x, N, n) (not in span(1, x, u) for u = N + n alone).
* a28-ad4-g131-gd31: 9 | 2 | 4 | 13; all 9 level-1 products needed for N; 6 inversion ANDs
  (operands functions of N); 13 last-layer products with operands in span(1, x, N, n).
* x^33's coordinates are not in span(1, x, level-1 products) in either file.

## 2. Every last-layer AND is a GF(4) norm **[V]** (`spectral.py`)

Writing each operand as Tr(A x) + g(N): for all 13 last-layer ANDs of the AD5 file,
A'/A = w^{+-1}, and g = Tr_K(s v), g' = Tr_K(w^{-+1} s v) with v = n + gamma N for ONE fixed
gamma = g^17 (the header's u up to scaling of N). Hence each AND equals
N_{Q/GF2}(Lambda(x) + G(v)) = Lambda^3 + G^3 + Tr_{Q/2}(Lambda G^2), Lambda Q-linear in x, G Q-linear
in v. Indexing members by (Y, zeta) = (A s, s^3) in F* x mu_5 (the three cube roots of zeta give
the same product **[P]**), the AD5 file uses three classes zeta = g^153, g^102, g^51 with
5, 3, 5 members. (Same GF(4) pattern in the AD4 file: no x^5- or N-class in any x-wedge.)

## 3. Grading and fibre spectra **[P]**

f = sum_e p_e x^e; grade = e mod 17. Squaring multiplies e by 2 (order 8 mod 17), so
V0 (functions of N, dim 16), V_QR (QR = {1,2,4,8,9,13,15,16}, dim 120), V_NQR (dim 120) are
closed; products add grades.
* x-linear forms: QR. Quadratic forms Tr(c x^d): d = 3, 5 classes NQR, d = 9 class QR, d = 17 (N)
  grade 0. x^-1 = x^254 has grade 16: QR.
* V_QR in fibre coordinates: f(x) = Tr(phi(N(x)) x), phi : K* -> F, phi(v) = sum_{e in Z/15} f_e v^e,
  f_e = sum_{x in F*} f(x) x^-(1+17e). Target Tr(b x^-1): only f_14 (= b^16). Tr(c x^9): only
  f_1 (x^9 = x N on fibres).
* GF(4)-norm member (Y, zeta) **[P, V]**: QR spectrum f_14 = Y, f_11 = zeta Y, f_1 = gamma Y + A^18,
  f_4 = gamma^4 zeta Y, all other f_e = 0. Pure-x part ("junk") Tr(Ax)Tr(wAx) has quadratic
  components (C1, C2, C3, C4) = (A^3, 0, A^9, 0) in the x^3, x^5, x^9, N classes
  (C_d = A B^{2^d} + A^{2^d} B with B = wA). Grade-0 part Tr_K(zeta v^3) depends only on zeta.

## 4. Stage-1 (norm) bound

Least k with N's coordinates in span(1, x, k products of x-linear forms) = least number of
rank-2 alternating forms on F_2^8 whose span contains the 4-dim space V_N (all 15 nonzero forms in
V_N have rank 8; V_N = form space of GF(16) multiplication).
* k = 9 SAT **[C]** (`stage1.py`, CaDiCaL 1.5.3, 33 s): stage 1 <= 9.
* **Retracted:** the earlier "k = 7 UNSAT" used c = [I_4 | C'] for a FIXED basis of V_N. That is
  unsound (row reduction changes the target basis), so the result is void. Same flaw in the first
  `cover.py`/`wsat.py`; all encodings now leave c free.
* Sound symmetry breaking now used: the group x -> a x^(2^i) (a in F*, order 2040) maps V_N to
  itself; its orbits on the 10795 rank-2 forms (2-dim spaces of linear forms) have sizes
  2040, 2040, 1020, 510, 2040, 2040, 1020, 85 (8 orbits) **[C]**. One product is fixed to each
  orbit representative in turn, lex order on the rest, c free. Results: see STATUS / section 7.
* **k = 7 impossible** **[C, exhaustive, solver-free]** (`stage1_enum.py 7`): with P1 one of the 8
  orbit representatives, U = V_N + P1 (d = 5) and the other 6 forms must have images in a <= 2-dim
  subspace of Lambda^2/U (cover lemma, section 7); for every representative: 10605 image points,
  buckets of size <= 2, 1 form inside U, 12096 candidate planes, none spans U. The method finds the
  known 9-cover of the AD4 file when given 3 of its products (validation). So **stage 1 >= 8**.
* **k = 8 impossible** **[C, exhaustive, solver-free]** (`stage1_enum.py 8`): P1 = the product of
  least orbit index, mapped to its representative (8 cases); P2 = any other product (all 10795
  forms of orbit index >= P1's; P2 is never in V_N + P1 since V_N has no forms of rank < 8);
  U = V_N + P1 + P2 (d = 6), the other 6 forms have images in a <= 2-dim subspace of Lambda^2/U;
  every (P1, P2) tested exactly with the cover lemma: no cover. Run time 6780 s on one CPU.
* Hence **the norm N = x^17 (equivalently GF(16) multiplication, mod linear terms) needs exactly
  9 ANDs in one AND level** [C]: the level-1 quadratic complexity equals the bilinear rank 9
  (Barbulescu et al.). Deeper (multi-level) computations of N are not covered by this.

## 5. Last layer in the GF(4)-norm family

* Output-pairing ("n-block", e = 14 and 11) alone: 10 members suffice **[P, V]**
  (5 classes x 2 members, Y_zeta = zeta^-1 Z, Z = <z, z'>, z, z' K-independent; verified in
  `fam_check.py`). Within the family >= 10 **[P]** (achievable first coordinates have dim
  <= k - dim Z, dim Z >= 2 since at most 5 classes). So the binding constraints are the junk.
* `nblock.py` (first version) modelled the n-block target as {y -> b y}; its k = 10 UNSAT
  contradicts the verified 10-construction, so that model was wrong; result discarded.
* Generic SAT of the last layer (operands in span(x, N, n), 16 dims, q = 80) is not viable
  **[C]**: 13 free products not solved in 10 min; fixing 10 of the A28 products: 2 s; fixing 8:
  > 170 s.

## 6. Accounting: why all known designs give 28

Let l = level-1 ANDs (span W contains V_N), i = inversion ANDs, k = last-layer members,
J = dim of the x-quadratic junk the outputs need from W. A form with C2 = 0 and rank 2 is a GF(4)
norm, which has C4 = 0; so W cannot lie in {C2 = 0}, i.e. rho2 := rank(C2 on W) >= 1, and
dim(W & {C2 = 0, C4 = 0}) <= l - 4 - rho2 **[P]**. Hence l >= 4 + J + rho2 >= 5 + J and
total = l + i + k >= 5 + J + i + k.
* Karatsuba over GF(4) (two GF(16)/GF(4) products sharing n: 6 Q-products x 2 norm-ANDs):
  k = 12, J = 6 -> 11 + 5 + 12 = 28 **[P]**.
* A28: k = 13, J <= 5 (l = 10) -> 28.
* 10-member design: J = 8 (the junk map (eps1, eps2) -> F^2 is injective unless z1/z2 in K,
  which kills the n-block) **[P]** -> 13 + 5 + 10 = 28.
All have k + J = 18. With i = 5, a 27 in this family needs k + J <= 17 (and rho2 = 1, and the
grade-0 residue absorbed by the inversion's span). Conjecture [H]: k + J >= 18 in the family.

## 7. Further results (after restart)

* **MC(GF(16) inversion) = 5** **[C]** (`mc_small.py`, Courtois-Hulme-Mourouzis encoding without
  symmetry breaking, CaDiCaL): k = 3 UNSAT (1 s), k = 4 UNSAT (76 s), k = 5 SAT (1.6 s).
  So the middle stage cannot drop to 4 ANDs as a function of N alone.
* The A28 (AD5) last-layer set S (13 members) has, with the 5 inversion ANDs fixed and the
  grade-0 residue required to vanish: no kernel combination (combos are unique) and junk
  dimension **J = 3** **[C]** (`kj_search.py`, `wsat.py`). So the accounting bound
  l >= 4 + J + rho2 is not tight; the binding constraint is the level-1 cover itself.
* **Cover lemma [P]:** if a d-dim space U lies in the span of l rank-2 forms, their images in
  Lambda^2/U span <= l - d dims (dim span P = dim(span P mod U) + dim(U & span P)). Hence for
  l - d <= 2 an exhaustive test: bucket all 10795 rank-2 forms by image mod U and enumerate the
  <= 2-dim image spaces (`cover_enum.py`).
* **No 9-product stage 1 fits the A28 last layer** **[C]**: U = V_N + junk(S) has d = 7; images of
  rank-2 forms mod U: 10745 distinct nonzero points, buckets of size <= 3, no form inside U; no
  plane carries 9 forms spanning U (exhaustive). So 9 + 5 + 13 = 27 is impossible with exactly the
  published last layer and inversion (this is why the file needs 10 level-1 ANDs).
* Annealing over subsets of the 1275 GF(4)-norm members (`kj_search.py`, and `kj_struct.py` with z
  restricted to a subspace Z) does not find feasible low-cost sets from random starts (best cost
  20-23 vs 16 for A28): the feasible region is needle-like; replaced by exact joint SAT
  (`joint.py`: l level-1 products + k members + fixed inversion, c free, lex per group;
  validated: with all A28 operands fixed it is SAT in 0.1 s).

## 9. Exhaustive last-layer search over a fixed E (`zdfs.py`)

For fixed E (span of everything before the last layer) and targets T: a k-set S of members works
iff T in span(S) + E. Let pi = projection mod (E + T); then rank pi(S) <= k - 8. f_11 (the
z-coordinate) vanishes on E and on T [V: level-1 products have QR support {0,1}, x has {0}], so
pi(S) -> Z = span{z_m} is onto. Case rank pi(S) = dim Z = r: pi is a linear function of z on S.
For every r-dim Z (200787 for r = 4) a DFS over the 15 points of Z picks members (z, zeta) whose
pi values extend linearly; every assignment with >= k members is checked exactly. Members at one
z with equal pi (multiplicity <= 2 over all z [C]) are all taken. Validation: the A28 set has
rank pi = 5 = dim Z with 11 distinct points (two points carry 2 members) [C].
Run: E = AD5 (10 level-1 + 5 inversion), gamma = g^17, r = 4, k = 12 (=> 10 + 5 + 12 = 27).

Validation [C]: `zdfs.py --r 5 --k 13` on the A28 subspace Z (basis 116,250,207,28,145) over the
AD5 E finds 69 leaves with >= 13 members; maximal pi-consistent families of sizes 19, 13, 13
(939 s for this single Z, so r = 5 cannot be run over all 97155 Z).

**The A28 neighbourhood cannot give 9 + 5 + 13** **[C]** (`cand13.py`): every 13-subset of these
families that is a valid last layer over the AD5 E (2321 sets) was re-expressed over E_min: all
have unique output combinations, junk dimension 3 (682 sets, dim U = 7) or 4 (1639 sets,
dim U = 8), and for none does a 9-product stage 1 exist (cover lemma, exact).

Further exhaustive runs (results in STATUS): k = 12 with dim Z = rank = 4 over the AD5 E
(gamma = g^17), over the AD4 E (gamma = g^34, the AD4 file's value), over AD4 level-1 + AD5
inversion (gammas g^17, g^34, none) [a hit there would be 26]; and k = 12 with dim Z = 3,
rank 4 (`zdfs3.py`, complete since 12 members on 7 points force a doubled point).

**Results of these runs** [C, exhaustive within the stated case; GF(4)-norm members with the
given gamma; every assignment with >= 12 members checked exactly against T + E]:
| E (level-1 + inversion) | gamma | case | Z tested | hits | total if hit |
|---|---|---|---|---|---|
| AD5 (10 + 5) | g^17 | dim Z = rank = 4 | 200787 | 0 (10 leaves, none covers T) | 27 |
| AD4 (9 + 6) | g^34 | dim Z = rank = 4 | 200787 | 0 | 27 |
| AD4 L + AD5 inv (9 + 5) | g^17 | dim Z = rank = 4 | 200787 | 0 | 26 |
| AD5, AD4, AD4L+AD5inv | g^17 / g^34 | dim Z = 3, rank <= 4 | 97155 each | 0 (no Z passes the count prune) | 27 / 26 |
Not covered: dim Z = 2 with 12 members (needs >= 4 members per point), other gamma for AD5 / AD4,
members with independent N-part (wfree), non-GF(4) members, other stage-1 covers W.

Builder (`build27.py`): from (level-1 pairs, members) it builds a circuit by exact linear algebra
and XOR chains; validated by rebuilding the A28 structure: aes_check OK, A = 28, G = 552.

## 8. Papers

* Stoffelen 2016: MC proved for several 4x4 / 5x5 S-boxes (Table 1; max 5 among 4x4: Minalpher).
  GF(16) inversion is not treated, hence the SAT check above.
* Barbulescu et al. 2012 (Table 3): bilinear rank of GF(2^4) multiplication is 9 (2025 optimal
  formulae). Our stage-1 question is the level-1 *quadratic* complexity of the same 4 forms, which
  can a priori be lower (between half and all of the bilinear rank).
* Mirwald-Schnorr 1992: L = L1 for a single quadratic form and for pairs (one AND level suffices);
  for sets of forms, level-one complexity is sandwiched by tensor rank (Thm 5.2); no general
  nonlinear lower bounds. So our stage-1 bound (>= 8, k = 8 pending) is for level-one products only;
  a deeper stage 1 is not excluded by it.

See section 8 (filled in after reading Stoffelen 2016, Barbulescu et al. 2012, Mirwald-Schnorr
1992).
