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

8. **Levels vs stages, and explicit vs spanned N^-1** (answer to L2 / coordinator, 02:30 UTC).
   (a) L2's "10-AND last layer" (hub 29/5/134-138, AND levels 10|2|3|4|10) is in the 63 files:
   by operand spans it is 10 S1 + 6 MID + 13 LAST, all 13 GF(4)-norm members (gamma g^187),
   Jx = 3, dim U = 7 [C, decomp_all]; 3 of the 13 members just sit at AND level 4 because their
   operands are ready early. Likewise the A31 joins (9|1|2|6|13) are 9 + 5 + 17 with 4 of the 17
   last members at level 4. AND level is a scheduling fact; the stage roles above are by operand
   spans and are unaffected. (b) Everything here about N^-1 is about SPANS: "rank of n in the
   circuit span = 4" holds in all files but one. Explicit wires are a different matter [C,
   `nwires.py`]: number of non-constant wires lying in span(1, n): A28 AD5/AD4 0, hub A29
   (10|2|3|4|10) 0, umizame A29 1, A30 g147 2, BP A32 9, A32 AD4 9, hub A31 9. So A28 circuits never
   materialise any nonzero GF(2)-combination of n's coordinates as a wire - n exists only inside
   the operands of the last layer (each operand mixes x, N and n) - which matches L2's count of
   explicit N^-1 signals (54 of 101 pinned, none in A28). (L2 reports none for A30; with my
   definition A30 g147 has 2 such wires - definitions differ: one combination of n's
   coordinates vs all four coordinates.)

(Caveat, 10.2: the 13-norm-member property holds for these files, not for A28 circuits in
general - later A28s have 11 or 12 members plus a non-member pair - and the 63 files come from 3
independent designs.)

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
  Re-checked 02:50 for X3: (1) the degree fact was re-verified independently on a NIST circuit's
  output tables (`lb_check2.py`: 255 x degree 7); (2) the span step needs only that every
  element of D has degree <= 6 and every nonzero output combination degree 7; (3) "first top
  AND" uses the sub-circuit of its ancestors (<= t ANDs), so Schnorr's bound applies; (4) the
  restriction lemma is applied to f = a_t with c chosen per step, and an AND whose left operand
  is already constant costs no equation; NOT/XNOR/constants are affine and change nothing.
  The bound is weak (13) and says nothing about structure; it is the only general bound we have.
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
* **zdfs / zdfs3 (track C's tools) over umizame's prefix (9 + 5), gamma none, k = 13 - none**
  [C, exhaustive within each case; log `.../H1/zdfs/run.log`, 01:04-01:34 UTC]:
  (dim Z, rank pi) = (3,3): 97155 Z, 0 leaves (24 s; maxmult 1 means at most 7 members);
  (3,4) zdfs3: 97155 Z, 0 checks (394 s; complete since 13 > 7 points);
  (4,4): 200787 Z, 0 leaves, 0 hits (1263 s).
  The same (4,4) case over umizame-L + AD5-inv was started and stopped at 01:40 (CPU 12 became
  shared, addendum 01:35); it and the uncovered cases (4,5) [partial via zdfs3], all 15 gamma != 0
  over umizame's E, and AD4-L + AD5-inv are specified in `~/xs-campaigns/2026-11-15-study/QUEUE.md`
  (section "H1") for the overnight run. Memory: 16 MB peak per job (measured).

## 7. Follow-up from 01:50 UTC: the 9+5+13 target (coordinator request) - scope, for H2

Read H2/NOTES.md first (01:40). H2 covers: the row problem (5 late per isolated row [C]); the
relaxed tower model (v independent) with umizame's 9 early products forced, row-local members (no
K = 13/14 for any gamma [C]) and all 1275 members (jsat, gamma 6, running); v-junk parities;
normspan ((4,4,5) needs 11 > 9 [C], so my (4,4,5) row in TRICKS is now excluded, not [H]).
**H1 covers, without overlap:** the graph model (true functions of x, operands in
span(1, x, N, n)), stage 1 NOT fixed (cover test of U from scratch, any 9-cover), members of one
gamma with gamma solved per candidate; (a) the exact condition list as a fast tester
(`cond27.py`); (b) exhaustive small neighbourhoods of the 30 A28 layers and of umizame's layer;
(c) larger neighbourhoods as QUEUE.md jobs. H1 does not run SAT over the full member pool.

### 7.0 Scope label (X3 critique, 03:00 UTC)

Everything in 7.1-7.4 is **[C / P, 1275-member model]**: it assumes every last-layer AND is a
GF(4)-norm member (x-ratio in {w, w^2} with the inverse n-ratio), a model read off the A28 files,
not derived. X3 proved [C] that a parallel top layer needs >= 10 products and that at exactly 10
the tensor spans are member spans; for 11-13 non-members (semi-members) are possible. Section 8
extends the work to them.

### 7.1 Exact conditions as fast tests (the "(a)" part) [1275-member model]

Model: last layer = k GF(4)-norm members (z_m, zeta_m), one gamma; stage 1 = any 9 level-1
products; middle = BMP 5-AND (n only). Facts (all checked by script, see `nfast.py` docstring):
* [C, coeffcheck.py] coefficient of x^239 (class of x^-1) of a member is Y = z/zeta (all 1275
  members, gamma none/1/g^17/g^187); coefficient of x^188 (class 47) is z (sampled members, two
  gammas). These classes occur nowhere else in the circuit (S1: weight <= 2; MID: multiples of
  17), so for each output combination c: (i) sum c Y = b_j, (ii) sum c z = 0 are NECESSARY.
* [C, junkfit.py, sampled members] x-junk coefficients: c_3 = z^3 zeta, c_9 = z^9 zeta^3 +
  gamma^8 Y^128, c_5 = 0, c_17 = 0 (gamma none; for gamma != 0 c_17 lies in V_N, free).
* [C, parity.py; agrees with H2 vjunk.py] N-junk of an output = function of its class-parity
  vector only; free iff parity in Pi(gamma): Pi(none) = {0, 11111}; for gamma != 0 Pi is 3-dim,
  spanned by one free class e_f and two class pairs (5 groups of 3 gammas, table in
  `.../H1/parity.txt`). H2 [C]: no nonzero N-junk lands in G's 30 classes, so with a 5-AND
  middle every used output combination must have parity in Pi(gamma).
* Test (`nfast.py`, no truth tables): K_Pi = {c : sum c z = 0, parity(c) in Pi}; need
  Y(K_Pi) = F; x-junk Jx >= dim J(K_Pi) - dim J(ker Y) (exact if excess 0), J(c) = (sum c z^3 zeta,
  sum c z^9 zeta^3 + gamma^8 (sum c Y)^128). **Validation [C]:** on all 10 distinct published
  layers it reproduces decomp.py exactly: A28 AD4 layers fail the parity test (they need the
  6-AND middle), A28 AD5 pass with Jx = 3, umizame pass with Jx = 3 (g182 variant: 2).
* `cond27.py`: the same conditions on truth tables (R1 n-block, R2/R3 feasibility with n only,
  R4 junk with q-parts, R5 = exact 9-cover test of U via track C's cover_enum / G's SAT).
  Validated: A28 AD5 -> J 3, U not 9-coverable; umizame -> J 3, coverable (k = 15);
  A28 AD4 -> fails R3.

### 7.2 Consequences (proved from the necessary conditions above) [P, 1275-member model]

Notation: rows P (classes used, r of them), sizes n_P, D_P = span of differences of row P's
z-values, d = dim(sum D_P), p = dim(Pi restricted to the used classes), C = span of the 8 output
combinations (C -> F bijective by (i)), C0 = C cap {all parities even}.
**Lemma [P].** For c in C0 the row sums w_P = sum_{m in P} c_m z_m lie in D_P, sum_P w_P = 0 and
Y(c) = sum_P zeta_P^-1 w_P; c -> (w_P) is injective on C0 (Y factors through it). Hence
8 - p <= dim C0 <= sum_P dim D_P - d <= sum_P min(n_P - 1, d) - d, and d <= dim Z <= k - 8.
* **Theorem 1 [P, 1275-member model, given the cited facts]: gamma = 0 (umizame type, operands x + n only):
  k >= 14, and k >= 15 unless all 5 classes are used.** (Pi = {0, 11111}: r < 5 needs
  (r-1) d >= 8 and k >= 8 + r + d -> k >= 15 (r = 3, d = 4 is umizame); r = 5 needs d >= 2 and
  k >= 14.) So no umizame-type layer gives 9+5+13 = 27 or 9+5+12, whatever stage 1 is; the
  umizame layer (15) is optimal among <= 4-class gamma = 0 layers.
* For gamma != 0 the bound gives k >= 12 (`parity.py`), with k = 12 forcing one of two rigid
  shapes: (A) 3 rows of 4 with d = 3, p = 2; (B) all 5 classes, d = 2, p = 3, row sizes with
  sum(n_P - 1) = 7, every n_P <= 3.
* **Theorem 2 [P, 1275-member model]: shape (A) is impossible.** Every class triple with p = 2 contains the free
  class f of Pi(gamma) (a triple avoiding f contains at most one of the two pairs, so p <= 1), so
  e_f is a parity of some c in C (dim C/C0 = p forces parity(C) = Pi_used). For that c the row
  sums satisfy w_f = -(sum of the others) in D, so row f lies in D and (w_P) lies in the image
  W0 of C0 (C0 -> W0 is onto by the dimension count) - then c + c' (c' in C0 with the same
  w-vector) is a nonzero element of C with Y = 0, contradicting (i).
* Shape (B) is not excluded by this argument. What it must look like [P, same reasoning]:
  parity(C) = Pi (all 3 dims) and C0 -> W0 bijective (dim 5); for the e_f lift row f lies in D
  and n_f in {1, 2} (for n_f = 3, D_f = D and the lift falls into W0); for each pair pattern
  e_a + e_b the rows a, b lie in one common coset of D; Z = D + <u, v> (dim <= 4). Filter 1
  (Y injective on W0; `shapeB.py`) passes 111600 of 118110 (gamma group, D, sizes, deltas)
  configurations, so it does not kill (B); the full enumeration over cosets and points
  (~1e10 sets in Python) was not attempted. **Open, small, explicit: handed to H2.**
* So with a 5-AND middle a GF(4)-norm layer has k >= 12 always, and k = 12 only in shape (B).

### 7.3 Small exhaustive neighbourhoods (the "(b)" part) [C, 1275-member model, `nbhd.py`, stage 1 free]

Each set was tested with R1 (n-block), R2/R3 (n-only feasibility), R4 for all 16 gammas, and R5
(exact cover_enum) whenever J <= 3. Logs `.../H1/nbhd/*.jsonl`.

| start layer | move | sets | pass R1 | feasible (set, gamma) | J <= 3 | 9-coverable |
|---|---|---|---|---|---|---|
| A28 AD5 g124 (gamma g^17) | swap 1 of 13 for any of 1262 | 16406 | 675 | 369 | 21 | 0 |
| A28 AD5 g128 (g^187) | same | 16406 | 691 | 369 | 21 | 0 |
| A28 AD5 g150 (g^34) | same | 16406 | 707 | 369 | 21 | 0 |
| A28 AD4 g131 / g141 / g176 | same | 3 x 16406 | 883 each | 12 each | 4 each | 0 |
| A28 any | drop 1 (k = 12) | 13 each | 0 | - | - | - |
| umizame (4 variants) | drop 2 (k = 13) | 105 each | 27 | 54 (all J = 8) | 0 | - |
| umizame g137 | drop 3, add 1 (k = 13), 3 of 8 chunks | 215460 | 13318 | 1419 (all J = 8) | 0 | - |
| A28 AD5 g124 (all 16 gamma) | swap 2 of 13 (removed pairs 0-20 of 78) for any 2 of 1262 (`swap2.py`) | 100257066 | 1349 pass n-block + parity | Jlb: 936 x 5, 384 x 4, 29 x 3 | 29 | 0 |

swap2.py cross-check: for all 29 J = 3 sets, cond27 (truth tables) gives the same J = 3 and the
exact cover test says not 9-coverable (dim U = 7) - nfast's junk formula agrees with the truth
tables on these new sets. Remaining removed pairs of g124 and the other 5 A28 layers:
QUEUE.md "H1-b" (234 chunks of ~80 s).
(The umizame drop-3-add-1 chunks were stopped: Theorem 1 already excludes gamma none, and every
gamma != 0 result was J = 8.)

## 8. Beyond members: semi-members over fixed 9-spans (03:00-04:00 UTC; X3 SEMI.md)

**Split with H2 (as agreed through the coordinator):** H1 = few non-member products over FIXED
stage-1 spans (published prefixes), exhaustive over all products; H2 = the generator (gen13)
over general member + semi-member sets.

* **Lemma S [P].** Product (Tr(Ax) + Tr_K(s n) + ...)(Tr(A'x) + Tr_K(s' n) + ...) (other V0 parts,
  N-parts, constants do not matter): its x(x)n tensor has class components
  y_d = A^(2^d) s' + A'^(2^d) s, d = 0..3 (d = 0 class 127, d = 2 class 47, d = 1, 3 the classes
  15, 111; d = 0, 2 agree with coeffcheck.py). y_1 = y_3 = 0 forces r = A'/A with r^2 = r^8, i.e.
  r in GF(4)*, and s'/s = r^2: a member (r = w, w^2) or the zero tensor (r = 1). So every
  semi-member has a class-15/111 part, and nothing else in a three-stage circuit has one (X3 4.1).
  This is the same statement as X3's semi_mod.py (no semi coset in M8): a lone semi-member among
  members cannot enter any output.
* **Consequence [P].** Over a fixed E and a fixed set X of kept products, if exactly
  j = d(X) = dim(T + E + X) - dim(E + X) new products must be added, each must project into
  T-bar = pi(T) (pi modulo E + X), so each has zero class-15/111 part: semi-members are useless
  without slack. Two compatible semi-members (X3 (a)/(b)) can close only ONE missing dimension
  together (pi(s1) + pi(s2) must lie in T-bar). So "11 members + 2 semi-members = 13" needs an
  11-subset with d <= 1.
* **Published-prefix data [C, keep.py, `.../H1/keep/mixed_prefixes.txt`]:** over AD4 level-1 +
  AD5 middle and over AD4 level-1 + umizame middle, the AD4 layer has d = 1 only when member 0 is
  dropped (12-subset), all other 12-subsets d = 2, all 11-subsets d >= 2 (minimum 2, exactly the
  12 subsets {0, j}). AD5 and umizame layers over these and over umizame-L + AD5 middle: d >= 3
  for <= 13 kept. Hence over these 9 + 5 prefixes **no 11 published members + 2 semi-members**
  [C + P], and "12 + 1" can only be closed by a member or a zero-tensor product.
* **12 + 1, exhaustive over ALL products [C, `fixk.py`, O2 = span(1, x, N, n, middle products),
  2^18 operands l with linear solve for m; positive control: the full AD4 layer is closed (by
  products of N-functions, H2's 28)]:** AD4 layer minus member 0 over AD4-L + AD5-mid and over
  AD4-L + umizame-mid: **no single product closes it** - so no 27 of the form
  9 + 5 + 12 + 1 from this layer [C, case: FIXED prefix, extra AND with both operands in O2;
  chains and a re-chosen stage 1 are not covered, see 10.2].
* **11 + 2 over all products [C, fixk.py, O2]:** AD4 g131 layer minus {0, j} (j = 1..12, the
  only 11-subsets with d = 2), over AD4-L + AD5-mid and AD4-L + umizame-mid: 24 cases, each
  exhaustive over 2^18 l's; in every case exactly ONE of the three nonzero T-bar elements is
  reachable by a single product (presumably re-adding member j), never two independent ones, so
  **no two products complete any of them** - no 27 = 9 + 5 + 11 + 2 from this layer. Log
  `.../H1/fixk/ad4_11p2.jsonl` (48 chunks, 02:36-02:57 UTC).
* d-scan (`dscan.py`) of the other AD4-type layers (g141, g176; own stage 1 + AD5 g124 / g150 /
  umizame middle): the same structure - exactly one special member whose removal keeps d = 1
  (g141: member 3, g176: member 1), all other 12-subsets d = 2, 11-subsets d >= 2 only with the
  special member removed. Their 12+1 / 11+2 runs (O2) and the 12+1 runs with OV = aff(x) + all
  functions of N (2^24 operands, X3's full operand model) are in QUEUE.md "H1-c".
* Scope of section 8 results: fixed published prefixes and subsets of published layers; extra
  products over O2 (exhaustive, any type, members and semi-members included); a 13-member layer
  mostly NOT from a published layer is H2's generator problem.

## 9. The new 9 + 5 + 14 circuits: can 14 become 13? (03:20-04:00 UTC, coordinator request)

Inputs: X1b `aes-sbox-a28-ad5-g158-gd27-x1b-span-2cabef6153f4` (roles 9 S1 + 5 MID + 14 LAST,
12 GF(4)-norm + 2 other members, Jx 3, dim U 7) and H2's 10 built circuits
`h2-ad4a-g1-c8c7227f-s{58,59,76,83,103,110,114,372,467,709}` (9 + 5 + 14, all GF(4)-norm, Jx 2).
Stage 1 and middle FIXED (each circuit's own), so junk coverability is automatic. **Every [C] in
this section is in that case (fixed prefix, replacements with operands in O2); chains and a
re-chosen stage 1 are not covered (10.2).**
* **(a) drop 1 [C, d14.py]:** in all 11 circuits every 13-subset misses exactly one output
  dimension (d = 1 for all 14 drops). No 13-subset works.
* **(b) 2 -> 1 [C, d14.py + fixk.py, O2 = span(1, x, N, n, middle), all 2^18 l with linear
  solve]:** in each circuit exactly ONE pair has d = 1 (X1b {4,5}; s58 {5,6}; s59 {6,7};
  s76 {6,7}; s83 {5,7}; s103 {1,4}; s110 {2,8}; s114 {2,4}; s467 {2,5}; s709 {4,11}; s372 none);
  the other 90-91 pairs have d = 2 (one product cannot close them). For each d = 1 pair:
  **no single product closes it.** Positive control: dropping one member, fixk re-finds exactly
  that member (6-10 equivalent (l, m) forms) in chunk 0.
* **(c) 3 -> 2 [C, same]:** triples with d = 2: those containing the d = 1 pair are excluded by
  (b) [P: a product reaching the second T-bar direction would close the pair]; the 14 others
  (2 per circuit at most, listed in `.../H1/fixk/triples_todo.txt`): no product reaches any
  T-bar direction at all, so no two products complete them.
* **19 further circuits [C, t14.py, O2, 03:25-03:36 UTC]:** H2 s1039 s1312 s1315 s1318 s1320
  s1328 s1329 s1334 s1336 s1338 s946 (9+5+14), H2 ad5-g14-s2 / s9 / g14v-s0 (10+5+13), X1b g169
  g170 g221 (9+5+14), g157 g214 (10+5+13). Same picture everywhere: every single drop leaves
  d = 1; 0-1 pairs with d = 1 (none closable by one product); 0-2 triples with d = 2 (at most one
  T-bar direction reachable, s1328 {6,9,12}; never two). **No 27.** Log `.../H1/fixk/t14_new.jsonl`.
  For the 10+5+13 circuits only last-layer products were dropped (dropping a stage-1 product is
  not covered).
* OV (aff(x) + all functions of N, 2^24 operands, X3's operand model) for X1b's pair: 4 of 32
  chunks (operands l < 2^21) done, nothing reached; stopped to give CPU to the O2 sweep. All OV
  runs and any further circuits: QUEUE.md "H1-d" (`t14.py`, `queue/t14_all.sh`).
* Observation [C, 30 circuits]: in every 14-member layer each member is "needed" (d = 1 for
  every single drop) and the pair/triple redundancies are rare and never repairable by one
  product - the 14th AND is structural in this family, not slack.
* Scope: stage 1 and middle fixed to each circuit's own; new products with operands in O2 (or
  OV); 1 or 2 replacements. Not covered: replacing >= 3 members, other stage-1 spans.

## 10. Audits and relabels (04:20-04:40 UTC)

### 10.1 cover_sat SAT branch (X3b: it times out on positive controls)
G's `eval3.cover_sat(U, l, limit)` is exact only in its enumeration branch (track C's cover_enum,
used when l - dim U <= 2); otherwise it calls SAT with a time limit and returns None on timeout.
* **My uses:** only `cond27.cover` -> `nbhd.py` and `swap2.py` (R5). Checked every logged record
  [C, scan of `.../H1/nbhd/*.jsonl`, `.../H1/swap2/*.jsonl`]: all 105 cover tests (76 nbhd, 29
  swap2) had dim U = 7 with l = 9 (enumeration branch, exact); none went to SAT, none timed out.
  The validation runs of cond27 (A28 AD5 False, umizame True) were also dim U 7 (enumeration).
  So "9-coverable: 0" in 7.3 stands as [C].
* **Would a timeout have counted as "not coverable"?** In the code, yes silently (R5 None is
  falsy in `if ok:`). Fixed 04:25: nbhd.py and swap2.py now log "UNDECIDED" for None. No past
  result is affected (no None occurred).
* Not using cover tests at all: keep.py, zdfs/zdfs2 (fixed E), nfast.py, fixk.py, t14.py,
  d14*.py (fixed prefix: coverability is implied), junkrank/junk (ranks only).
* **Track G camp-X12/X13 "cover=UNSAT" [C, configs `~/xs-campaigns/2026-11-14-G/cfgX12.json`,
  `cfgX13.json` + `camp-X1*/eval.jsonl`]:** 2707 layers K = 13 with l = 9, dim U = 7 (e = 2);
  553 K = 12, l = 10, dim U = 9 (e = 1); 445 K = 12, l = 10, dim U = 10 (e = 0). All are in the
  enumeration branch (l - dim U <= 2): **exact; no relabel needed.** (eval_v.py writes "timeout"
  for None; no such record exists.)
* **Track C's cover-lemma uses** (stage1_enum k = 7, 8; the "no 9-product stage 1 fits A28 AD5's
  U" test; cand13's 2321 sets with dim U 7 / 8 and l = 9): all have l - d <= 2, i.e. the exact
  enumeration; C's own SAT runs (stage1.py k = 9 SAT, qmc) gave SAT answers, not timeouts.
  No relabel needed. Only G's NOTES 3.1 phrase "one hour of CHM SAT did not finish" was already
  stated as undecided.

### 10.2 Case statements (X3b critique; no new compute)
* NOTES 8 "no 27 of the form 9 + 5 + 12 + 1 ... whatever stage the extra AND belongs to" and
  "11 + 2": **[C, case: stage 1 and middle FIXED to the named published prefixes, kept products =
  subsets of the AD4 layer, the new products have both operands in O2 = span(1, x, N, n, middle
  products) (OV where stated)].** Not excluded: extra ANDs reading stage-1 products, members or
  outputs (chains), and any re-chosen stage 1 (with stage 1 free, completions exist - X3b found
  them for H2 s59's pair, and then the cover of the new U decides).
* NOTES 9 "no 27 by dropping or replacing 1-3 last-layer products": **[C, case: each circuit's own
  stage 1 and middle fixed; replacements with operands in O2; 1 drop, 2 -> 1, 3 -> 2].** Same
  exclusions as above.
* NOTES 1 / TRICKS 0 "every A28 top layer is 13 GF(4)-norm members": true for the A28 files in
  the 63 analysed [C on those files] but **not a property of A28 circuits in general**: the later
  spangen A28s are 11 members + a singleton-coset pair, and X1b g158 (NOTES 9) is 12 members +
  a pair (decomp: 12 norm + 1 x|xNn + 1 other). Also: the 63 files are not 63 independent data
  points - they come from 3 independent designs (Boyar-Peralta/BMP, umizame, the A28 contribution)
  plus derivations (linear re-optimisation, hub operators).

## 5. Failures / pitfalls (kept for the record)

* gf.Span.reduce only clears the leading bit (not a full reduction); using it as a projection
  gave wrong keep-set numbers in the first `keep.py` run (d(15) = 6 for the complete umizame
  layer). Fixed with a fully reduced echelon basis; first output overwritten after the fix
  (it was obviously inconsistent). Same pitfall in a first `junkrank.py` (dependent junk basis,
  rank-0 element); fixed.
* `decomp.py` first used all 8 bit-tables of N and n as a "basis" (rank 4 each), so every operand
  split failed; fixed by selecting independent ones.
