# Semi-members: the rank <= 2 tensor view of the top layer (X3, 2026-11-15)

Self-contained reference for H1 / H2. Labels: **[P]** proved here, **[C]** exhaustive computation in the
stated case, **[H]** opinion. Code: `strategies/X3/`; data: `~/xs-campaigns/2026-11-15-study/X3/`.

## 1. Definitions

F = GF(2^8) (0x11B), K = GF(16), Q = GF(4), N = x^17, n = N^-1 = x^238 (n(0) = 0), V0 = functions of N.
Tr = trace F -> GF(2), Tr_K = trace K -> GF(2). T = span of the 8 outputs Tr(b x^-1).

* **x(x)n tensor.** The 32 functions Tr(A x) Tr_K(e n) span a 32-dim space B (independent: checked on
  truth tables, `bil_tb.py`). Its univariate exponents are 2^i - 17 2^j: the four cyclotomic classes of
  127, 15, 47, 111. An element of B is a 4 x 8 GF(2) matrix (a GF(2)-linear map F -> K);
  **rank** = rank of that matrix. T_b = the outputs = the K-linear maps (dim 8). [C] all 255 nonzero
  elements of T_b have rank 4.
* **Tensor of a product.** For operands l + g, l' + g' with l = Tr(A x) + c, l' = Tr(A' x) + c' and
  g, g' in V0, write lam_g = the n-linear component of g (the part Tr_K(e n); V0 splits over GF(2) into
  the classes of N^k, and n-linear = k in {7, 11, 13, 14}). The tensor of the product is
  t = l (x) lam_g' + l' (x) lam_g, of rank <= 2. N-linear parts of the operands (gamma) do not change t.
* **Type** of a rank-2 tensor Tr(A1 x) Tr_K(e1 n) + Tr(A2 x) Tr_K(e2 n): the pair
  (class of A1/A2, class of e1/e2), classes Q = GF(4) \ {0, 1}, K = GF(16) \ GF(4), F = the rest.
  The class does not depend on the basis chosen for the two planes (r, 1/r, r + 1, ... stay in the class).
* **Member** (track C's GF(4)-norm member): type (Q, Q) with the inverse-ratio condition; 1275 tensors.
* **Semi-member**: a rank-2 tensor that is not a member but shares its coset mod T_b with at least one
  other rank <= 2 tensor. [C] these are exactly 107,100 tensors, of types (K, K), (K, Q) and (Q, K).

## 2. Result 1: any parallel top layer in this operand model needs >= 10 products

**Statement [C + P].** Let a circuit consist of a prefix whose ANDs are x-quadratics or functions of N
(any number, any depth) and m further ANDs, each with both operands in aff(x) + V0 (so no top AND reads
another top AND, and no raw stage-1 product is a top operand). If all outputs are in the span, m >= 10.

**Proof.** [P] Let pi be the projection of functions onto the classes 127, 15, 47, 111 (linear, since
functions decompose uniquely by cyclotomic class). pi kills affine functions (class 1, 0), x-quadratics
(weight-2 exponents: classes 3, 5, 9, 17), functions of N (exponents divisible by 17) and the functions
Tr(A x) N^k for k outside {7, 11, 13, 14} (exponents 2^i + 17k; the 112 exponents 2^i + 17k, k = 1..14,
are pairwise different because 2 has order 8 mod 17; k = 15 gives Tr(A x) on x != 0). Hence
pi((l + g)(l' + g')) = the tensor t above, pi(prefix) = 0, pi(output) = itself. So T_b lies in the span of
the m tensors, each of rank <= 2.
[C] (`bilc.c`, exhaustive over all 2,270,775 nonzero tensors of rank <= 2): T_b contains none of them
(m = 8 impossible), and modulo T_b they fall into cosets of size

| coset size | cosets | tensors |
|---|---|---|
| 1 | 2,162,400 | 2,162,400 |
| 2 | 38,250 | 76,500 |
| 3 | 10,200 | 30,600 |
| 5 | 255 | 1,275 |

m = 9 means span = T_b + <j>, and all rank <= 2 elements of that space lie in the single coset j + T_b,
which would need 9 of them. The largest coset has 5. QED.
Independent check [C]: `zcos.c` recomputes the cosets from 256-bit truth tables of the products
(Tr(A1 x) + Tr_K(e2 n))(Tr(A2 x) + Tr_K(e1 n)) modulo Aff + Quad(x) + V0 + T: 2,270,775 distinct residues
and the same histogram.

Not covered: chained top ANDs; top operands containing raw stage-1 products; prefix ANDs of odd degree.
(Adding the 979,200 products (Tr(A x) + z) Tr_K(e n), z a coordinate form of x^33, creates only singleton
cosets [C, `zcos` family 3], so 9 stays impossible with those too.)

## 3. Result 2: at m = 10 the members are forced

**Statement [C].** The 10-dimensional spaces S containing T_b that are spanned by tensors of rank <= 2 are
exactly 10,200, and each is spanned by 15 members (three 5-cosets c1, c2, c1 + c2).

**Proof.** S = T_b + J, dim J = 2, three nonzero cosets, which must hold >= 10 tensors: sizes are in
{0, 1, 2, 3, 5}, so one coset has 5. `bil10.py` enumerates every plane J containing a 5-coset and a second
coset of size 5 or 3 with >= 10 tensors in total, and computes the rank of all its tensors:

| coset sizes | planes | rank of the tensors |
|---|---|---|
| (5, 5, 5) | 10,200 | 10 |
| (5, 5, 5) | 595 | 6 (one K-line: 17 lines x 35 planes) |
| (5, 3, 3) | 15,300 | 6 |
| (5, 3, 2) | 61,200 | 6 |

Only the first row spans a 10-dim space. (The sum of two 5-cosets is always a 5-coset.) 10,200 is the
number H2 found inside the member family. With H2's junk result (10-member layers have x-junk 8 and
v-junk 4 at gamma = 0) this closes m = 10 at gamma = 0. **For m >= 11 nothing forces members.**

## 4. Result 3: which tensors share a coset, and what their junk is

**[C] (`semi.py`, `semi_export.py`)** Types of the tensors in cosets of size >= 2:

| coset size | cosets | content of each coset | tensors |
|---|---|---|---|
| 5 | 255 | 5 of type (Q, Q) = members | 1,275 |
| 3 | 10,200 | 3 of type (K, K) | 30,600 |
| 2 | 22,950 | 2 of type (K, K) | 45,900 |
| 2 | 15,300 | 1 of type (K, Q) + 1 of type (Q, K) | 15,300 + 15,300 |

No tensor with an x-ratio or n-ratio outside K shares a coset. So the semi-members are 107,100 tensors:
91,800 with x-plane {A, kA}, k in K \ GF(4) (the x-plane lies in a K-line A K but is not a GF(4)-line),
and 15,300 with a GF(4)-line x-plane but n-ratio in K \ GF(4).
(Correction to my 02:30 message, which said all 107,100 have x-ratio outside GF(4).)

**[P] x-junk.** With u = Tr_{F/K}(A x) (so Tr(A x) = Tr_K(u), Tr(kA x) = Tr_K(k u), k in K):

    Tr_K(u) Tr_K(k u) = Tr_K(k u^2) + Tr_K((k + k^2) u^3) + Tr_Q((k + k^4) u^5)

(expand both traces, group by d = j - i; d = 1 and d = 3 give the u^3 terms, d = 2 the u^5 term, and
u^5 = N_{K/Q}(u) is in Q). As functions of x: u^3 has classes 3 and 9, u^5 = N_{K/Q}(Tr_{F/K}(A x)) has
only class 5 (exponents (1 or 16) + (4 or 64): 5, 65, 20, 80). In track C's notation the junk components
are C1 = A^3 (k + k^2), **C2 = A^5 (k + k^4)**, C3 = A^9 (k + k^8), C4 = 0. So:
**the x-junk has an x^5-component exactly when k is outside GF(4).**
Numerical check [C] (`semi_check.py`): coefficient of x^5 equals A^5 (k + k^4) for 5 values of A and all
14 k in K \ {0, 1}; it is 0 for k in {w, w^2} only.
The same identity with u = e n gives the n-junk Tr_K(e n) Tr_K(k' e n): its N^10-type part
Tr_Q((k' + k'^4)(e n)^5) is present exactly when the n-ratio k' is outside GF(4).

**Why this matters [H, uses H1's numbers].** H1: every known stage 1 spans V_N plus 5 spare dimensions whose
x^5-projection has rank exactly 2; member junk has C2 = 0, so members can use at most 3 spare dimensions
("capacity 3"), and A28-AD5 fails to be 9+5+13 only because its 3 junk dimensions are not 9-coverable.
Type (K, .) products reach the two x^5 dimensions. The capacity-3 limit is a property of the member
family, not of the stage.

## 5. Files

* `~/xs-campaigns/2026-11-15-study/X3/semi_members.tsv`: 108,375 lines (members + semi-members):
  `tensor coset coset_size A1 A2 e1 e2 xclass nclass` (hex; classes Q / K as above). Witness product at
  gamma = 0: **(Tr(A1 x) + Tr_K(e2 n)) * (Tr(A2 x) + Tr_K(e1 n))**; its tensor is
  Tr(A1 x) Tr_K(e1 n) + Tr(A2 x) Tr_K(e2 n). Tensor bit 8j + i = coefficient of x_i * (bit b_j of n),
  x_i = bit i of the integer x, (b_0..b_3) = (0, 2, 4, 5).
  Checked [C] (`semi_verify.py 400`, 122 cosets, 142 pairs): two witnesses of one coset differ by a
  nonzero output combination modulo Aff + Quad(x) + V0.
* `bil_cosets2.txt`: the same cosets as `C coset size t1 t2 ...`; `bil_tb.txt`: echelon basis of T_b.
* gamma: to move to v = n + gamma N add Tr_K(e gamma N) to the operand next to each Tr_K(e n); the
  tensor and the coset are unchanged, the junk gets x(x)N terms (class 9 = x-quadratic, plus cubic terms
  that must cancel), exactly as for members.

## 6. Facts about relations over a fixed prefix (gamma = 0) [C]

Prefix E = umizame's 14 ANDs (NIST a29-ad5-g137), products = the gamma = 0 witnesses:
* all 2,270,775 products are pairwise different modulo span(1, x, E) + T (`zcos` with J = prefix): no two
  products differ by an output combination;
* sample (the first 3000 of the 108,375 members + semi-members against all others, `lines.c`): 246,436
  triples sum into span(1, x, E) + T, and every one of them sums into span(1, x, E) itself (no output
  part). So useful relations have at least 4 terms on this sample.

## 7. What is not claimed

* Nothing here shows that a 13-product layer with semi-members exists; it shows the member model is a
  strict subfamily with a provable limitation (C2 = 0) and gives the smallest natural extension.
* The coset tables are for the x(x)n part only; junk feasibility (9-cover of U, middle classes) is the
  job of the existing exact tools (cond27 / nfast, gen13, zdfs, eval3).
* Tensors in singleton cosets (2,162,400, all other types) are not excluded for m >= 11 either; they are
  simply not suggested by any structure.

## 8. How a semi-member can enter a layer: relations among cosets [C, `semi_mod.py`]

A product appears in an output combination only through a linear relation among the cosets (mod T_b) of the
layer's tensors. The 255 member cosets and 0 form an 8-dim subspace M8 of the 24-dim quotient.
* No semi-member coset lies in M8. **So one semi-member added to a set of members is in no relation and is
  useless ("12 members + 1 semi-member" is vacuous).**
* Modulo M8 the 48,450 semi cosets fall into 4,335 classes: 2,550 classes with 10 cosets, 1,275 with 12,
  510 with 15; together they span the whole 16-dim quotient.
* Minimal meaningful uses: (a) two semi-members of one T_b-coset (sum = output combination + junk);
  (b) two semi-members whose cosets lie in one class mod M8: the coset sum is a member coset c, and the
  layer needs member tensors of coset c (3-term relation semi + semi + member).
* File `~/xs-campaigns/2026-11-15-study/X3/semi_classes.tsv`: coset, class mod M8 (0 for member cosets),
  coset size. Two semi-members are compatible in sense (b) iff their cosets have the same class.

## 9. Positive control on real circuits [C, `layer_tensors.py CIRCUIT`]

The tensor of every sink AND is read off the truth table (unique expression in
Aff + Quad + V0 + x(x)N + x(x)n), so this also covers gamma != 0.

| file | sinks | ranks / types | tensor span | dim J_t | T_b in span |
|---|---|---|---|---|---|
| NIST a28-ad5-g124 | 13 | 13 members (type (Q,Q), 5-cosets; 11 distinct cosets) | 13 | 5 | yes |
| NIST a29-ad5-g137 (umizame) | 15 | 15 members (5 distinct cosets, 3 members each) | 12 | 4 | yes |
| NIST a32-ad4-g117 | 17 | 15 of rank 1 + 2 of rank 2, all in singleton cosets (not members, not semi-members) | 17 | 9 | yes |

So the known 28s and 29s are pure member layers with all cosets in M8, and the A32-AD4 family (same
type as the hub A31s) is the only known use of tensors outside the member cosets.

Size of the smallest new case ("11 + 2", section 8 (b)): pairs of semi cosets in one class mod M8:
2,550 x 45 + 1,275 x 66 + 510 x 105 = 252,450 coset pairs (each coset holds 2 or 3 tensors); in-coset
pairs (section 8 (a)): 22,950 + 15,300 + 3 x 10,200 = 68,850.

## 10. Does the x^5 junk survive in a relation? [C, `semi_c5.py`]

For two tensors of one T_b-coset the output combination they give carries the sum of the two x-junks.
x^5-component of that sum (C2 = A1 A2^4 + A1^4 A2 per tensor):

| coset size | types of the pair | pairs with x^5 cancelling | pairs with x^5 present |
|---|---|---|---|
| 5 | (Q,Q), (Q,Q) | 2,550 (all) | 0 |
| 3 | (K,K), (K,K) | 7,650 | 22,950 |
| 2 | (K,K), (K,K) | 15,300 | 7,650 |
| 2 | (K,Q), (Q,K) | 0 | 15,300 |

So both kinds exist: 45,900 in-coset pairs give an output combination whose x-junk has an x^5 part (these
are the ones that can use the x^5 dimensions of a stage 1), and 22,950 semi pairs behave like members in
this respect.

Stage-1 side [C, `s1planes.py`]: every level-1 product of NIST a29-ad5-g137, a28-ad4-g131, a28-ad5-g124
and a32-ad5-g104 has operand ratio outside K (type F; necessary for an N-component, since a K-ratio plane
has C4 = 0). So no member or semi-member junk form equals a stage-1 product; junk is only ever absorbed
by combinations.
