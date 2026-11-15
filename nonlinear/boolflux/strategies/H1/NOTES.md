# H1 (structure analyst): how the known low-AND AES S-box circuits really work

Evidence labels: **[C]** computed exactly / exhaustive within the stated case (script named, on the
named files only), **[P]** proved here (argument given), **[H]** heuristic, observation or
recollection. Data: `~/xs-campaigns/2026-11-15-study/H1/`. Notation as in `strategies/C/NOTES.md`:
F = GF(2^8) (0x11B), K = GF(16) = {x^17}, w = g^85 (g = 3), N = x^17, n = N^-1 (0 -> 0),
V_N = span of N's 4 coordinates, V0 = functions of N (16-dim).

## 0. Method and tools (all in this directory, all run in < 1 s per file)

* `xag.py FILE [--json OUT]`: every AND as L*R, L, R affine over [1, x, earlier ANDs] (symbolic
  and as truth tables). Per AND: AND level, algebraic degree of product and operands, the
  cyclotomic-coset support of the univariate polynomial of operands and product (basis-free w.r.t.
  the AES field), membership of each operand in named spaces (X = aff(x), N, n, V0, X+N+n, X+V0,
  GF(4)-norm x^85, x^-1), fan-out (later operands / outputs), and a role:
  S1 = both operands affine in x, MID = both operands functions of N, LAST = both in
  span(1, x, N, n), LASTV0 = both in aff(x) + V0, OTHER = anything else (a stage-merging AND).
  Per AND level L: dim E_L, and how much of N, n, x^-1, outputs, x^85 lies in E_L.
* `decomp.py FILE...`: unique output decomposition y = sum c a + affine (the ANDs are linearly
  independent in every file, [C]); Jx = dim(V_N + S1-parts of outputs) - 4 (x-quadratic junk the
  outputs take from stage 1), U = V_N + that junk, J0 = N-function junk beyond span(1, N, n),
  each S1 product's uses, and each last-layer operand split as c + Tr(Ax) + Tr_K(tN) + Tr_K(s n)
  (pair type, ratio A'/A, gamma = t/s).
* `junk.py`: junk in coset coordinates (c3, c5, c9) of Tr(c3 x^3) + Tr(c5 x^5) + Tr(c9 x^9).
* `junkrank.py`: rank distribution of the alternating forms in U, min rank per junk class.
* `fibre.py`: operands as Tr(Ax) + g(N) with the full K-spectrum of g (for non-(N, n) operands).
* `keep.py PREFIX MEMBERS...`: keep-set table d(X) = dim(T+E+X) - dim(E+X) over all subsets.
* `lb_degree.py`: degree of all 255 output combinations.

Files analysed (63): all NIST A28 (14), A29 (4, umizame-derived), A30 (2, umizame-derived), A32
(14, Boyar-Peralta family incl. AD4/AD7 variants) from the pin 3d80774, and all 27 A28-A31 files of
`~/xs-campaigns/2026-11-14-hub/best/`. Per-file reports: `.../H1/xag/*.txt|json`,
`.../H1/decomp_all.{txt,json}`.

## 1. The universal skeleton [C, for each of the 63 files]

1. **Every circuit is strictly three-stage in the operand sense.** Every AND is S1, MID or LAST
   (LASTV0 in one file, see 1.7). No AND has operands mixing x-linear terms with MID products or
   with S1 products other than through N and n (one operand may be purely x-linear: BP's
   n|x products); there is no OTHER AND in any file. (Even umizame's "early" ANDs are exactly the 9 S1 products that also
   compute N: section 3.)
2. All ANDs are linearly independent: dim span(1, x, ANDs) = 9 + K.
3. N's 4 coordinates are in E_1 (stage 1 = 9 or 10 level-1 products; the least subset spanning
   V_N is all of them: 9 of 9, 10 of 10 (AD5)). n's coordinates appear only at the end of the
   middle. **No output dimension is in E_L for any level below the last**: rank of outputs in
   E_L is 0, 0, ..., 0, 8.
4. MID: 5 ANDs (AD5 / BP / umizame), 6 (AD4, depth-2 inversion), 7 (hub A30); all operands
   functions of N; P cap V0 = 10, 11, 12 resp. (n, N, constant and 1, 2, 3 extra N-functions).
   The GF(4) norm x^85 is never available except as a by-product in some 6-/7-AND middles
   (one coordinate; NIST A32 AD4, hub A29 AD4 g140/g148, A30 g139).
5. Degree profile: S1 products degree 2, MID degree 4 and 6, LAST degree 7 (8 in one file).
   Univariate coset supports: S1 {1,3,5,9,17}(+0); MID {17,51,85}, {17,119}, {17,51,85,119};
   LAST: BP {15,47,111,127}; umizame {0,3,9,47,51,127}; A28 {0,3,9,17,21,47,51,119,127}
   (127 = x^-1's class; 3, 9 = x-quadratic junk; 51 = N^3; 17/119/21 appear only when operands
   contain N, i.e. gamma != 0).
6. Last-layer operand anatomy (every operand is c + Tr(Ax) + Tr_K(tN) + Tr_K(sn)):

| family | files | l + mid + k | last-layer types | Jx (dim U) | J0 | gamma = t/s |
|---|---|---|---|---|---|---|
| Boyar-Peralta | NIST A32 AD5/AD7 (12) | 9+5+18 | 18 x  Tr(sn) * Tr(Ax)  (bilinear) | 0 (4) | 0 | - |
| BP + one 5-member row | NIST A32 AD4 (3), hub A31 (9) | 9+6+17, 9+5+17 | 12 bilinear + 3 n|x+n + 2 x+n|x+n, not GF(4)-norm (A'/A = g^145) | 2 (6) | 0 | - |
| umizame | NIST A29 (4), A30 (2) | 9+5+15, 9+6+15 | 15 GF(4)-norm members, operands x + n only | 2-3 (6-7) | 0 | 0 |
| A28 AD5 | NIST (3), hub (4) | 10+5+13 | 13 GF(4)-norm members, operands x + N + n | 3 (7) | 0 | one gamma per file (g^17, g^34, g^187) |
| A28 AD4 | NIST (11), hub (6) | 9+6+13 | 13 GF(4)-norm members | 2 (6) | 1 | g^34 or g^204 |
| hub A29/A30 | hub (6) | 10+6+13, 10+7+13 | AD5-type layer, extra middle AND(s) for depth 4 | 3 (7) | 0 | g^187 |

   GF(4)-norm member = AND whose operands have x-parts in ratio A'/A in {w, w^2} and n-parts in
   the inverse ratio (C/NOTES section 2): the product is N_{GF(4)/GF(2)}(Lambda(x) + G(v)),
   v = n + gamma N. **All 13-member layers have gamma != 0; all 15-member layers have gamma = 0.**
7. Deviations found: (a) hub `a29-ad4-g130` (from the hub archive) never computes N^-1 exactly:
   only 3 of n's 4 coordinates are in the circuit's span; 10 of its last operands are
   Tr(Ax) + Tr_K(sn + tN) + [N != 0] (fibre.py: K-spectrum has the v^15 term), i.e. the middle
   computes an "inverse" that is wrong at the single point 0 and the last layer repairs it; 11
   last products have degree 8. It still costs 29 (10+6+13). (b) BP family: the S1 products are
   never used by outputs (Jx = 0); all other families leak S1 products (and MID products) into the
   outputs additively. These are the only deviations; nothing in any file computes an output bit
   early, merges stages inside an AND, or uses another subfield chain.

**Answer to the user's question [C on these 63 files]:** none of the known circuits deviates from
"stage 1 -> GF(16) inverse -> last layer" except additively (junk). So the known record circuits
give NO evidence about what a non-three-stage 27 would look like; equally, nothing known rules it
out (section 4).

## 2. Span structure that decides the count

Totals are l + mid + k with l >= cover(U), U = V_N + x-quadratic junk, mid >= MC of
span(n, N-junk) [C: 5 if the N-junk is in one of G's 30 classes, else >= 6].

* [C] Quadratic space after level 1 = l (9 or 10); V_N inside it; junk used Jx = 0..3.
* [C] The S1 span always has (c3, c5, c9)-projection of rank l - 4 and **c5-rank exactly 2** in
  every file (`junk.py`); output junk of GF(4)-norm layers has c5 = 0 (as C/NOTES section 6
  predicts), the BP+1-row junk has c5 != 0. [H] If every 9-product level-1 cover of V_N has
  c5-rank >= 2, then a 9-product stage 1 can absorb at most 9 - 4 - 2 = 3 dims of norm-type
  junk (C's bound l >= 4 + J + rho2 with rho2 = 2).
* [C] **Why umizame's junk fits in 9 products and A28's does not** (`junkrank.py`): in umizame's
  U (dim 7) every one of the 7 junk classes mod V_N contains a rank-4 form (15 rank-4 forms in U);
  in A28-AD5's U (dim 7) three junk classes have minimum rank 6 (only 6 rank-4 forms); in A28-AD4's
  U (dim 6) one class has min rank 6. In the BP+1-row family the junk contains rank-2 forms (two S1
  products lie in U). [H] Min rank per junk class is a cheap proxy for 9-coverability: G's 1702
  evaluated 13-member walk layers (started from A28 layers, junk 3, exact cover test each) were all
  non-coverable [C per layer, H as a search; `~/xs-campaigns/2026-11-14-G/STATUS-auto.md`].
* [C] keep-sets (`keep.py`, k = 13): over umizame's own prefix (9 + 5), a 13-member layer can keep
  at most 9 of umizame's 15 members (|X| = 9 needs d = 4 new dims from 4 new members); min d by
  |X| = 10..15 is 4, 3, 2, 2, 1, 0. Over any of the prefixes umizame / A28-AD5 / A28-AD4 / BP,
  foreign layers (A28 members over umizame's prefix etc.) miss >= 3 output dims even when all
  kept (their junk is private to their own stage 1). Files: `.../H1/keep/*.txt`.
* [C] **Rows = zeta-classes.** Grouping the GF(4)-norm members by zeta = s^3 in mu_5 (s = n-part
  of the L operand): umizame (5,5,5) in 3 classes (= its 3 Karatsuba rows, 5 late ANDs each);
  A28 AD5 (5,3,5) (g124) or (5,4,4) (g150); A28 AD4 4 classes (3,4,4,2) / (4,4,3,2). [P] zeta
  determines the GF(4)-linear functional of n up to GF(4)* (5 such = the points of P^1(GF(4))),
  so a class is a "row" in the Karatsuba sense; Karatsuba uses 3 of the 5 points, AD4 uses 4.
  The A28 gain is a row with only 3 late members, and it occurs only together with gamma != 0.
* [C] **Track C's member model covers all of them, but its exhaustive cases do not cover
  umizame.** `zcheck.py`: every last product of umizame (gamma none) and A28 AD5 (gamma g^17)
  equals a member (z, zeta) of C's 1275-member model modulo E. `zrank.py`: all 30 A28 files
  (NIST + hub) have dim Z = rank pi = 5 (the "linear" case zdfs handles); all 6 umizame-derived
  files have dim Z = 4, rank pi = 7 (excess 3; z-values 6 distinct points with multiplicities
  3,3,3,3,2,1, the 3 rows sharing points). A 13-member layer over a 9 + 5 prefix has rank pi <= 5
  (T must be in span(E + S)), so one that kept umizame's excess 3 would have dim Z <= 2 - exactly
  the case C/NOTES lists as not covered; excess 1-2 with dim Z = 3-4 is the other uncovered zone. `zdfs2.py` (this directory) closes dim Z <= 2 exhaustively (section 6).
* [C] n-block equations verified on umizame, A28 AD5, A28 AD4 (`nblock_check.py`): per output,
  sum c Y = b_j (coefficient of x^239) and sum c z = 0. Parities: umizame uses every row an even
  number of times in every output (N-junk identically 0); A28 AD5/AD4 have odd row parities in 5
  resp. 7 of 8 outputs.
* [C] gamma twins (`gamma_twin.py`): same (z, zeta) indices, other gamma -> minimal x-junk 8
  instead of 3 (both A28 AD5 and umizame, all 15 other values). gamma is forced by the member set.
* Invariants shared by all 28/29s [C]: three-stage skeleton (1.1); 9 or 10 S1 products; 5 or 6
  middle ANDs; 13 or 15 GF(4)-norm members; Jx in {2, 3}; outputs only at the last level.
  Differences: gamma (0 vs != 0), the junk's rank profile, where the extra AND sits (S1, middle).
* C/NOTES section 6's conjecture "k + J >= 18" is already contradicted with the exact J values:
  A28 AD5 has k + Jx = 13 + 3 = 16, AD4 13 + 2 (+ J0 1), umizame g182 15 + 2 = 17. What binds is
  not dim U but whether U is 9-coverable and the N-junk 5-realisable.

## 3. umizame decoded (paper https://umizame.github.io/S-box_29-AND/, read 00:30 UTC)

Canright all-normal tower; H = W G = L Y^16 + R Y; D = LR + WZ(L+R)^2, Q = D^-1, outputs need
RQ and QL. Each GF(16) product by Karatsuba over GF(4) = 3 rows (a, b, c) = (L_i, R_i, Q_i).
Prop. 4: for a, b, c in GF(4), {ab, bc, ca} cost 3 (early: p_j = tau(W^j a) tau(W^j b)) + 5
(late) = 8 ANDs instead of 9; the late cells are (tau(ra)+tau(tb)+tau(Wc))(tau(Wra)+tau(Wtb)+
tau(c)) with shears, and their x-only junk lies in span(p1, p2, p3). In our XAG terms [C]: the 9
early ANDs ARE the 9 S1 products (LR = the norm computation); the 15 late ANDs are GF(4)-norm
members with gamma = 0; Jx = 3 with U inside the span of those 9 products. Saving vs BP: exactly
one AND per Karatsuba row (3 total). The hub A31 / NIST A32-AD4 family saves one AND in one row
with a different (non-norm) 5-member row (12 bilinear + 5 mixed members).

## 4. Lower bounds: what is actually known

* **[P] MC(AES S-box) >= 13** (and the same for x -> x^-1 on GF(2^8), which differs by a free
  affine map). Proof: [C, `lb_degree.py`] all 255 nonzero output combinations have degree 7.
  Let a_1..a_k be the ANDs in topological order and D = span(1, x, {a_i : deg a_i <= 6}). The
  output span meets D only in 0, so >= 8 ANDs have degree >= 7. Let a_t be the first such; any
  function f computed with t ANDs has degree <= t + 1 (Schnorr's bound; restriction proof: for
  i = 1..t the left operand of a_i is affine on the current affine subspace V; impose it = c,
  which makes a_i affine on the smaller V; of the two choices of c at least one keeps
  deg(f|V) >= deg(f|V_old) - 1 (write f = l g + h: if both h and g + h had degree < d - 1 so would
  g). After t steps f is affine on V, so deg f - t <= 1). So t >= 6, a_1..a_5 have degree <= 6 and
  are distinct from the >= 8. Hence k >= 5 + 8 = 13.
* [H, literature recollection + web search 00:40] Boyar-Peralta/BMP give the upper bound 32 and
  NIST lists "< 32 ?" as open; the Schnorr degree bound MC >= deg - 1 is standard. Jeon, Baek, Kim,
  "Toward Finding S-Box Circuits With Optimal Multiplicative Complexity", IEEE Trans. Computers
  73(8):2036-2050, 2024 (doi 10.1109/TC.2024.3398507) claims "tighter lower bounds for the MCs of
  AES and MISTY S-boxes than previously known"; the number could not be retrieved (paywalled) -
  the user may want to fetch it. We know of no published bound anywhere near 27.
* [C, track C] GF(16) inversion MC = 5 (CHM SAT, CaDiCaL): k = 4 UNSAT. Applies to any circuit
  whose "middle" is a function of N alone; also gives MC(S) >= 5 by restriction to the subfield
  (weaker than 13).
* [C, Barbulescu et al. 2012, via C/NOTES 8] bilinear rank of GF(16) multiplication = 9 (bilinear
  formulas only). Mirwald-Schnorr 1992: one AND level suffices for single quadratic forms and
  pairs; no general nonlinear lower bounds. Stoffelen 2016: exact MC of 4x4/5x5 S-boxes.

### 4.1 Assumptions of every earlier exact result of ours (what is NOT excluded)

| result | exact case it covers | NOT excluded |
|---|---|---|
| C: stage 1 >= 9 (k = 7, 8 impossible) | N's coordinates in span(1, x, k products of x-linear forms), one AND level | N computed with depth >= 2 or using non-x-linear operands; circuits that never compute N |
| C/G: GF(16) inversion = 5 | ANDs whose operands are functions of N computing n | middles using x (not functions of N) or producing a function other than n (see 1.7a) |
| G: 5-AND middles realise 30 of 127 spans span(n) + <v> | 5 products, operands functions of N, target n plus one N-function | 6+ AND middles, middles not functions of N, more than one extra function |
| C: no 9-product stage 1 fits the A28 AD5 layer | the published 13 members and inversion fixed | other layers |
| C cand13: A28 neighbourhood cannot give 9 + 5 + 13 | 13-subsets of maximal pi-consistent families around the A28 Z | layers far from A28, gamma = 0 layers, other Z |
| C zdfs table | GF(4)-norm members with the stated gamma over the stated fixed E, k = 12, dim Z = rank = 4 (and dim Z = 3) | dim Z = 2; other gamma; other E (in particular umizame's E, any 9-product E with k = 13); non-norm members; members with independent N-part |
| G: AD4 layer needs a 6-AND middle | AD4 layer with AD4 level 1 | other layers |
| G walks (270+ / 2516 layers, junk 3 none coverable) | [H] walks from A28 layers, 13 members over O = span(x, N, n), real 5-AND middles | everything not visited |
| H1 keep-sets | 13-member layers keeping subsets of a published layer over a published prefix (necessary condition only) | layers keeping < 9 members |

Everything above assumes the three-stage skeleton; **no exact result of ours says anything about
circuits whose ANDs mix stages, that never compute N or n explicitly, or that use a different
decomposition of x^-1** (e.g. through the GF(4) norm x^85: x^-1 = x^84 (x^85)^2, never seen in
any record circuit).

## 6. Exact runs by H1 (CPU 12, guarded)

* **zdfs2: GF(4)-norm last layers with dim Z <= 2 - none** [C, exhaustive in this case;
  `zdfs2.py`, log `.../H1/zdfs2/run.log`, 00:40-01:04 UTC, 80 runs of 13-46 s]. For each prefix
  E and each of the 16 gamma values (none = umizame type, and the 15 elements of K*), every
  2-dim Z (10795) and every subset of size >= k of its 15 members was tested exactly (prune:
  pi-rank of all 15 > 7; only the 85 GF(4)-lines Z survive for gamma none, none for gamma != 0):

| E (level 1 + middle) | k | total if hit | hits |
|---|---|---|---|
| umizame 9 + umizame 5 | 13 | 27 | 0 |
| A28-AD5 10 + 5 | 12 | 27 | 0 |
| A28-AD4 9 + 6 | 12 | 27 | 0 |
| A28-AD4 level 1 (9) + AD5 inversion (5) | 13 | 27 | 0 |
| umizame 9 + AD5 inversion (5) | 13 | 27 | 0 |

  Positive control (`zdfs2_control.py`): umizame's 15 products, mapped to model members, pass
  the same exact test over umizame's E with pi-rank 7 (the prune threshold); no 14-subset passes.
  Scope: members of one gamma; dim Z <= 2 only; the listed E's only. This closes the
  "dim Z = 2" gap listed in C/NOTES section 9 for these E's (for k = 12 over the AD5 and AD4 E it
  is the missing case of C's table).
* **rho2 SAT (is there a 9-cover of V_N with x^5-rank <= 1?) - not decided.** `rho2_sat.py` =
  C's stage-1 encoding + rank constraint; the positive control (k = 9, rank <= 2, which the
  record circuits satisfy) did not finish in 13 min (C's unconstrained k = 9 instance: 33 s), so
  the UNSAT question was not attempted; stopped 00:40. The [H] "capacity 3" statement stays [H].
* zdfs / zdfs3 (track C's tools) over umizame's prefix, gamma none, k = 13, cases (dim Z, rank)
  = (3,3), (3,4), (4,4): running from 01:04 (`.../H1/zdfs/run.log`); results below when done.

## 5. Failures / pitfalls (kept for the record)

* gf.Span.reduce only clears the leading bit (not a full reduction); using it as a projection
  gave wrong keep-set numbers in the first `keep.py` run (d(15) = 6 for the complete umizame
  layer). Fixed with a fully reduced echelon basis; first output overwritten after the fix
  (it was obviously inconsistent). Same pitfall in a first `junkrank.py` (dependent junk basis,
  rank-0 element); fixed.
* `decomp.py` first used all 8 bit-tables of N and n as a "basis" (rank 4 each), so every operand
  split failed; fixed by selecting independent ones.
