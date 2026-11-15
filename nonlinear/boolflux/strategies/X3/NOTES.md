# X3 (fresh-perspective red team for 27 ANDs): notes

Labels: **[C]** computed exactly / exhaustive within the case stated on the same line; **[P]** short proof
given here; **[H]** heuristic, analogy or opinion. Data: `~/xs-campaigns/2026-11-15-study/X3/`.
Notation as in H1: F = GF(2^8), K = GF(16), N = x^17, n = N^-1, V0 = functions of N, T = span of the 8
outputs, V_N = span of N's coordinates. "Top AND" = an AND of degree 7 or more; "prefix" = the other ANDs.

## 0. Summary (what the outside view found)

1. [P]+[C] The degree bound (H1 section 4: MC >= (deg - 2) + n) is **tight for inversion in GF(8) and
   GF(16)** (3 and 5) and **fails by at least 2 in GF(32)**: bound 7, exhaustive result MC >= 9
   (section 2; a verified 11-AND circuit exists).
2. [C] In GF(16) **no optimal circuit is "three-stage"**: all 156,960 5-AND circuits (operand-space count,
   section 2) are 1 quadratic AND + 4 cubic ANDs, the cubic ANDs read each other (AND depth >= 3), and the
   norm to GF(4) is never computed. The exact optimum of the GF(16) analogue of our skeleton is >= 7
   (section 2.3). So at the one size where everything is known, the skeleton our 28s share costs 40 % more
   than the optimum, and the optimum has features (sequential top ANDs, no norm) that no known AES circuit
   and none of our searches has.
3. [C] On AES, the same "tight top" cannot start over any known prefix: over the non-sink ANDs of the
   A28-AD5, A28-AD4, A29 and BP32 files there is **no product of two prefix forms that lies in
   span(prefix) + T** (section 3). Every known top product carries junk.
4. [C] **Any parallel top layer whose operands are (affine in x) + (any function of N) needs >= 10
   products**, for any prefix made of x-quadratics and functions of N and however the junk is absorbed,
   and the 10-dimensional solutions of the bilinear part are exactly the 10,200 spans of GF(4)-norm
   members H2 found (section 4, SEMI.md). So in the three-stage family the open totals for 27 are
   9+5+13, 9+6+12, 10+5+12; 10 or 11 top products are not excluded by this argument alone.
5. [C] The member model (1275 tensors) is 0.056 % of the rank <= 2 tensors (2,270,775). Exactly 107,100
   more tensors share a target coset with another one ("semi-members", K-ratio operand planes); their
   junk can have an x^5-component, which member junk never has [P]. All exhaustive 12/13 results of
   C / H1 / H2 before 02:45 UTC were inside the 1275. Reported 02:30; H1 and H2 were redirected (SEMI.md).
6. [C] Adding class-9 quadratic operands (coordinates of x^33 = x^16 N) to the top layer creates no new
   coset structure (all singletons); 9 products stay impossible (section 4.4).

## 1. Assumptions shared by all known 28-32 circuits and by our searches

Each line: the assumption, who relies on it, and what is known outside it.

| # | assumption | status |
|---|---|---|
| A1 | x^-1 = x^16 * N^-1 through K = GF(16) (N and N^-1 both computed) | all 63 files [C, H1]; the only cheap two-factor monomial route [P, H4 section 1; X3 section 5.1] |
| A2 | N is computed completely, at AND level 1, by 9-10 products of x-linear forms | all files; "9 is exact" only for one level of products of x-linear forms [C, track C]. Not known: MC of x -> x^17 with products of non-linear operands |
| A3 | the middle is a function of N alone and computes N^-1 exactly | all files but one (H1 1.7a). 5 is exact for K-inversion [C]; **nothing is known about MC(x -> x^-17) as an 8 -> 4 function** (degree bound 8, construction 14) |
| A4 | all top ANDs are parallel: no top AND reads another top AND or an output | all 63 files [C, H1 1.3]. False for every optimal GF(16) circuit [C, section 2] |
| A5 | top operands lie in span(1, x, N, n) | all files (one uses aff(x) + V0). The >= 10 bound of section 4 covers aff(x) + V0; raw stage-1 products or middle products as top operands are only covered by H3's windows (classes in Sigma_U) |
| A6 | top products are GF(4)-norm members (or bilinear n * x) | 28s and 29s; hub A31 / NIST A32-AD4 use 5 non-norm products. All 12/13 exhaustive results assume it |
| A7 | intermediate degrees are 2 (stage 1), 4 and 6 (middle), 7 (top): **no cubic or quintic intermediate** | all files [C, H1 1.5]. A circuit that merges stages must have odd-degree intermediates |
| A8 | prefix size 14 or 15, top size 13-18 | bounds: prefix >= 5, top >= 8 [P, H1]; with A5: top >= 10 [C, section 4] |
| A9 | all 8 outputs appear only at the last level; junk is cancelled additively | all files [C, H1] |
| A10 | searches start from known circuits and keep them valid (hub moves, windows with the rest fixed, walks from published layers) or enumerate a structured family | all tracks. From-scratch general search is not feasible beyond 4-5 bits [H, G 2.1; X3: BoolFlux from the ANF gives 11 for GF(32) inversion, exact value in 9..11] |
| A11 | AND depth is small (4-5) | published circuits. For goal A depth is free; the GF(16) optimum has depth 3-5 for 5 ANDs (most at 4-5) [C]. Any AD cap in a goal-A search is an extra assumption |
| A12 | ANDs are linearly independent modulo affine functions | WLOG [P]: a dependent AND that is last in its dependency can be dropped |
| A13 | representation = AES field | irrelevant [P, H4]: linear changes are free |

Why AND depth >= 4 in all low-AND circuits: [P, H4 3.1] at depth 3 a level-3 operand has degree <= 4, so
N^-1 (degree 6) cannot be an operand; the K-route is impossible and the GF(4)-norm route costs 35.

## 2. Small fields: what optimal inversion circuits look like (tools `tight.c`, `orbits.py`, `skel4.py`)

Degree bound [P, H1's argument for general n]: for x^-1 in GF(2^n), n >= 4 (degree n-1, all 2^n - 1 output
combinations of degree n-1): a function computed with t ANDs has degree <= t + 1, so the first AND of
degree n-1 has index >= n-2, i.e. >= n-3 ANDs of lower degree come first, and >= n ANDs have degree n-1:
MC >= 2n - 3 (n = 3: x^6 is quadratic, the bound is 3).

| n | degree bound | exact MC | source |
|---|---|---|---|
| 3 | 3 | 3 | [C] CHM SAT: 2 UNSAT, 3 SAT (`gfinv.py`) |
| 4 | 5 | 5 | [C] 4 UNSAT (track C), 5 SAT |
| 5 | 7 | >= 9, <= 11 | [C] no 7- and no 8-AND circuit (2.2); [C] 11: circuit `.../X3/gf5-b/best.circ.txt` (BoolFlux from the ANF, 60 s, both verifiers) |
| 8 | 13 | <= 28 | - |

### 2.1 Tight shape and the deficit argument [P]
Deficit d_i = dim(T mod V_i), V_i = span(1, x, a_1..a_i); d_0 = n, each AND lowers it by at most 1, and
a_i lowers it iff a_i lies in V_(i-1) + T but not in V_(i-1). If after L ANDs the deficit is still n and
only n ANDs remain, each remaining AND must lie in V_L + T (H3's Lemma 1). `tight.c` enumerates this
shape completely: every 2-dim operand space at each step (operands = any combination of inputs and ALL
earlier ANDs, so chains among top ANDs are included; constants do not change spans), the last M ANDs
filtered by membership in V_L + T. With MC = 2n - 3 the shape is forced with L = n - 3.

### 2.2 Results
* n = 4, L = 1, M = 4 [C, complete]: 156,960 circuits (as sequences of operand planes). AND depth 3:
  15,720; depth 4: 80,400; depth 5: 60,840; **none of depth 2**. 30 of the 35 possible first ANDs complete
  (one orbit of size 30 under x -> a x, Frobenius; the 5 that fail are the GF(4)-structured planes).
  [P] The only quadratic in the final span is the first AND, and it has rank 2, while both norm coordinates
  Tr(c x^5) have rank 4: **no optimal circuit contains any coordinate of the norm x^5.**
* n = 5, L = 2, M = 5 [C, complete, 3 s]: **0 circuits, and no node at level 3**: for no (a_1, a_2) is
  there a product a_3 in (V_2 + T) \ V_2. So MC >= 8 and the deficit is always 5 after 3 ANDs.
* n = 5, L = 3, M = 5 [C, complete: first AND fixed to the representative of the single orbit of 155
  operand planes under x -> a x and Frobenius, all 651 second ANDs in 18 chunks, 1,706,651 nodes,
  `run_n5.sh`, logs `.../X3/n5_L3_*.log`, 01:54-02:54 UTC]: **0 circuits.** Since the deficit is 5 after 3
  ANDs in every circuit, an 8-AND circuit must have this shape: **MC(x^-1 in GF(32)) >= 9.**
  Level counts (count-only rerun and the logs): 644 second ANDs, 1,700,384 (a_2, a_3) prefixes, about
  5,600 nodes at levels 4-5 (so products a_4 in V_3 + T do exist for some prefixes; in the last chunk:
  204 at level 4, 3 at level 5, 0 at level 6), none reaches level 8. A 9-AND circuit can therefore be
  4 free + 5 tight or 3 free + 6 with one junk dimension; neither was enumerated.
* Controls: the same program finds the GF(8) circuits (L = 0, M = 3) and the GF(16) circuits (above); CHM
  SAT gives 3 and 5 for those fields.

### 2.3 The skeleton's analogue in GF(16) [C, `skel4.py`, partial]
Stage 1 = l products of x-linear forms, last layer = m parallel products of forms in
span(1, x, stage-1 products). With l = 1: least m is >= 7 for all 35 choices (so no parallel-top circuit
with one quadratic AND has fewer than 8 ANDs). The norm x^5 needs l >= 3 products (two rank-4 forms whose
sum has rank 4), and the top needs m >= 4, so the three-stage analogue costs >= 7 [P]; its exact value
(l = 3, 4) was not computed (Python too slow on the shared CPU).

### 2.4 Reading [H]
* Exact values 3, 5, then >= 9 (n = 3, 4, 5) against the degree bound 3, 5, 7: the bound is met only while
  the field is tiny. **Extrapolating the degree bound to n = 8 (13) is not supported**; nor is any smooth
  extrapolation of three points, one of which (n = 4) is degenerate because inversion in GF(4) is linear.
  The data do not say whether 28 is far from or close to optimal.
* What the data do say: at n = 4, the only size with subfields where the optimum is known, the
  three-stage skeleton costs >= 7 against 5, and every optimum chains its top ANDs and avoids the norm.
  So skeleton-optimality has one exact counter-example and no supporting case.
* What the n = 4 optimum does that AES circuits do not: (i) top ANDs chained, (ii) one cheap quadratic
  absorbs all junk, (iii) no norm. On AES (i)-(ii) fail over the known prefixes (section 3), so a tight
  top needs a different prefix.

## 3. "Tight top" test on AES [C per file, `tightaes.py` = H3's chain.py with U = all sinks, m = r = 8]

Question: prefix E = all non-sink ANDs of a known circuit; is there a chain of 8 new ANDs (operands:
x, E and earlier new ANDs, any depth) giving all outputs? Then every new AND lies in span(1, x, E) + T.

| file | \|E\| | products of prefix forms in span(E) + T, not in span(E) | result |
|---|---|---|---|
| NIST a28-ad5-g124 | 15 | 0 | UNSAT at step 1 |
| NIST a28-ad4-g131-gd31 | 15 | 0 | UNSAT at step 1 |
| NIST a29-ad5-g137 (umizame) | 14 | 0 | UNSAT at step 1 |
| NIST a32-ad5-g104 (BP) | 14 | 0 | UNSAT at step 1 |

So over a prefix made of stage 1 + K-inversion, no single product is junk-free; a top layer of 8 + s
products needs s >= 1 junk dimensions and the chain argument gives nothing more. (Log:
`.../X3/tightaes.jsonl`.) H3's deep.py covers s > 0 only with new classes inside Sigma_U.

## 4. The bilinear part of the top layer: >= 10 for all products, not only members

### 4.1 Setting [P]
Functions x^(2^i) n^(2^j) have exponents 2^i - 17 2^j, which fall in exactly four cyclotomic classes
(127, 15, 47, 111; 8 dimensions each), and the 32 functions x_i n_j are independent (checked,
`bil_tb.py`). For any g in V0 write g = lam_g(n) + rest; x_i * rest has exponents 2^i + 17k with
k outside {7, 11, 13, 14}, all different from the 32 above, and x-quadratics, functions of N and affine
functions also avoid the four classes. Hence the projection pi onto the four classes is linear on
functions, kills every prefix AND that is an x-quadratic or a function of N, and maps a product
(l + g)(l' + g') (l, l' affine in x; g, g' in V0) to the tensor l (x) lam_g' + l' (x) lam_g, a 4 x 8
matrix of rank <= 2. The outputs map onto T_b (dim 8; all 255 nonzero elements have rank 4).
So for a circuit = (prefix of x-quadratics and functions of N, any number) + (m parallel products with
operands in aff(x) + V0): **T_b lies in the span of m tensors of rank <= 2.**

### 4.2 Result [C, `bilc.c`, `bil10.py`, exhaustive]
* There are 2,270,775 nonzero tensors of rank <= 2. Modulo T_b they fall into 2,211,105 cosets: 2,162,400
  cosets with 1 tensor, 38,250 with 2, 10,200 with 3, 255 with 5; none in T_b.
* m = 9 would need a coset with 9 tensors: **impossible; m >= 10.** (m = 8 is impossible since T_b has no
  rank <= 2 element.)
* m = 10 needs a 2-dim J whose three cosets hold 10 spanning tensors, so a 5-coset is involved. All
  candidates enumerated: 10,200 planes with coset sizes (5,5,5) and rank 10; the others ((5,3,2): 61,200,
  (5,3,3): 15,300, 595 more (5,5,5)) have rank 6 only. **The 10-dim solutions are exactly 10,200**, the
  number H2 found inside the member family; the 1275 tensors of the 5-cosets are the members. So at
  m = 10 the member structure is forced [C], and H2's junk count (J_x = 8, J_v = 4 at gamma = 0) closes it.
* Check: `zcos.c` recomputes the same statistics from truth tables modulo Aff + Quad + V0 + T (dimension
  48 + 8): identical counts.

### 4.3 What this leaves open [H]
Full statements, proofs, tables and file formats: **SEMI.md** (written for H1 / H2). In short:
* [C] The tensors sharing a T_b-coset are the 1275 members (type (Q,Q): x-ratio and n-ratio in
  GF(4) \ {0,1}) and 107,100 "semi-members" of types (K,K) 76,500, (K,Q) 15,300, (Q,K) 15,300
  (K = ratio in GF(16) \ GF(4)). For m = 11, 12, 13 nothing forces members.
* [P] x-junk of Tr(Ax) Tr(kAx), k in K: x^5-component A^5 (k + k^4), nonzero iff k is outside GF(4)
  (checked numerically, `semi_check.py`).
* [H] H1's junk capacity 3 (stage 1 has 5 spare dimensions, only 3 with x^5-component 0) is a property of
  the member family; K-ratio products can reach the two x^5 dimensions.
* [C] A single semi-member among members is useless: member cosets form an 8-dim space M8 that contains no
  semi coset; semi cosets form 4,335 classes mod M8 (10, 12 or 15 cosets each). Smallest meaningful
  cases: two semi-members of one coset, or of one class mod M8 (252,450 coset pairs) (`semi_mod.py`).
* [C] Positive control (`layer_tensors.py`): NIST a28-ad5-g124 = 13 members, tensor span 13, J_t 5;
  umizame = 15 members, span 12, J_t 4; NIST a32-ad4-g117 = 15 rank-1 + 2 rank-2 tensors in singleton cosets.
* [C] Over umizame's prefix (gamma = 0 witnesses): no two of the 2,270,775 products differ by an output
  combination; on a sample (3000 x 108,375) every 3-term relation among members + semi-members lies in
  span(prefix) (no output part) (`zcos.c` with a prefix J, `lines.c`).
* Track G's llay walks allow all products but start at published layers and found only members; C, H1, H2
  exhausted members. Semi-member layers were not enumerated before 02:45 UTC (H1, H2 redirected then).

### 4.4 Quadratic operands [C for the count, P for the algebra]
Z = x^33 = x^16 N (8 class-9 quadratics) gives a second embedding of the outputs: y = Z n^2. A product
Tr_K(a zeta) Tr_K(b n) (zeta a K-coordinate of Z) has pieces N^(1-2^d) l: d = 0 is LINEAR (free), d = 1 is
the target, d = 2, 3 are junk: two junk pieces instead of three, and 3 such products give one output bit
plus a linear function with no junk (standard: 4). But: adding all 979,200 products (l + z) * lam to the
family gives no new coset with more than one element (`zcos` family 3: histogram 1: 3,141,600, 2: 38,250,
3: 10,200, 5: 255), so 9 stays impossible and no mixed structure appears; and the zeta forms need 4 more
x-quadratic dimensions per K-product in stage 1. [H] Assessed as not competitive.

## 5. Routes to <= 27 outside the skeleton, assessed

| route | idea | numbers | verdict |
|---|---|---|---|
| R1 chained top | top ANDs read top ANDs / outputs, as in every optimal GF(16) circuit | AES: 0 junk-free products over 4 known prefixes [C]; x(x)y relations all have rank 8 [P, 5.2] | needs a new prefix; no construction |
| R2 semi-member top | 13 (or 12) top products from the 107k semi-members + members, junk capacity 5 | >= 10 [C]; search space 85x the member model | **most promising unexplored, uses existing exact tools** |
| R3 merged prefix | compute n = x^-17 directly with < 14 ANDs (odd-degree intermediates) | degree bound 8, construction 14; unknown | open sub-problem, well defined (8 -> 4 bits); SAT infeasible, needs an idea |
| R4 quadratic operands | y = x^33 n^2, 2 junk pieces instead of 3 | >= 32 as a pure route | no |
| R5 other factorisations | x^-1 = u v with v in a small space | only multiples of 17 / 85 give < 8-dim factors [P]; GF(4) route 35+ (H4) | no |
| R6 small-field analogy | learn the structure of exact optima for n = 4, 5, 6 | n = 4 done; n = 5 in [9, 11] | cheap, queued (section 7) |

### 5.1 Two-factor monomial routes [P]
x^-1 = x^a x^b needs wt(a) + wt(b) >= 7 and the coordinate space of x^b has dimension = size of the
cyclotomic class of b: 8 unless 17 | b (4) or 85 | b (2). Two 8-dim factors mean an F x F product
(bilinear rank >= 15 > 13; a bilinear count, so [H] as a statement about junk-using layers). So K (and
GF(4), H4) are the only cheap monomial routes; everything else must be a non-monomial identity.

### 5.2 Why chained tops do not follow from xy = 1 [P]
x_i y_j has exponents 2^i - 2^j: classes of 2^d - 1, d = 1..7; d = 7 is the target class (x^128 y = y^128)
and d = 1 is linear (x^2 y = x). But Tr(c x^128 y) as a tensor in x (x) y has rank 8 (the y-forms
Tr(c e_i y) span everything), so one output bit costs 8 products of known outputs: no shortcut. Same for
y N = x^16 (K-product, 9). The GF(16) chains are not of this algebraic type.

## 6. Critique of H1-H4 (as sent to the coordinator)

02:30 UTC (status files of 02:20-02:30):
* H1 Theorem 1, the swap neighbourhoods and H2's gen13 were inside the 1275-member model, which came from
  observing the A28 files, not from a proof: label "[.., 1275-member model]". (H1 added the label at
  03:00, section 7.0 of its notes, and a section 8 on semi-members.)
* H3: every slack > 1 window restricts new classes to Sigma_U, the old 13-dim span; with U = all sinks
  that only re-arranges the existing junk space. The slack-1 chain results are exact as stated.
* H4: the AD3 work serves goal F; "no design <= 30 outside the tower" is constructions only.
* All: "three-stage is universal [C on 63 files]" is a sample of 3 independent designs and descendants.
02:45 and 02:50: SEMI.md; correction of the type counts; "12 members + 1 semi-member" is vacuous.
05:00: see section 8.

## 7. Queue
QUEUE.md entry "X3: small-field inversion from scratch" (1 CPU, low priority): BoolFlux from the ANF on
GF(32), GF(64), GF(128) inversion (`queue_small.sh`), to get verified upper bounds next to the exact lower
bounds above. Not queued: the 9-AND GF(32) enumeration (needs a faster product enumerator, unvalidated).

## 8. Critique of H1-H4, X1/X1b, R1/R2 (X3b, sent 04:30 UTC; notes as of 03:20-04:15)

Over-claims:
1. X1 NOTES 1 "[C] flips and redec do not change span{1, x, products}": false for redec (one new dimension cb,
   section 10.1). X1b now filters by U (X1 NOTES 8), but section 1 still states it.
2. "Three-stage is universal" and "every A28 top layer is 13 GF(4)-norm members" (H1 1, [C on 63 files]):
   the 63 files are 3 independent designs plus descendants. Every 28 found tonight is three-stage because
   every generator preserves it (gen13 = member model; walks, windows and joins from three-stage starts), so
   it is no evidence. "13 members" already fails outside the 63: spangen A28s (11 + singleton pair), X1b g158
   (12 + singleton pair carrying its U's x^5 direction).
3. H1 8 "no 27 of the form 9+5+12+1 (whatever stage the extra AND belongs to)": fixed prefix, operands in O2.
   It excludes extra ANDs reading stage-1 products, members or outputs, and re-chosen stage 1s. H1 9 and
   H3 R8 are fixed-prefix too. Shown concretely in 10.3: fixed prefix gives no product (O2 and OV); stage 1
   free gives completions, and only the U' test kills them.
4. H4 "no design outside the GF(16)-tower pattern reaches 30": a statement about 6 constructions, not [C].
5. H3's sidecar for 28/5/210/31: "how: chain slack-1 re-solve", but the method is deep2 amax 1.
6. G's cover_sat SAT branch (l - dim U >= 3) times out on positive controls (`x3b_covctl.py`), so its
   None/False answers are undecided; only pair enumeration (l - dim U <= 2) is exact. Own error: X3b's 04:05
   "one forced U'" came from a key bug (corrected in 10.3).
Boxed-in assumptions: (a) stage 1 fixed to published spans in nearly all exact runs, while H2 5.5 shows
12-member layers are plentiful once x-junk is free, so the problem is the joint layer + 9-cover of U;
(b) middle = BMP or a published middle, single gamma; "BMP WLOG" is proved for members only (H2 vjunk), not for
semi/singleton pools; (c) parallel tops with operands in span(x, N, n, mid); no search chains top ANDs
(every optimal GF(16) circuit does, section 2); (d) pools = 1275 members (+ 107k semi); the 2.16M singleton
tensors that real A28s use are touched only by H2's untested qall2.
Most promising unexplored direction [H]: a joint stage-1-free search with x^5-capable pairs. Run gen13
K = 13 over many 9-product covers (H2's queued 2100 Karatsuba covers, H4's 200 generated covers) with members +
free-n-junk singleton pairs (`x3b/singleton_classes.npz`), and judge each hit by the 9-cover of its U.
Evidence: X1b g158 is the only 28 whose U has an x^5 direction, and that direction comes from such a pair.
Second: chained tops (no tool exists).

## 9. Failures and pitfalls
* Plain CHM SAT: GF(16) k = 4 (UNSAT) did not finish in 100 s on the shared CPU; GF(32) k = 6 neither.
  Not used for n >= 5.
* `sa.c` (fixed-K annealing on the rank deficit): solves GF(16) K = 5 in 7 s, stalls at deficit 3-4 for
  GF(32) K = 8..10 (2.5 M moves each). Confirms G 2.1: deficit-scored search is useless beyond 4 bits.
* `skel4.py` in Python is too slow for l = 3, 4 on a shared CPU (timeout); `bil.py` likewise (replaced by
  `bilc.c`).
* `zcos.c` first version: macro self-initialisation bug gave one residue; fixed, then validated against
  `bilc`.
* CPU 12 is shared by about six processes (10-17 % each); all timings here are wall times on that share.
* (X3b) `wsl.exe -- bash -lc '...$f...'` expands `$f` / `$O` in the outer login shell (empty): loops and
  variables must live in script files (`x3b_*.sh`). Two docstrings had invalid escapes `K \ GF(4)`
  (SyntaxWarning only); made raw strings 03:05 UTC. Checker: `x3b_check.sh`.

## 10. X3b (took over from X3 at about 03:05 UTC 2026-11-15)

X3 stopped at a usage limit; X3b continues in this directory with the same labels. Tools added:
`x3b_check.sh` (syntax check), `x3b_tocirc.py` (.bfx -> NCFF), `x3b_junk.py REF FILE... [--cover]`
(per-level span overlap with REF, H1's U = V_N + S1-parts of the outputs, junk coordinates
(c3, c5, c9) of stage 1 and of U, per-level output parts, exact 9-cover of U via G's `cover_sat`),
`x3b_v0ops.py` (V0 parts of top operands beyond span(1, N, n)), drivers `x3b_run1-3.sh`.
Logs: `~/xs-campaigns/2026-11-15-study/X3/x3b/` (run2.log = decomp + tensors, run3*.log = junk).

### 10.1 H3's A28 28/5/210/31 and X1's spangen A28s against NIST g124 / g128 [C, these 15 files]

Files: NIST a28-ad5-g124, a28-ad5-g128, H3 `h3-d2-a29-ad5-g134-gd17-7-a28-ad5-g210`, and the 11 polished
spangen outputs `X1/spangen1/span-*.bfx` (one walk from hub a28-ad5-g125; 8 distinct product spans).

| file(s) | per-level span shared with g124 (L1..L5, of 10/11/13/15/28) | top tensors | U vs g124 | junk of U |
|---|---|---|---|---|
| g128, H3 g210 | 10, 10, 10, 14, 22 (H3 = g128 at every level, X1b) | 13 members; H3 = g128's 13-dim tensor span, 10 tensors identical, 3 other members | identical | 3 dims, c5 = 0 |
| spangen 000, 008, 009, 001 | 10, 11, 13, 15, 27 | 11 members + 2 singleton-coset rank-2 tensors (not member, not semi) | identical | same |
| spangen 010 | 10, 11, 13, 14, 27 | 13 members; operands in aff(x) + V0, not in span(1, x, N, n) | identical | same |
| spangen 002, 004, 007 | 9, 10, 12, 14, 27 | 13 members | identical | same |
| spangen 003, 005, 006 | 9, 10, 12, 14, 26 | 11 members + 2 singleton-coset tensors | identical | same |

All 15: three-stage by H1's role test (S1 10 / MID 5 / LAST or LASTV0 13, profile 10|1|2|2|13), A_eff 28,
top tensor span dim 13 with J_t = 5, decomp Jx = 3, dim U = 7, least N-cover within the file 10,
**U is the same 7-dim subspace as g124's** (dim(U cap U_g124) = 7), its junk coordinates have rank 3 with
**no x^5 part** (c5 = 0), and **the exact 9-cover test of U fails for every file** (G `cover_sat`, l - dim U
= 2, exhaustive pair enumeration; control g124 = H1's cond27 result).

What the span changes are [C for the identification, P for the mechanism]:
* **Top redec of g124's equal-usage pair {g17, g26}** (H3's dependent sink pair). In every file with
  non-member tensors, the two singletons sum to 6a7b2973 = tensor(g17) + tensor(g26) of g124
  (6a6a6a30 + 00114343), with four different splits (007b297b + 6a000008, 43620043 + 29192930,
  6a006a73 + 007b4300, 00112938 + 6a6a004b). Mechanism [P]: ab + cd = (a+c) b + c (b+d) replaces
  span{ab, cd} by span{ab + cb, cb + cd}: same sum, one new dimension (cb), hence 27 of 28 shared.
  So X1 NOTES 1 "[C] flips and redec do not change span{1, x, products}" is false for redec (true for
  flips); this is exactly where X1's ">150 new spans" come from in this sample.
* **010: value-at-0 rebracketing in the middle.** The extra V0 part of the top operands (dim 1 mod
  span(1, N, n)) has no N^k coefficient for k = 1..14, i.e. it is the indicator of x = 0
  (1 + x^255), made from middle products 9 + 13. A product l(x) * (v + e delta_0) differs from
  l(x) v by e l(0) delta_0: junk in one fixed direction only [P].
* **002-007: a new 10-product stage 1** (9 of 10 dims shared). Same V_N, same U; its spare part has
  c5-rank 3 instead of 2 (H1's "x^5-projection rank exactly 2" holds on the 63 files it covers, not for
  every A28), but the c5 = 0 part of the spare space is still 3-dim, so H1's "capacity 3" is unchanged.

Reading:
* [C] H3's A28 is a member re-basis of g128 (no semi-members, no non-members); its G = 210 is the rebuilt
  XOR network. Only basis-dependent quantities differ: its outputs take 2 dimensions of V_N directly
  from stage 1 (S1-parts span 5 dims vs 3 in g124), which is free. No new junk direction.
* [C, these 11 outputs] X1's spangen spans are not new junk structures: U, J_t, the tensor span and the
  9-cover verdict are those of g124. Their non-member tensors (outside the 1275 and the 107,100) are
  a real exception to "every A28 top product is a member", but they only enter as a pair with a
  member-coset sum (consistent with H1 Lemma S / SEMI.md 8: non-member products need a partner).
* [P] Any 28 with g124's U inherits "U not 9-coverable", so none of these opens 9+5+13 by shrinking
  stage 1. Neither changes the top layer's junk, so neither opens 9+5+12 or 10+5+12 [H].
* [H] To use X1b's walk for goal A it should be filtered by U (or by the junk coordinates of U, in
  particular c5 != 0), not by the span hash: `x3b_junk.py REF FILE...` gives this in about 1 s per file.

### 10.2 Singleton-coset pairs: the family the member and semi-member pools miss [C, gamma = 0 witnesses]

SEMI.md 7 said singleton-coset tensors are "not suggested by any structure". X1's spangen A28s use two of
them per layer, as a pair whose cosets sum into M8 (all four pairs: coset sum 00fbd4d4, a member coset).
So the next family after semi-members is **pairs of singleton-coset tensors in one class mod M8**
(the relation "singleton + singleton + member", SEMI.md 8 (b) with coset size 1).
`x3b_pairs.py` (all 2,270,775 rank <= 2 tensors, reproduces the coset histogram of SEMI.md 2):
* the 2,162,400 singleton tensors lie in 65,025 of the 65,535 nonzero classes mod M8 (none in M8), 6-244
  per class (median 30): **64,458,900 compatible pairs**, against 252,450 + 68,850 for semi-members.
`x3b_pairjunk.py` (witness (l_u1 + lam_v2)(l_u2 + lam_v1); x-junk = l_u1 l_u2 depends only on the
x-plane, n-junk = lam_v1 lam_v2 only on the n-plane, both mod linear):
* none of the 35 n-planes has n-junk in span(1, N, n) by itself (36 distinct residues incl. 0, i.e. each
  plane its own); a pair's n-junk sum is free iff both have the same n-plane (or both rank 1):
  **36,876,825 compatible pairs with free n-junk sum, of which 36,414,000 have an x^5 component in the
  x-junk sum** (c5 != 0) - the junk direction members never have (SEMI.md 4) and H1's capacity-3 limit
  is about.
* Not checked: gamma != 0 witnesses, x(x)N cross terms, middle classes beyond BMP, and whether any such
  pair fits a 9-product stage 1. These are the necessary first filters, not a construction.
[H] Reading: the exhaustive 12/13 results of C, H1, H2 cover the 1275 members (and H2's member-seeded
semi runs <= 4 semi-members); none covers layers with singleton pairs, and real A28s are not inside the
member model once redec is applied. The family is about 200x larger than the 321,300 semi pairs (115x with free n-junk) but has the same
structure (pairs with a member-coset sum), so gen13 with pair seeds (as H2's class-seeded gen13c)
applies directly; the data file `x3b/singleton_classes.npz` (tensor, coset, class) is the input.

### 10.3 H2's 9 + 5 + 14 (h2-ad4a-g1-c8c7227f-s59 / s58): how far from 27 (04:00 UTC, coordinator request)

Structure [C, x3b_junk / decomp / layer_tensors]: stage 1 = AD4 g131's level-1 span (9 of 9 shared), BMP
5-AND middle (J0 = 0; g131 itself has a 6-AND middle and J0 = 1), 14 GF(4)-norm members, gamma g^34, tensor
span 14, J_t = 6, **U = g131's U exactly** (dim 6, junk 2, c5 = 0). So H2 trades g131's 6th middle AND for
a 14th member: 9 + 6 + 13 -> 9 + 5 + 14, same U.
Windows (`x3b_dropk.py`, `x3b_drop.py`; d_b = missing output dims after dropping W, stage 1 free, i.e. all
x-quadratics allowed, middle and the other members fixed):
* every single member: d_b = 1 (no member is redundant even with any stage 1) [C];
* exactly one slack-1 pair, members (6, 7) = ANDs 20, 21 (s58: (5, 6)); slack-1 triples (2, 4, 12), (3, 4, 5)
  and 11 more containing (6, 7); 90 quadruples with d_b = 3; three 5-sets with d_b = 3 (slack 2).
12 + 1 on the pair (= 9 + 5 + 13 = 27 if it closed):
* fixed prefix (H1 fixk.py, the file's own stage 1 + middle): no single product, operands in O2
  (span(1, x, N, n, middle), 2^18) or OV (aff(x) + all functions of N, 2^24, `x3b_fixk_ov.sh`) [C];
  positive control: dropping one member, fixk re-finds it.
* stage 1 free (`x3b_fixkq.py` = fixk with Quad in place of the stage-1 products): completions exist.
  **CORRECTION 04:20:** `x3b_cand.py` / `x3b_cand2.py` keyed U' by `U.nf(q)` for q in U (always 0), so they
  reported "one U'" and cover-tested only the first U' of each run. Superseded by `x3b_cand3.py` (exact
  linear junk, distinct U' keyed canonically, every U' tested; validated: same products and dims as cand/cand2).
  Results with cand3 (O2 = span(1, x, N, n, middle), every l, all m in the kernel coset) [C]:
  pair (6, 7): 16 products, **4 distinct U', all dim 7, none 9-coverable** (exact pair enumeration);
  s58 pair (5, 6): 64 products, 12 U', all dim 7, none 9-coverable. So the pair -> 1 move gives at best
  10 + 5 + 13 = 28. OV for the pair: completions only in 2 of 16 blocks of 2^20 l, but their U' were
  tested with the buggy key only -> rerun in the QUEUE.md job "X3b" (`--ov`).
11 + 2 on the triples (cand3, O2, stage 1 free): (2, 4, 12): 8 / 24 / 40 products per T-bar class, 1472 pairs,
92 distinct U', all dim 8, none 9- or 10-coverable; (3, 4, 5): 0 / 64 / 32, 2048 pairs, 119 U' (dim 7: 32
pairs, dim 8: 2016), none 9-coverable (exact), none 10-coverable (exact for dim 8; SAT for dim 7) [C].
Not covered: OV for the triples; quadruples (10 + 3) and the slack-2 5-sets; extra products reading stage-1
products or other members (chains); a different middle (5-AND middles other than BMP: G's 30 classes).
[H] Reading: in every window tested the AND saved in the layer reappears as junk (dim U 6 -> 7 -> 8) that stage
1 must pay for: the layer/stage-1 trade is conserved, as in A28-AD5 (10 + 5 + 13, U dim 7). The slack-2
5-sets (d_b = 3 for 5 dropped) are the only windows that could save two layer ANDs and survive one extra
stage-1 product (10 + 5 + 12 = 27); they are the natural next test (needs a d = 3 completion search).

### 10.4 Slack-2 and all minimal windows k <= 5, stage 1 free: s59, s58, X1b g158 (04:05-04:20 UTC) [C, O2]

Tool `x3b_cand3.py FILE W O [LIMIT] [MAXC]` (any d <= 4): products per T-bar class as above; U' computed by
linearity (U' = V_N + span_i(q(e_i) + sum_j alpha_ij q(p_j)), q = quadratic part in Quad / V_N coordinates,
alpha from the classes; D = 0 in every window, so U' is forced per completion); every distinct U' tested
for a 9- and a 10-cover; a completion with predicted total <= 27 is built and aes_checked automatically
(G `build_tables` + `campaigns/aes_check.py`). **Build-path control:** s58 W = (0, 8, 10) (16 completions with
a 10-coverable U' of dim 8, predicted 10 + 5 + 11 + 2 = 28) built with X3B_BUILD_MAX=28: verified A28,
28/6/594/30 (`X3/found/x3b-h2-ad4a-g1-c8c7227f-s58-a28.ci-drop0-8-10-1794716278.circ.txt`; dominated).
Cover-test exactness: G's SAT cover path (l - dim U > 2) times out on both positive controls (g124's U
with l = 10, g131's U with l = 9, 45 s; `x3b_covctl.py`), so only the pair-enumeration answers
(l - dim U <= 2) count: 9-cover exact for dim U' >= 7, 10-cover for dim U' >= 8.
Minimal slack windows (`x3b_dropk.py FILE 5 min`):
* s59: (6,7); (2,4,12), (3,4,5); (0,1,4,9), (2,3,5,12); slack-2 5-sets (2,3,4,5,12), (2,4,6,7,12), (3,4,5,6,7); 7 more
  5-sets with d = 4.
* s58: (5,6); (0,8,10); (1,2,4,12), (1,3,10,12), (2,3,4,10); slack-2 (0,5,6,8,10); 7 more 5-sets with d = 4.
* X1b g158 (9|1|2|2|14, U dim 7 with an x^5 junk direction (c5 rank 1), 9-coverable; top = 12 members + a
  singleton pair AND18 (rank 2) + AND19 (rank 1) with coset sum 00863e3e = a member coset, i.e. a 10.2 pair):
  (4,5) = exactly that pair; (7,8,13), (8,10,11); (7,10,11,13); slack-2 (4,5,7,8,13), (4,5,8,10,11), (7,8,10,11,13).
Results (O2, stage 1 free):

| file | window | d | completions | distinct U' | dim U' | 9-cover | 10-cover | best total |
|---|---|---|---|---|---|---|---|---|
| s59 | 2,4,6,7,12 | 3 | 640 | 10 | 9 | no | no | - |
| s59 | 2,3,4,5,12 / 3,4,5,6,7 | 3 | 0 | - | - | - | - | - |
| s59 | 0,1,4,9 | 3 | 27,904 | 433 | 9 | no | no | - |
| s59 | 2,3,5,12 | 3 | 42,240 | 618 | 8-9 | no | no | - |
| s58 | 5,6 | 1 | 64 | 12 | 7 | no | (SAT) | - |
| s58 | 0,8,10 | 2 | 1,792 | 107 | 7-8 | no | yes (16, dim 8) | 28 |
| s58 | 0,5,6,8,10 | 3 | 0 | - | - | - | - | - |
| s58 | 1,2,4,12 | 3 | 0 | - | - | - | - | - |
| s58 | 1,3,10,12 | 3 | 57,344 | 874 | 7-9 | no | yes (64, dim 8) | 28 |
| s58 | 2,3,4,10 | 3 | 49,152 | 706 | 7-9 | no | no | - |
| g158 | 4,5 | 1 | 64 | 12 | 7 | no | (SAT) | - |
| g158 | 7,8,13 / 8,10,11 | 2 | 0 | - | - | - | - | - |
| g158 | 7,10,11,13 | 3 | 0 | - | - | - | - | - |
| g158 | the three slack-2 5-sets | 3 | 0 | - | - | - | - | - |

d = 4 windows (k = 5 with 4 replacements, 9 + 5 + 13 = 27 iff some U' is 9-coverable; 10-cover skipped as it
gives 28), 04:22-04:40 UTC:
* s59, all 7: (0,1,2,9,12) 835,584 completions (U' dim 9: 2,048, dim 10: 833,536), (0,1,3,5,9) 622,592,
  (0,6,8,10,11) 1,679,360, (0,7,8,10,11) 1,656,832, (1,5,6,11,13) 974,848, (1,5,7,11,13) 1,656,832 (dims 8-10),
  (3,8,9,10,13) 839,680: **no 9-coverable U'** (dim 8-9 ones tested exactly; dim 10 impossible).
* s58, all 7: (2,3,5,11,13) 1,245,184, (2,7,8,9,13) 1,572,864, (4,6,10,11,13) 1,245,184 completions, none 9-coverable;
  (0,1,3,8,12), (0,2,3,4,8), (2,3,6,11,13), (4,5,10,11,13): no completion.
* g158, all 5: no completion.
OV for the s59 pair (6,7): the complete 2^24-l scan (x3b_cand, hit detection correct) found products only in
blocks 0 and 6; cand3 on both blocks: 16 products each, 4 U' of dim 7, none 9-coverable [C].
**So for s59, s58 and X1b g158, every minimal slack window with k <= 5 has no completion giving 27** [C, O2
operands (OV for the s59 pair), the file's own middle, the other top products kept, stage 1 = any 9 (or 10)
level-1 products; truncation: none (largest 1.68M of the 3M cap), kernel dims 2-3 (cap 10)].
Not covered: windows k >= 6; OV except the s59 pair; new products with stage-1 products or top products as
operands (chains); other middles; the other ~60 9+5+14 files (QUEUE.md "X3b", `x3b_night.py`). Not covered at all: chained new products (reading
kept top products or stage-1 products), a different middle.
[H] Pattern: whenever a window frees an AND, the forced U' grows by at least one dimension beyond what 9
products cover; the 10-coverable cases reproduce 28. The trade "one top AND <-> one junk dimension" held in every
window here and in H1 section 9 (fixed prefix).

### 10.5 Pair windows of all built 9+5+14 / 10+5+13 files (04:43-04:58 UTC) [C, O2, stage 1 free]

`x3b_night.py SHARD 20 --kmax 2 --tag day-pairs` (20 short xsfg jobs; logs `X3/day-pairs/shard*.log`,
summary `x3b_daysum.sh`): 86 files (73 H2 `H2/found/h2-*-a28`, incl. 3 AD5-type 10+5+13 and one AD4-middle file;
13 X1b `X1/x1b/*/found/aes-sbox-a28-*`). 18 have no slack pair; 68 pair windows were run: 52 have completions
(16 or 64 products), **every one gives U' of dim 7, none 9-coverable** (exact); 16 have no completion.
No 27 from any 12 + 1 pair move in these files. Triples and larger windows of the other 83 files: QUEUE.md "X3b".
