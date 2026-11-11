# Cyclic systems versus circuits

Report of the delegated investigation of 2026-11-11 (machine work; no human review, nothing
formalized), saved by the main agent from the investigator's final message. Status words as in
`../README.md`. "Exhaustive" means a program tried every case of the stated finite family; the programs
are in this directory. The main agent re-ran `min_example.py`, `examples_verify.py` and
`mc_reencode.py` and checked Example 1 and Theorems C(i) and W by hand; the audit of section 3 has had
no second review.

## 0. Answers

1. **L_cyc(M) < L(M) is possible** (proved; verified by two independent programs). Smallest case:
   n = 5, six target rows, L_cyc = 6, L = 7 (Example 1); a 5-row subset has the same values. It is
   smallest in three senses: no counterexample has n <= 4, none has L_cyc <= 5 (Theorem B, by hand), and
   at n = 5 none has fewer than 5 rows (exhaustive). Invertible matrices: none at n = 5 (exhaustive),
   first at n = 6 (Example 2: L_cyc = 7, L = 8). MixColumns flavour (invertible, all rows and columns
   odd, no short relation): none at n <= 6 (exhaustive), examples at n = 7 (Example 3: L_cyc = 10,
   L = 11).
   Structural reason: a cyclic system is a set of 3-term equations that determines every value
   uniquely; a circuit is such a system that can moreover be solved one equation at a time. The first is
   "the equation matrix is invertible over F_2", the second "the equation matrix is triangular after
   permutation". Feedback loops are invisible to F_2-rank arguments.
   L_cyc = L is proved for: one or two target rows; n <= 4; L_cyc <= 5.
2. **Audit.** No lemma of PROOF.md uses the order of the gates essentially. Ten of them are *written*
   with the order (1.1, 2.1, 3.1, 3.2, 4.1, 4.4, 7.1, 7.3, 7.4, 10.3(ii)); each has an order-free proof
   (section 3). Read with the dictionary of section 3.1, PROOF.md proves **L_cyc(MixColumns) >= 75**
   (conditional on PROOF.md being correct for circuits and on this audit). Since L_cyc is the same for
   a matrix, its inverse, its transpose and every re-encoding (Theorem C), the same argument gives
   L >= 75 for InvMixColumns and for every other systematic form of the same code. The method cannot
   separate MixColumns from these, and cannot prove more than L_cyc(MixColumns) <= 88.
3. **What detects the difference** (Theorem W, proved): in a circuit every nonempty set of gate
   equations contains a non-input signal that occurs in exactly one of them; a cyclic system only
   guarantees a signal that occurs an odd number of times. Equivalently a circuit stays uniquely
   solvable when its equations a + b + c = 0 are given arbitrary nonzero coefficients over any field
   with at least three elements; a non-circuit cyclic system does not. Whether L_cyc < L for
   MixColumns itself is open; on the recorded circuits both MixColumns and InvMixColumns stand at 88.

## 1. Definitions

Vectors live in F_2^n; e_1..e_n are the unit vectors (the inputs); E = {e_1, .., e_n}.

* For a finite set S of distinct nonzero vectors, R(S) = { rho in F_2^S : sum_s rho_s s = 0 } is its
  relation space. If S spans F_2^n then dim R(S) = |S| - n.
* A **triple** of S is a 3-subset {a, b, c} of S with a + b + c = 0. As a formal vector it is a
  weight-3 element of R(S).
* S (containing E) is a **cyclic set** if its triples span R(S). Its size is |S| - n. A cyclic system
  for M is a cyclic set containing the rows of M. L_cyc(M) is the least size.
* S (containing E) is a **circuit set** if the closure of E under "two points of a triple of S are in,
  so the third is in" is S. The mask set of a normalized circuit with G gates is a circuit set of size
  G and conversely. L(M) is the least size of a circuit set containing the rows of M.
* A **based cyclic system** (S, T) is a cyclic set with a chosen basis T of R(S) made of triples
  (|T| = |S| - n). The gate equations of a circuit are such a basis.

All statements are about sets of *distinct* vectors unless "multiset" is said.

## 2. Can L_cyc be smaller than L?

### 2.1 Proposition 1 (three descriptions). Proved.

(a) S is cyclic iff there are G = |S| - n triples whose G x G incidence matrix on the columns S \ E is
invertible over F_2.
(b) (Multiset version.) Let formal variables v_1..v_(n+G) and G three-term equations be given, the
first n variables being the inputs, such that the G x G matrix on the non-input variables is
invertible. Then every variable has a determined value in F_2^n, and the set of distinct nonzero
values is a cyclic set of size <= G. So allowing repeated or zero vectors does not change L_cyc.
(c) S is a circuit set iff there are G triples whose matrix on S \ E becomes triangular with nonzero
diagonal after a permutation of rows and columns.

*Proof.* (a) Restriction of R(S) to the coordinates S \ E is injective (a relation among unit vectors
is zero) and dim R(S) = |S \ E|, so it is bijective; the triples span R(S) iff G of them are
independent iff their restrictions are. (b) Let W be the multiset of values and pi: F_2^W -> F_2^S send
the coordinate of a variable to the coordinate of its value (to 0 if the value is 0). pi maps R(W)
onto R(S). The G equations are independent elements of R(W), of dimension G, so they span it. The image
of an equation is a triple of S if its three values are distinct and nonzero, and 0 otherwise. Hence
R(S) is spanned by triples, and |S| - n <= G. (c) An order "each new element is the sum of two earlier
ones" is exactly a triangular arrangement. QED

### 2.2 Theorem A (anatomy of a cyclic set). Proved.

Let S contain E, S' the closure of E in S, Q = S \ S'. Let Gamma be the graph on Q with q ~ q' iff
q + q' is in S', c its number of components, and for a triple T inside Q let chi(T) in F_2^c be the sum
of the unit vectors of the components of its three points.

(a) S' is a circuit set; every triple of S meets Q in 0, 2 or 3 points.
(b) S is cyclic iff the chi(T), T over the triples inside Q, span F_2^c.
(c) If {q1, q2, q3} is a triple inside Q, any two of its points are in different components of Gamma
or at distance >= 3 in Gamma.

*Proof.* (a) Closure. (b) Restriction R(S) -> F_2^Q is onto with kernel R(S'), and R(S') is spanned by
triples. So S is cyclic iff the restrictions to Q of the triples meeting Q span F_2^Q. A triple with two
points in Q restricts to an edge of Gamma; edges span the vectors of even weight on every component, and
the quotient of F_2^Q by them is F_2^c, in which a triple inside Q becomes chi(T). (c) Distance 1 would
put q3 = q1 + q2 in S'. Distance 2 (q1 ~ r ~ q2) gives q1 + r = s, r + q2 = s' in S', so q3 = s + s'
completes a triple with two points in S'. QED

### 2.3 Theorem B (no small counterexample). Proved; confirmed exhaustively at n = 4, 5.

If S is cyclic and not a circuit set, then |Q| >= 6 and n >= 5. Hence L_cyc(M) = L(M) whenever
L_cyc(M) <= 5 or n <= 4.

*Proof.* By (b) there is a triple inside Q. Suppose |Q| <= 5; five points carry at most two triples.
*One triple {q1,q2,q3}:* c = 1, Gamma is connected, a shortest q1-q2 path has length >= 3 with inner
vertices x, y different from q3; so Q = {q1, x, y, q2, q3} and q3 is adjacent to none of q1, q2
(distance 1), x (distance 2 to q1), y: Gamma is not connected. *Two triples {p,a,b}, {p,a',b'}:* p is
adjacent to nobody, so c = 2, the other component is {a,b,a',b'}, and both chi equal (1,0): rank 1.
Contradiction. Finally Q avoids S' and S' + S', so its elements have weight >= 3; for n <= 4 there are
only five such vectors. QED

### 2.4 Example 1 (the smallest counterexample). Proved; verified by `min_example.py` and `enum5.c`.

n = 5, strings list the coefficients of e_1..e_5.

    Q = { q1 = 11100, a = 11110, b = 11111, c = 01111, q2 = 00111, q3 = 11011 },   S = E + Q.

The triples of S are exactly

    {e4, q1, a}  {e5, a, b}  {e1, b, c}  {e2, c, q2}  {e3, b, q3}  {q1, q2, q3}.

They are independent and |S| - n = 6, so S is cyclic. No triple contains two unit vectors, so the
closure of E is E: S is not a circuit set. For M = Q: L_cyc(M) = 6; a 6-gate circuit would have mask
set exactly S, impossible; a 7-gate circuit exists. So **L_cyc(M) = 6 < 7 = L(M)**. The 5-row set
Q \ {b} also has L_cyc = 6, L = 7 (exhaustive).

Why it works: each element is obtained from a neighbour by adding a unit vector, and the loop is closed
by q1 = q2 + q3. Every element is explained by the others, none by the inputs alone. All 60 non-circuit
cyclic sets of size 6 at n = 5 are images of this one under permutations of the coordinates.

### 2.5 Theorem C (L_cyc does not see which boundary vectors are the inputs). Proved; checked on all 83,328 invertible 5x5 row sets.

(i) *Re-encoding.* Let B = (e_1..e_n, r_1..r_m) be the units and the rows of M, I a choice of n of these
vectors forming a basis, phi the linear map sending them to e_1..e_n, and M_I the matrix whose rows are
the images of the other m vectors. Then L_cyc(M_I) = L_cyc(M).
(ii) *Inverse.* For invertible A: L_cyc(A^-1) = L_cyc(A) <= min(L(A), L(A^-1)).
(iii) *Transpose.* For an m x n matrix without zero row or column: L_cyc(M^T) = L_cyc(M) + m - n.

In coding terms: L_cyc(M) depends only on the code generated by (I | M^T) up to permutation of its
coordinates, and (for m = n) is the same for the dual code.

*Proof.* (i) If S is a cyclic system for M then phi(S) has the same size and an isomorphic relation
space, and contains the units and the rows of M_I. (ii) is (i) with I = the rows. (iii) Take a minimum
based cyclic system (S, T) for M. Put one unknown u_t per triple, one input z_j per row and one unknown
o_i per input. For every element v of S write the *star equation*: the sum of u_t over the triples
containing v, plus z_j if v carries row j, plus o_i if v = e_i, is zero. A star has D_v >= 2 terms. The
star equations at the non-inputs are the transposed matrix of T, so the u_t are determined, and
o = M^T z. Splitting a star with D >= 4 terms into D - 2 three-term equations with D - 3 new variables
keeps unique solvability. By Proposition 1(b) the distinct nonzero values form a cyclic set for M^T of
size at most sum_v (D_v - 2) = G + m - n. Apply this to M^T as well. QED

Consequence: a circuit for A with G gates, read with its outputs as inputs, *is* a cyclic system of
size G for A^-1.

### 2.6 Examples 2 and 3 (invertible matrices). Proved; verified by `exact6.c` / `exact7.c` and `examples_verify.py`.

**Example 2 (n = 6).** B has rows y1 = x2+x6, y2 = x3+x4, y3 = x1+x4+x5, y4 = x5+x6, y5 = x1+x3,
y6 = x1+x2+x5 and a 7-gate circuit (t = x1+x5; y3 = t+x4; y6 = t+x2). A = B^-1 has rows
100101, 111110, 100111, 110111, 011010, 011110 and **L_cyc(A) = 7 < 8 = L(A)**. Read from the outputs,
the seven equations have seven unknowns x1..x6, t; every equation contains at least two unknowns and
every unknown occurs at least twice: no equation can be solved first, yet the system is invertible.

**Example 3 (n = 7, MixColumns flavour).** B has the rows 0101010 1110000 1010001 0110001 1011000
0001110 0010011 and a 10-gate circuit. A = B^-1 has rows 1110101 1101101 0111000 1001001 0101111
1100100 1011101 (all row and column weights odd; no relation of weight < 4 among the 14 boundary
vectors, the largest possible minimum in dimension 7). **L_cyc(A) = 10 < 11 = L(A)**, while
L(B) = L_cyc(B) = 10. So L(A) != L(A^-1) happens, and it is the same phenomenon as L_cyc < L.

### 2.7 Theorem D (few rows). Proved for one and two rows; three and four rows open.

*Rank lemma.* In a based cyclic system let J be a set of basis triples, U the set of their points. Then
the number of non-unit elements of U is >= |J|; and if J is connected (as a hypergraph),
dim span(U) <= |J| + 1.
(i) One target t of weight w: L_cyc = L = w - 1. (ii) Two targets: L_cyc = L.
Observed: at n = 5 no counterexample has fewer than 5 rows (exhaustive); at n = 6 none among 60,000
random 3-row sets and 60,000 random 4-row sets, 30 among 40,000 random 5-row sets.

### 2.8 Example 4 (a cyclic system that is a circuit for no choice of inputs). Proved; `moore_example.py`.

At n = 5 every non-circuit cyclic set becomes a circuit set when another basis contained in it is taken
as the inputs (exhaustive, `enum5b.c`); Examples 1-3 are of this kind. This is not general. Take the
graph with vertices a0..a3, r0..r11, o and the 36 triangles (a_i, a_(i+1), r_i), (a_(i+1), r_i, r_(i+1)),
(r_i, r_(i+1), o), i = 0..11, indices of a mod 4 and of r mod 12 (a disc whose boundary runs three times
around a 4-cycle). S = the 52 edge vectors e_u + e_v; they span dimension 16; the triples of S are the 36
triangles. Over F_2 the triangles have rank 36 = 52 - 16: S is cyclic of size 36. Over F_3 the oriented
triangle equations have rank 35, so for every spanning tree there is a nonzero g vanishing on the tree,
and the closure of the tree stays inside {g = 0}. Hence with any spanning tree as inputs:
L_cyc = 36 < L, and this survives every re-encoding. So

    L(M)  >=  min over re-encodings I of L(M_I)  >=  L_cyc(M),

and both inequalities can be strict.

### 2.9 Proposition E (how far apart). Bound proved; sharpness unknown.

If S is a minimum cyclic system for M with Q, c as in Theorem A, then
L(M) <= L_cyc(M) + c (|Q| - 3) <= L_cyc(M)^2. Observed: the gap is exactly 1 in all 49,086
counterexamples at n = 5 and in every sampled case at n = 6, 7. Whether L <= C * L_cyc is open.

### 2.10 Data

n = 5, exhaustive over all 2^26 sets of non-unit vectors (`enum5.c`, `enum5.out`):

| quantity | value |
|---|---|
| circuit sets / cyclic sets / cyclic not circuit | 65,374,699 / 65,423,650 / 48,951 |
| non-circuit cyclic sets by size 6..16 | 60, 1200, 6975, 14060, 14242, 8442, 3085, 740, 130, 16, 1 |
| target sets M with L_cyc < L (of 2^26) | 49,086; largest gap 1; never L_cyc > L |
| fewest rows of a counterexample | 5 (60 sets, L_cyc 6, L 7) |
| invertible 5x5 (83,328 row sets): L_cyc < L / L(A) != L(A^-1) | 0 / 0 |
| flavoured 5x5 (12 row sets) | all L_cyc = L = 8 |

n = 6 (`exact6.c`, `n6_study.py`): all 3,763 flavoured row sets: no gap, L in {8, 9, 10}. 60,000 random
invertible: 116 with a gap, always with L_cyc = min(L(A), L(A^-1)) and minimum relation weight <= 3.
n = 7 (`exact7.c`, `n7_study.py`): of 3,000 random flavoured A with a 10-gate circuit, for 24 the
inverse has no circuit with <= 10 gates; all have minimum relation weight 4.

"Flavoured" = invertible, every row and column of odd weight, rows of weight >= 3. "No relation of
weight below 6" cannot be met for n <= 8.

## 3. Audit of PROOF.md for based cyclic systems

Setting: (S, T) is a minimum based cyclic system of M = MixColumns or of M^T.

### 3.1 Dictionary

| PROOF.md (circuit) | order-free meaning for (S, T) |
|---|---|
| signal, mask | element of S |
| gate equation | member of T (a triple); no operand/result distinction |
| G | |T| = |S| - 32 |
| y | number of members of T with three even points (EEE); every other member has exactly two odd points (OOE) |
| x | (number of even elements of S) - y |
| h | number of odd elements outside the boundary B |
| fan-out d_v | D_v - 1, D_v = (number of members of T containing v) + 1 if v is an input + 1 if v is an output |
| adjoint a(result of gate t) | u_t, the unique solution of the star equations |
| k_v | K_v = number of odd terms of the star at v; K_v is even and equals 2*ceil(k_v/2) |
| f_v | max(0, D_v - 2 - K_v/2) |
| raw transpose | dual system of Theorem C(iii) |
| canonical association | splitting in which every pair of odd terms is joined directly |
| origin of a transpose gate | the element v whose star the triple belongs to |
| Q, e_1 | number of members of T with odd u_t; number of EEE members with odd u_t |
| odd graph | vertices: odd elements; edges: OOE members of T, labelled by their even point |

### 3.2 Order-free proofs for the lemmas whose written proof uses the order

**1.1.** Distinct and nonzero: definition. An element outside B lying in only one member of T can be
deleted with that member, contradicting minimality.

**2.1.** For a component K of the odd graph let psi_K: S -> F_2 be the indicator of the odd elements of
K. psi_K has even sum on every member of T, hence is orthogonal to R(S), hence is the restriction of a
linear functional lambda_K, which on the units is the indicator of the inputs in K. So an odd element of
K has odd weight on the inputs of K and even weight on the inputs of every other component; an even
element has even weight on each. No lambda_K is zero, so every component contains an input. The y EEE
members are independent relations among the even elements, so y <= (number of even elements) - dim E,
i.e. x >= 32 - c.

**3.1, 3.2.** Theorem C(iii) with m = n. A star with D terms of which K are odd is split by a trivalent
tree with D - 2 inner nodes; the odd edges of the tree form K/2 disjoint paths, so the number of EEE
triples is <= D - 2 - K/2 with equality iff every path has one inner node.

**4.1.** Two members of T on the same pair of points have the same third point, so are equal.

**4.4 and every later "subset of the gate equations, hence independent".** Independence of T is part of
the definition.

**6.1.** Count odd terms over all stars: sum_v K_v = 3Q + 64; the count of OOE triples of the dual then
gives x(dual) = Q/2.

**7.1.** In the dual of the dual the adjoint is constant on each tree: a value V_v; the star of u_t reads
V_p + V_q + V_r = 0 and the terminals give V = e_i at the inputs. The values of S satisfy these
equations and the solution is unique.

**7.3.** The original triples are one way of splitting the stars of the double dual; the canonical
splitting has at least as many EEE triples in every star.

**7.4.** A dual variable lying in exactly two triples is a new variable of a tree; in a canonical
splitting the new variables are even.

**10.3(ii), last step.** "Every component of the odd graph contains an input" is part of 2.1 above.

### 3.3 Lemma by lemma

| item | text uses order | holds for cyclic systems, why |
|---|---|---|
| 1.1 | yes | yes, 3.2 |
| 1.2 | no | yes, counting |
| 2.1 | yes (induction over gates) | yes, 3.2 |
| 2.2, F1, Cor 2.3 | no | yes; x >= 24 |
| (3.1), 3.1, 3.2, (3.3) | yes (reverse order, rooted trees) | yes, Theorem C(iii) and 3.2 |
| 4.1 | yes | yes |
| 4.2-4.3, 4.5-4.7 | no | yes |
| 4.4 | yes ("latest signal") | yes, by definition |
| 5.1, Cor 5.2 | no | yes |
| 6.1 | mildly | yes, 3.2 |
| 6.2 (A), (B) | no | yes |
| 7.1, 7.3, 7.4 | yes | yes, 3.2 |
| 7.2, 8.1-8.3, Prop 8.4, 9.1, Prop 9.2 | no | yes |
| 10.1 (L1)-(L23), 10.2, 10.4, 10.3(i) | no | yes |
| 10.3(ii) | yes (one sentence) | yes, by 2.1 |
| section 11 | no | yes |

**No lemma uses the order essentially.**

### 3.4 Outcome. Conditional (on PROOF.md being correct for circuits, and on this audit, a single machine pass).

With "normalized minimum circuit" replaced by "minimum based cyclic system", PROOF.md proves:

> every cyclic system for AES MixColumns has size at least 75:  75 <= L_cyc(M) <= L(M) <= 88.

Consequences. (a) By Theorem C the bound holds for L of InvMixColumns, of the transposes, and of every
matrix obtained by taking another information set of the 64 boundary vectors as inputs. (b) The finite
facts F1-F14 are statements about the boundary configurations only. (c) An argument of this kind (gate
equations as formal vectors over F_2, counting, transposition) bounds L_cyc and nothing more; it is
complete for MixColumns only if L_cyc(M) = L(M).

### 3.5 Stress test of the order-free versions. Observed.

`cyclic_identities.py` builds 3,000 based cyclic systems that are not circuits on their basis triples,
constructs duals and double duals, and checks 1.2, 2.1, 3.1, 3.2/(3.3), 6.1, 6.2 with (A) and (B), 7.1,
7.2, 7.3, 7.4, 8.1. No violation (`ident.out`). The test systems are not minimum. The statements that
depend on the finite facts of MixColumns (section 4 from F2 on, section 10) are not covered by this
test; for them the audit rests on reading the proofs.

## 4. What separates circuits from cyclic systems

### 4.1 Theorem W (weights). Proved.

Let S contain E, P = the set of its triples, K a field with at least three elements. For a choice w of a
nonzero element of K for every incidence (triple, point), let N_w be the P x (S \ E) matrix of these
weights. Then

* S is a circuit set iff N_w has rank |S| - n for **every** w;
* S is cyclic iff N_1 has rank |S| - n over F_2.

For a based system (S, T), with the square matrix of T: it is a circuit on the triples of T iff the
matrix is nonsingular for every w, iff it is triangular after permutation, iff the **leaf property**
holds: every nonempty subset R of T contains a non-input element lying in exactly one member of R.

*Proof.* Circuit => the gate triples give a triangular submatrix with nonzero diagonal. Not a circuit =>
Q is nonempty and every triple meets Q in 0, 2 or 3 points; choose w with sum zero over the points of Q
in each triple (a, -a; or three nonzero elements with sum 0, which exist iff |K| >= 3); then the
indicator of Q is in the kernel. Based version: peel elements lying in exactly one remaining triple; the
peeling order reversed is a gate order; if peeling stops, each remaining column has >= 2 entries in the
remaining rows and weights with zero column sums make the remaining square block singular. QED

Reason in words: the difference between L and L_cyc is the identity 1 + 1 + 1 != 0 in F_2. A feedback
loop is consistent only because of F_2 cancellation; a causal system is consistent whatever the
coefficients. Every argument that uses the gate equations only through F_2-linear algebra
(independence, rank, parity) is an argument about cyclic systems.

### 4.2 Statements true for circuits and false for cyclic systems. Proved (each fails in the example named).

* Some non-input mask has weight 2 (the first gate). Fails in Example 1.
* Some output lies in no gate equation other than its own (the last gate). Fails in Example 1.
* Leaf property: there is no nonempty family R of gate equations in which every non-input signal that
  occurs, occurs at least twice. PROOF.md only uses the weaker "no family in which every signal occurs
  an even number of times" (Lemmas 4.4, 4.6, 10.2, 10.3).
* L(A) and L(A^-1) may differ (Examples 2, 3); L_cyc cannot.

None of these is used in PROOF.md. A lower-bound argument that is to go beyond L_cyc has to use the
leaf property (or the order directly) somewhere.

### 4.3 Is a gap plausible for matrices like MixColumns? Observed / open.

* Flavoured matrices with L_cyc < L exist (Example 3). About 0.8% of the sampled flavoured 7x7 matrices
  with a 10-gate circuit have an inverse with L_cyc < L. None exists for n <= 6 (exhaustive).
* For MixColumns itself nothing is decided. L_cyc(MC) = L_cyc(InvMC) <= 88.
* Recorded circuits (`mc_reencode.py`): the recorded 88-gate MixColumns circuit of depth 5, read from
  its outputs, is **not** a circuit for InvMixColumns (the closure of the 32 outputs has 44 of the 120
  masks); it is a cyclic system of size 88 for InvMixColumns. The recorded 88-gate InvMixColumns
  circuit of depth 17 read from its outputs **is** a circuit for MixColumns, as are the recorded
  InvMixColumns circuits with 89, 90, 92, 93, 94, 96 and 101 gates (those with 104 and 118 are not).

## 5. Unresolved

1. **Is L_cyc(MixColumns) = L(MixColumns)?** Unknown. The 75 proof cannot tell. To go beyond L_cyc a
   proof must use the leaf property, and no linear-inequality form of it is known that fits the
   helper-type system of PROOF section 10.
2. The audit (section 3) was done by one machine pass; the order-free proofs of 3.1, 3.2, 6.1, 7.1, 7.3
   should be reviewed independently before "L_cyc >= 75" or "L(InvMixColumns) >= 75" is recorded as more
   than conditional.
3. Is L <= C * L_cyc for a constant C? Only L <= L_cyc^2 is proved; every observed gap is 1.
4. Counterexamples with three or four rows: none found, not excluded for n >= 6.
5. Is the minimum over re-encodings of L(M_I) equal to L_cyc(M) for MixColumns-like codes? (False in
   general, Example 4; true for every set at n = 5.)
6. n = 8 analogues were not computed.

## 6. Files

| file | purpose | usage |
|---|---|---|
| `enum5.c`, `run_enum5.sh` | every 5-input set: circuit / cyclic; L and L_cyc of all 2^26 target sets | `bash run_enum5.sh` (82 CPU-s) |
| `enum5b.c` | n = 5: every non-circuit cyclic set is a circuit set for another basis | compile with gcc -O2 -fopenmp (85 CPU-s) |
| `min_example.py` | Example 1, n = 4, orbit count; independent of the C code | `python3 min_example.py` |
| `exact6.c`, `n6_study.py` | exact L, L_cyc for n <= 6 | `python3 n6_study.py MODE [COUNT] [SEED]` |
| `exact7.c`, `n7_study.py`, `n7_exact.txt` | same for n = 7 | `python3 n7_study.py COUNT SEED [EXTRA]` |
| `examples_verify.py` | Examples 2 and 3, pure Python | `python3 examples_verify.py` |
| `moore_example.py` | Example 4 | `python3 moore_example.py` |
| `cyclic_identities.py` | stress test of section 3.5 | `python3 cyclic_identities.py 1500 7` (34 CPU-s) |
| `mc_reencode.py` | recorded MixColumns / InvMixColumns circuits read from the outputs | `python3 mc_reencode.py` |

All runs under `ulimit -v 8000000`, at most 4 threads, about 15 CPU-minutes in total. No SAT solver.
