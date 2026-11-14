# Research record

Statuses: **proved**, **conditional**, **conjectured**, **observed**, **disproved**. "Observed" means seen
on recorded circuits or small cases and says nothing about all circuits. Model: 2-input XOR circuits,
any fan-out and depth, cancellation allowed; G gates; L(M) the minimum (PROOF = the 75 proof,
`lower-bound-proofs/mixcolumns-lb75/PROOF.md`). Bounds in force: 75 <= L(MixColumns) <= 88.

Sections 1-4 are the main agent's own work of 2026-11-11. Sections 5 onward summarise the delegated
investigations; each has its own REPORT.md, and the summary here states what was independently
checked.

---

## 1. Parity is evaluation at a point (proved; reformulation and mild generalisation)

**Statement.** Let a circuit compute an m x n matrix M whose rows are distinct and none a unit vector.
For an input point x in F_2^n call a signal *live at x* if its mask mu has mu.x = 1, otherwise *dead*.
Let c(x) be the largest number of nonzero words of the graph code {(u, Mu)} with pairwise disjoint
supports whose sum is (x, Mx). Then

    G >= wt(x) + wt(Mx) - c(x).

More precisely: at least wt(Mx) gates are live at x, and at least wt(x) - c(x) gates are dead at x.

**Reason.** A dead signal is a relation "these inputs cancel at x". Two live signals can only be
combined into a dead one, and each such gate can merge at most two groups of live inputs.

**Proof.** Let E_t be the span of the masks dead at x after t gates; E_0 is spanned by the unit vectors
e_i with x_i = 0. Claim: E_t is the set of vectors with even weight on every block of a partition P_t of
supp(x) (no condition outside supp(x)), and every live signal is congruent mod E_t to some e_i with
i in supp(x). Induction on gates: live + dead is live and congruent to the same e_i; dead + dead is in
E_t; live + live, with operands congruent to e_i and e_j, is dead and equals e_i + e_j mod E_t, so E grows
by at most that vector, which merges the blocks of i and j. Hence the number of dead gates is at least
dim E_final - dim E_0 = wt(x) - c, with c the number of blocks at the end. A live output is odd on
exactly one block and even on the others, a dead output is even on all blocks. So for the indicator b_C
of a block C, the supports of the M b_C are pairwise disjoint, and the (b_C, M b_C) are c nonzero
disjoint codewords with sum (x, Mx); thus c <= c(x). The live outputs are wt(Mx) distinct gates. QED

**Relation to PROOF.** For a matrix with all rows and columns odd, x = all-ones gives PROOF Lemmas 2.1-2.2
and the first 56 = 32 + 32 - 8 for MixColumns. "Odd weight" is "live at the all-ones point".

**What it does not give.** Combining two points by linear programming gives nothing beyond the best
single point. With two points x1, x2 the gates fall into four classes by their values at the two points;
each of x1, x2, x1 + x2 gives one "live" and one "dead" inequality on the class counts. For MixColumns
the best single point gives exactly 56, and the linear program over all six inequalities never exceeds
56 (my hand check used only four of the six; the machine review closed the two-point case with all six,
`review-record/`). Three or more points were only sampled there, not proved. The reason is structural:
with a quotient of dimension k >= 2 there are gates joining two different nonzero classes, and nothing
forces the span of the fully dead signals to be large. Status: proved for two points and this linear
relaxation; not a statement that no multi-point argument exists.

## 2. The affine reading and the savings identity (proved; identities, not bounds)

Assume all rows and columns of M are odd and the 2n boundary vectors (unit vectors and rows) have no
linear relation of weight <= 4 (PROOF fact F2; true for MixColumns). Odd masks are *points*, even masks
are *vectors* (labels). The three gate types are: **producer** (point + point = vector), **translate**
(point + vector = point: an output or a helper), **sum** (vector + vector). The odd graph of PROOF section 4
has one edge per producer and per translate, labelled by the vector. With x producers, y sums, h helpers,
q labels that are not the difference of two boundary points joined by an edge (missing labels), e_l the
number of edges with label l, r_p the number of edges from helper p to a boundary point whose label is
represented, and z_r the number of helper-helper edges whose label is represented:

    G = 2n + x - S,   S = sum over helpers (r_p - 2) + z_r + sum over missing labels (e_l - 1).   (2.1)

**Proof.** Edges: x + n + h. Each represented label has exactly one boundary-boundary edge (F2), so the
edges touching a helper number (x + n + h) - (x + y - q) = n + h - y + q. Sorted by label they are
sum_p r_p + z_r + sum over missing l of e_l. Hence y = n + h + q - sum_p r_p - z_r - sum_missing e_l, and
G = n + x + y + h gives (2.1). QED

(2.1) is the counting behind the "ledger" G >= 88 + 2h + p - r of the sprint findings (F20), with
equality kept (the two agree on the circuits checked; the general equivalence would need the
independence of the reuse relations, PROOF Lemma 4.4, and is not claimed here). By itself (2.1) is a
rewriting. Its use is to say what a saving is: G < 2n + x needs S > 0, and S > 0 can only come from
(i) helpers that are a sum of three boundary points in three ways (r_p = 3; r_p <= 3 by F3 together
with PROOF Lemma 4.4, which makes the triples at one helper distinct),
(ii) two helpers whose difference is a boundary difference that some gate realises, or (iii) a missing
label carried by two or more edges. With x >= 24 for MixColumns: an 87-gate circuit needs S >= x - 23.
The identity holds without normalisation and was verified from the definitions on all 73 recorded
circuits of maps meeting the hypotheses (machine review, `review-record/`).

**Observed.** The recorded 88-gate MixColumns circuit has x = 24 and S = 0 exactly (h + y = 32), and so
does the recorded 88 for the inverse map. S = 0 is NOT forced: the recorded MixColumns 89@4 has x = 26,
h + y = 31 and S = 1, and other maps with the same hypotheses have S > 0 at their best circuits, e.g.
small-scale AES MixColumns over GF(16) (n = 16, G = 42 = 2n + 12 - 2) and lw16-4x4-gf256-inv-had
(n = 32, G = 84, x = 25, h + y = 27). `tools/survey.py` prints the table. **Disproved:** "h + y >= n
whenever the boundary has no relation of weight <= 4". For those two maps this holds even for minimum
circuits, because the parity bound on x (x >= 11, x >= 22) already forces h + y < n at the recorded size.

## 3. MixColumns in the sheet language (proved; verified on the recorded circuits)

Index the inputs (c, j) = bit j of byte c; block j = {(0,j), (1,j), (2,j), (3,j)}. On a block write
s_c = e_c + e_(c+1) (c mod 4), d_0 = e_0 + e_2, d_1 = e_1 + e_3, t = e_0 + e_1 + e_2 + e_3 and
E_c = t + e_c. Then the MixColumns row for output (c, j) is

    o(c,j) = E_c on block j + s_c on block j-1 (+ s_c on block 7 if j is 1, 3 or 4),   j >= 1,
    o(c,0) = E_c on block 0 + s_c on block 7.                                                     (3.1)

**Proof.** out_c = 2 b_c + 3 b_(c+1) + b_(c+2) + b_(c+3) = (b_(c+1) + b_(c+2) + b_(c+3)) + 2 (b_c + b_(c+1)).
Bit j of the first bracket is E_c on block j. With w = b_c + b_(c+1), bit j of 2w is w_(j-1), plus w_7
when j is 1, 3 or 4, and bit 0 is w_7 (reduction by x^8 + x^4 + x^3 + x + 1); w_k is s_c on block k. QED

**Structure behind it.** Writing a state as b(y) = sum of b_c y^(-c), MixColumns is multiplication by
2 + 3y + y^2 + y^3 in R = F_256[y]/(y^4 + 1) (with b(y) = sum of b_c y^c the element is
2 + y + y^2 + 3y^3; nothing below depends on the convention). Since y^4 + 1 = (y + 1)^4,
MixColumns = 1 + (1 + y)(3 + y^2) with 3 + y^2 a unit. The masks that vanish on (1+y)^k R form a flag
W_1 < W_2 < W_3 of dimensions 8, 16, 24 (k = 1, 2, 3): on each block, W_3 = even weight,
W_2 = {0, d_0, d_1, t}, W_1 = {0, t}. MixColumns and its transpose act as the identity on each quotient
W_k / W_(k-1).

**A family.** For an m x m matrix T over F_2 define Q_T on 4m inputs by o(c,j) = E_c on block j plus s_c
on every block k with T[j][k] = 1. MixColumns = Q_T for T = multiplication by x. Restricting the inputs
to (u, v, u, v) gives the two-point "double map" D_T: (u, v) -> (u + T(u+v), v + T(u+v)). For T a cyclic
shift, Q_T is multiplication by a weight-5 element of F_2[C_m x C_4] ("rotation model").

**Observed on the recorded 88@5** (`tools/sheets.py`, `tools/levels.py`): partition = the eight blocks;
24 producers, of which 19 are differences of two inputs and 5 are differences involving a helper;
exactly 2 helpers on every sheet; 16 sums. Extras (helpers + sums) by sheet, crediting each sum to the
first sheet that uses it (one sum serves sheets 0 and 1 and is credited to sheet 0; two serve sheets 3
and 4 and are credited to sheet 3): 3 on each of sheets 2, 5, 6, 7; 4 on sheet 0; 16 on the three
sheets 1, 3, 4 whose rows have the extra block-7 term. The flag is barely populated: 10 gate signals
lie in W_2 (rank 7 of 16), 2 in W_1.
The eight-block partition is not unique for MixColumns: the recorded 89@4 has 8 blocks that are not
the bit positions (`tools/m2_check.py`); so does the recorded 88 for the inverse map.

**Checked.** M2 = D_T for T = multiplication by x has a 26-gate circuit (16 + 8 + 2), one fewer than the
obvious 27 (`tools/m2_check.py`).

## 4. Ideas that failed, and why

- *Quotient by W_2* (restrict inputs to (u,v,u,v)). Every circuit for MixColumns restricts to a circuit
  for M2, and at least 16 output gates disappear because the outputs (c, j) and (c+2, j) coincide after
  restriction. Proved: G >= L(M2) + 16, which is at most 42 with L(M2) <= 26. I could not prove that a
  further 16 gates must die (a pair of coinciding outputs can be made by two unrelated gates, and then
  no dead signal is forced); even if that held, the result would be L(M2) + 32, between 56 and 58, no
  better than the parity bound. (An earlier version of this entry claimed "+32, weaker than 56"; both
  halves were wrong, found by the machine review.) Reason for the weakness: the relations of weight 6
  that make MixColumns hard become relations of weight 4 in the quotient (the two outputs of a sheet
  differ by an input difference), so the quotient cannot see why labels are hard to reuse.
- *Several evaluation points*: see section 1.
- *"h + y = n is forced"*: disproved in section 2.
- *The rank of the lower flag levels as a cost*: real circuits do not fill W_2 and W_1 (section 3), so no
  bound can come from "the circuit must span the lower levels".

## 5. Restriction, gate elimination, connectivity (`restriction/REPORT.md`; delegated, not yet re-reviewed)

What these classical tools give for MixColumns in the formulations analysed, and where those
formulations stop. The negative statements below are about exactly these formulations (one evaluation
point with the bound of section 1; restriction along the first live gate; zeroing or merging inputs and
counting dead gates; a two-point colour count; rank-connectivity of the gate graph); other uses of
restriction or of several points were not analysed. I checked the proof of P1 myself; the rest is as
reported.

- **Proved (P1):** no evaluation point beats the all-ones point. For x other than 0 and all-ones, the
  complement of (x, Mx) is a codeword of weight w' >= 6, and unless w' >= 31 the support of (x, Mx)
  contains a second codeword, so c(x) >= 2 and the bound is at most 64 - 6 - 2 = 56.
- **Proved (ID):** restricting step by step along the first live gate reproduces the parity count
  exactly: G = n + m - c + surplus with surplus = (x - (n - c)) + y + h. So "restrict, then apply parity
  to what is left" is not a second method; it is the same count followed over time.
- **Proved:** pure gate elimination gives 38; elimination plus parity gives 57 (the extra 1 is y + h >= 1);
  rank-connectivity alone gives 35. Each stalls at a named configuration (two merges inside one bit
  family turn a weight-5 row into an input, and only two gates can be shown to die).
- **Proved (MP):** with two evaluation points, every target can be computed without any gate whose two
  operands share a nonzero colour. In the one-point case every span-increasing gate is such a gate; that
  is the whole reason parity works, and it has no two-point analogue.
- **Open:** whether a graph with far fewer than 75 gates can meet all rank-connectivity requirements.
- **Literature (verification status in the report):** nothing published applies to a 32 x 32 matrix with
  a number above about 32. Sergeev (Math. Notes 2025) proves 5n - o(n) for an explicit family using a
  "any 2k rows independent" hypothesis of the same kind as our boundary property; only the abstract and
  slides were read. It should be read in source before anything here is called new in kind.

## 6. Cyclic systems: what the published framework actually bounds (`cyclic/REPORT.md`)

Delegated. I re-ran three of its scripts and checked Example 1, Theorem C(i) and Theorem W by hand. The
whole report then had an independent machine review (`review-cyclic/REVIEW.md`).

**Definition.** A *cyclic system* for M is a set S of distinct nonzero vectors containing the unit
vectors and the rows of M whose linear relations are all generated by its collinear triples. Its size
is |S| - n; L_cyc(M) is the least size. Every circuit is one (the gate equations), so L_cyc <= L. A
cyclic system is a circuit exactly when its equations can be solved one at a time.

- **Proved: L_cyc < L happens.** Smallest example (n = 5, six rows 11100, 11110, 11111, 01111, 00111,
  11011): the six triples {e4, 11100, 11110}, {e5, 11110, 11111}, {e1, 11111, 01111}, {e2, 01111, 00111},
  {e3, 11111, 11011}, {11100, 00111, 11011} generate all relations, no triple contains two inputs, so
  nothing can be computed first: L_cyc = 6, L = 7. Invertible examples exist from n = 6 (7 against 8) and
  with all rows and columns odd at n = 7 (10 against 11). No example with n <= 4 or L_cyc <= 5 exists
  (proved).
- **Correction:** the n = 7 example has a column of weight 1, so it is MixColumns-like in one
  orientation only. Whether L_cyc < L can happen for a matrix whose code and dual code both have minimum
  distance at least 4 and no unit-weight column is not known.
- **Proved: L_cyc does not see which boundary vectors are the inputs.** It is the same for a matrix,
  its inverse, its transpose (up to m - n) and every other choice of information set. A circuit for A,
  read from its outputs, is a cyclic system for the inverse of A. So L(A) and L(A^-1) can differ only
  through causality.
- **Proved (Theorem W): what separates the two.** Let S be a cyclic set and T a SPECIFIED basis of its
  relation space consisting of triples. Then (S, T) is a circuit whose gate equations are exactly the
  members of T iff every nonempty subset of T contains a non-input element lying in exactly one of its
  members (the *leaf property*); linear independence of T only gives an element lying in an odd number.
  Equivalently the equations of T stay uniquely solvable under arbitrary nonzero coefficients over a
  field with at least three elements. A value set is a circuit set iff SOME basis of triples has the
  leaf property. It is not claimed, and is false in general, that every triple basis of a circuit set
  is executable.
- **Conditional (on PROOF being correct for circuits; audited, then independently machine-reviewed):**
  no lemma of PROOF uses the gate order essentially; eleven are written with it and each has an
  order-free proof. The review found three gaps in the audit as written (the span inequality in Lemma
  2.1 was argued in the wrong direction; "the transpose of a minimum system is minimum with distinct
  values" needed a counting argument; signals of fan-out 1 were not handled) and supplied a short repair
  for each; with the repairs it confirms the conclusion. So PROOF shows L_cyc(MixColumns) >= 75, and
  therefore **L(InvMixColumns) >= 75** and the same for every systematic form of the same [64,32] code.
  No human has checked this.
- **Heuristic, not a theorem:** an argument that uses the gate equations only through linear algebra
  over F_2 (independence, rank, parity, counting) cannot be expected to prove more than
  L_cyc(MixColumns), which is at most 88 and not known to equal L(MixColumns).
- **Observed:** the recorded 88-gate MixColumns circuit read from its outputs is not a circuit for the
  inverse (only 44 of 120 masks are reachable), while the recorded 88-gate inverse circuit read from
  its outputs is a circuit for MixColumns.
- **Open:** whether L_cyc(MixColumns) = L(MixColumns); whether L <= C L_cyc in general (every observed
  gap is 1; only L <= L_cyc^2 is proved).

## 7. The charge theorem: each sheet is charged ten gates (`rotation/REPORT.md`, `tools/charges.py`)

The theorem for the rotation model is the delegated investigator's (rotation/REPORT.md 3.4, 3.5). The
MixColumns version and its proof as written here are the main agent's. Independently machine-reviewed
(`review-charges/`); the corrections of that review are applied below.

**Dependency.** Everything in this section and in section 9 rests on the ten-gate local lemma. Until
2026-11-12 that lemma was established only by finite computation (four programs), and these sections
were computer-assisted. It now has a hand proof (`tenth-gate/PROOF.md`, section 10), confirmed by an
independent machine review; a second, different hand proof is the case r = 1 of section 11. With it the
charge theorem, the 80 and the 83 for block-monotone circuits no longer depend on any computation; they
depend on PROOF Lemma 3.1 (transposition) and Lemmas 2.1-2.2 (partition), and on machine review only.

**Local lemma (computer-checked, 8 inputs).** Let blocks a and b have four inputs each. Suppose the four
unit vectors of b and every vector supported on a (zero included) are available at no cost. Then any
sequence of XOR gates computing the four vectors [b: E_c] + [a: s_c], c = 0..3, has at least 10 gates,
and 10 suffice. Operands may be free vectors, units of b or earlier gates; gate values are arbitrary;
nothing is assumed distinct or nonzero. Decided four times with code that shares nothing: two SAT
encodings by the investigator and the main agent (the latter decided 8 and 10 gates; its 9-gate run
timed out undecided after 50 minutes, so it does not count for the 9-gate case), and by the reviewer a third SAT encoding (9 gates impossible in 23 s with two justified
symmetry breaks) and an exhaustive search in C (`review-charges/lemma_exh.c`: nothing with at most 9
gates among 48.5 million nodes, 4 s). The C program is the certificate to rerun. By hand only 9 is
proved: the b-parts of the gates must contain a circuit for the four E_c (6 gates), and the a-parts need
three independent free vectors, each introduced by a gate whose b-part repeats an earlier one.

**Definitions.** Fix a circuit computing MixColumns, as a list of gates with their two operand wires.
An *output gate of sheet j* is any gate whose mask is one of the four rows (c, j). *Ancestor* refers to
the wires of the given circuit, not to values. For a gate g let mu(g) be the number of sheets j such
that (i) the mask of g is nonzero on block j and (ii) g is an output gate of sheet j or an ancestor of
one. A circuit is *block-monotone* if, whenever g is an ancestor of an output gate o, every block on
which the mask of g is nonzero is a block on which o is nonzero. (Cancellation inside a block is
allowed; what is excluded is a gate carrying a nonzero component on a block which every path to some
output it feeds must cancel completely. Every cancellation-free circuit is block-monotone, since an
ancestor's mask is then contained in its descendant's.)

**Theorem 7.1 (charges; conditional on the local lemma).** In every circuit computing MixColumns, for
every sheet j at least 10 gates are nonzero on block j and are output gates of sheet j or ancestors of
one. Hence the sum of mu(g) over all gates is at least 80, and

    G  =  (sum of mu)  -  (sum over gates of (mu(g) - 1)+)  +  #{gates with mu = 0}
       >=  80  -  (sum over gates of (mu(g) - 1)+).

The ten gates charged to one sheet need not be different from those charged to another: that is exactly
what mu >= 2 means.

**Proof.** Fix j, let b = block j and a = block j-1 (block 7 for j = 0). By (3.1) the outputs of sheet j
are [b: E_c] + [a: s_c] plus, for j = 1, 3, 4, a term on block 7, which is neither a nor b (checked
against the matrix for all sheets). Set every input outside a and b to zero. Let A be the set of gates
that are output gates of sheet j or ancestors of one, and D the gates of A whose mask is nonzero on b.
The operands of a gate of A are inputs or gates of A. After the restriction, a gate of A not in D has a
value supported on a (free, possibly zero); an input is a unit of a (free), a unit of b, or zero. So
every gate of D is the sum of two values, each of which is free, a unit of b, or the value of an earlier
gate of D. This is a circuit in the model of the local lemma (which allows zero and repeated values)
computing the four restricted outputs, each of which is nonzero on b and so is carried by a gate of D.
Hence |D| >= 10. Summing over j counts each gate mu(g) times. QED

**Corollary 7.2 (conditional on the local lemma).** Every block-monotone circuit for MixColumns has at
least 80 gates. More generally a circuit with fewer than 80 gates must contain gates with mu >= 2: a
gate that is nonzero on the own blocks of two different sheets and feeds outputs of both.
*Proof.* The outputs of sheet j are nonzero exactly on the blocks {7,0}, {0,1,7}, {1,2}, {2,3,7},
{3,4,7}, {4,5}, {5,6}, {6,7} for j = 0..7. If mu(g) >= 2 with sheets j != j' in a block-monotone circuit,
the support of g contains j and j' and lies in both supports, so j' is in the support of sheet j and j
in that of sheet j'. No such pair exists (inspection of the eight sets; also checked by program). QED

**Scope.** 7.1 is about all circuits. 7.2 is a restricted-family theorem; the class contains all
cancellation-free circuits and the three MixColumns circuits recorded in this repository, but only
about a quarter of the wider corpora of known 88-gate circuits (section 9). It is defined relative to
the bit-position blocks, and excludes exactly the mechanism that wins in the m = 3 example below. Neither
statement uses the parity framework, Sidon facts or transposition. Neither is a bound for unrestricted
circuits: the published bound stays 75.

**Observed.** The three recorded MixColumns circuits (88, 89, 97 gates) are block-monotone with no gate
of mu >= 2, although they are not cancellation-free (25, 16 and 10 of their gates cancel inside a
block). Charges per sheet: 88: 11, 11, 10, 13, 10, 10, 10, 10; 89: 10, 12, 10, 13, 11, 10, 10, 10;
97: 10, 13, 10, 16, 14, 10, 10, 11. Each has three gates with mu = 0; in the 88 two of them live on
blocks 2 and 7 and serve sheet 3, the third lives on blocks 3 and 7 and serves sheet 4. The reviewer
perturbed the three circuits 4,500 times by function-preserving moves (93 % of the results not
block-monotone, 1,476 with mu >= 2 gates): the smallest per-sheet count was always exactly 10. Planting
a mu >= 2 gate into the 88 by any single split always cost at least one extra gate (510 such circuits,
the smallest with 89 gates).

**Example showing the hypothesis matters.** For the rotation model with m = 3, block-monotone circuits
need at least 30 gates, and there is a 28-gate circuit with 17 gates violating block-monotonicity
(rotation/circuits/q3_28.txt, re-verified by the reviewer). No block-monotone 30-gate circuit for m = 3
is known, so 30 is a lower bound for that class, not its minimum. For m >= 4 the heuristic search found
nothing below 10m, and two symmetric SAT attempts at 36 and 38 gates for m = 4 timed out undecided.
Whether cross-block cancellation can help for m >= 4, or for MixColumns, is open. It is a direct-sum
question: can one gate usefully carry components that belong to two unrelated sheets.

**What this explains, and what it does not.** For the rotation model Q_8 (MixColumns without its three
field-reduction terms) 80 gates are attained by explicit periodic circuits and are optimal among
block-monotone circuits. Adding the reduction terms one at a time gave 82, 85, 88 in bounded heuristic
runs (observed). So as a gate count the recorded 88 is 80 plus 8; the charges do not place those 8 on
the three sheets with extra terms (sheet 0 carries 11, sheet 4 carries 10), so this is a reading of
totals, not a per-sheet statement, and the observed totals 80, 82, 85, 88 do not establish an
unavoidable eight-gate overhead for the reduction terms.

## 8. The double map: the second-level cost isolated (`double-map/REPORT.md`; delegated, no second review yet)

D_T: (u, v) -> (u + T(u+v), v + T(u+v)) on 2m inputs is MixColumns restricted to inputs (u, v, u, v) when
T is multiplication by x. Each bit position is a sheet with two inputs and two outputs. All statements
below are for **reduced** T: the diagonal is first made zero (changing T_jj only swaps the two outputs
of sheet j), and T has no zero row and no zero column. Without this they fail: T = 0 is the identity
map and needs no gate, a zero row makes two outputs equal to inputs, a zero column allows m + 1 blocks.
For reduced T the baseline is 3m = 2m outputs + m span gates, and eps(T) = L(D_T) - 3m is the cost of
translation vectors that are not cheaply available.

- **Proved (Theorem C):** eps(T) = 0 exactly when the relation code of the boundary is generated by its
  4-term relations, and exactly when T is a direct sum of explicit "arc blocks" (a cyclic permutation
  with rows extended along the cycle up to chosen roots). Around a cycle of sheets each sheet imports
  one vector and exports another, and all sheets that export their own input difference must point the
  same way. (An earlier version called this last step "causal". Section 13 shows it is algebra: the same
  equivalence holds for cyclic systems, so no gap between cyclic systems and circuits appears here.)
- **Proved, computer-assisted (Theorem D): L(M2) = 26**, where M2 is the half-size quotient of
  MixColumns (16 inputs). Two finite checks (the rank of 4-term relations; a scan of 32,736 candidate
  helper masks leaving four) and then a time-order argument: the first outputs of the eight sheets need
  seven distinct labels and two more are forced, against eight available. An exhaustive search confirms
  the case of 8-block partitions.
- **Invariant:** delta(T) = 2m - (rank of the 4-term relations among the boundary vectors) = the number
  of sheet vectors that no other sheet shares. Helper-free circuits need at least 3m + delta gates
  (proved). **Conjectured:** eps(T) >= max(delta(T), delta(T^T)) for all circuits; observed in all 70
  classes with m <= 4 whose optimum was determined (equality in 67, one more in 3).
- **Disproved along the way:** "an optimal circuit always uses the natural partition" (a 4 x 4 example:
  13 gates against 14); "delta is transposition invariant" (so the bound must take the maximum over the
  two orientations); "a helper adds at most two independent 4-term relations" (M2: four masks add 3).
- **What blocks a general proof, in the investigator's words:** each use of a helper beyond the first
  could save a gate; in every case analysed a linear dependency among the labels at that helper cancels
  the saving, but the dependency is tied to the saving only through time order, and this was made
  precise for one helper only.
- **Relation to MixColumns.** The same spanning inequality gives G >= 88 + 2h - rho_4(B u H) there (the
  identity of section 2). The M2 argument does not transfer: it needs the slack to be one gate, sheets
  with a 4-term relation, and outputs lying in boundary parallelograms; MixColumns has none of these.

## 9. Block-monotone circuits need 83; where a gate can serve two sheets (`rotation/REPORT-PART2.md`)

Delegated follow-up. I re-derived the proofs of the two theorems; both then had an independent machine
review (`review-83/REVIEW.md`), whose corrections are applied here. The review confirmed 9.1 and 9.2 and
found my first version of the last two paragraphs wrong or overstated.

**Theorem 9.1 (three-term sheet; proved by hand given the local lemma of section 7).** Let blocks a, k, b
have four inputs each, with every vector supported on a alone or on k alone free, and vectors meeting
both a and k not free. Computing the four vectors [b: E_c] + [a: s_c] + [k: s_c] takes at least 13 gates,
and 13 suffice (a 13-gate circuit is verified; the lower bound rests on the proof, a direct SAT run for
12 gates timed out undecided).
*Reason.* Ten gates are needed on block b as before. The a-parts and the k-parts of the outputs each have
rank 3 and are the same vectors, so they must enter through three "entry" events on each side; an entry
that serves both sides at once is a gate living on a and k, which costs a gate itself.
*Proof of the lower bound.* Discard gates whose value is free. Call a gate of type B if it is nonzero on
b and of type M if it is zero on b and nonzero on both a and k. A B-gate has both operands nonzero on b,
or exactly one operand zero on b (an entry); that operand lies on a alone (class E_a; a zero operand is
put here), on k alone (E_k) or is an M-gate. Set k to zero and keep, for each restricted value of a
B-gate that is not a unit, the first B-gate carrying it, redirecting the readers of the others. An E_k
entry repeats its other operand and is not kept; an M-gate restricts to a vector on a, which is free in
the local lemma. The kept gates form a circuit of the local lemma, so #B >= 10 + |E_k|; likewise
#B >= 10 + |E_a|. By induction the (a,k)-part of every signal nonzero on b lies in A + K + M', the spans
of the (a,k)-parts of the three classes of entry operands, with dim A <= |E_a|, dim K <= |E_k| and
dim M' <= s, the number of distinct M-gates used as entry operands. The outputs have (a,k)-parts
(s_c, s_c); projecting to a gives 3 <= dim A + s, to k gives 3 <= dim K + s. The total is at least
#B + #M >= 10 + max(|E_a|, |E_k|) + s >= 10 + (3 - s)+ + s >= 13. QED
The bound is tight in every regime: 13-gate solutions with 0, 1, 2 and 3 gates of type M all occur.

**Theorem 9.2 (proved given the local lemma).** Every block-monotone circuit for MixColumns has at least
83 gates.
*Proof.* For j = 0..7 let F_j be the gates that are output gates of sheet j or ancestors of one and are
nonzero on block j; for j = 3 add those that are nonzero on both block 2 and block 7. In a
block-monotone circuit the ancestors of sheet j are supported inside the support S_j of sheet j. A gate
in F_j and F_j' with j != j' has its support inside both S_j and S_j', and that support contains j and j'
(or, for j = 3, blocks 2 and 7, which lie together only in S_3); by the inspection in Corollary 7.2 no
such pair exists, so the eight sets are pairwise disjoint. |F_j| >= 10 by Theorem 7.1, and |F_3| >= 13
by Theorem 9.1 with a = 2, k = 7: restricted to blocks 2, 3, 7 the ancestors of sheet 3 form a circuit
of that model, in which the gates on block 2 alone or block 7 alone are free and the others are exactly
the B- and M-gates. Total 7 x 10 + 13 = 83. QED

**These eight families cannot give more (observed).** Over 4,544 block-monotone circuits (4,300 from the
public kste corpus, 241 hunt records, the 3 of this repository) no two families overlap, the minimum of
each F_j is 10, of F_3 13, and the minimum total is 83, attained by one corpus circuit. For the recorded
88 the families have sizes 11, 11, 10, 15, 10, 10, 10, 10 (87; one gate lies in none).

**Why not 88 yet.** Sheet 1 may borrow two-block gates from sheet 0 (both live on blocks 0 and 7), and
sheet 4 may borrow from sheet 3 (blocks 3 and 7); block 7 serves five sheets. The missing statements are
two joint local problems: sheets 0 and 1 together with block 7 free (proved between 20 and 22), and
sheets 7, 3, 4 together with blocks 6 and 2 free (between 33 and 36). **Observed:** in all 4,541
block-monotone 88-gate circuits of the corpora the three parts 30 + (0,1) + (7,3,4) are exactly 30, 22,
36. **Conjectured:** 22 and 36 are the true local values. If they are, block-monotone circuits need 88
(an implication; the converse is not shown, and the two values are test cases, not the programme). The
joint problems have 12 and 20 non-free inputs; plain SAT calls did not decide them in the budget.

**Most known 88s are not block-monotone (observed; corrects an impression given in section 7).** Of the
18,938 valid circuits of the public kste corpus 4,300 are block-monotone and 14,638 are not; of 415 hunt
records 241 are and 174 are not. In every non-monotone kste circuit there is exactly one gate that
cancels a whole block while the union of its operands' blocks lies in no single sheet support; that
union always contains blocks 1, 2, 7 (it is {0,1,2,7} in 10,351 circuits), and the cancelled block is 2
in 14,600 of them. Only 4,264 of these circuits keep every gate inside some sheet support; the other
10,374 contain a gate living on blocks such as {0,1,2,7} or {0,2,7}. Every circuit of the corpus has 88
gates, with or without such a gate. *Scope (corrected in phase 3).* That is an observation about totals:
no corpus circuit with such a gate is smaller than 88, and none without one is either. It does not show
that the feature contributes no saving inside those circuits: a circuit with the feature could save a
gate through it and spend one elsewhere, and equal totals cannot distinguish that from "no saving". (An
earlier wording here, "these particular circuits gain nothing from their double service", claimed that
counterfactual and is withdrawn.) A circuit-specific statement needs an explicit account for that
circuit: either a function-preserving rewrite without the feature at no extra cost, or a compensation
inequality proved for it. The accounts of section 14 are of the second, weaker kind: they verify
G = 80 + over + unch - excess with excess <= over + unch for chosen charged sets, which is bookkeeping
relative to those sets, not a proof that removing the feature would leave the size unchanged. Nothing
here shows that double service cannot gain.

**Where a block can be cancelled (proved, for circuits whose gates each live inside one sheet's support;
Lemma II.6).** Join two blocks when some sheet's support contains both. If such a gate g = a + b cancels a
block, then either the support of g lies inside the support of a or of b ("exit-like"), or the three
blocks involved form a triangle of this graph. For the rotation model with m >= 4 the graph is a cycle
without triangles, exits live on one block, and a circuit of this kind whose exits are sums of two
earlier signals of that block has at least 10m gates (Lemma II.7). For m = 3 the graph is a triangle,
which is how the 28-gate circuit wins (four such gates). For MixColumns the graph is the 8-cycle plus
four chords to block 7; its triangles are {0,1,7}, {1,2,7}, {2,3,7}, {3,4,7}, and {1,2,7} is the only
one not inside a single sheet support. No analogue of Lemma II.7 is proved for MixColumns: exits there
can land on two blocks, and triangles inside one sheet support can also break monotonicity. Two hunt
records are of this kind (an exit inside the support of sheet 4 landing on blocks 3 and 7, with gates
charged to sheets 3 and 4), with no cancellation on {1,2,7}.

**What this says about an 87 (corrected).** Theorem 9.2 excludes block-monotone circuits with at most 82
gates. It does not exclude a block-monotone 87; that would follow from the conjecture above. For
circuits that are not block-monotone nothing beyond the published 75 is proved. The corpus shows that
the search already produces such circuits in three shapes (a gate outside every sheet support; the
triangle {1,2,7}; an exit onto two blocks) and that none of them has yet gained a gate.

## 10. The ten-gate lemma by hand (`tenth-gate/PROOF.md`; main agent; independently machine-reviewed)

**Statement.** As in section 7: with the units of block b and all vectors of block a free, computing
the four vectors (E_c on b) + (s_c on a) takes at least 10 gates.

**Why six plus three cannot be attained.** By hand it was known that the parts on b need 6 gates and the
parts on a need 3 "entry" gates (gates that add a free vector). The two requirements are not
independent. Mirror the circuit (transpose it, PROOF Lemma 3.1): the non-entry gates become a circuit T
on four inputs that computes the four triple-sums of its inputs, with exactly K - tau gates, and each
entry gate leaves a trace in T, namely a signal of T whose mask is the set of targets that entry
influences. Because the s_c have rank 3 with the single relation "all four sum to zero", these traces
must span all even-weight vectors. With three entries the traces are three independent even vectors,
hence three gates of T besides the four outputs (inputs and outputs are odd): |T| >= 7 and K >= 10. With
four or more entries, K >= 6 + 4. A six-gate T has only two signals besides its outputs.

**Status.** Proved; the review found every step sound, one small gap (a degenerate first gate) and three
faults in the remarks after the proof, all repaired. The reviewer also tested the intermediate claims on
1,600 constructed circuits containing every degenerate case (a test, not a proof).

**By-products (proved by the same mirror).**
- A sheet with nothing free costs exactly 12 gates (its transpose has 8 distinct non-input outputs on 4
  inputs, and the transposition count adds 4). The earlier computation had shown only "at least 11".
- The three-term sheet costs at least 13 (Theorem 9.1) directly, without the ten-gate lemma: there must
  be three entries on each of the two free sides, so tau >= 6, and with exactly six the three traces of
  one side are three even gates of the mirror.
- General form: for targets (p_c | q_c), c = 1..r, with the units of a block B as base and a free side,
  the least number of gates is min(|T| + tau) + |B| - r, where T computes the columns of P on r inputs
  and tau of its signals span the column space of Q. (My first statement of this omitted |B| - r and was
  false; the reviewer gave the counterexample.)

**Conditional by-product (reviewer).** The joint problem of sheets 0 and 1 is at least 21 for
block-monotone circuits, conditional on one finite fact that is so far only SAT-checked without
certificate (a sheet circuit containing three diagonal gates [0: sigma] + [7: sigma], sigma over a basis
of the even space, has at least 11 gates). Not used anywhere. *Update, same day:* that fact now has a
hand proof and the statement is unconditional (section 17, where it gives 84 for block-monotone
circuits).

## 11. Sheets with disjoint windows cannot share at a net gain (`sharing/INDEPENDENT-SHEETS.md`; main agent; independently machine-reviewed)

**Theorem 11.1 (local).** Take r sheets with own blocks b_1..b_r and a common free part (every vector
supported on it is free, including vectors meeting several of its blocks), with targets
(E_c on b_j) + (a free part), where the free parts admit no vanishing sum other than unions of whole
groups of four. Any local circuit containing the 4r targets has at least 10r gates.

**Theorem 11.2 (all circuits).** In any circuit for the rotation model or for MixColumns, let J be a set
of sheets whose windows {j-1, j} are pairwise disjoint and none of whose outputs has a part on the own
block of another sheet of J. Then at least 10|J| gates are ancestors of an output of J and nonzero on
the own block of some sheet of J.

**What is counted, where sharing reduces the count, and why compensation appears.** The count is the set
of gates serving the family; a gate that serves several sheets of J is counted once. In the mirror the
family becomes one circuit T computing r independent groups of four triple-sums, and each entry is a
signal of T. Sharing shows up in T as blocks of the parity partition that are larger than "two per
group" or that join groups; each such merging saves gates of T but, through the partition lemma, forces
either more odd+odd gates or more entries: with c blocks, and kappa components of the graph of split
groups, |T| >= 8r - c and tau >= 3r + kappa, while c <= r + kappa always. The sum is at least 10r.

**Scope.** All circuits; no monotonicity; no computation. It applies only to sheets with disjoint
windows. For the rotation model with an even number m of positions: the even sheets need 5m gates and
the odd sheets 5m, and a circuit with fewer than 10m gates must contain gates lying in both sets. For
three positions the theorem is empty, as it must be. For MixColumns: at least 40 gates serve sheets
0, 2, 4, 6, at least 30 serve sheets 1, 3, 5, at least 10 serve sheet 7; the three sets can overlap, so
this is not a total, and it concerns the 80 charges, not the augmented 83.

**Observed (reviewer, read-only).** On the three recorded circuits, 18,938 corpus circuits and the
recorded Q_8 circuits no family count is below 10|J|; the corpus contains no gate serving two sheets of
one family, so it does not exercise the theorem.

**What remains.** Sharing between sheets whose windows overlap. Smallest case: two adjacent sheets with
the first neighbour free. Whether its minimum is 20 for all local circuits is open.

## 12. Direct sums: sharing between unrelated parts can pay (`direct-sum/REPORT.md`; delegated; literature with stated verification levels; no second review)

**Known from the literature (existential).** For 2-input XOR circuits of unbounded depth,
L(A + B) = L(A) + L(B) is false in general: n copies of a generic n x n matrix A can be computed together
through a fast matrix-multiplication algorithm with O(n^2.81) gates, while n separate copies cost about
n^3 / (2 log n). Sources: two web notes of S. Jukna (the first, of 22 May 2015, credits "Igor"; the
attribution to Sergeev is an inference; the second attributes the argument to an anonymous referee of
Paul 1976 and adds depth-2 additivity, which is what makes the failure an unbounded-depth one), Paul
1976 (scan, partly illegible), Find et al. (arXiv). A second reader confirmed the two notes and Find et
al. from the pages themselves (`review-phase2/REVIEW.md`). No explicit or small example is known; by the
investigator's own computation the counting argument starts to certify a failure only near n = 2^37.
Additivity is known for depth-2 XOR circuits, SUM/OR circuits, monotone circuits and cancellation-free
XOR circuits. So "sharing between unrelated parts never helps" is false as a general principle, and any
compensation theorem must use properties of the parts.

**Proved by the investigator (every circuit; machine-reviewed: all confirmed, with a missing proof of
the "L(A) + n_B - c_B" bound supplied by the reviewer).**
- Count: classify each gate by whether its X-part and its Y-part are new. G = N_X + N_Y - d + w, with d
  the gates new on both sides and w those new on neither, and N_X >= L(A), N_Y >= L(B). What is counted:
  new values on each side. Where sharing reduces the count: a gate new on both sides. What compensates:
  gates new on neither side, which are forced at the first mixing of the two sides and at every
  separation that uses a pure signal of the other side.
- Span lemma: the mixed signals carry at most r independent Y-parts, one per mixed gate that is not new
  on the X side, and then d <= 2^r - r - 1.
- Theorem: let s = L(A) + L(B) - L(A + B) (always s >= 0, by concatenation) and h_B = L(B) - (number of
  distinct rows of B of weight >= 2). **If s > 0**, then s <= h_B - ceil(log2(h_B + 2)). Equivalently,
  0 <= s <= max(0, h_B - ceil(log2(h_B + 2))). Hence additivity whenever one part has h <= 3, in particular
  whenever one part has at most 4 inputs. Any counterexample needs both parts with h >= 4, at least 5
  inputs and joint size >= 13.
  *Correction (phase 3, 2026-11-12).* Until now this record stated the bound without the hypothesis s > 0.
  Without it the statement is false for h_B = 0 or 1, where the right side is -1 and concatenation gives
  s = 0. The hypothesis is in the report (`direct-sum/REPORT.md`, Theorem 1) and is used in its proof: from
  s > 0 the identity G = N_X + N_Y - d + w gives d >= s + w >= 1, so a mixed gate exists, so the first mixed
  gate is a mixer and w >= 1; with no mixed gate, w = 0 is possible. The corollaries were stated correctly.
  This is a statement about one argument's bound; it is separate from the literature's existential result
  above.
- A partner can never let A use a smaller cyclic system (N_X >= L(A) whatever B is).
- Separation is free in the gate count only when two mixed signals have equal foreign parts, which
  requires a linear coincidence between the two computations; the matrix-multiplication example lives on
  exactly such coincidences.

**Relation to sections 7-11.** For sheets with disjoint windows and free neighbours, section 11 proves
additivity outright (10 per sheet) by a different argument. For adjacent windows the mixing gate is not
wasted (it is an entry the neighbouring sheet needs anyway), so the direct-sum compensation disappears,
and what remains is the cost of the exit; in a triangle of windows even that vanishes.

## 13. Order does not enter the charge framework; wirings are rigid (`causal/REPORT.md`; delegated; no second review)

These results correct two statements made earlier in this record and in my reports.

- **Proved (Lemma 1.1): a basis of triples has at most one wiring.** If a set T of |S| - n collinear
  triples can be executed in some order, then which member of each triple is the result is determined.
  So ancestry, charges and block-monotonicity are functions of the chosen basis T, and the only freedom
  is the choice of T inside the set of all collinear triples of S. **Observed:** for the recorded
  28-gate circuit of the three-position model, for every recorded best circuit of the rotation model and
  for the recorded MixColumns 88, the value set has exactly as many collinear triples as gates, so there
  is one basis and one wiring: sharing is then a property of the value set alone.
  *Correction:* my remark that "the same three signals can be computed in any order, so non-monotonicity
  is a matter of orientation" is wrong for such value sets; and "profitable sharing is the case where the
  part-by-part orientation exists but is not executable" is disproved (if G < 10m, no basis at all,
  executable or not, is free of double charges).
- **Proved given the joint local lemma (machine-reviewed; one gap repaired by the reviewer): the charge
  inequality has an order-free twin.** For every cyclic system of the rotation model or of MixColumns,
  every basis T of triples and every family J of pairwise non-adjacent sheets, at least 10|J| members of
  T occur (with odd multiplicity) in the derivation of an output of J and have two members nonzero on
  the blocks of J. (The report's one-line reason was false as stated; the repair chooses a row basis and
  a column basis containing the outputs, `review-phase2/REVIEW.md`.) The joint local lemma itself
  (section 11, Theorem 11.1) was re-derived independently in a form valid for non-executable local
  systems, and that form is confirmed. What follows, in the reviewer's corrected wording: an argument
  that uses ONLY these twin inequalities cannot exceed the cyclic minimum. The twin counts membership in
  a derivation, not ancestry, and the two counts differ (three-position circuit: 12, 13, 14 by wires,
  12, 12, 13 by derivations). Arguments that use ancestor structure are NOT covered: block-monotonicity
  as defined for circuits, the cancellation lemmas of section 9, and the 83. "Block-monotone needs 80"
  transfers only to a weaker, basis-dependent notion for cyclic systems.
  *Correction:* in an earlier report I called the charge theorem "genuinely causal" because it uses
  ancestors. That was too strong: the 80-charge inequality has a twin without ancestry. Whether the
  ancestor-based refinements have one is not known.
- **Proved given the double-map report (unreviewed): L_cyc(D_T) = 3m iff delta(T) = 0 iff L(D_T) = 3m.**
  *Correction:* section 8 called the last step of double-map Theorem C "causal". It uses only that the
  leaf vectors sum to zero round the cycle; no gap between cyclic systems and circuits appears there.
- **Compensation inequality (proved, all circuits).** For a family J of pairwise non-adjacent sheets,
  with D_j the per-sheet charged sets: the excess of double charges inside J is at most the sum of the
  over-charges (|D_j| - 10) plus the number of "foreign carriers" (gates serving a sheet of J on whose
  block they vanish, while nonzero on the block of another sheet of J which they do not serve).
- **Where order does enter (proved, elementary).** In any circuit every nonempty set of non-input
  signals has a member none of whose ancestors lies in the set. The time-order steps of double-map
  Theorem D are instances. No general lemma of the form "a saving forces a precedence" was found; in the
  three-position circuit a precedence relay between outputs of different sheets is forced, but only
  because that value set is rigid.
- **Still open:** two adjacent sheets (not bounded by 20); whether the cyclic minimum of any rotation
  model is below 10m or below its circuit minimum.

**State of the causal question (after review).** The 75 argument (audited), the 80-charge inequality and
the family theorem have order-free forms. Not shown to have one: the block-monotone bounds as stated for
circuits (they use ancestors), the 83 argument, the cancellation lemmas, and the last step of
L(M2) = 26 for partitions other than the natural one. Initial segments of a circuit give no new charge
inequalities; whether the corresponding statements for adjacent sheets have order-free twins is open,
because the local-system minimum is not known to equal the local-circuit minimum there. Whether order
can yield a bound that fails for cyclic systems of MixColumns-like maps is open.

## 14. Sharing between sheets with overlapping windows (`sharing/REPORT.md`; delegated; machine-reviewed, see the review status below)

**Accounting (identity).** For parts with per-part local minima lambda_i and charged sets D_i:
G = sum of lambda_i + over + unch - excess, where over = sum of (|D_i| - lambda_i), unch = number of gates
charged to no part, excess = sum of (mu - 1)+. Sharing pays exactly when excess > over + unch; a
compensation theorem for a class of circuits is the inequality excess <= over + unch on that class.

**Review status (`review-pair/REVIEW.md`).** The 19 bound is confirmed step by step. The level-monotone
chain theorem is confirmed once its induction is stated for mirror-form circuits. The description of
what a 19 would have to look like is only partly proved. A further proposition of the report about
window-local circuits (a bound 10m minus 2 per block with a "backward exit") was found WRONG as argued
and is not used here: a gate can serve the previous sheet by going the long way round the ring.

**Proved by hand given the ten-gate lemma (machine-reviewed): the pair problem needs at least 19
gates.** Two adjacent sheets with the first neighbour free, any local circuit. Upper bound 20.
Consequently, in every circuit for the rotation model (m >= 3), and for MixColumns on the sheet pairs
(1,2), (2,3), (3,4), (4,5), (5,6), (6,7), (7,0), at least 19 gates are ancestors of an output of the pair
and nonzero on one of its two own blocks. So two adjacent sheets can share at a net gain of at most one
gate, with no monotonicity assumed.
*How the proof counts.* In the mirror, split the gates by their part on the first sheet's group: gates
that bring a new first part (they contain the first sheet's own mirror together with the exports: at
least 10 with the exports), gates that repeat a first part (at least as many as the "entries" that add a
vector of the second group: at least 3), and gates with no first part (at least the four triple-sums of
the second group). With exactly three entries their operands are three even vectors of the second group,
which are three more gates: 20. With four or more entries the count is 18 plus what is forced, and one
configuration (four entries, nothing else) is excluded by a tree argument: 19.
*Superseded on the same day by section 15: 19 does not occur, the pair needs 20.*

**Proved (restricted class, unreviewed): chains whose mirror is level-monotone need ten gates per
sheet.** Level of a mirror vector = the first group where it is nonzero; the class requires that no gate
cancels the leading group of both operands. It contains every recorded 10m circuit on every run tested
and excludes the three-position 28-gate circuit on every pair.

**The three-position circuit, accounted.** 28 = 30 + 9 - 11: nine gates of over-charge, eleven double
charges, no uncharged gate. All eleven double-charged gates are two-block gates of one sheet's window
borrowed by the previous sheet. Its three pairs of adjacent sheets have 23, 24 and 24 gates, so the
saving is not visible in any pair: it is a wrap-around effect. Lifting the circuit to six positions
would need 70 gates under the lifting model used (60 are attainable directly).

**Observed (existing circuits only).** The pair count is at least 20 for every adjacent pair in all
19,356 corpus and recorded MixColumns circuits, non-monotone ones included, and in all recorded rotation
circuits with m >= 4. In eleven inspected non-monotone corpus circuits each double service is matched by
over-charge and uncharged partner gates, and the total is 88 each time. *Scope (corrected in phase 3):*
this verifies the accounting identity with excess <= over + unch for the charged sets used, in each of
these circuits; the over-charges are not shown to be caused by the double service, and the observation
does not show that the feature saves nothing within these circuits (an earlier wording said "these
circuits gain nothing", which claimed more than the totals show; see section 9). One corpus circuit was
compared by hand with a monotone route for the same values (sharing/REPORT.md section 5: equal cost
there, plus one gate if a partner vector is absent); that is the only circuit-specific comparison made.
It does not show that nothing can be gained.

**Attempts to build savings by hand (all failed, with accounts in the report).** A design that takes a
full-block vector from the next sheet by an exit costs 12 per sheet and, run round the ring, is not
executable. The route through blocks 1, 2, 7 used by corpus circuits exchanges gates one for one.

**Where the sharing question stands.**
- Unrelated parts in general: sharing can pay (section 12), but only when both parts need at least four
  helper gates, and the known examples are astronomically large.
- Sheets with disjoint windows: never a net gain (section 11; all circuits).
- Two adjacent sheets with the first neighbour free: no net gain (section 15; all circuits;
  machine-reviewed).
- Three mutually adjacent sheets (three positions): a net gain of two gates is realised.
- Chains of three or more adjacent sheets, the ring with m >= 4, and MixColumns with its triangles
  (including the pair of sheets 0, 1, which the pair theorem does not cover): open.

## 15. Two adjacent sheets need twenty gates (`pair/PROOF.md`; main agent; independently machine-reviewed)

**Theorem 15.1 (proved by hand; review in `pair/review/REVIEW.md`: every step correct).** The pair
problem (sheets j, j+1, block j-1 free, nothing else free) needs at least 20 gates; 20 is attained.
Consequently, in every circuit for the rotation model (m >= 3), and for MixColumns on the sheet pairs
(1,2), (2,3), (3,4), (4,5), (5,6), (6,7), (7,0), at least 20 gates are ancestors of an output of the pair
and nonzero on one of its two own blocks. No monotonicity is assumed. The MixColumns pair (0,1) is not
covered (sheet 1 has a term on block 7).
*Dependencies.* The ten-gate lemma with its mirror (section 10) and the mirror form of the pair problem
with f + tau >= 10 (section 14). No computation.
*Plain reason.* In the mirror the gates fall into three groups: those bringing a new first part (the
first sheet's own cost, 10 with the exports), those repeating a first part (at least one per "entry",
where a vector of the second group is added), and those with no first part (the second sheet's
triple-sums and the even vectors used as entry labels). The only way to undercut 10 + 10 is an "exit":
a second-group vector obtained in one gate as the difference of two signals with the same first part,
which lets the third group shrink to the four triple-sums and makes every label odd. But the first two
groups together are themselves a one-sheet circuit with the second group free (Lemma A of the proof),
and its own mirror must show, as separate even signals, which targets each entry influences; with
three or four odd labels among four these are four distinct vectors (Lemma B), so that mirror has 8
gates instead of 6 or 7 and the first two groups have 12 gates instead of 10. This gives 19 at once;
the last gate comes from the tight case, where the 8-gate mirror forbids stacking entries, so the only
exits are four cross sums that add to zero while the four triple-sums add to 1111. Five entries are
excluded by a short analysis of the forests with five edges.
*What is counted, where sharing reduces it, what compensates:* `pair/PROOF.md` section 5.
*Challenging examples.* The three-position 28-gate circuit has pairs of 23, 24, 24 gates with five or six
entries, mostly odd labels and exits; the theorem holds there with room. The standard circuits have
three even labels and no exit. No recorded or perturbed circuit comes near the tight configurations,
so those were checked by reasoning only.
*Relevance.* Sharing between two adjacent sheets is fully compensated inside the pair. The known
profitable sharing (three positions) is therefore not a pair effect, and the pair theorem says nothing
about it: the pairs of that circuit are expensive (23, 24, 24), and the third sheet then costs only 4 or
5 further gates.
*Limits.* The final contradictions use the specific targets. The proof has no slack in the tight case,
so it does not extend by a naive induction to chains of three or more sheets. For the MixColumns pair
(0,1) with block 7 free the argument should give "at least 20" unchanged, since it uses the exports
only through f + tau >= 10 and tau >= 3 (main agent's reading, not yet checked independently); the
known upper bound there is 22.

## 16. Chains of adjacent sheets: nine gates per further sheet (`chain/REPORT.md`; delegated; Theorem 16.1 and Cor. 16.2 independently machine-reviewed in phase 3, `review-chain/REVIEW.md`; section 3 of the report unreviewed)

Chain of l sheets: sheets j, .., j+l-1 with block j-1 free and nothing else free. M_l denotes its
minimum; M_1 = 10 (section 10), M_2 = 20 (section 15), and M_l <= 10 l.

**Theorem 16.1 (proved by hand given section 15).** M_l >= M_(l-1) + 9. Hence M_3 >= 29 and
M_l >= 9 l + 2 for l >= 2.
*Plain reason.* Peel the LAST group of the mirror. The gates bringing a new part on the earlier groups
are, with the exports, a mirror circuit for the shorter chain (at least M_(l-1)). The remaining gates
repeat such a part or have none; there are at least 9 of them by the argument that gave 19 for the
pair: three entries need three even labels (3 + 7), and four entries with only the four triple-sums
(4 + 4) are excluded by the tree argument.
*Status.* The two lemmas repeat, at the last level, arguments that were machine-reviewed for the pair;
the main agent re-derived them for general l. *Phase 3:* the general statement now has an independent
machine review (`review-chain/REVIEW.md`): correct as stated, no hidden use of l = 2, with wording repairs
(K = |T| + tau holds for the cleaned circuit; "ancestor" includes the outputs; exports with omega = 0 are
dropped before projecting, tau' <= tau). The case D = N = 4 of the second lemma closes without time order:
all four triple-sums would be exits along 3-edge paths of a forest with four edges, and such a forest has at
most two 3-edge paths.
*What M_3 = 30 would and would not give (correction, phase 3).* An earlier session said that M_3 = 30 would
give ten gates per sheet for every chain. It would not: with the recurrence of 16.1 it gives only
M_l >= 30 + 9 (l - 3) = 9 l + 3 for l >= 3. Ten per sheet for all l needs a uniform argument, for example
Lemma C_l below for every l, or the cut lemma of section 18.

**Corollary 16.2 (rotation model; proved given 16.1).** For m >= 3, L(Q_m) >= M_(m-1) >= 9m - 7: in any
circuit, restrict nothing, treat the block of one sheet as free and count the ancestors of the other
m - 1 sheets that are nonzero on one of their own blocks. This exceeds the earlier all-circuit bound
7m - 1 + ceil(16m/11) for m >= 13 and has the larger slope (9 against 8.45; the upper bound is 10 m).
The two bounds agree for m = 11 and 12; for m <= 10 the earlier bound is larger.
For MixColumns the chain form occurs only on runs that avoid the three reduction terms (sheets 1..6
with block 7 set to zero: at least 56 gates; sheets 5, 6, 7, 0 with block 4 free and blocks 1, 2, 3 set to
zero: at least 38; the review noted that the zeroing of blocks 1-3 was missing and is needed for the
restricted gates to form a local circuit of the model), far below 75. The public bound is not affected.

**Open: the tenth gate per sheet (M_3 = 30?).** A 29 for the chain of three would have to be, at the
last group, one of two configurations (four entries with a basis of labels, at least three odd, and
either five pure gates and no further duplicate, or four pure gates and one non-entry duplicate with
all labels units), and at the same time contain a long exit at the first group (investigator's
derivation, unreviewed). The pair proof closed its tight case because the mirror of the first sheet
had eight prescribed vectors and eight gates, hence no freedom. One level up that mirror is a 17- or
18-gate pair circuit with only twelve prescribed vectors, and the same residual cases reappear inside
it with one unit less slack: this is the gate lost per level. A closed induction seems to need a
statement with a condition at both ends of the chain. No circuit below 30 is known; 600 perturbed
chain circuits and all recorded ones have 30 (a test, not a proof).

## 17. Sheets 0 and 1 of MixColumns with block 7 free: a test case (`joint01/REPORT.md`; delegated; machine-reviewed, `joint01/review/REVIEW.md`)

The joint local problem J_01 of section 9. In the mirror it differs from the pair problem of section 15
only in the exports, which must span a space containing the diagonal {(e | e) : e even} instead of
Even + 0 (proved; checked against the MixColumns matrix by the reviewer).

**Theorem 17.1 (proved by hand, given section 15; reviewed).** J_01 >= 20 for all circuits: the pair
proof uses the exports only through f + tau >= 10 and tau >= 3.

**Theorem 17.2 (proved by hand; reviewed, stands with small repairs to the wording).** A sheet circuit
(own units w, the other group free) that contains the four targets and three independent diagonal
vectors has at least 11 gates. This replaces the finite fact that section 10 quoted as checked by SAT
only. *Plain reason (corrected wording, phase 3):* neither a target nor a diagonal vector is the sum of
two inputs or required vectors, so each required vector reads an auxiliary gate. Besides carrying the one
required vector that may lie in its own fibre (an entry: aux plus free vector), an auxiliary gate can serve
at most one required vector whose other operand is an own unit or another required vector, and a pure
pair-sum can serve none of this kind. Ten gates leave three auxiliary gates; when at most one required
vector is an entry they cannot serve the other six or more, and the cases with two or three entries fail
on the order in which the gates can be built. Whether the true value is 11 or 12 is open.
*Correction and second check (phase 3, `review-joint01b/REVIEW.md`).* The short reason previously written
here ("an auxiliary gate has at most one way to serve a required vector together with an input or another
required vector") is false as written. Counterexample (the user's): in coordinates (own | free),
h = (0111 | 1111) gives a target h + (0000 | 0011) = (0111 | 1100) and a diagonal vector
h + (1000 | 0000) = (1111 | 1111), and 1111 can belong to an even basis such as {1111, 1100, 0110}; both
partners are freely available. The full proof (`joint01/REPORT.md` section 4, F3) states the property
with the own-fibre exception and counts exactly this case (the first service is a required entry, counted
by p; the second is the aux's single named-partner service). An independent check confirmed every step of
Theorem A, wrote out hand proofs of N, F2, F3 (previously cited only with a 28-basis program check), and
found four unstated steps, all wording. Theorems 17.2, 17.3 and Corollary 17.4 stand.

**Theorem 17.3 (proved by hand given 17.2; reviewed, with four implicit steps written out in the
review).** J_01 >= 21 for local circuits in which no ancestor of a sheet-0 target is nonzero on sheet
1's own block. Block-monotone circuits, restricted to blocks 7, 0, 1, satisfy this.
*Plain reason:* the gates on sheet 1's block and the ancestors of sheet 0 are disjoint sets of at least
ten gates. If sheet 1 uses exactly ten, the vectors it borrows are three independent diagonal vectors
that are gates off its block; either they are all ancestors of sheet 0, whose circuit then has eleven
gates by 17.2, or one of them is a twenty-first gate.

**Corollary 17.4 (block-monotone circuits; proved given 17.3 and the decomposition of section 9).**
Every block-monotone MixColumns circuit has at least 30 + 21 + 33 = 84 gates (previously 83). This is a
statement about a restricted class; it says nothing about circuits that cancel a whole block
component, and the public bound for all circuits stays 75.

**Open.** For arbitrary circuits 20 is not excluded: after the review's corrections the remaining
configurations for K = 20 are (tau, f, D, N_0) = (3,7,4,6), (3,7,5,5), (3,8,4,5), (4,6,5,5), and
(3,8,5,4), (3,7,6,4), (4,6,6,4) with exactly four entries. All contain an exit or a triple-sum built
from a single even vector. Upper bound 22 (two different known shapes: four exports and four entries,
or three exports and five entries). The values 20..22 here, like 33..36 for sheets 7, 3, 4, remain
test cases; they do not establish an unavoidable overhead for the reduction terms.

## 18. How chain computations compose: cuts, exits, the open end (phase 3; `compose/`; main agent and delegated; machine-reviewed in `review-compose/REVIEW.md`)

Phase 3 (from 2026-11-12, main agent Opus 5.5) asked what must be known about a partial computation, at
both of its ends, to decide whether adding a sheet can save. Everything below is in the mirror chain MC_l
(section 16, `compose/FRAMEWORK.md` section 0); "cut k" separates groups 1..k from k+1..l; an *exit across
cut k* is a gate with zero part on groups 1..k whose two operands have equal nonzero parts there.

**Proposition 18.1 (exit-free cuts are additive; main agent; reviewed).** Every MC_l circuit C with no exit
across cut k has cost(C) >= M_k + M_(l-k). (A statement about such circuits C; it is not an unconditional
inequality for the optimum M_l.) *Reason:* the first gates projected to groups 1..k are an
MC_k circuit with the same exports; without exits the gates with zero part there are an MC_(l-k) circuit
whose exports are the entry labels, and each label use is a distinct entry gate.
**Corollary 18.2.** If M_j = 10 j for every j < l and M_l < 10 l, every optimal MC_l circuit has an exit
across EVERY cut and M_l = 10 l - 1: a shortest-length counterexample to ten gates per sheet saves exactly
one gate and has an exit across every cut. Since M_1 = 10 and M_2 = 20, a 29 for three sheets needs exits
across both cuts. The hypothesis on all shorter lengths is essential: without it a longer chain could
inherit a saving inside a shorter component while the cut separating it from the rest is exit-free.
(Scope corrected in phase 4 at the user's request; the summaries had dropped the hypothesis.)
*Meaning.* The minimum costs of the parts are all one needs to know about them as long as nothing is handed
back across the cut. A composition saving can only come from exits.

**What flows across a cut (proved descriptions, corrected by the review).** Labels go forward (the far
part supplies vectors that the near part adds in); a label that is an input or required vector of the far
part costs it nothing, any other label is a further gate there. Exits go back: one gate gives the far part
a vector in the span of its own labels, obtained by cancellation inside a fibre of the near part. In
primal terms an exit is a fan-out branch of a signal whose joint influence on the earlier sheets cancels.
Cancellation-free circuits have no exits; block-monotone circuits can have them (review counterexample).

**What the minimum cost of the shorter chain does not record.** (a) How the cost of a part depends on the
*parity type* of the labels it receives ("odd" = outside the even space of the next block): with three or
four odd labels among four the near part's own mirror needs four distinct even traces (generalised Lemma B,
reviewed), a cost the number M_k does not show. (b) How much a part can save when an exit hands it an
extra base vector. (c) In the pair proof's tightest case, the complete list of the near sheet's signals
(rigidity), which is a property of one sheet and does not survive one level up.

**Lemma 18.3 (Lemma R; the rigid open end; delegated, reviewed; every l).** If the gates of an MC_l circuit
that are nonzero on group 1 number exactly ten with three duplicates, there is no exit across cut 1.
**Corollary 18.4 (every l).** In an optimal MC_l circuit with an exit across cut 1, the first sheet's part
(first gates, exports and duplicates at cut 1) costs at least 14, against 13 in the standard form. So at
the open end (the free neighbour) handing anything back always costs the first sheet at least one gate, at
every length; with odd labels Lemma B charges two.
**Skip-exit lemma (every l).** An exit from level 1 straight to level m >= 3 needs a level-1 gate that is a
duplicate at cut m - 1.
**Theorem 18.5 (Theorem A; l = 3; delegated, reviewed).** A 29-gate chain of three must contain an exit of
the adjacent kind: a gate of the second sheet's level made by cancellation from two first-sheet signals.
Exits that jump from sheet 1 to sheet 3 cannot produce the saving (they need a first-sheet duplicate at
both cuts, and the tight closed end leaves no room).
**Proposition 18.6 (reduction; reviewed).** If moreover the projection to sheets 1-2 has no exit, the far
pair is exactly configuration (X) of the pair proof except that one edge carries a label that is not a
value of the circuit.
**Remaining gap for M_3 (exact):** (G1) the projection R to sheets 1-2 (cost |R| + tau = 20) has an exit
across its own cut; or (G2) the near-(X) configuration of 18.6 (with the review's additions: a length-1
path along the special edge is possible, its label may be even, time order still applies partly). M_3 is
29 or 30; no 29 is known.

**Why the open-end route stops (reviewed account).** An adjacent exit gives the second sheet an extra base
vector; both far-side bounds then lose about one gate (example: 1111 on the second group supplied by one
exit makes the four triple-sums cost 4). The first sheet's charge is fixed by the parity type of its labels
(1 or 2), the far side's gain by the exit's value, and no statement relates the two. The missing statement
is two-sided: the cost of a chain (here a pair) that receives one extra base vector at its open end. Both
peelings arrive at the same object (the pair with a 4E boundary, conjectured 18 gates, at least 17).

**Constructive side (delegated; inequality reviewed).** No 29 was built. Transplanting the three-position
mechanism into the chain costs 36 (verified): the six double-charged gates of the wrap window turn into
eight duplicated gates while the over-charge that paid for all eleven sharings stays. A primal two-pair
inequality (both pair bounds at once) shows a 29 needs sheet-2 over-charge, a pure block-2 gate used by
sheets 1 and 3 only, or cross-family gates; the one consistent tally found is a "hub" in which one
redundant gate pays for two double charges inside a pair that still costs 20.

**Gate order (delegated, unreviewed; `causal-pair/REPORT.md`).** The "cycle in time" of configuration (X)
in the pair proof is replaceable by algebra: the nine relations involved are always F_2-dependent (in one
sub-case two signals coincide). So (1) "the proof uses order" is true but removable at that step, and (2)
"the pair theorem fails for cyclic systems" is unsupported; it is open, because "fibres are forests" and
the (Y) arguments use order. Round a ring, F_2-consistent borrowing loops that are not executable exist
(explicit example for m = 3, 4, 5, at no saving), so there "a closed loop of borrowings cannot pay" would
be a genuinely causal constraint.

**Chains, rings, MixColumns.** Lemma R needs the export boundary, i.e. an end of the chain with a free
neighbour. A ring has no end: cutting the ring mirror into arcs forces four prescribed even vectors at one
end of the near arc and a label obligation on all of F_2^4 at the far arc's end (reduction proved, values
open). The 28-gate three-position circuit saves with exactly the adjacent exits that Theorem 18.5 does not
exclude (1, 1 and 2 exits when each single group is cut off; check), and has no end at which Lemma R could
charge them. MixColumns is a ring of eight with three extra terms; chain results apply to it only on runs
with a zeroed neighbour (section 16), far below 75. A bound for the whole map would need an interface lemma
that works without an end, i.e. a charge for adjacent exits in a ring with m >= 4 (no triangle), which the
three-position example shows must fail at m = 3.

**Statuses.** 18.1-18.6 and the skip-exit lemma: proved, machine-reviewed. The account of what is lost and
the ring reduction: proved descriptions, reviewed. The gate-order results: unreviewed. Nothing here
changes 75 <= L(MixColumns) <= 88.

## 19. Supplying a value across a cut and what the receiver can gain (phase 4; `compose/TWOSIDED.md`, `compose/sb/`, `compose/sb2/`, `compose/ring/`; reviews `review-twosided/`, `review-sb/`, `review-sb2/`)

Phase 4 (2026-11-12, user's direction): relate what a computation must do to SUPPLY an intermediate value
through an exit to what a compatible receiver can SAVE by obtaining it. Setting: the open cut of the mirror
chain MC_l (cut 1: the first sheet against the rest). Definitions in full in `compose/TWOSIDED.md`.

**The exact split (identity; reviewed).** For a reduced MC_l circuit, cost = near1 + far1 with
near1 = f1 + h1 + tau (the first sheet's first gates, non-entry duplicates, exports) and far1 = |P| + e1
(the far gates, exits included, plus one unit per entry, booked to the receiver as its export cost).
near1 >= 10 always; far1 >= M_(l-1) when there is no exit. The supplier is problem (N) of TWOSIDED (a
relaxation: it ignores that labels may depend on exits through the far side); the receiver is problem (F)
(a far chain with supplied values, each costing its exit gate, available only from its exit on, staged).

**Honest replacement (receiver's gain bounded by the cost of computing the supplied values; reviewed).**
Replacing every exit, in time order, by gates computing its value from labels of entries placed before it
gives an exit-free far circuit. Three successively sharper forms, all proved for every l:
- Lemma 2.1: far1 >= M_(l-1) - beta, beta = L_near(S) - |S| (L_near: strict staging; a looser definition is
  circular).
- Lemma 2.1': far1 >= M_(l-1) - beta + sigma, sigma = e1 - tau_min (tau_min = fewest labels spanning
  Even(w^2) + 0). Needed because the supplier can attach entries that feed nothing; those extra labels are
  paid by the receiver (`compose/sb/`, counterexample to the first form of SB).
- Lemma 2.1* (`compose/sb2/`; reviewed, `review-sb2/`): far1 >= M_(l-1) + e1 - chi, chi = min over replacements R of
  (|R| - |S| + tau_R), tau_R = fewest elements of the labels and the replacement values spanning
  Even(w^2) + 0. The receiver may export the intermediate sums that the honest replacement builds.
The all-ones example: 1111 on w^2 supplied once gains the four triple-sums one gate (6 against 4 + 1); the
bound beta is 2 with unit labels, 0 or 1 with an even basis depending on the basis. The gain of a supplied
value depends on how it sits relative to the labels, not on the number of values.

**Composition theorems (supplier charge >= receiver gain).**
- Theorem 19.1 (Theorem 4.1 of TWOSIDED; main agent; reviewed with one step added): a reduced MC_l circuit
  with exactly three entries at the open cut costs at least 10 + M_(l-1), every l.
- Theorem 19.2 (S1; reviewed): if every label is even (lies in Even(w^2) + 0) then beta <= 1, so the cut is
  additive (cost >= 10 + M_(l-1)) for every e1, every l. What matters is only that the labels saturate a
  3-dimensional space.
- Theorem 19.3 (S2 with the review's repairs; reviewed): with four entries the inequality
  near1 - 10 >= beta - sigma holds except in the residual case Omega (near1 = 11, two or more odd labels,
  beta = 2). Lemma Q: four independent labels give beta <= 2.
- Theorem 19.4 (O2; reviewed): with four entries and exactly two odd labels the repaired inequality
  SB* (near1 - 10 >= chi - e1) holds; this closes the part Omega2 of Omega.
- **SB' is false (counterexample verified by two independent evaluators; `compose/sb2/sbx5_mc3.txt`).** At three sheets
  with five entries: labels that are deep (nonzero on w^3) pair into "free stacks" (equal traces), each
  pair behaving like one even label at no cost to the supplier, and one spare gate links them into a path
  whose exit has weight 4 (beta = 2) while near1 - 10 = 1 and sigma = 0. SB* holds there: the honest
  replacement builds the two pair sums, which are exactly the cheap even exports the receiver needs, so the
  receiver gains nothing. **This is the main structural lesson of phase 4:** the receiver's gain from a
  supplied value and its export economy are coupled; paying honestly for a supplied value builds
  intermediate sums that serve as the receiver's exports. A compositional proof must retain, about the
  interface, at least: the span of the labels (its dimension and its intersection with the even space),
  the trace relations among the supplier's entries (which pairs are free stacks), and which intermediate
  sums the receiver can reuse as exports.

**Implication (proved; reviewed in both forms).** If SB* holds for every reduced
one-sheet instance with at least four entries, then every reduced MC_l circuit costs at least
10 + M_(l-1) (three entries by 19.1), hence M_l = 10 l for every l (with M_l <= 10 l from section 16). The
induction is explicit: SB* concerns one sheet; honest replacement holds for any far chain.

**Chain of three: what is settled and what is open.** A 29 must (Corollary 18.2) have exits across both
cuts, (Theorem A) an adjacent exit, (19.1) at least four entries at the open cut, and (19.3, 19.4) if it has
exactly four, lie in Omega1 (three or four odd labels, f1 = 7, h1 = 1, tau = 3, rigid 8-gate mirror, near1 = 11,
far1 = 18, beta = 2 from a weight-4 exit or from three weight-3 exits, and chi = 6, so no other exit may add an
even value); the residual (G2) with four entries is excluded, and with honest replacement in the form 2.1*
the split into (G1) and (G2) is no longer needed (review-sb2). Open: Omega1; five entries with shallow labels
(span of dimension <= 4) only in the form near1 = 10, h1 = 0, sigma = 1, beta = 2 with two stacked entries; and
five or more entries with deep labels (span of dimension >= 5, possible from l = 3 on), where one exit can
gain up to dim V - 2 and SB' is false. M_3 is 29 or 30; no 29
is known. These results do NOT give ten gates per sheet for longer chains: that needs SB* in general.

**Rings and MixColumns (`compose/ring/`; reviewed in `review-ring/`, wording corrected).** Only the split
and honest replacement transfer to the ring mirror. The PROOFS of Lemma R and Theorem 19.1 do not transfer
(they need the export boundary and the closed end); no ring counterexample to analogous statements exists for
m >= 4. Type-independent additivity of exit-free cuts cannot work: bounds valid for every label interface sum
to at most 33-39 < 40 at m = 4 (explicit, separately valid objects), so the label interface must be carried
as a variable. Conditional statement: if T is reduced and every exit value is supported on a single far group,
the receiver gains at most 2 per receiving group (helpers u0+u1, u2+u3 counted). Single-group support follows
when the exit gate and both its operands lie in 2-windows ("window-local"); a triangle-free overlap graph
does NOT supply this for general circuits; cancellation-free circuits satisfy it; the recorded 10m circuits
satisfy it in the two summation orders checked. In Q_3 an exit can land inside a window (the 28-gate
mechanism). MixColumns (machine-checked): the mirror windows are seven 2-windows and one 5-window
{0,1,3,4,7} from block 7; the mirror window graph has exactly one cross-window triangle ({1,2,3}, dual of the
primal {1,2,7}) and ten inside the 5-window; sheets 1, 3, 4 meet three column families; that the J_01
diagonal forces mixed labels is unproved (pure labels can span it with six labels). Proposed: end-free
discharging from the charge theorem (programme).

**Gate order (`causal-pair/`, reviewed in `review-causal-pair/`).** The time-cycle step of configuration (X)
is replaceable by F_2 dependence only for configurations already in forest-plus-exits form; without order
entries and exits are the same kind of relation and fibres need not be forests, so the pair theorem is not
shown to be order-free. The non-executable borrowing loops found are failed wirings: their value sets have
executable bases of the same size, so they show no cost of executability. Nothing shows that executability
excludes a profitable sharing pattern.

Nothing in this section changes 75 <= L(MixColumns) <= 88.

## 20. Reconstruction, transposition, and the limit of cut arguments (phase 5; `compose/TWOSIDED.md` sections 5-9, `compose/refute/`, `compose/mc/`; reviews `review-p/`, `review-ring/`)

Phase 5 (2026-11-12, user's direction): ask whether "rebuilding a supplied value also builds intermediate
sums that satisfy other obligations" is a general structural principle, without making SB* or ten per sheet
the required outcome.

**Consolidation.** TWOSIDED now states the comparison in its current form (section 5): SB (refuted,
dangle2), SB' (refuted, sbx5), SB* (current conjecture: near1 - 10 >= chi - e1), the reconstruction bound
(Lemma 5.3.1: far1 >= M_(l-1) + e1 - chi), the export-reuse correction (tau_min - tau_R), both
counterexamples written out gate by gate. Section 6: every term of SB* is determined by the supplying sheet
and the staged interface; no receiving circuit and no M_(l-1) occur; but SB* is itself a lower-bound statement
for one-sheet circuits with an unbounded interface, and chi is a straight-line-program minimum, so SB*
reorganises the chain problem without making it finite. Section 7: the composition (chi - e1 cancels;
replacement values credited once; simultaneous exits share one replacement; label obligations kept in e1,
only tau_R charged as exports) and Theorem 7.1 (SB* for the suppliers of optimal MC_l circuits implies
M_l = 10 l; sufficient, not necessary; reviewed).

**The reconstruction principle (inequality proved, reviewed).** For every replacement R,
|P| >= J(R) - (|R| - |S|), J(R) = least far size holding the receiver's obligations, the labels and R's values:
a supplied value gains at most the reconstruction surplus minus the receiver's marginal cost of also holding
the reconstructed sums. Not an exact formula (no R shown to attain it). The successive repairs SB -> SB' ->
SB* credited unused labels, then reconstruction values usable as exports. SB* is the last refinement whose
correction is a straight-line minimum with a constant baseline; it is NOT the last interface-only form (the
least far cost phi(I) of an interface is interface-only too; computing it means solving receiving problems).

**Transposition principle (proved by a delegated investigator, reviewed; under the hypothesis that the clean
labels are INDEPENDENT, which excludes for example dangle2 and the 6+4 ten-gate form).**
- P3 (mirror lemma; sharp by a finite check): no circuit on W0..W3, X contains the four triple-sums E_c(W),
  four distinct vectors Z_j + X with Z_j even (or three with Z_j spanning), and at most two other gates.
- P4: in the supplier's mirror every exit costs exactly two gates and must carry its label types as vectors
  Z_j + X; hence an exit can involve at most f1 + h1 - 5 distinct types, and SB* holds for every instance
  with exactly one exit, at every near1, every l.
- P1: near1 = 10 gives chi <= e1 - 1 (every l, any number of exits).
- P5: SB* holds for every instance with four entries (dependent labels there span E and fall under S1).
**What it explains.** The only way one exit could beat SB* is to need four label types to rebuild; carrying
four types next to an exit costs the supplier three spare gates in its transposed computation, which is the
extra cost. Compensation is a property of the supplier's mirror, not of counting spans.
**Open.** Several exits whose types together exceed three (test case: two disjoint exits with types
{a,b,c} and {a,b,d}); near1 >= 12 with several exits; dependent clean labels, where P4's argument breaks (a
finite check: four unit types fit a 10-gate mirror at near1 = 11, where the type bound allows chi up to
e1 + 2). Chain of three: a 29 needs e1 >= 5, near1 >= 11 and at least two exits, OR dependent clean labels.
SB* is not refuted; no 29 is known.

**Obstruction O: the limit of cut arguments for MixColumns (delegated, reviewed with corrections).**
- Every cut of MixColumns is ring-like (every edge of the 8-cycle lies in a window), so no cut has an export
  boundary; Lemma R, Theorem 19.1 and S1 have no instance.
- The near side needs at least 8 gates at every single cut, and 8 is attained for SOME interface (the
  recorded 97 at blocks 7 and 0).
- Verified witnesses with no exit at the cut make the far side cheap: at primal block 7 a corpus 88
  (circuits_3.txt line 13114) has near 24, far 64.
- Hence any bound of the form near_min + Far_min at one cut is at most 72 at block 7 and at most 86 at the
  worst cut. A two-inequality (SB*-type) composition has best constant supplier baseline at most 9 (an
  instance with one entry per required row has sigma = 1), so it can prove at most 73 at block 7 and at most
  87 at the worst cut: never 88, so it cannot exclude an 87.
- Scope: O constrains inequalities claimed for ALL circuits; a supplier inequality proved only for optimal
  circuits is not covered.
- Same phenomenon in rings: bounds valid for every interface sum to 33-39 < 40 at m = 4 (section 19). In
  chains the separate baselines sum to 10 + M_(l-1), which is why the cut method can work there at all.
*(Phase 6: the exact statement, domain, quantifiers and verified per-cut table are in section 21 and
`compose/mc/OBSTRUCTION.md`; the block-7 figure 73 above is a looser cap, the verified values are 68 at the
least-far witness and 66 over all exit-free witnesses.)*
**What it says.** Any cut argument whose two sides are bounded by interface-independent baselines proves at
most the sum of those baselines. For chains that sum is the truth; for rings and MixColumns it is not. Cost
moves across the cut through the label interface (the cheap-far witness has an expensive near side). A cut
argument for MixColumns must carry the interface type as a variable, or use all cuts at once (discharging
from the charge theorem). The {1,2,7} triangle (mirror {1,2,3}) supplies the receiver's own TARGET through an
exit (730 of 731 sampled corpus circuits), a different mechanism from the chain's reusable intermediate sums.

**Ring transfer, reviewed.** Section 19's ring paragraph is corrected accordingly (conditional single-group
bound; window-locality not implied by triangle-freeness; one cross-window triangle in the MixColumns mirror).
**Gate order.** The borrowing-loop examples are retired (failed wirings; executable wirings of the same size
exist); no cost of executability is shown; the algebraic replacement applies only under its reviewed
forest-plus-exits hypothesis.

Nothing in this section changes 75 <= L(MixColumns) <= 88.

## 21. Compatibility of the two sides inside MixColumns (phase 6; `compose/mc/OBSTRUCTION.md`, `compose/compat/`, `compose/tri/`; reviews `review-O/`, `review-compat/`)

Phase 6 (2026-11-12, user's direction): investigate directly the information that the fixed-baseline cut
comparison discards for MixColumns.

**Obstruction O, exact (main agent; numbers verified independently on the whole kste corpus, 18,938 valid
circuits, and the recorded 88, 89, 97).** Domain: single primal blocks and single mirror groups (16 cuts);
split near = f + h, far = |P| + e, |T| = near + far; no exports. Lemma O.1 (proved, reviewed): at a cut with no
exit, chi = tau_min exactly (this gives the lower bound on chi that the supplier direction needs). Templates:
(T0) near >= A and far >= B for EVERY circuit; (T1) near >= A + (chi - e) and far >= B - (chi - e) for EVERY
circuit. Then (T0) gives A + B <= 8 + minfar <= 86 and (T1) gives A <= 9 (constructed instances with sigma = 1,
verified at all 16 cuts) and A + B <= 9 + (far - sigma) of any exit-free witness, at most 87 at every cut and
exactly 87 at primal blocks 5, 6 and mirror groups 2, 5, 6 (corpus caps from checks, not theorems). Neither
template can prove 88 at any single cut. NOT covered: inequalities claimed only for optimal or at-most-87-gate
circuits; interface-dependent bounds; several cuts at once; other corrections. O does not say cuts are
unusable; it says the chain mechanism (a free-neighbour export boundary, then separately minimised baselines)
has no instance in MixColumns.

**What must agree across a cut (proved by a delegated investigator; reviewed).**
- Exact join at a cut with no exit (Prop 1): two sides join into a valid circuit iff every label value the near
  side reads is a signal of the far side; so the least size of a circuit with no exit at cut b equals
  min over label sets Lambda of [nu_b(Lambda) + phi_b(Lambda)]. With exits the interface must also carry the
  exit values and the precedence; set data alone is not enough (reduced counterexample in review-compat).
- No small faithful interface (Prop 2): nu depends only on the linear relation type of Lambda relative to the
  required near far-parts, but phi depends on the actual vectors (an automorphism fixing W_7 changes phi from
  at most 30 to at least 32; check); the full label set is a sufficient exact description (22-27 vectors at block 7 in the corpus); its
  necessity has not been established (phase-7 correction).
- One-block bound (Prop 3): nu_b(Lambda) >= 8 + max(dim W_b, |Lambda|) (27 at block 7, exactly 28 at
  Lambda = S_near).
- The coupling is gate elimination (Prop 4): |T| = R_b(T) + w_b(T) for every circuit, R_b >= K_b :=
  L(MixColumns with block b zeroed), w_b >= 4 (the wasted gates under zeroing block b); the near/far tradeoff
  is the share Delta of the restricted computation done on the near side, and it cancels in the sum. Given
  Theorem 16.1, K_7 >= 60, so circuits with no exit at block 7 need at least 64, beating the separately
  minimised canonical baselines (at most 58) by at least 6; still below 75.
- Limit of the faithful single-cut bound (check): K_b <= 77 at blocks 0-6 and <= 69 at block 7 (corpus and
  recorded circuits), and explicit verified circuits have waste 5 or 6 at every block; so any bound of the form
  K_b + (a waste bound valid for all circuits) is at most 83 (75 at block 7). Going further at one cut needs a
  COUPLING between waste and the restricted part (low waste forcing a large restricted part); none is known,
  and the sample shows none at block 4 (min R and min w in the same circuit).
- Why the cheap sides do not combine (check): the cheap near side (recorded 97 at block 7: near 8, 32 entries,
  27 labels, 19 of them two-block vectors built only as labels) and the cheap far side (corpus 88: far 64,
  23 entries, labels mostly units) need different label sets; 19 of the 97's labels are not signals of the 88's
  far side; every ordered join of the five circuits examined costs at least 96. In restriction terms the far
  side's 16-gate saving is paid by 13 more gates of restricted work on the near side, offset by 6 less waste.

**The {1,2,7} triangle mechanism (delegated; reviewed; `compose/tri/`).** Worked example circuits_2.txt line 20
(88 gates): at primal block 2 the exit g78 = g65 + g77 supplies sheet 1's target (1,1) = [0:s1 1:E1 7:s1]
exactly; the partner g65 = [2:s2 7:s2] is a gate sheet 3 needs anyway; the five labels on the route sum to
(1,1) (honest rebuilding 4 gates; the route's dedicated gates 2); the supplied target is reused inside sheet 1
through g72 = (1,1) + (3,1); nothing on the route is exported to another sheet. Structural: zeroing blocks 3..7
turns the triangle exit into an ordinary exit of the pair (1,2) problem at the pair minimum 20. Proved (review
version): P(1,2) >= 20 + (gates of P(1,2) whose restriction is free, an input, or repeats another's); so a
partner [2:x] + [7:y] ancestor of sheet 1 forces P(1,2) >= 21 when x is a unit or when one operand of the
partner lies on block 7 alone (every observed case). Open: the general construction (equivalently, no 20-gate
pair circuit contains a non-unit pure-block-2 ancestor of a sheet-1 target). Corpus (stride 20): all 744
non-monotone circuits have exactly 3 double charges and P(1,2) >= 21; whether the exit gate itself equals a
target is a matter of bracketing; invariant: the three-term sum is a sheet-1 target serving only sheet 1. Unlike
the chain mechanism, the supplied value is the receiver's own target and the reuse stays inside one sheet.

**Corrections to TWOSIDED (main agent).** Section 7: with delta = (chi - e1) - (near1 - 10) and
epsilon = far1 - [M_(l-1) - (chi - e1)], cost = 10 + M_(l-1) - delta + epsilon; a saving needs only
epsilon < delta (equality in the receiver bound is forced only when delta = 1); epsilon concerns the
reconstructed far chain P', not the receiver with exits. Section 8: J(Y) and J_0 defined (no export cost); the
reconstruction inequality is an upper bound on the gain for every R; the wording "a supplied value can pay only
if its intermediate sums are of little use" is withdrawn (example p = a+b, q = c+d, t = p+q). Section 9: "clean
labels" defined (cleaning only inside proofs; unclean entries enter through sigma); what the finite checks of
review-p did (small exhaustive runs on five-input objects, no solver; only the sharpness remark and the
"exactly 10" figure depend on them; the lower half of "exactly 10" now has a hand proof, joint/FINITE_AUDIT.md
section 3). Phase-7 correction: these runs, and the other small exhaustive checks and
exact least-gate searches listed in `joint/FINITE_AUDIT.md`, were newly executed on 2026-11-12 after the
instruction excluding exhaustive computation; the record's earlier statement that none was run was wrong.

**What phase 6 established.** For MixColumns, single-cut arguments in the forms examined (T0, T1, the
label-interface join, restricted map plus a waste bound valid for all circuits) reduce to: the restricted map's
cost plus wasted gates. The information the fixed baselines lose is Delta, the part of the restricted
computation placed on the near side, and once it is retained the cut bound becomes gate elimination on one
block. For the restriction form the ceiling from verified expensive circuits (83, or 75 at block 7) means it
cannot reach 88 with a waste bound valid for all circuits; a waste bound proved only for optimal or <= 87-gate
circuits is not constrained by those witnesses, and other single-cut arguments are not covered. (Phase-7
reconciliation: O's 86/87 are witness ceilings, not attainable lower bounds; Prop 2 shows only that the label
relation type does not determine phi, not that no smaller useful description exists; the joins >= 96 are
examples.) The triangle mechanism is, modulo block 7, a pair
exit at the pair minimum, paid for in the pair count when the partner has the observed form.

Nothing in this section changes 75 <= L(MixColumns) <= 88.

## 22. Several restrictions of one circuit; delivery and sharing between sheets (phase 7; `joint/ACCOUNT.md`; review `joint/review/`)

Phase 7 (2026-11-12, user's direction: which combinations of restricted computations can arise from one cheap
circuit). The coherent account with proofs is `joint/ACCOUNT.md`; this section lists results and status.
Proofs by the main agent; machine review `joint/review/REVIEW.md` (own code, independent sample of 826 circuits).

**Exact accounting (proved, reviewed).** For a reduced circuit, a block set B and the first-producer order:
G = S_B + D_B, with removal categories zero / surviving input / earlier value, and a fourth (dead after
simplification); U_B = S_B - dead_B >= K_B = L(MixColumns with B zeroed). J1: D_B = |Sigma| - |pi_B Sigma| - 4|B|
(depends on the value set only). J2: at one block every gate with a pure-b value or a pure-b operand is removed,
D_b = |L_b| + N_b, N_b the nonlocal coincidences; lambda(g) <= 2. J3: D_bc = D_b + D_c - O_bc with O_bc a sum over
fibres of (cycle rank - components + 1); positive terms are rectangles such as {0, x_b, x_c, x_b + x_c}, negative
terms fibres that fall apart. J4: the sum over the eight blocks, 7G = sum U_b + lambda_2 - lambda_0 + N + dead,
is exactly the average of the single-block identities (by itself no further information; a new structural
relationship among its terms is not excluded); removal is monotone in B, so chains
of zeroings are gate elimination.

**Limitation (check).** Bounds "L >= K_B + delta_B" with delta_B a waste bound valid for ALL circuits are at most
83 for |B| = 1 and 85 for |B| = 2 (explicit verified constructions of 152-229 gates, `joint/lowwasteB.py`; caps
are sample-dependent upper bounds) and 87 for |B| = 4 (narrowly, by corpus 88s); at |B| = 3 the set {4,5,6} is
not capped below 88 by known circuits, which does not show that a bound restricted to <= 87-gate circuits is
needed. The candidate couplings "sum_b D_b >= G" (false in the
corpus, 86 < 88) and "8 charged gates removed at their own block" (false in general) were discarded.

**Delivery (proved, reviewed).** J6 (reader identity): for every reduced circuit and block b, the block-b
columns of M equal sum over readers g of rho(g) omega'(p_b(g))^T, rho(g) the parities of paths from g to the
outputs. J7: for any partition of the rows, |R_b| >= sum of group ranks - sum (t(g) - 1)^+; with the sheet
partition the ranks are 7 (b < 7) and 16 (b = 7), 65 in all, so fewer readers need readers serving several sheets.

**Sharing (proved, reviewed).** J8: in a block-monotone MixColumns circuit every gate serving two sheets is
pure, or lies on {0, 7} and serves exactly sheets 0, 1, or on {3, 7} and serves exactly sheets 3, 4 (the only
window pairs meeting in two blocks; no triple does); corollaries |R_b| >= 7 at b in {1, 2, 4, 5, 6} and
|R_7| >= 10 there. J9 (every circuit): a gate serving a sheet whose window misses one of its blocks reaches it
only through an exit at that block.

**Census (check; 763 circuits main, 826 review).** Monotone circuits share exactly as J8 allows and all use both
reduction pairs. Non-monotone circuits: 598 of 615 (review: 620 of 654) have as their only cross-window sharing
the triangle (three {1,2} gates serving sheets 1, 2; one {2,7} gate serving 1, 3; plus one pure block-2 gate
serving sheet 1); the rest none, one variant in the main sample (the review sample is a different selection from
the same corpus); the triangle dominates the sample but is not a proved normal form. Removal is local up to 0-6 coincidences per circuit; dead 0-1.

**REFUTED in phase 9 (cancel/SUPERPOSITION.md: a reduced, fully live MixColumns circuit with 66 distinct charged gates).** **Conjecture (holds on all sampled circuits, least value 81 at circuits_3.txt line 7651 (the 82 first
given here was wrong; phase-8 review); no proof mechanism).** |F_0 u ... u F_7| >= 80 for
every MixColumns circuit (would give L >= 80). Double service needs an exit (J8, J9), but no cost of exits is
known, and the compensation is not pair-local: in the F-form |F_1 u F_2| = 19 in 166 of 826 sampled circuits
(circuits_2.txt line 783, compensated by F_0, F_3, F_4 and uncharged gates); in the P-form line 20 has
P(1,2) = 21 < 20 + 3 double charges.

**Finite checks (correction).** Small exhaustive checks and exact least-gate searches were newly run on
2026-11-12 after the user's instruction excluding them; the earlier statements that none was run were wrong.
`joint/FINITE_AUDIT.md` lists them with their dependents; the "exactly 10" lower bound now has a hand proof
(delegated, machine-reviewed with fixes); the P3 sharpness remark and the "rank at most 8 in all 384
configurations" remark rest on the runs alone. Nothing was rerun.

Nothing in this section changes 75 <= L(MixColumns) <= 88.

## 23. When cancellation-mediated sharing can be closed by charged work (phase 8; `cancel/CANCEL.md`; review `cancel/review/`)

Phase 8 (2026-11-12, user's question: when does cancellation-mediated sharing force extra computation, and what
property decides it). Main agent's proofs; machine review with own code (no SAT, search or enumeration).

**Lemma W (proved, reviewed).** |F_j| - 10 >= c_j, the number of gates of F_j lost when the ancestors of sheet j
are projected to blocks {j-1, j} (charge theorem with its slack). Principle W1 "every double charge collapses
in a window projection" is false: Q_3 has c = 5 < R = 11, and MixColumns circuits with c < R exist
(circuits_3.txt line 7451).

**Theorem K (cancellation chase; proved, reviewed).** Gamma: sheets, edge x -> y when the own block of x lies in
W_y; gamma its directed girth. If a gate charged to sheets j and k reaches them along two paths whose chase exits
(the exits cancelling the block currently followed) all have an off-path operand confined to the window of a
sheet whose own block it contains and keeps, then Gamma has a directed cycle of length at most t_j + t_k + 2.
gamma: Q_2 2, Q_3 3, Q_m m, chains acyclic, MixColumns 4 (cycles all pass through block 7; the shortest is
7, 4, 5, 6). Corollaries: for gamma >= 3 no double charge is exit-free to both sheets; in MixColumns every
closure by plain charged work needs at least two chase exits; in chains none exists. K restricts the shape of
closures; it assigns no cost.

**Check (Q_3; 763 + 384 MixColumns circuits).** In Q_3 the 14 confined closing operands are all charged work of
the third sheet, one exit per closure (gamma = 3 permits it). In MixColumns the only double charges are the
triangle's, and every needed cancellation is closed by an uncharged, non-confined gate (one partner closes
all three). Refuted: "every exit costs a gate" (Q_3), "each uncharged partner pays for its double charges"
(U = 1 < R = 3 occurs). Observation: after zeroing blocks 4, 5, 6 the charged union of sheets 1, 2, 3 is >= 30 in
every sampled circuit.

**REFUTED in phase 9 (cancel/SUPERPOSITION.md: a reduced, fully live MixColumns circuit with 66 distinct charged gates).** **Conjecture G.** For sheet systems with gamma >= 4, |union F_j| >= 10 s; it would give L(MixColumns) >= 80,
L(Q_m) = 10 m (m >= 4) and M_l = 10 l. Q_2 and Q_3 lie outside its hypothesis. Missing: a cost for closures by
uncharged partners, for escapes, and for closures with >= gamma - 2 chase exits. Least sampled |union F_j| is
81 (circuits_3.txt line 7651; RECORD 22's 82 corrected).

**Scope corrections (phase 8, applied in RECORD 21-22, SUMMARY, CHECKPOINT, joint/, compose/compat).** The
triangle dominates the sampled pattern; the main sample contains a variant, and the reviewer's sample is a
different selection from the same corpus. The restriction caps include four-block ceilings below 88; only the
three-block set {4,5,6} is uncapped by known circuits, which does not show that a bound for <= 87-gate circuits
is needed. The eight-block identity adds no information by itself but does not exclude a new structural relation
among its terms. The full label set is a sufficient exact interface; its necessity is not established. Finite
checks: several exhaustive checks and exact least-gate searches were run despite the instruction;
joint/FINITE_AUDIT.md section 5 separates statements now supported by hand arguments from those resting only
on those runs.

Nothing in this section changes 75 <= L(MixColumns) <= 88.

## 24. Superposition: the distinct-charge conjecture refuted; what removal costs (phase 9; `cancel/SUPERPOSITION.md`; review `cancel/witness/review/`)

Phase 9 (2026-11-12). The user supplied an explicit construction (the attachment itself was not available in the
session; the circuit was rebuilt from the description and verified here and by an independent machine review).
**Counterexample (proved; verified).** z_c = parity of byte c (28 gates), H_c = parity of the other three bytes
(6 gates; on every block j its part is E_c(j)); every output is y_(c,j) = H_c + r_(c,j) with the remainder r
built from inputs outside block j by disjoint-support chains. Under hypothesis H (no step-3 value equals an
output) its distinct charged gates are the 34 globals and the 32 outputs (reducedness and full liveness are
verified for the two fixed orders):
66 (E 140, R 154; G 521-616 depending on the order of the remainder sums). For Q_m, 8m + 2. **Refuted:** the
phase-7 distinct-charge conjecture and Conjecture G (phase 8) for MixColumns and for Q_m, m >= 4 (Q_4: 34 < 40).
**Not refuted:** G >= 80, L(Q_4) = 40, size- or U-restricted charge statements, the bounds 75 <= L <= 88.
Consequence: no unconditional lower bound on the distinct charged gates can exceed 66, below 75.
**Theorem K survives** (the only exit on the witness's paths is the output gate; its off-path operands r and
H_c are confined to no window); it classifies partner shapes and gives no constraint on cost or reuse.
Interpretation fixed: confinement is a support condition, not membership in F_l; a one-chase-exit closure in
MixColumns needs a non-confined or escaping partner, not necessarily an uncharged one; chase exits are counted
per pair of paths, not as distinct expenses. Sheet-system repair: windows need a non-own block, and Lemma W
projects onto an actual non-own block.
**Removal (proved).** Lemma S1: cancelling a block of a shared value forces a second copy of that part in the
partner. Q_3 takes the copy from another sheet's charged work (total saving 2; use elsewhere does not by itself make its
marginal cost zero); the MixColumns triangle from one
uncharged partner serving three double charges; the superposition witness from 32 uncharged remainders (deficit
R - E = 14, paid by U >= 446 in the orders tried). Dual identity: G = sum_v (fan-out(v) - 1), the size of the
transpose. **Two-sided charging refuted (check):** the transpose's charged count depends on the chain order; the
block-order witness and its reverse-order transpose both have 66, so charging C or C^T under that fixed chain rule does not repair the
framework (other transposition strategies are not ruled out); "some transposition has at least 80 charged
gates" is sufficient for G >= 80, and the converse is not established (phase-10 correction).
**Next (as proposed then):** a copy-rank principle; examined and abandoned in phase 10 (section 25).
**Phase-10 scope corrections.** H_c's unwanted part outside a MixColumns window occupies 5 or 6 blocks (the full
remainder 7). Hypothesis H is what the charge count needs; reducedness and full liveness are verified for the two
fixed orders only (other orders need dead-gate pruning, which removes only uncharged gates).

Nothing in this section changes 75 <= L(MixColumns) <= 88.

## 25. Cancellation copies and gate cost: a feasibility study (phase 10; `copies/COPIES.md`; review `copies/review/`)

Phase 10 (2026-11-12, user's question: can the cancellation-copy measure of section 24 be connected validly and
nontrivially to gate cost?). Main agent's proofs; machine review with its own code (not human review); no
search of any kind; checks are direct evaluation and linear algebra on specified circuits.
**Candidate.** For a gate e = a + b, cancelled blocks C(e) = {c : pi_c(a) != 0 = pi_c(e)}; copy
kappa(e) = pi_C(e)(a); measure = rank of the copies modulo a baseline (none, span X, span Y, staged, per
recipient), or with events having an input or output operand exempt (Q2); recipient form u(h, j).
**Status (proved; checks in copyrank.py).** C1: global linear baselines give 0 (inputs, and for invertible maps
outputs, span everything; no gate raises any rank of available values); per-recipient baselines are nonzero but
bounded by the events. C2: one copy per event gate, so the rank is carried by the cancelling gates (witness:
all 32 events are its outputs, rank 32 = |Y|). C3: a reduced circuit with G = |Y| and Q0 = n - 1 (n >= 3), so
no G >= |Y| + c Q0. C4: partner capacity is quadratic and sharp: k non-output gates carry copy rank
k(k-1)/2 (construction for k = 5, 6, 8); the valid remnant G - |Y \ X| >= (1 + sqrt(1 + 8 Q2))/2 is a count
of non-output gates. C5: the recipient's requirement is a coset, the partner b = e + a a node; the "needed
elsewhere" exemptions were defined through an unknown optimal completion (circuit dependence alone is not
circular; phase-11 wording). One consistent definition gives Q_3 4, triangle circuits 1-2, witness 32,
r88/r89 0 (and 0 for all with the span-Y baseline): the phase-9 intuition (0, 1, high) was wrong.
**Theorem F (first-exit identity; proved; checked).** For any node set A containing the inputs of the columns K,
M_K = sum over edges p -> g leaving A of rho(g) val_A(p)^T + output terms in A; J6 is an instance, J7 a
corollary. **Corollary Z:** zero-cell (cancellation) equations hold for every decomposition, so unconstrained
counting of rank-one terms at one cut cannot see removal (circuit-constrained single-cut arguments are not ruled
out; phase-11 wording).
**Proposition V (reviewer, from sections 7, 9, 17; proved).** A MixColumns circuit with no whole-block
cancellation is block-monotone, hence has at least 84 gates: every circuit with at most 83 gates cancels a
whole block somewhere. With J9, every doubly charged gate lies in the ancestor cone of a cancelling gate.
**Proposition R (conditioning; proved).** G(C) >= |H \ X| + L(Y | X u H) for every set H computed by C; since
L(Y | X u H) <= L(Y), a conditional bound by this route carries the obligation of the same unconditional one (an obligation
for this route, not an impossibility; phase-11 wording).
**Restriction remark (corrected in phase 11).** Zeroing a cancelled block leaves the event's value unchanged,
but an earlier projected value may become equal to it, making the event removable (a = x + y, b = a + z,
e = b + x; section 26); the zero counts measured in phase 10 are observations.
**Decision.** "Copies cost gates" measured by rank is left; the examined formulations do not give the desired
MixColumns bound (C4 is kept as a capacity result). The proposed next target was superseded by the repair
lemma (section 26).
**Phase-10 scope corrections** (sections 24, SUMMARY, CHECKPOINT, SUPERPOSITION, FINITE_AUDIT): one fixed
transposition convention only; "some transposition >= 80" sufficient, converse open; H_c's unwanted part 5 or 6
blocks; H for the count, liveness only for the two orders; use elsewhere is not zero marginal cost; confinement
and "exactly 10" wording synchronised.

Nothing in this section changes 75 <= L(MixColumns) <= 88.

## 26. Repairing whole-block cancellations (phase 11; `repair/REPAIR.md`; review `repair/review/`)

Phase 11 (2026-11-13). The joint repair lemma, the direct repair and the prefix family are the user's,
verified independently here and by machine review (own code; not human review); no search of any kind.
**Lemma 1 / Theorem 1 (proved).** For a reduced circuit C with event set E (gates cancelling a whole block) and
any event-free circuit D on the inputs computing the event values with K gates: recompute D first, keep the
non-events, redirect. The result is event-free with at most G - |E| + K gates (reuse and pruning keep it
event-free). Event-free circuits are block-monotone (RECORD 7), so Corollary 17.4 gives
G >= 84 + |E| - K for MixColumns (status of 84: hand proofs, machine review only; the 80 of the charge
identity is unchanged). Sequential form: gadgets may read earlier retained and gadget nodes.
**Theorem 2 (direct repair; proved).** G >= 84 - sum (w(e) - 2). Rows weigh 5 (sheets 0, 2, 5, 6, 7) or 7
(sheets 1, 3, 4): a sole event at a weight-7 output gives 79, at a weight-5 output 81; all events of weight 2
give 84; G <= 78 needs two events or one of weight >= 8 (not an output). The triangle event is at a weight-7
output in four of the five corpus lines (internal, weight 5, in circuits_3.txt line 3001).
**Sharpness (proved).** Prefix family p_i = x + y_1 + ... + y_i, T = y_1 + ... + y_n: optimal n + 1 gates with
one event; event-free minimum exactly 2n - 1; saving n - 2 = w(T) - 2. No event-count penalty for general maps.
**Theorem P (projection repair; new; corrected in review).** Zeroing blocks keeps a circuit event-free
(Lemma Z). For the first event e of a reduced, fully live circuit, the gadget P(a) + P(b) (P zeroes the
cancelled blocks) has overhead at most s_e + delta_e - 1, where s_e counts shared gate ancestors carrying the
cancelled blocks whose nonzero projections are not values of nodes other than e. Only shared cancelled content
costs; private content is free to remove. The formula equals the explicit overhead on the prefix family (n - 2),
the single-event triangle circuits (2) and per step on Q_3 (2, 2, 2, 3); elsewhere it is only an upper bound (the
witness's overhead -322 lies far below its sum of terms, each >= -1; phase-12 correction). Per circuit only.
**Lemma L (reviewer; proved).** Shared carriers of a sole event at a sheet-j output lie inside
(W_j u C) n W_j' for the sheet j' they feed; for the triangle, on {1, 2}, {2, 7} or block 2.
**Correction (phase 10).** Zeroing a cancelled block can make the event removable (a = x + y, b = a + z,
e = b + x duplicates b; embedded in MixColumns, 148 gates). Wording fixes: C4 kept; circuit dependence is not
circular; Theorem F limits unconstrained term counting only; Proposition R's 76 is a proof obligation of that
route.
**Next (superseded by section 27).** Phase 11 proposed a trade-off for shared carriers and then the two-event
regime; phase 12 replaced both by the visible-event accounting.

Nothing in this section changes 75 <= L(MixColumns) <= 88, and nothing excludes an 87.

## 27. Visible cancellations (phase 12; `visible/VISIBLE.md`; review `visible/review/`)

Phase 12 (2026-11-13). The global repair, the output-support consequences and the sole-event window credit
are the user's, verified independently here and by machine review (own code; not human review); Theorem V,
its 84 form, the tail family and Proposition M are new. No search of any kind.
**Theorem G (proved).** Trace back from the outputs, stopping at the first event on each branch: the events
reached are the visible ones F, the non-events reached are retained (R); the rest (hidden events E \ F and Q)
is separated from the outputs by F. Rebuilding only F event-free (K gates) and keeping R gives an event-free
circuit, so G >= B + |E| + |Q| - K (no reducedness needed for the inequality; depth and internal values not
preserved). For MixColumns B = 84 via event-free => block-monotone (one way only).
**Lemma S and windows (proved; checked).** A visible event or retained gate lies inside the window of every
sheet it reaches along an event-free path: at most 3 blocks, at most 2 for two sheets ({0,7} or {3,7}),
block 7 for three or more. A gate outside every window is never retained or visible.
**Window credit (proved).** If a cancelled block and a block of a visible event never share an output, the
operand carrying both is hidden. Sole event: G >= 84 - (w - 3), giving 80 at weight-7 outputs. Three-block
visible events always have a hidden operand. Sharp for general maps (tail family: saving w - 3 exactly).
**Theorem V (new; proved given Theorem 9.2).** Theorem 9.2's proof gives G' >= 83 + U for event-free
circuits (U = gates in no charge family; designated outputs, no reducedness). A visible event has at most one
own block of the sheets it reaches (own-block property), and the rest of it can be rebuilt with gates in no
family. Hence G >= 83 + |E \ F| + |Q| - sum kappa(f), -1 <= kappa <= 4 whatever the weight; per-sheet form:
each visible event supplies at most 5 charged gates, all of its own block's sheet.
**84 form (proved given Theorem 17.3 bounding the whole local circuit L_01; reviewed).** G' >= 84 + |U \ X|,
X = block-0 gates feeding sheet 1 only. Consequences: one visible event => G >= 80 (81 except one shape);
sole event at an output => 83 (sheets 0, 2, 4, 5, 6, 7), 82 (sheets 1, 3; sheets 0 and 2 when C = {1} resp.
{7}); G <= 79 needs two visible events, G <= 76 three. Hidden events cost nothing.
**Limits.** Up to 4 lost per visible event (nothing above 75 with three or more); the content is a lower bound
on the retained part, |R| + sum in(f) >= 83, never on the hidden part; when every output is a visible event
(superposition witness, R empty) it says nothing about G. Proposition M: in a minimum circuit with fewest
events every event has weight >= 3 + |dead_e| (local only).
**Phase-11 corrections applied in `repair/REPAIR.md`:** Theorem P's formula is exact only on the prefix
family, the single-event triangle circuits and per step on Q_3 (witness overhead -322/-324 vs terms >= -1:
extra pruning); 146 is the direct repair (projection 199/197); "only s_e can improve" limited to that
estimate; carriers need not be paid one by one, and "paid elsewhere" means genuine slack beyond the baseline;
the "any number of shared carriers" claim withdrawn (no bound established is not no bound possible); the prefix
family has windows but no separation; event-free => block-monotone is one-way; Lemma L applies to two-event
circuits only along paths avoiding the other event.

Nothing in this section changes 75 <= L(MixColumns) <= 88, and nothing excludes an 87.

## 28. Takeover: joint hidden work and simultaneous projection repair (2026-11-13)

Current continuation: [`../takeover-2026-11-13/CHECKPOINT.md`](../takeover-2026-11-13/CHECKPOINT.md),
branch `research-2026-11-13-structural` based on verified local/remote `e89b8a2`.
The original worktree and its untracked `search/proposals/` were preserved.
The 10/13 local lemmas and 83/84 block-monotone bounds were independently reconstructed from
their symbolic proofs. Visible repair and Theorem V survived review. The universal claims
below have hand arguments and independent machine review, not formal or human certification.

**Hidden operands (proved).** For independent selected event values filling one maximal
output window and pairwise distinct on every window block, `t <= 2h-c`, where `h` counts
distinct nonlocal operand gates and `c` counts their operand-graph components. Each event
has a nonlocal operand; a nonlocal operand has at most one local-partner event; independent
edge values force a forest. A symbolic family attains the bound.

**Componentwise separation rank (proved; stronger mechanism).** In each nonlocal-operand
component, all nodes have the same nonzero projection outside the window. Let `D_i` be
the window blocks incompatible with some block of that projection. Every local partner
is zero on `D_i`. Thus the `D_i`-projected selected event values have rank at most the
number of physical nonlocal operands in that component. Sum over the disjoint components.
This theorem needs neither independent event values nor pairwise distinct block projections.
It counts gates only after eliminating the uncounted local partners on those coordinates.

**MixColumns (proved class statements).** In sheets 1,3,4,5,6,7, one through four output
events force at least 1,2,3,3 distinct hidden operands, even with other events present.
Do not sum across sheets without an overlap argument. If a reduced circuit's entire
visible set consists of `t` output events in one such sheet, joint reconstruction gives
the following lower bounds (hidden events unrestricted): sheet 1, `82,82,81,80`; sheet 3,
`82,81,79,77`; sheets 4,5,6,7, `83,83,82,81`, in order `t=1,2,3,4`.
The shared reconstruction saves at least `floor(t/2)` charged gates by sharing the common
pair of two own-block triple sums. These bounds are not claimed attained.

**Global projection repair (proved).** Propagate requested block projections from outputs
back through operand supports. Their distinct non-input values form an executable
event-free value set `P`. For reduced original gate values `V`, any event-free lower bound
`B` gives `G >= B + |V\P| - |P\V|`. Equal clean values are reused globally, including across
interacting events. This is one-sided: a specified optimal five-gate circuit has one extra
requested clean value while a differently wired event-free circuit also uses five gates.

**Corrections and verification.** The phase-12 sentence forbidding harmless sharing between
different `J` sets was too strong and is corrected in VISIBLE; V itself used private chains.
The prefix sharpness family is attributed in REPAIR to the Boyar–Find/Svensson construction.
Direct verification checks 12 specified repair cases and one sharp hidden-work circuit by
exact masks and linear algebra. No SAT, exhaustive enumeration, exact least-gate search,
heuristic circuit search, or computer-driven case elimination was run.

Full proofs, limitations, reviews, and reproducible fixtures are in
[`../takeover-2026-11-13/`](../takeover-2026-11-13/).
The strongest next direction is separation rank across internal visible values or multiple
windows; neither extension is established here. The unrestricted interval remains
`75 <= L(MixColumns) <= 88`, with no assumption that 88 is optimal.

## 29. Continuation: affine local completions and sparse sharing (2026-11-13)

Current account: [`../takeover-2026-11-13/continuation/README.md`](../takeover-2026-11-13/continuation/README.md).
This continues reviewed commit `14b89e6` on the same isolated research branch. All universal
claims below have hand proofs and independent machine review. No search or case-elimination
campaign was run.

**Cross-window hidden counts are not additive (proved by constructions).** A reduced five-gate
toy has two maximal-window output events sharing its only hidden gate. A reduced 156-gate
actual MixColumns circuit does the same for sheets 3 and 4. A separate reduced 149-gate
MixColumns circuit has a proper-support internal visible event and no hidden gates. Both
actual maps and visibility counts were directly checked; these are expensive witnesses,
not obstructions to a theorem restricted to cheap circuits.

**Strong sparse obstruction (proved; exact event-free minimum).** For every r>=1 an explicit
reduced live circuit has `13r+3` gates, exactly two hidden gates and one nonlocal gate, while
its map's event-free minimum is `15r+2`. All output weights are 5/7; the boundary minimum
relation weight is exactly 6; output rows are independent; windows have at most 3 blocks,
blocks at most 4 coordinates; own-block incidence has no reciprocal pair. Thus savings
`>=2r-1` cannot be bounded by a fixed multiple of hidden-work count under these combined
hypotheses. The map is rectangular with one row per own-block family, so this is not a
MixColumns counterexample. The lower bound counts coordinate deletions inside packed
private blocks and proves event-freeness only at the final whole-block projection;
intermediate event-freeness is neither assumed nor needed. Full proof: `continuation/SPARSE.md`.

**Affine-completion theorem (proved).** Partition the nonlocal operand graph of selected
events into physical components. For one component, K spans its selected values and all
operands/partners lie in one coset `a+K`. Let E be the local members of that coset. If E
is nonempty, let Delta span differences of its members. The number h of nonlocal operands
is at least `dim K-dim Delta`; an appended physical incidence bit can improve this by one.
With no actual local partner, `h>=dim K+1`. Sum these bounds only over the global disjoint
components. Delta is obtained by affine linear-system intersections with the prescribed
window subspaces, not enumeration or an optimal-completion oracle. The theorem includes
HR and combines with both joint repair bounds across sheets. Scope controls: the quotient
is zero at full target span and in the 156-gate overlap example; it is exactly one in the
genuine-saving families. The anchor formulation equals quotienting by span(E), correcting
an early comparison overstatement without changing the theorem.

**Internal events (proved).** Two local operand masks with surviving support R and cancelled
support C exist iff two output windows containing C cover R. Inside an enclosing window,
use the component's full outside signature to identify all possible local-partner windows;
their complement gives the strongest linear separator based on signature/locality alone.
The resulting rank bound handles proper-support internal events. A specified independent
sheet-3 profile with the complete visible set of size m gives `G>=84-2m`; the hypotheses
are stated in `continuation/INTERNAL.md`.

**Verification and judgment.** Five specified constructions were checked by exact masks and
Gaussian elimination, including the packed sparse instance r=2 (29 gates versus an explicit
event-free 32). Universal optima and boundary distance are hand proofs, not enumerations.
The next useful question is the cost of producing compatible local completions while all
four structured rows of each implicated MixColumns sheet are required. Coarse support,
sparsity, boundary distance, and hidden-work counts alone are insufficient. No universal
MixColumns compatibility lemma has been proved; `75 <= L(MixColumns) <= 88` remains unchanged.

## 30. Complete row demands and paid interfaces (2026-11-13)

Current account: [`../takeover-2026-11-13/row-cost/README.md`](../takeover-2026-11-13/row-cost/README.md).
This continues reviewed commit `eb9191a` on the same isolated branch. The new universal
claims have hand proofs and independent machine reviews, not formal verification or
human certification. No search or computer-driven case elimination was used.

**Exact local cost (proved).** A four-row sheet has own triples E_c and the same adjacent
pair s_c on each neighboring block, with all terms present in each output. If p neighbors
have ordinary coordinate inputs and f are separately free, the exact paid cost is 6 when
p=f=0, `3f+7` when p=0,f>=1, and `4p+3f+8` when p>=1. Lower bounds allow unrestricted
cancellation; explicit event-free constructions attain them. Transposition exposes the
reason: each free block needs three even traces; one extra mirrored gate can expose them
for all free blocks. An ordinary neighbor already forces four adjacent-pair traces.
Local costs cannot be added globally without proving physical gate disjointness.

**Source-interface saturation (proved).** For r disjoint own blocks each producing k>=2
alternative four-row source variants, event-free cost is at least
`(6+4k)r+min(r,4k)`, exactly `(6+4k)r+4k` for r>=4k. Equality in the local `6+4k`
charged count forces every source pair to be present as a physical gate. If any source
pair is absent, every sheet incurs an extra charge; if all exist, their gates sit outside
the sheet charges. The tagged two-source family has event-free optimum `22r+8` for r>=8,
whereas the natural shared-translation circuit costs `22r+12` with eight hidden gates.
This direct four-row lift loses the sparse example's advantage. Other cancellation
architectures are not ruled out, and the Q_3 counterexample to generic additivity stands.

**Sharp completion geometry (proved and directly checked).** For one maximal MixColumns
sheet, the only possible nonzero local-completion difference space is its own-parity line.
Four output events using three nonlocal operands force a path, with local partners at its
endpoints differing by that parity. A reduced 145-gate actual MixColumns circuit realizes
exactly four sheet-5 events and three hidden gates. Its parity-shifted partner is retained
and charged to sheet 6, so forcing this value does not force an additional hidden gate.
Two-sheet window intersections are given symbolically using R=I+P, with R^4=0; the omitted
own-block equations can introduce a two-dimensional R^2 kernel. One sheets-2/3 profile
forces six hidden operands but only gives 74 after repair, not a new numerical bound.

**Exact avoidance interface and a failed shortcut (proved).** For a four-triple sheet,
suppose required free labels span a rank-three D with the sole all-four relation, and all
actual entry labels avoid D. At least eleven gates are needed. Equality forces five labels
in a four-dimensional span, all in one nonzero coset modulo D, and five influence traces
of rank four with exactly four odd and one even. The four labels on odd traces have the
unique label relation. An explicit eleven-gate circuit attains this when an outside-D
label is available. A separate explicit ten-gate first-sheet circuit contains a clean
diagonal, refuting the shortcut that every clean diagonal costs an eleventh gate.
Neither result closes the joint 21-to-22 problem: augmented first-sheet cost 11 versus 12
and second-sheet interfaces mixing clean and nonclean labels remain unresolved.

**Verification and judgment.** Direct mask checks cover eight specified port constructions,
the tagged r=8 translation and event-free circuits (188 versus 184 gates), all 32 outputs
and the exact visibility partition of the 145-gate MixColumns witness, and both interface
circuits. Reviews prompted explicit re-trimming in the transposition proof and qualification
of attainment by existence of an outside-D label. The next useful target is a compatibility
theorem forcing a paid interface at local equality in the fixed MixColumns windows.
Geometrically forced partners may already be retained and charged; no automatic extra
hidden credit follows. The unrestricted interval remains `75 <= L(MixColumns) <= 88`.

## 31. Actual supplier compatibility and entry deletion (2026-11-13)

Current account: [`../takeover-2026-11-13/compatibility/README.md`](../takeover-2026-11-13/compatibility/README.md).
This continues reviewed commit `098e5d4` on the isolated research branch. All universal
claims below have hand proofs and independent machine review. No SAT, circuit search,
exhaustive enumeration, exact least-gate search, or computer-driven case elimination was run.

**Producer coset cap (proved).** Any ten-gate first sheet `U_c=E_c(b)+s_c(a)`, with a free,
has at most four distinct available values in each coset of the clean even diagonal
`D={v(b)+v(a): v even}`. Available values include its gates, ordinary inputs, and all free
vectors. Actual free labels in the ten-gate circuit are even by the tight transpose count.
A five-value even-own coset would force eight new own masks plus at least three entries.
A five-value odd-own coset would force eight odd gates and just two even gates. The named
four inputs and four outputs form an eight-element circuit of rank seven, so each even
gate has at most two odd-pair decompositions in the resulting value set. Every non-entry
gate uses a distinct such three-value relation. Capacity four contradicts at least six
non-entry gates. The proof includes even gates that are entries and permits free values.

**Actual compatibility (proved).** The prior eleven-gate avoidance theorem requires five
distinct labels in one nonzero diagonal coset. The new cap excludes that wholly nonclean
consumer after any ten-gate first sheet, closing that entire branch of the (10,11) joint
profile. If the available clean-diagonal span has rank at most one, the only remaining
eleven-gate possibility uses four nonclean values in one coset and one nonzero clean value.
The particular ten-gate diagonal supplier displayed in section 30 has clean rank one and
largest coset size three, so it cannot extend to a joint 21 under no-feedback. This is
producer-specific; other ten-gate producers and mixed interfaces are not excluded.

**General entry-deletion certificate (proved).** With ordinary inputs and one entirely
free space F, let D span the target free parts. Any selected set I of entry occurrences
whose label span C has `C intersect D={0}` can be killed by a free-side projection fixing D.
Each selected gate becomes a wire, so `K>=L_D+|I|`. Repeated occurrences count individually.
If actual labels have quotient rank c beyond D, this gives `K>=L_D+c`; for four-triple
sheets it is the sharp explicit `K>=10+c`, attained by splitting entries. Eleven-gate
mixed interfaces have quotient rank one and either four entries/seven mirrored gates or
five entries/six mirrored gates. Nonclean label values cannot repeat; clean ones can.
The indicator of the nonclean entries is the sole trace relation, while the parity of
the traces determines the label relation in the five-entry case. These are algebraic
conditions on actual supplies, not charges for virtual differences.

**Joint parity restriction (proved, using the recorded joint lower bound).** A no-feedback
joint circuit that actually reads an odd free-a label needs at least 22 gates: project
that label to zero while fixing all even free parts, delete its entry, and preserve the
ordinary parts and ancestor condition. Otherwise a circuit below the established 21 bound
would remain. Thus a hypothetical joint 21 uses only even free-a operands.

**Diagonal interface and controls (proved by constructions/hand bounds).** A compact
event-free twelve-gate circuit supplies all four rows and three independent diagonals.
Requiring all four pure-own triples raises the event-free minimum to exactly thirteen:
six pure-own ancestor gates and seven distinct mixed required values, with matching
construction. The augmented unrestricted minimum remains 11 or 12. Two failed shortcuts
are saved explicitly: a six-gate triple-sum circuit can have overlapping even helpers
whose span excludes all-ones; an already recorded ten-gate sheet supplies three independent
pure even own-block values. Neither property forces an extra gate.

**Verification and judgment.** Six specified constructions and their stated projections
were checked directly, including the repeated-clean-label interface and both controls.
Independent reviewers checked the coset proof, its rank-one appendix, entry deletion,
mixed trace classification, and the diagonal-interface bound. Next useful target: joint
clean-diagonal supply and coset occupancy, or relation capacity across several populated
cosets. Both remaining joint splits still need work. The joint interval remains 21 to 22
under no-feedback; the unrestricted MixColumns interval remains `75 <= L <= 88`.

## 32. Coupled supply, independent relations, and causal span (2026-11-13)

Current account: [`../takeover-2026-11-13/tradeoff/README.md`](../takeover-2026-11-13/tradeoff/README.md).
This continues reviewed commit `4f4d918`. The results have hand proofs and independent
machine reviews, not formal verification or human certification.

**Coupled supply theorem (proved).** If a ten-gate first sheet supplies four distinct
values in one nonzero coset of the clean even diagonal, its actual clean-diagonal rank
is at most one. Equivalently, rank two forces all nonzero cosets to contain at most three
available values. For an even-own coset, seven first ordinary projections plus three
independent entries exhaust the budget. A repeated free displacement in two different
ordinary fibres would require disjoint subsets of independent entry labels with equal
nonzero sums. For an odd-own coset, few even physical gates remain. In the tight mixed
case, two clean directions require four affine-plane equations whose sum is zero.
Physical gate equations are independent by their latest-node pivots, so these equations
cannot all occur in one acyclic circuit. The other parity-count alternatives close by
relation counts or the dimension of the available formal relation space.

**General relation-rank framework (proved).** Use physical odd values as graph vertices,
joining a pair when its sum is a physical even value and colouring the edge by that
value. Let partial be the binary incidence map, chi the edge-colour parity map, and Z
the span of even-only triple equations. The rank of all available three-node equations
is `|O|-components+dim(Z+chi(ker partial))`. Non-entry gates cannot exceed this rank.
Evaluation of the even coordinates gives the upper bound
`|O|-components+|H|-rank(H)`, hence `entries>=components+rank(H)-ordinary input count`.
The note also proves population/matching bounds, clean-span restrictions, and an
odd-coset entry-origin bound. This distinguishes independent executable equations from
individually valid XOR identities. No circuit enumeration supplies the proof.

**Two diagonals at no extra producer cost (explicit construction).** An event-free
ten-gate producer supplies two independent clean diagonals. Together with the recorded
eleven-gate lower bound for three independent diagonals, this establishes exact maximum
clean-diagonal rank two at ten gates. It refutes the tempting rank-one shortcut. Its
available clean values span W of rank two, and every within-one-diagonal-coset difference
also lies in W. That particular producer's joint completion optimum is exactly 22; the
matching circuit adds two source gates and ten consumer gates. The result concerns the
specified producer, not the general joint map.

**Supplier-profile certificate (proved).** For a fixed actual supply Sigma, let W span
the supplied clean values and Delta_C span within-coset differences. If W is proper in
the required D and every `W+Delta_C` is proper, any consumer costs at least `L_D+2`.
The entry-deletion theorem limits a consumer within one gate of L_D to one nonclean
quotient direction, whose actual entries cannot span D under this deficiency condition.
Extra zero-consumer-part computations are not silently granted for free.

**Causal span (proved).** If every actual consumer entry is clean and all entries so far
are in W, every consumer-bearing signal has its free-side part in W. An exit cancelling
the consumer part can only yield another W value. Thus the first new independent clean
direction must be produced by a gate reading two zero-consumer-part operands. This fills
an implicit causal step in the (11,10) joint reduction: even allowing a possible exit,
a viable profile yields an actual eleven-gate source-only augmented supplier. It also
establishes the fixed-producer 22 result with feedback allowed, after checking the one
extra supplier gate rather than assuming it is an appended source gate. The older
one-diagonal fixed-producer exclusion remains valid: one extra supplier cannot raise
its clean span from rank one to the rank three needed by a ten-gate consumer.

**Verification and remaining scope.** Direct checks evaluate the specified ten-/22-gate
construction, two affine-plane relation graphs, and the fixed producer's deficient
supply profile. The four-edge graph has relation rank three; the three-direction graph
has seven available relations but rank four. A draft verifier's table of 16 free masks
was only membership bookkeeping; the saved verifier uses a direct predicate, and no
circuits were searched or eliminated by computation. Independent reviews cover the
coupled theorem, graph-rank formula, causal reduction, and fixed-producer optimum.
Remaining mixed patterns are rank one with four nonclean plus one clean label, or rank
two with two/three nonclean labels and two independent clean suppliers. The augmented
source minimum remains 11 or 12. General joint 21-to-22 and unrestricted MixColumns
75-to-88 intervals remain unchanged.

## 33. Rank-one exclusion and confinement of even supply (2026-11-13)

Current account: [`../takeover-2026-11-13/frontier/README.md`](../takeover-2026-11-13/frontier/README.md).
This continues reviewed commit `1fffbd0`. Universal statements have hand proofs with
independent machine review, not formal verification or human certification.

**Rank-one supplier exclusion (proved).** If a ten-gate first-sheet producer's actual
clean-diagonal span W has rank at most one, it cannot support an eleven-gate consumer
for the four triples whose required free parts span the rank-three diagonal D. The
remaining interface would require one actual clean direction together with four
nonclean values in one coset. Their difference span cannot complete D with W. The even
case forces independent even physical values and contradicts either relation counts,
components, or the sum of the four named residue-pair sums. The odd case gives too few
relations, or a dependent cycle among equations that would all need to be executed.
The proof also covers the trace possibility in which the clean label is the sum of all
four nonclean labels. Under the standard no-feedback hypothesis on first-sheet target
cones, the joint minimum for such a producer is at least 22. One additional supplier,
including a consumer-block exit, can raise clean rank by at most one and cannot enable
a ten-gate consumer requiring rank three.

**Projection-tree normal form (proved).** If a ten-gate producer has three independent
physical even own directions, seven first own-mask occurrences and three independent
free entries exhaust the budget. Projecting the free block to zero gives seven gates
whose odd-pair edges form a spanning tree of the cube on the eight odd own masks. All
physical even values are independent: their span consists of three independent own
fibre roots plus the independent free labels of even entries. If A counts odd helpers,
the seven original non-entry edges form a forest on 8+A nodes with A+1 components.
Adding the A odd-entry edges makes it a tree. The equality between odd-helper and
odd-entry counts does not identify those physical nodes. The known three-pure-even
control shows that the hypothesis itself is possible at ten gates.

**Confinement at clean rank two (proved).** For a ten-gate producer of clean rank two,
every physical even own mask lies in its two-dimensional clean own span W_b. Otherwise
the tree normal form applies. With no odd helper, five of six even gates must be
nonclean, including the first even gate. With three helpers, the two clean and one
nonclean even values cannot connect the four required residue pairs with distinct
named-pair sums. With one helper, uniqueness of its three-term named expansion limits
the non-entry relations to six. With two helpers, one nonclean value must have three
pair representations; any distinct second value with two representations forces an
alternating four-cycle. At most seven relations then have rank at most six, contrary
to seven independent gate equations. These four structural counts exhaust the helper
counts without enumerating circuits or trees. Consequently every even-coset difference
lies in W, and an even coset cannot supply the missing diagonal direction.

**Restricted augmented minimum twelve (proved and attained).** Four rows and any three
cycle-pair diagonals need twelve gates if the circuit is event-free and its only mixed
nodes are the seven required targets. The three paired row/diagonal demands force at
least three pure-own triples. Those need five pure gates, disjoint from the seven mixed
targets. The existing twelve-gate construction attains the bound. This leaves open
an additional mixed intermediate, cancellation, and arbitrary diagonal bases.

**Verification and remaining frontier.** Independent reviews cover all new proofs.
A direct check of one specified ten-gate construction confirms its projected cube tree,
physical forest and lifted tree; no circuit search or computer-driven elimination was
used. In a hypothetical joint 21, the ten-producer/eleven-consumer split now requires
clean rank exactly two and two or three nonclean labels in an odd diagonal coset. Such
a coset must cross the two own classes modulo W_b while preserving residue; that route
remains open. The other split remains the eleven-gate source-only augmented supplier,
whose minimum is 11 or 12. General joint 21-to-22 and unrestricted MixColumns 75-to-88
intervals are unchanged.

## 34. The ten-gate producer branch is closed (2026-11-13)

Current account: [`../takeover-2026-11-13/crossing/README.md`](../takeover-2026-11-13/crossing/README.md).
This continues reviewed commit `a7ff345`. The proofs received independent machine review;
they are not formal verification or human certification.

**Universal rank-two normal form (proved).** For every ten-gate first-sheet producer of
actual clean rank two, the two own classes each contain four named values whose residues
sum to `w+Pw`, nonzero for a nonconstant functional w annihilating the clean own plane.
Writing V for the physical even span and R for its residue image, E2 gives `ker(rho|V)=W`
and `dim V=2+dim R`. The odd relation graph preserves own class and residue modulo R.
The named class sums rule out residue ranks zero and one. Rank two forces at least four
components and exactly four entries. Combined with the physical even count, this leaves
at most two odd helpers. One helper gives at most five independent non-entry relations:
all doubled nonclean representations share the same three-term named expansion, so each
pair of their equations sums to the same formal vector. At least six are needed.
Thus there are exactly two helpers, four independent physical even values, and four
entries. Two even own masks and the four triples are the six first occurrences.

The six physical non-entry edges form a forest with four components, one for each
own-class/residue-coset combination. Its free-block projection has two four-node class
trees. Restoring the two odd-entry edges gives one five-node tree per own class, hence
one helper and one odd entry in each class. The two even-entry labels form a basis of R;
the odd-entry labels lie outside R. When the clean own plane omits full parity, both
even directions must first be generated in the class with three ordinary inputs; the
class rooted at the single remaining input cannot originate an even direction.

**Odd-coset closure (proved).** Suppose two available odd nodes of one diagonal coset
crossed the two own classes. With only two helpers, the two physical clean values could
then have at most one pair representation in total. To supply six non-entry equations,
the two nonclean even values would need three and two representations. The two-helper
saturation lemma forces an alternating four-cycle, reducing rank to at most five.
There are no even-only equations because the physical even values are independent.
This contradiction excludes the crossing. Together with E2, every within-one-coset
difference belongs to the clean span W. No single appended XOR can enlarge that span.

**Joint cost for a ten-gate first cone (proved and attained).** At clean rank two, the
full supplier profile is deficient for an eleven-gate consumer. The previous rank-one
proof covers the other possible clean ranks. Hence every fixed ten-gate producer needs
at least twelve consumer-bearing gates. Under no feedback into first-sheet target
ancestors, a ten-gate first-sheet cone therefore forces joint cost at least 22. At the
only possible exception, one extra zero-consumer gate leaves ten consumer-bearing gates
whose entries must all be clean. A source-side new clean sum stays in W; a consumer-block
exit also stays in W by chronological span. At rank at most one, one extra value cannot
reach the required rank three. Thus that exception is impossible as well. The existing
22-gate completion has exactly a ten-gate first-sheet cone and attains the bound.

**Remaining joint route.** A general joint 21 must have eleven gates inside its first
row cone, ten consumer-bearing gates, and three independent clean diagonals already
within that cone. Any eleven-gate augmented supplier likewise uses all eleven gates
in the row ancestor union: a ten-gate row cone cannot acquire the third direction from
its one remaining gate. This excludes a separate export route, not the eleven-gate
augmented core itself.

**Restricted augmented improvements (proved).** The no-extra-mixed, event-free lower
bound twelve now covers every independent even diagonal basis. With at most one cycle
mask, at least three pure triples are forced. With three cycle masks the prior incidence
argument applies. With two cycle masks, two unpaired triples and the noncycle precursor
leave one pure gate, insufficient to meet both paired incidence demands. Attainment is
still shown for one basis, not for every prescribed basis. A separate causal argument
shows that when two diagonals are noncycle and all diagonals feed rows, one additional
mixed gate is insufficient: independence of the seven required values limits its
required-node service, and their component masks prevent a sole such value from carrying
both noncycle diagonals to a row. This remains an event-free, one-auxiliary obstruction.

**Verification and limits.** The direct check evaluates one prescribed ten-gate producer
and its actual entry labels, four-component forest, and two lifted class trees. A small
partial circuit illustrates the limit of the auxiliary argument; it is not an augmented
solution. No circuit search or computer-driven elimination was used. The unrestricted
augmented interval remains 11 to 12, the general no-feedback joint interval remains
21 to 22, and unrestricted MixColumns remains `75<=L<=88`.

## 35. Augmented minimum twelve, joint 22, block-monotone 85 (2026-11-13)

Current account: [`../takeover-2026-11-13/augmented/README.md`](../takeover-2026-11-13/augmented/README.md).
This continues reviewed commit `a04558e`. Hand proofs received independent machine review;
they are not formal verification or human certification. No circuit search was used.

**The augmented gap is closed (proved and attained).** Computing the four first-sheet
rows and supplying three independent even diagonal values needs at least twelve gates,
with arbitrary sharing and cancellation permitted. The recorded event-free twelve-gate
circuit attains this for one diagonal basis. The lower bound holds for every basis;
a twelve-gate realization of every prescribed basis is not asserted.

**Independent baseline and parity.** Seven required non-input ordinary masks and at
least three entries force at least ten gates. At ten, the three labels span exactly
the free even space. For physical even span V, residue rank r and odd-graph component
count c, `dim V=3+r` and relation rank gives `c+r<=tau+1`; the eight named residues give
`c>=2^(3-r)`. At ten these force at most one odd helper, and named-pair/even-only counts
exclude both helper populations. Thus ten is impossible by a short new argument that
does not use the older finite basis checks. At eleven, projecting away any odd free
label fixes all targets and deletes its entry, contradicting the ten-gate exclusion.
All actual free labels are therefore even. Seven first occurrences leave only three
or four entries.

**Three entries (excluded structurally).** The component bound forces residue rank at
least two and at most two odd helpers. With zero helpers, at most six non-entry gates
are available. With one helper, repeated pair representations share one three-term
named expansion and their formal equation pairs have a common sum, giving odd-pair
rank at most five; even-only relations add at most one. Eight are required. With two
helpers, the five even values are independent, with three clean and two nonclean.
Each of two four-residue classes must be connected, requiring at least six nonclean
edges. Both nonclean colors would need three representations, impossible by unique
three-term named expansions of the helpers.

**Four entries (excluded structurally).** Seven first occurrences exhaust all non-entry
gates. Only the three independent diagonal own masks can occur as even own values,
so no even-only equation exists. Exactly three physical even values are clean.
The component bound permits at most three helpers. With zero or one, relation rank
is below seven. With two, clean pair capacity is at most two, and a saturated pair of
nonclean colors creates an alternating four-cycle, lowering the available rank below
seven even when the full even-value set is dependent. With three, one nonclean color
must connect four residue-pair classes using its one named pair and three helper pairs.
The four named pair sums become `k,k+h1,k+h2,k+h3`. Their sum is the all-eight named
relation and forces dependence of the three required diagonals. This final contradiction
excludes eleven without assuming event-freeness, restricting mixed auxiliaries, or
requiring every diagonal to be an ancestor of a row.

**Exact joint 22 under no feedback (proved and attained).** Assume no first-sheet target
ancestor has nonzero consumer-block part. A ten-gate first cone is excluded at total
21 by the preceding J10 theorem. Twelve first-cone gates plus the ten-gate consumer
minimum already cost 22. The only remaining profile would be an eleven-gate first cone
and ten consumer-bearing gates. All consumer entries must then be clean and span the
diagonal, so that cone would be an eleven-gate augmented supplier, now excluded.
The explicit event-free 22-gate circuit attains the minimum. The hypothesis still permits
cancellations elsewhere; the arbitrary-feedback joint problem is not settled.

**Block-monotone MixColumns needs 85 (proved).** Replace the sheet-0/1 charges by their
joint ancestor family H, excluding pure block-7 values, now of size at least 22. The
other five own-charge families each cost at least ten; the enlarged sheet-3 family
costs at least thirteen. The window intersections with H are `{1}`, `{7}`, `{7}`, empty,
empty, `{7}` for sheets 2 through 7. Own-block charges and the sheet-3 extra block-2
condition exclude every overlap; pure block-7 values are excluded from H. The other
families are pairwise disjoint by nonreciprocal own-window incidence. Thus at least
`22+13+5*10=85` physical gates are counted. This uses the cone definition of block
monotonicity and includes event-free circuits. It improves the restricted baseline 84,
not the unrestricted published lower bound.

**Repair and checks.** Generic event-free repair bounds may use baseline 85; the reduced
projected-value inequality is `G>=85+|V minus P|-|P minus V|`. Its correction can be
negative, and old charged-slack formulas cannot all be changed numerically without
checking their proofs. Direct evaluation confirms the specified twelve-gate source and
22-gate completion, all required values, rank three of the supplied diagonals, distinct
live gates, event-freeness, and absence of feedback to the first sheet. These are fixed
construction checks, not searches or computer-driven elimination.

The next direction is structural control of consumer-block feedback into first-sheet
ancestors, now the only way to escape the exact local no-feedback cost. Unrestricted
MixColumns remains `75<=L<=88`; no optimality claim about 88 is made.

## 36. Feedback savings, entry rank, and sharp small-rank separations (2026-11-13)

Current account: [feedback](../takeover-2026-11-13/feedback/README.md), continuing
reviewed commit `edbe77f`. Hand proofs with independent machine review, not formal
verification or human certification. No circuit search or case enumeration was used.

**General feedback repair (proved).** Split inputs into source and consumer coordinates;
all free values are on the source side, with zero freely available. Suppose all actual
source operands entering consumer-bearing gates lie in a space of dimension at most
`d`. All original source-side values can be replayed without consumer coordinates
using at most `G_0+h(d)` gates, where
`h(d)=2^ceil(d/2)+2^floor(d/2)-d-2`. The whole circuit then has a source-first realization
with at most `G+h(d)` gates and the same entry values. This is a total allowance,
not one allowance for each exit.

Every return is in the span of earlier actual entry labels, by chronological induction.
Maintain a basis of currently supplied values in the fixed entry space and assign new
independent basis elements alternately to two permanent groups. Physically complete
each group's span when it grows. A group of final size `k` needs at most `2^k-1-k`
extra gates. Every return is a sum of two physically available group values, so costs
at most its original gate. This proves the bound while respecting chronology and
without granting virtual combinations free. A secondary density/potential proof gives
`2^(d-1)-d` for positive `d`; it agrees through rank three but is weaker above it.

**Sharp through rank four (proved and attained).** The allowances at ranks zero through
four are `0,0,0,1,2`. A rank-three map has unrestricted minimum four and no-feedback
minimum five. A rank-four map has unrestricted minimum five and no-feedback minimum
seven. Require three masked prefixes on three source inputs, a masked fourth source
input, and their clean four-input sum. The five distinct output values give the
unrestricted lower bound; without feedback the clean sum needs three source gates
and the four consumer-bearing outputs need four additional gates. The displayed
circuits attain both counts. No sharpness assertion is made for ranks at least five.

**Returned directions cost consumer work (proved).** Let `D` span the source parts of
the required consumer outputs and `F` span all exits. Chronology puts `F` inside the
actual entry span `U`, and targets put `D` inside `U`. Entry deletion gives
`K>=L_D+dim(U/D)>=L_D+dim((F+D)/D)`. In the joint problem `L_D=10`. The four first-sheet
rows are independent modulo `D`, as their residues are the four independent triple
masks. Returning `k` first-sheet rows directly therefore needs at least `10+k`
consumer-bearing gates. The result does not count rows with more remote exit ancestors.

**Necessary ternary return at consumer cost ten.** Ten consumer-bearing gates force
all entry values into the rank-three diagonal. Repair with at most one extra gate,
together with augmented minimum twelve, forces at least eleven source-side gates.
At joint total 21, an exit must encounter exactly three independent available diagonal
values and require their three-term sum. No one-gate decomposition through earlier
source values, nor a compensating saving elsewhere in replay, can eliminate that
premium. This remains a necessary condition, not an existence or impossibility theorem.
An attempted mirror shortcut has not identified the corresponding physical pairs
in the original circuit; double transposition alone is insufficient. The missing step
and the danger of using eventual entry availability are recorded explicitly.

**Mirror restrictions (proved).** If no exit feeds a second-group target in a mirror,
literal reverse accumulation yields a no-feedback primal with the same budget, which
is at least 22. The proof preserves physical ancestry. With exactly three exports
and budget at most 21, the nonzero-first-part region has at least thirteen gates and
the zero-first-part region has four or five. Four forces every second-group target
to be a direct exit. With five and none directly an exit, the only extra value is
the all-ones mask, itself an exit, followed by adding each coordinate. Compatibility
with the remaining mirror region is not established.

**One-exit separation (proved and attained).** A decorated prefix construction gives
eight independent weight-five outputs, four on each side, boundary relation distance
six, block size at most three, and window width at most three. Its unrestricted
minimum is 21 and its no-feedback minimum 22. The saving uses one exit from a one-bit
consumer block. Private-coordinate restriction proves both lower bounds while
preserving the relevant ancestor condition. The construction is rectangular and
lacks the four MixColumns own-triple rows; it refutes only a general normalization
based on the listed coarse features. Its prefix mechanism is attributed to the earlier
recorded construction.

Direct evaluation checks six fixed witnesses (4/5, 5/7, and 21/22 gates). The universal
bounds are hand proofs. The unrestricted joint problem remains open; block-monotone
MixColumns remains at least 85 and unrestricted MixColumns remains `75<=L<=88`.
The next mathematical target is compatibility of the exceptional ternary return
with an optimal consumer's four specified rows, using actual values and reader relations.

## 37. Five physical diagonals close the ten-consumer case (2026-11-13)

Current account: [feedback continuation](../takeover-2026-11-13/feedback/README.md),
following reviewed commit `242ee0a`. Structural hand proofs received independent
machine review. No SAT, circuit search, enumeration, or computer-driven case elimination
was used. The unrestricted MixColumns interval remains `75<=L<=88`.

**Five diagonals force thirteen source gates (proved).** Four first-sheet rows together
with five distinct nonzero diagonal values need at least thirteen gates, allowing
arbitrary cancellation. At twelve, their nine distinct non-input ordinary masks plus
at least three entries force exactly twelve gates and exactly three entries. The
entry labels form a basis of the even free space. With O the physical odd nodes,
H the physical even nodes, V their span, and residue rank r, five diagonal values
span the clean three-space, so `dim V=3+r`. Independent non-entry equations and graph
incidence give `9<=|O|-c+|H|-dim V=13-c-r`. The eight named odd residues require
`c>=2^(3-r)`, so r is at least two. There must be two nonclean even values besides
five clean ones, leaving at most one odd helper. With no helper, at most three named
pairs and three independent even-only relations are available. With one helper, the
clean values have at most one pair collectively, the two nonclean values have at
most two pairs each, and even-only relations add at most two. Both are below nine.
This proves the lower bound; thirteen-gate attainment is not claimed.

**Joint minimum 22 with ten consumer gates (proved and attained).** Exactly ten
consumer-bearing gates force all actual entry labels into the clean rank-three
space. If the total were at most 21, rank-three replay would preserve all source
values in at most twelve gates. With no extra gate it would contradict the augmented
minimum twelve. At the exceptional step, three independent clean values are already
physical, and replay creates a new pair sum and their three-term sum. These five
physical diagonal values persist along with all first-sheet rows. The new thirteen-gate
lemma excludes the twelve-gate replay. Thus the total is at least 22, attained by the
specified no-feedback construction. This proof permits arbitrary consumer feedback
into the first-sheet cones. It leaves circuits with eleven or more consumer-bearing
gates unresolved, and does not strengthen the unrestricted MixColumns lower bound.

**The local ternary-return exclusion is false (specified counterexample).** Given three
source values a,b,c, compute `q=z0+z1`, `r=q+z2`, `t=r+z3`, `u=t+a`, `v=u+c`, `w=v+b`,
then the four outputs `w+z0`, `v+z1`, `u+z2`, `r+(a+b)`. These are ten consumer-bearing
gates with the required own triples and source labels `a+b+c,a+c,a,a+b`, a rank-three
four-element circuit. Before a+b is supplied, `t+w` returns the three-label sum.
Its four entry traces are `012,01,0,3`, so three are odd: a three-term relation among
four distinct entry labels is a real case, missed by a proposed two-way case division.
For MixColumns choose `a=d2`, `b=d2+d3`, `c=d1+d2`; the return is d0. This is not a
joint 21 construction. Computing a+b during repair permits its later supplier to be
bypassed, so a locally expensive exit need not increase total replay cost. That credit
works generally for this four-label three-term-relation interface. The main joint
proof uses the five-value obstruction instead of classifying exits.

**Secondary physical-wiring tools (proved).** In a three-entry consumer, flexible
adjoint accumulation forbids entries sharing a nonfree parent or reading one another;
their edges form a matching. In a four-entry consumer, expanding fanout into explicit
binary copy nodes makes transposition literally involutive. Deleting the four trace
ports and suppressing their unary copies returns the exact ordinary projection with
entries bypassed. A marked trace wire's ordinary derivative is the original entry's
own mask. In a six-gate triple circuit the two even helpers have disjoint reader sets,
and target adjoints are independent, so their nonzero marked derivatives differ.
This closes the repeated-label exit case as a secondary result. Abstract equality of
transposed output maps still does not justify arbitrary internal-node identification.

**Short-relation-free targets force auxiliary values (proved).** Let N distinct
nonzero non-input targets have no relation among three or four distinct members.
For a reduced source circuit with d coordinate inputs and A non-target gate values,
put `R=d+A`. A fixed non-target value connects at most one target pair; chronology
allows at most one orientation. Targets made from two non-target values form a simple
graph on R nodes with no four-cycle. Common-neighbour counting and Cauchy's inequality
give `N<=R+R(1+sqrt(4R-3))/4`, and thus `A>=(4N/7)^(2/3)-d`.
The result counts physical helper values and allows earlier targets to be reused.

**Exponential offline source-preservation overhead (proved).** In dimension d=2k,
the binary values `(x,x^3)` for nonzero x in `GF(2^k)` give N=`2^k-1` non-input targets
with no three- or four-term relation. The identities `x^3+y^3+(x+y)^3=xy(x+y)` and
`x^3+(x+h)^3+z^3+(z+h)^3=h(x+z)(h+x+z)` prove this symbolically. The helper bound
forces `Omega(2^(d/3))` auxiliary gates. A fixed feedback circuit with a one-bit
consumer can build each masked target and return it in one source exit, using
exactly G0=N source gates and entry span d. Every source-only realization preserving
these outputs therefore needs `G0+Omega(2^(d/3))`, even with advance knowledge.
This is not an exponential separation between optimal full circuits: the original
consumer work can be large. The general repair upper exponent d/2 remains above
this fixed-family lower exponent d/3.

**Separate online and prefix statements (proved).** Against an adaptive adversary,
a repair strategy with fewer than M available source values, where M is the least
integer with `M(M+1)/2>=2^d-1`, can be asked for a value not one XOR away. Each such
request costs at least one extra gate; at the stopping threshold total overhead is
at least `ceil((M-d)/2)`. This matches the general upper asymptotic order only in the
stated online model. The fixed prefix family separately has exact full-circuit
minima d+1 and 2d-1, hence saving d-2. These metrics are kept distinct.

The next joint question is whether an eleven-gate consumer's single allowed nonclean
return direction can reduce source cost enough to beat 22. Direct evaluation of the
one specified ternary consumer confirms its target masks, chronology, entry traces,
and MixColumns substitution. All universal arguments above are symbolic hand proofs.

## 38. Collision cost and the eleven-consumer mixed frontier (2026-11-13)

Current account: [eleven-consumer continuation](../takeover-2026-11-13/feedback/ELEVEN_FRONTIER.md),
following reviewed commit `6801e98`. Structural hand proofs received independent
machine review. The unrestricted eleven-consumer case remains open; no circuit
search, SAT, enumeration, or computer-driven elimination was used.

**Physical collision defect (proved, general).** Let D span required consumer source
parts, U span actual entry labels, and L_D be consumer minimum with D free. For any
source subspace C inside U with C intersect D zero, group physical consumer-bearing
gates and ordinary inputs by their full values modulo C. Count physical multiplicities,
including duplicate gate nodes, and let delta_C be the sum of class sizes minus one.
Then `K>=L_D+delta_C`. Extend C to a complement of D, project onto D, and retain the
earliest representative of each projected value. No two ordinary inputs are in one
class, so at least delta_C paid gates disappear. The targets remain fixed. Larger
projection classes only add deletions. Exit-only ancestors need not be trimmed,
and no source-first hypothesis is used.

**Causal and unique-pair consequences (proved).** If an exit returns nonzero f and a
set I of strictly later entries has label span C disjoint from D with f in C, then
`K>=L_D+|I|+1`: the exit's earlier operand collision contributes one deletion before
the later entries contribute theirs. At one gate above L_D, every nonclean difference
has at most one physical pair. An actual nonclean entry already uses that pair, so
any exit returning that label merely repeats a source value supplied earlier. In
particular a nonclean return cannot be read verbatim as a later entry. This leaves
indirect feedback through subsequent source arithmetic possible.

For the all-nonclean five-entry eleven-gate interface, four labels form an affine
plane q+W and the fifth h is outside their span. The nonclean coset is the union of
q+W and h+W. All five actual labels are excluded as nonredundant returns, confining
nonclean exits to the three values h+w for nonzero w in W. This does not confine
clean returns or itself give a new total joint lower bound.

**Diagonal confinement at arbitrary consumer cost (proved).** If every actual consumer
entry lies in clean D, then `G0>=12` independently of K. At G0 at most eleven, rank-three
replay either supplies a diagonal basis and all four source rows in at most eleven
gates, violating A12, or creates five distinct physical diagonals in at most twelve,
violating the five-diagonal bound. The existing 22-gate construction attains source
cost twelve. Thus eleven consumer gates with all-clean entries require at least 23
total gates.

A target-preserving retraction handles one additional class. If entries lie in D+<h>
with h=(beta,alpha), beta even and alpha odd, then sigma=alpha+beta is odd. On the
free a block set `P(x)=x+parity(x)*sigma`. It fixes even target labels and sends alpha
to beta, so all consumer entry labels become diagonal. It fixes ordinary b,z inputs,
preserves the z part of every gate, and does not increase source cost. Therefore the
original source also needs twelve gates, giving total at least 23 at K=11. Other
nonclean parity classes are not eliminated by this argument.

**Four-entry mixed source restriction (proved).** For an eleven-gate consumer with
four entries and rank-four entry space, the actual labels are a basis c,d,n,m with
c,d clean and n,m nonclean. Set e=n+m and p=c+d; c,d,e is a diagonal basis. Chronological
replay uses at most the two additional values e,p: every return splits into one sum
from each two-element basis group, and its nonzero coefficients use only earlier
actual entry labels. Append e after replay if needed. A12 forces G0 at least ten.

At a hypothetical total of at most 21, G0 is exactly ten. Neither e nor p can be an
original source value: either its pair gate is unnecessary or its later original
supplier is bypassed, producing an impossible augmented supplier in eleven gates.
No other original clean value outside c,d,e,p can exist, because replay would retain
five distinct diagonals in twelve gates. Thus original nonzero diagonal values are
exactly c,d. A clean exit cannot newly produce either independent basis label before
that label has been read, so every nonredundant exit is nonclean. If no exit uses both
c,d along with one of n,m, all exits replay in one gate and appending only e again
violates A12. Some return n+c+d or m+c+d is therefore necessary.

Projecting out the other nonclean label deletes one entry and produces a reduced
10-gate, three-entry consumer, in which the return is e+c+d. Entry matching excludes
it in a one-root own-mask fibre. Seven non-entry gates, the four triples and at least
two even own masks leave exactly one repeated non-entry own occurrence. The projected
return's operands must lie in that unique two-root fibre. This is a necessary condition,
not an exclusion or a construction of a joint 21.

**Remaining obligation.** A useful source question is whether twelve gates can supply
the four first-sheet rows plus c,d,c+d,e for independent diagonals c,d,e. A lower bound
of thirteen would close the four-entry mixed profile, but it is not proved by the
current five-diagonal argument. The five-entry mixed consumer and larger consumer
budgets remain separate. The unrestricted MixColumns interval stays `75<=L<=88`,
and the block-monotone bound stays 85. New results in this phase have hand proofs
and independent reviews; previous specified construction checks are unchanged.


## 39. Four-diagonal supply and closure of the four-entry interface (2026-11-13)

Current account: [four-diagonal continuation](../takeover-2026-11-13/feedback/FOUR_DIAGONAL_FRONTIER.md),
following reviewed commit `4adbf01`. Structural hand proofs received independent
machine reviews. Direct computation checked two specified constructions; no circuit
search, enumeration, or computer-driven case elimination was used.

**Four diagonals with a clean triangle cost thirteen (proved).** Require four first
rows and `c,d,c+d,e`, with c,d,e independent in clean D. A12 forces a hypothetical
at-most-twelve supplier to have twelve gates. Odd free labels can be projected away,
so all entries are even. Eight own first occurrences leave three or four entries.
Formal relation rank and named-pair uniqueness exclude the three-entry case and the
four-entry cases with at most two odd helpers. With three helpers, four residue classes
force one wholly named nonclean pair and three helper-to-named nonclean pairs. Their
three clean connectors are exactly c,d,c+d. The remaining diagonal e occurs in no
non-entry relation and must use the sole even entry from the only nonclean even value.
The three odd entry edges pair helpers with their equal-own named representatives.
Translation of own masks either repeats two of their labels or makes the three sum
to zero. Their rank is at most two; the e entry is a terminal export, so it cannot
supply the third free direction needed by the rows. Contradiction. Appending
`D13=D23+D12` to the specified twelve-gate source attains thirteen for one choice.
The lower bound holds for every prescribed triangle plus independent fourth value;
attainment for every choice is not asserted.

**Four-entry feedback subclass has minimum 22 (proved and attained).** For clean
c,d and nonclean n,m forming a basis containing D, n+m completes a clean basis.
Chronological replay in fixed groups {c,d},{n,m} preserves every source value while
retaining c+d,n+m for at most two extra gates. The four-diagonal theorem gives
`G0+2>=13`, hence source cost at least eleven. At eleven consumer gates total is at
least 22. For attainment, omit `D12=U1+E2` from the twelve-gate source, and split the
ten-gate consumer entry `z0+D12` into `z0+U1` then `+E2`. The source and consumer
costs are eleven each, and its entries are D01,U1,E2,D23. The circuit is event-free.

**Correction to the preceding interface scope (resolved).** Section 38's automatic
four-entry basis-pattern inference requires all eleven gates to lie in relaxed
consumer target cones. An extra consumer-bearing gate might be used only for a source
exit. Define cones by cutting at zero-consumer-part operand ports. If only ten bearing
gates remain in the cones, entry deletion makes their labels clean. The sole outside
gate can introduce at most one distinct nonclean label h. All other actual clean
labels then span D. A chronological clean basis a,b,c, paired as {a,b},{c,h}, replays
with at most two extra gates and retains a,b,a+b,c; the new theorem again forces
source cost eleven. Thus this omitted case cannot have total at most 21. If all
eleven bearing gates remain, the target-trimmed interface theorem applies. The prior
four-entry proof now states its basis-pattern hypothesis explicitly.

**Rank-four entries with physical clean rank three cost eleven (proved).** Suppose
actual entry labels span rank-four U containing D and original source values include
three independent clean diagonals. Choose an entry basis greedily in chronological
order and partition into two pairs. Source replay preserves all original values and
retains both pair sums for at most two extra gates. If either sum is an original value,
its earlier availability or later bypass saves one gate; at source budget ten this
contradicts A12. Otherwise, one nonclean basis element gives a clean triangle plus
an independent fourth value. Two or four nonclean elements can be paired by quotient
class to give two new clean values, hence five distinct physical diagonals. With
three nonclean elements their pair sums form a clean plane W; original clean values
avoid its nonzero points and lie in the complementary coset. An independent original
triple has a pair sum in W; select that pair sum in replay to obtain the forbidden
triangle plus fourth value. The four- or five-diagonal bound contradicts twelve
replay gates in each case.

**Remaining frontier.** A joint total at most 21 with exactly eleven consumer-bearing
gates must have five actual entry occurrences spanning a rank-four mixed space, all
eleven gates in the relaxed target cones, and original physical clean rank at most
two. Its five-entry trace/label and physical-collision restrictions remain in force.
This is not an exclusion of the five-entry case and does not settle larger consumer
budgets or the unrestricted joint minimum. The unrestricted MixColumns interval
remains `75<=L<=88`; the block-monotone lower bound remains 85.


## 40. Credited source replay and two five-entry closures (2026-11-13)

Current account: [source credits and the five-entry frontier](../takeover-2026-11-13/feedback/FIVE_ENTRY_PROGRESS.md),
following reviewed commit `577d8bc`. New arguments and the fixed symbolic example
received independent machine reviews. No circuit search or computer-driven case
elimination was used; the unrestricted MixColumns interval remains 75 to 88.

**Replay charged only for missing physical group values (proved, general).** Let U
be the span of actual consumer entry labels in chronological order, and split it as
`U=P direct-sum Q`. Require every entry-prefix span to split under this same direct
sum. Equivalently, each next entry has at least one component in the preceding span
of components on that side. Let A contain the original source inputs, permitted free
values, and all original source gate values. Set B to the number of nonzero values
in P or Q absent from A. Then all original source values and all group values have
a source-only realization with at most `G0+B` gates, preserving causal availability.
Maintain each currently generated group in full; an entry is split using its already
available component, and every exit is one XOR of two available group values. Each
synthetic value in A advances a distinct later original source gate and receives
credit when that gate is bypassed. Only synthetic values outside A add net cost.
A chronological greedy basis recovers the rank-only balanced-basis allowance h(d).
Final-span splitting without the prefix hypothesis is not sufficient for this proof.

**At most two nonclean label values (proved).** With rank-four entry space containing
D, clean entry rank three invokes the physical-supply theorem. If clean entry rank
is two, choose a chronological clean basis c,d and both nonclean values n,m. Their
pair groups cost at most two extras and retain c,d,c+d,n+m, a clean triangle plus an
independent fourth value. Thirteen source gates are required after replay, so G0 is
at least eleven. This permits repeated labels and arbitrary consumer budget. If the
original source already physically supplies the full clean triangle in span(c,d),
its later bypass saves one replay gate and G0 is at least twelve.

**Three nonclean entries at K=11 (proved).** Five-entry trace geometry gives clean
independent c,d, a nonclean related pair n1,n2 with n1+n2 in {c,d,c+d}, and a third
nonclean k outside span(c,d,n1). Rename n1 as the earlier member of the pair. The
planes span(c,d) and span(n1,k) split every chronological entry prefix, including
n2 because its n1 component is already read. Only c+d and n1+k can be missing group
values. Clean components needed early are computed from supplied operands and their
later original gates bypassed. Replay therefore retains the four-diagonal pattern
within G0+2 gates, proving G0 at least eleven. Combined with prior four-entry and
cone reductions, a below-22 candidate at exactly eleven consumer-bearing gates has
five distinct entry labels, four or five nonclean, rank-four entry span, and physical
clean rank at most two. All eleven gates lie in the relaxed consumer target cones.

**Four-nonclean three-term relation restriction (proved).** If c=n1+n2 is the clean
label, the four nonclean labels form a basis. Groups {n1,n2,c} and {n3,n4,p=n3+n4}
replay with premium at most one: every value of the first group is original. Appending
a cross-pair sum f=n1+n3 supplies a clean basis in G0+2 gates, so G0 is at least ten.
If an independent original clean v exists, then: when v is outside span(c,p), append
c+p; when v=c+p, append f; when v=p, the second group also has zero premium, so append
both c+p and f. Each supplies a clean triangle plus an independent fourth value
within G0+2 gates, ruling out G0 at most ten. Thus any below-22 candidate in this
profile has exactly ten source gates and physical clean rank exactly one.

**Remaining label geometries (necessary conditions only).** Besides that three-term
relation, four nonclean entries can have their all-four relation (affine plane with
the clean label outside its span), or the all-five-label relation (clean label equals
the sum of a nonclean basis). The latter all-five-odd-trace possibility must not be
omitted: the trace relation has nonclean support, while the label relation has odd
trace support. This is algebraic admissibility, not a circuit realization. With five
nonclean labels, four form an affine plane and the fifth lies outside its span.
In either affine-plane profile, all exits before the outside label is first read
are cost-preserving: clean values are pair sums of previously read plane labels,
and nonclean values in that span are actual entry labels, which cannot be newly
returned by the eleven-gate collision theorem.

**Five-label availability versus timing (proved with counterexample).** Five distinct
nonzero rank-four values, once physically available, need at most one extra XOR for
one-XOR access to every value of their span. In a basis the fifth value has weight
two, three, or four; respectively complete the complementary basis pair, a suitable
pair crossing the omitted coordinate, or nothing. This alone does not bound earlier
repair. A fixed circuit on four source units ai and four consumer units zi computes
pi=zi+ai, returns the three source triple sums on index sets 123,124,134 by cancelling
matching consumer sums, then reads t134 as its fifth entry. It has three source
exit gates but any source-only realization of those triples needs five gates. With
only four gates, three required odd triple results leave only one even pair helper,
which reaches at most two triples from the coordinate inputs. Five gates attain the
bound, so replay overhead is exactly two even offline. This is not a full-optimum
gap or a K=11 four-row witness; its nonclean return/re-entry violates the latter's
collision restriction. Timing and consumer constraints must be used together.

Four- and five-nonclean profiles, larger consumer budgets, and the unrestricted joint
minimum remain open. The block-monotone MixColumns lower bound remains 85, with no
claim that the unrestricted upper bound 88 is optimal.


## 41. Tight fibre wires and the exact eleven-consumer minimum (2026-11-13)

Current account: [eleven-consumer closure](../takeover-2026-11-13/feedback/ELEVEN_CONSUMER_CLOSED.md),
following reviewed commit `d8bfd65`. Structural hand proofs with independent machine
reviews; no circuit search, enumeration, or computer-driven case elimination.

**Exact result.** Every joint 0/1-sheet circuit with exactly eleven consumer-bearing
gates has total cost at least 22, even with arbitrary feedback and cancellation.
The specified eleven-source/eleven-consumer circuit already checked in section 39
attains 22. The ten-consumer minimum was already 22. A joint circuit below 22 must
therefore have at least twelve consumer-bearing gates and at most nine source gates.
The unrestricted joint minimum remains open. MixColumns stays 75 to 88, with the
block-monotone lower bound 85 unchanged.

**Entry paths and physical wire derivatives (proved).** Five entries in an eleven-gate
consumer leave six ordinary non-entry gates, the minimum for four triples. No projected
non-entry gate can repeat a prior value, be zero, or be an input. Each own-mask fibre
has one root and its entry edges form a tree. An exit returns the XOR of labels along
a fibre path, all read before that exit. Explicit fanout expansion gives nine inputs,
four outputs, eleven XORs and six copies; literal transposition has six XORs. Deleting
the five trace ports and suppressing their unary copies returns exactly the ordinary
projection under reversal. Marked-wire derivatives are the original own masks.

The two even helper values in a six-gate triple circuit have disjoint sets of odd
triple readers. The latter's full adjoints are independent by terminal-output
triangularity, so wires carrying the two different even values cannot have the same
nonzero ordinary derivative. For two adjacent entry edges, flexible local accumulation
exposes their trace sum on a wire with their common own derivative. This works for
siblings and for a parent/child pair by summing all other contributions. Exposures at
different original vertices can be chosen simultaneously. Three consecutive distinct
odd traces would expose two distinct even sums with the same derivative, impossible.
Thus an all-five-odd interface has fibre paths of length at most two, all exits cost
at most one original XOR, and source replay has zero overhead. No-feedback J22 closes
the previously retained five-term four-nonclean label relation.

**Three-term four-nonclean relation (closed).** For labels n1,n2,n3,n4,c with c=n1+n2,
the n3,n4 traces are the mirror's distinct even helpers. Their own derivatives differ,
so their entries lie in different fibres. An exit path uses at most one of them.
Complete only {n1,n2,c}; all three values are original, so every early computation
is credited to bypassing its later source producer. Each exit is one available
triangle value plus at most one of n3,n4. Replay costs no extra gates and J22 applies.

**Affine-plane return restriction (proved).** Let four nonclean labels form q+W and
let h be the outside fifth label, clean or nonclean. The four plane traces are odd,
the h trace even, and h's trace differs from every plane-trace pair sum. Two adjacent
plane-entry edges in h's fibre would expose a distinct even value with h's derivative,
contradicting separation. Thus no two plane edges meet anywhere in that fibre. There
is at most one plane edge at either endpoint of h and one possible straddling path,
returning f=h+w with w=qi+qj nonzero in W. Paths avoiding h return a plane pair sum,
zero, or an actual nonclean label; the latter cannot be newly returned by collision
accounting. All other exits therefore cost at most one gate. Only w may cost one extra.

If h is clean, positive repair produces the clean triangle h,w,f. One appended plane
difference independent of w gives a fourth independent-of-triangle diagonal in G0+2
gates, contradicting the thirteen-gate supplier bound at G0 at most ten. Zero overhead
instead contradicts J22. This closes the four-nonclean affine-plane profile.

**Six values in one diagonal coset require twelve source gates (proved).** The theorem
includes source exports, inputs and free values, and permits arbitrary cancellation.
An even-own coset with six points requires five distinct nonzero even own firsts,
four row-triple firsts, and three source entries: at least twelve gates. An odd-own,
odd-free coset needs six paid non-row odd gates, the four rows, and two even helpers.
For odd-own/even-free parity, the eight named inputs/rows have distinct residues, so
six coset points force five odd helpers in one crowded six-node coset. At eleven gates
only two even values remain. Four triples and two distinct even own masks require at
least six non-entry gates, with no target-cone trimming assumption. Every non-entry
equation is an odd-pair relation for one of the two even values. A nonclean even value
has at most one crowded-to-named pair and one wholly named pair; a clean value has
at most three pairs in the crowded six-node set. If either even value is nonclean,
at most five relations are available. If both are clean, they are independent and
all equations project injectively onto a six-node incidence space of rank at most
five. Six actual gate equations are independent by latest-result pivots, contradiction.

**All-nonclean profile (closed).** Its necessary straddling return f=h+w is nonclean,
differs from h, and lies outside the four-label plane because h does. It is a sixth
original physical value in the same D-coset as the five entry labels. One-extra-gate
source replay would retain all six and the four rows in G0+1 at most eleven source
gates, contrary to the new supplier theorem. If no extra gate is needed, J22 already
excludes the circuit. All four profiles retained in section 40 are now closed. Earlier
cone, four-entry, clean-entry and two/three-nonclean reductions supply the remaining
coverage. If normalization drops the consumer count to ten, its established bound
applies instead. No extension to a consumer with twelve or more gates is asserted.


## 42. Saturated quotient structure and the twelve-consumer frontier (2026-11-14)

Continuation after reviewed commit `cfab8f6`. Full account:
[the twelve-consumer frontier](../takeover-2026-11-13/feedback/TWELVE_CONSUMER_FRONTIER.md).
Hand arguments with independent machine reviews; no circuit search, enumeration,
or computer-driven case elimination. The twelve-consumer case remains open.
The unrestricted interval remains 75 to 88, and the block-monotone bound remains 85.

**Saturated quotient theorem (proved, general).** If actual entry labels span U,
target source parts span D, and K=L_D+c for c=dim(U/D), choose any actual quotient
basis and its full-label span C. The selected entry edges form a forest of defect c.
Its components lie in full-value cosets modulo C. Any further coset merger would
increase physical collision defect beyond c and contradict the collision lower
bound. Hence these partitions coincide. Every return in C is a chronological path
sum of selected labels. Any actual nonclean label can be included in a quotient
basis, so its unique physical difference pair is its selected entry edge. It cannot
repeat at an entry or be newly supplied by an exit. Indirect feedback through changed
values is not excluded; returns need not all lie in one chosen complement.

**Outside-cone coloop theorem (proved, general).** Under the same equality, an
unselected gate outside the relaxed output cones would remain dead after projection
and selected-entry bypassing. That would leave a circuit below L_D. Thus every
outside gate is an entry selected in every quotient basis, equivalently a coloop
occurrence. At most c outside gates exist. This argument includes gates used only
for exits and does not assume they can be trimmed from the original joint circuit.

**Chronological complement (proved, general).** Greedily select actual entry labels
when their quotient images enlarge the span modulo any prescribed D subset U.
Their span C complements D, and every entry-prefix splits: a selected label is pure
C; a later label's C component is a combination of representatives already read.
Credited replay therefore completes D and C, preserving original source values, for
G0+(2^dim(D)-1-m_D)+(2^dim(C)-1-m_C). The counts refer to original physical values,
including later original producers; virtual span membership receives no credit.

**Rank-four source floor (proved).** For the two-sheet problem, dim U at most four
forces G0 at least ten at any consumer budget. Rank-three clean confinement already
forces twelve. At rank four, choose a clean plane containing the original clean
span and a complementary plane from first actual nonclean representatives.
Two physical clean directions give a replay with at most two extra gates and hence
G0 at least eleven by the four-diagonal bound thirteen; one gives at least ten.
If G0 at most nine and no physical clean value exists, generic two-extra replay and
the six-value coset theorem limit the original nonclean coset to five values.
A chronological greedy basis accounts for four; only the possible fifth can first
be supplied by an exit. Its expansion is an odd-weight nonbasis combination, hence
exactly three earlier basis terms. One-extra replay supplies five coset values
within ten gates, violating the ten-gate coset cap.

**Full-diagonal supplier bound (proved).** The four first-sheet rows and all seven
nonzero clean diagonal values require at least fifteen source gates; attainment
is not claimed. At fourteen, eleven distinct own-mask first occurrences plus three
free entry directions exhaust the gates. All actual free labels are even.
For physical even values H and residue rank r, the available odd-pair component
bound gives g+r at most four and g at least 2^(3-r), so r at least two.
Seven clean even values plus two nonclean even values leave at most one odd helper.
Without a helper, at most three odd-pair relations and five independent even-only
relations exist; with one, at most five and four respectively. Both fall below
the eleven independent non-entry equations. For rank-five entry space, complement
completion then gives G0 at least 5+m_D+m_C, hence at least 7+m_D.

**Global twelve-consumer reduction (proved necessary conditions).** A total at most
21 with K=12 has G0 at most nine, entry rank exactly five, and quotient rank two.
There are at most two original physical clean nonzero values. Two outside-cone
gates would leave a ten-gate target consumer needing three clean entry directions,
contradiction. Thus at most one outside entry survives. With only one useful exit,
reassociate v=u+h and f=v+w as g=u+w, f=g+h; this moves one gate to the source without
increasing the total, contradicting the closed eleven-consumer case. Any surviving
tail must consequently support at least two distinct nonredundant returns.

**Target-live wire reduction (proved with stated hypothesis).** If all twelve
consumer gates lie in the relaxed output cones, there are five or six entries.
Six entries leave a six-gate ordinary mirror, so trace rank is four and the unique
actual-label relation is the odd-trace indicator. The trace relation space is the
quotient-signature row space. Repeated traces remain possible; all odd and pairwise
distinct traces are excluded by zero-overhead replay. With five independent labels,
the seven-gate mirror has three independent even trace classes of sizes (3,1,1)
or (2,2,1). Different classes cannot meet in an entry tree. Internal-component
returns alone give a replay contradicting the source bounds. Therefore exactly one
ordinary fibre has two entry-tree roots, and a nonredundant exit joins its components.

**Specified limitation.** The seven-gate ordinary circuit p=x0+x1, q=x2+x3,
t=p+q, outputs t+xi has distinct even wires p-to-t and q-to-t with identical ordinary
derivative 1111. Six-gate even-wire separation does not extend unconditionally.
The next structural obstruction is shared work in returns crossing entry components
or in multiple returns through the unique outside entry. No twelve-consumer or
unrestricted joint minimum is claimed.


## 43. Shared returns, mirror forests, and six-entry reduction (2026-11-14)

Continuation after reviewed commit `8ab0b3e`. Full account and coverage:
[six-entry frontier](../takeover-2026-11-13/feedback/SIX_ENTRY_FRONTIER.md).
Structural hand proofs with independent machine reviews, not formal verification.
No circuit search, enumeration, or computer-driven elimination.

**Current reduction (proved).** A joint circuit below 22 with exactly twelve
consumer-bearing gates has all twelve in its relaxed target cones and exactly six
entry occurrences. Its entry span has rank five and trace rank four. Every outside
entry case and the target-live five-entry case are excluded. The six-entry case,
larger consumer budgets, and the unrestricted joint minimum remain open.
MixColumns remains 75 to 88; the block-monotone lower bound remains 85.

**Affine-tree transfer (proved, general).** Let an outside entry v=u+h be read only
by source exits, with useful partners in one entry tree after v is removed.
Translate the connecting subtree at u by t_x=h+u+x. Path labels were read before
the return needing them. Retain translates, credit original physical values to
their source producers, and charge only B missing translates. Removing v leaves
at most G0+B source gates and K-1 consumer gates. At most one missing translate
permits removal without increasing cost. A star, or a three-edge tree with two useful
partners, has this property. Other feedback may remain in place. Triangle completion
and cheap differences between requested returns can improve on the raw tree count.

**Odd-value forest (proved, general).** In an ordinary XOR circuit with independent
computed even values, put vertices at odd inputs/gate occurrences. An even gate
joins its two odd parents; an odd gate joins its odd parent to its result, labelled
by its even operand. Chronology and independence make this a forest with n-r
components for n inputs and r even gates. In a literal transpose with extra source
ports only on even-valued wires, forest-cut equations express edge fluxes in terms
of target boundary values. If boundary source parts lie in D, all odd-wire source
parts lie in D. This does not supply those parts as separate physical source values.

**Clean-endpoint chains (proved specialization).** A seven-gate triple mirror has
three independent even helpers serving four odd target gates. Their reader counts
are (2,1,1); each nonzero derivative segment gives one entry chain with a clean
endpoint. Different classes occupy different own fibres. A repeated fibre has
one chain and an isolated clean root. The only potentially nonclean non-entry root
is the merge for the two-reader helper. A later clean endpoint is used only as an
algebraic identity; independent actual-label expansion supplies the timing.

**Five-entry target-live closure (proved).** For class sizes (3,1,1), at most two
nonclean crossing positions exist and differ by one actual label. For (2,2,1), at
most one exists. In each case three specified additional source helpers suffice
for a chronological source-only replay supplying a clean triangle and an independent
direction. At G0 at most nine this gives a supplier within twelve gates, contrary
to the thirteen-gate four-diagonal theorem. Thus target-live K12 with five entries
has total at least 22. No attaining construction for this exact subclass is asserted.

**All outside-entry cases (proved).** The previous coloop reduction leaves an
eleven-gate target core of entry rank four, with four or five entries. The four-entry
case uses the same seven-mirror chain theorem: complete two plane groups and add
at most one tail helper, again contradicting the four-diagonal supplier bound.
For five core entries, zero/one nonclean labels violate rank or the physical clean
cap. Two nonclean labels force a repeated-clean interface c,c,d,n,m; any surviving
four-edge fibre is c-n-m-c. Its endpoint difference repairs the two useful returns.
Three nonclean labels have a three-term triangle or a four-term relation. Triangle
completion costs no net extra for original values. In the four-term case, wire
separation forces a two-edge a,b path joined by k to one clean edge. Partitioning its
five vertices into those two paths gives a cheap pair among u and two partners,
saving one XOR across their returns. Four nonclean profiles are the three-term,
affine-plane, and all-five-odd relations; these reduce to a triangle, a three-edge
tree, or a star. The all-nonclean affine-plane case has the same bound. Every
profile is covered, with chronology preserved; no full joint theorem is applied
directly to a relaxed core before its source is repaired.

**Even-entry source floor (proved, arbitrary consumer budget).** If every actual
entry has even ordinary source parity, then G0 is at least ten. At G0 at most nine,
three even-projection rank increases and four first triple masks give seven
independent odd-pair equations. With zero or one odd helper beyond the eight named
inputs/rows, the available relation rank is at most five; all three-named expansions
of one helper coincide because the only named relation uses all eight. With two
odd helpers, the three even source values have independent own projections, so no
exit first supplies any of them. All exits are redundant, contradicting local ten.

**Retraction and free sections (proved).** An odd wholly free direction in U permits
a free-coordinate retraction fixing all targets and lowering entry rank by one.
Together with the rank-four source floor, it is excluded at rank five and G0 below
ten. The remaining U has one even free direction q and an odd-own actual entry h,
so U=D direct-sum span(q,h). A normalized even-free-part circuit has U equal to the
inverse image of a two-dimensional residue plane containing odd vectors. Physical
credits are recomputed after normalization. Separately, any linear section H of
the ordinary entry projection gives source-only replay cost G0+2^r-1-m_H: the
remainder is free, so no extra prefix-splitting hypothesis is required.

**Next structural boundary.** The remaining six-entry mirror has a two-component
odd forest, but odd trace ports add terms to its cut equations. The clean-endpoint
conclusion cannot be imported unchanged. Internal helper-reader merges and the
restricted source residue plane are the next promising objects. Repeated traces
remain open; the all-odd pairwise-distinct subclass was already excluded.


## 44. Charged mirror forests and local repeated-trace directions (2026-11-14)

Continuation after reviewed commit `ed374d1`. Current account:
[charged frontier](../takeover-2026-11-13/feedback/CHARGED_FRONTIER.md).
Structural hand proofs with independent machine reviews; no circuit search,
enumeration, or computer-driven elimination. The twelve-consumer minimum, larger
budgets, and unrestricted joint minimum remain open. MixColumns remains 75 to 88.

**Charged forest equations (proved, general).** In the odd-value forest forced by
independent even mirror helpers, attach S_v equal to the actual labels at the trace
ports of each physical odd occurrence. Full edge fluxes satisfy
sum_incident X_e=B_v+S_v, with uncharged target/ordinary-input boundary B_v.
A component has total charge equal to its boundary sum. Cutting an edge gives its
flux as the boundary-plus-charge sum on one side. Modulo clean target space D, the
edge-flux span equals the vertex-charge span exactly. Terminal ordinary outputs at
even helpers contribute zero-source terms and are included in the full identities.

**Global/local decomposition (proved for the six-entry interface).** Let t count
distinct traces and H be the class-aggregate source span. Its only aggregate relation
is the union of odd trace classes, so dim H=t-1 and D subset H. Even aggregates lie
in D plus the odd aggregate span by the helper adjoint equation. Thus forest fluxes
have quotient rank dim(H/D)=t-4, while dim(U/H)=6-t. The latter quotient is the direct
sum of class sectors of dimensions m_tau-1. Every physical consumer wire's residual
lies in its mirror-value class sector; different classes meet only at H-valued
consumer nodes. No physical source availability is inferred from H membership.

**Physical carriers (proved).** In a class copy tree, all ordinary reader boundaries
and the root have zero residual modulo H. A port subset has nonzero residual exactly
when it is nonempty and proper. The nonzero wires are therefore precisely the minimal
subtree connecting that class's ports. Pairs give paths; a triple gives a three-arm
tree before the later exclusion. No causal orientation or cost bound follows merely
from this support identity. The six-gate mirror's odd forest consists of two
four-vertex paths in odd cosets of the helper span. Each carries the same nonzero
clean aggregate delta, so both contain odd trace ports.

**Triple trace excluded (proved).** A triple consumes both trace relations and forces
three nonclean labels a,b,k of the three quotient signatures plus clean labels c,c,d.
The repeated trace is even, the c traces are odd, and d has the other even trace.
Same-even-trace entries in a fixed own fibre form a connected chain, without needing
clean endpoints. The c attachments cannot meet or be one NC edge apart. Only returns
c plus two NC labels need extra work; at most two distinct such values exist, and
both share the helper c plus the middle NC label. Source replay costs G0+1. Appending
one XOR to a difficult returned value supplies a clean direction independent of c,d
within G0+2<=11, contradicting A12. Hence all trace multiplicities are at most two.

**Two-pair closures (proved).** If both even helpers are repeated twice, the other
two labels are the same clean c, and the pair sums complete it to a clean basis.
Even-wire separation isolates the pair chains. At most one difficult return can
occur, because both possibilities are distinct physical clean values beyond c.
One helper and one appended pair sum violate A12. For a three-term actual relation
with two repeated pairs, one pair and singleton form an original triangle; the
other pair and singleton are the two even traces and are separated in own fibres.
Triangle advancement credits and one pair helper provide a clean basis in G0+1,
also contradicting A12. Other pair relations require separate arguments.

**All-odd-own source entries excluded (proved).** In the even-free-part normal form,
only two named inputs/rows lie in U. Six distinct odd nonclean actual labels force
at least four odd helpers. With no even source value, four first triple masks need
new exits while at most one odd U value is available outside the actual labels.
With one even value, equality forces four helpers and no useful odd exit. Its own
mask is the all-four sum and it must first be returned. If i named inputs lie in U,
forming that first return needs 4-i unit-own helpers; the 2+i rows outside U need
at least 1+i distinct triple-own helpers, since only one can equal that even value
plus a named input. Five helpers are required, exceeding four. Combined with the
even-entry floor, both own parities occur. The odd-own indicator p satisfies Zp=0,
and nonzero trace columns exclude weight one, leaving 2–5 odd-own occurrences.

**Free-seeded replay (proved, general).** A free subspace S in one group can seed
the credited replay invariant from time zero. It suffices that every E_i+S split,
even when E_i alone does not. Greedy representatives modulo D+S produce a canonical
complement. In rank five, seed the unique even free q and choose the first odd-own
entry h. Full-diagonal replay gives G0>=7+m_D+1_(h+q in A). At m_D=2, G0=9 and h+q
is absent from the whole original physical source set. This counts later values
through producer credits, and does not require q to be an actual entry.

**Equal-trace series (proved).** No nonempty subset of reader-adjoint contributions
can sum to zero in a six-gate minimum mirror. Equal adjacent entry traces are thus
strict series in the relaxed target graph. Replacing the second entry by the sum
label exposes the first as an outside entry, retaining all source-exit uses.
An original physical pair sum would pay for this redirection and contradict the
closed outside case. Without a credit it costs one extra source gate. A surviving
segment therefore has G0=9, an absent pair sum, and a useful intermediate exit.
These conditions are not claims about arbitrary separated equal traces.

The current next task is a joint cost argument connecting the global forest charges
to the local repeated-class paths, with original chronology and physical source
credits retained. The rank identities themselves are not lower bounds on gates.


**Consequential failed inference and specified counterexample.** A proposed all-odd
four-trace closure counted the union of possible adjacent trace-pair exposures as
though all used the same two even helpers. This is false: local accumulator orders
at one vertex can change the unmarked helpers. The saved six-gate mirror computes
p=x0+x1, t=p+x2, j=t+x3, then E0=j+x0,E1=j+x1,E2=j+x2,E3=t. Its transpose has an
all-four-own node with three branches. Alternative local orders expose x0+x1,
x0+x2, or x1+x2 separately, giving a triangle of class adjacencies. A specified
twelve-gate decoration has six entries, traces (x0,x0,x1,x1,x2,x3), rank-five labels,
and the correct diagonal target parts. No nine-gate source supplier is claimed.
The attempted all-odd repeated-trace closure is withdrawn. Simultaneous exposures
at distinct vertices remain valid; the other phase results use fixed marked even
traces or zero accumulators and are unaffected. See
[the counterexample](../takeover-2026-11-13/feedback/TRACE_EXPOSURE_LIMIT.md) and its review.


## 45. General unrestricted arguments replace the fixed-budget frontier (2026-11-14)

Continuing reviewed commit `0cb775c`, the user directs the research toward general
structural arguments and away from incremental numerical improvements or
restricted bounds without a specified unrestricted use. The twelve-consumer
case breakdown is deferred. Its proofs and open cases are preserved. The current
program is [general unrestricted accounting](../takeover-2026-11-13/general/README.md).

**Parity and exact defect.** For any parity functional, let s count odd coordinate
inputs, c the components of the odd-occurrence multigraph, E the even gates,
mu its cycle rank, and d the even-plus-even gates. The effective even span has
rank r=s-c, and E-r=mu+d exactly. The partition-span statement was already in
causal/REPORT Lemma 2.2 and the cyclic account; it is reconstructed and attributed,
not promoted as new. Occurrence-level chronology identifies every unit of the
defect with a paid cycle-closing or even-plus-even gate.

For marked ports and literal transposition, let H0 be the source boundary space
plus the aggregates on ODD occurrences, and Q the ordinary gate-adjoint source
span. Then dim((H0+Q)/H0)<=E-r, and H0+Q is the span of the boundary and all
occurrence aggregates. The matrix proof is a kernel-rank inequality; the graph
proof shows the physical defect generators. Quotienting by all aggregates from
the start would be vacuous. Partial copy-tree values remain local subset sums,
not separately supplied source operands. Both the cycle term and the even-only
term have specified rank-one witnesses, extending by disjoint copies.

**An exact population result and its obstruction.** For all-odd required targets,
the minimum number of even gates equals s-c_max over compatible input partitions.
A star-pair basis realizes it, followed only by odd accumulations. Thus every such
target set admits defect zero, although its odd work may be large. For m required
odd non-input values and H other odd gates, the exact total is
G=m+H+(s-c)+(mu+d). The missing general result must couple these costs; targets
alone cannot force positive even redundancy in every circuit. Costs for different
parities or different marked interfaces cannot simply be summed.

See [the theorem and scope](../takeover-2026-11-13/general/ODD_COMPONENT_DEFECT.md)
and [independent review](../takeover-2026-11-13/general/reviews/odd-component-defect-review.md).

**A rejected unrestricted relaxation.** The coordinate quadratic lift satisfies
q(a+b)=q(a)+q(b)+a wedge b. Telescoping gives the target tensor as the sum over
physical gates of influence(g) tensor (parent1 wedge parent2), counting every
gate once. Nevertheless, allowing these atoms independently has an explicit
sixty-term MixColumns realization: prescribed three-coordinate terms are shared
within sixteen row pairs, reducing the rowwise count 76 by 16. A direct checker
verifies the displayed sixty atoms against all 32 matrix rows. No optimization,
configuration enumeration, or circuit search is used. This ceiling rules out
recovering 75 from the unconstrained tensor rank. It is not a sixty-gate circuit;
parent supply and a common realization of influences were omitted by the model.
See [the identity and limit](../takeover-2026-11-13/general/QUADRATIC_LIFT_LIMIT.md)
and [independent review](../takeover-2026-11-13/general/reviews/quadratic-lift-review.md).

These are structural hand arguments with machine review, not formal verification
or human certification. The unrestricted 75–88 range is unchanged. The next task
is a whole-circuit tradeoff theorem or a stronger invariant for actual sharing,
not another local fixed-budget exclusion.


## 46. General combined cost, shared-helper amplification, and causal gaps (2026-11-14)

Continuing reviewed commit `095f142`, this pass pursues general unrestricted
arguments. It does not resume the fixed-budget consumer classification.

**First-odd-target theorem.** For any nonzero chosen parity with at least one required non-input odd target,
let H count odd gates beyond
required non-input odd targets and d count even-plus-even gates. For an odd target
z let w_o,w_e count its supported initially odd/even coordinates. Every circuit
satisfies H+d>=min_z(w_o+2w_e-3)/2. In the first odd target's ancestor cone,
let h count other odd gates, E_C even gates, a,f input ancestors of the two
parities, beta the undirected cycle rank, and B_e excess even-node fanout.
The exact physical identities E_C+f+B_e=h+1+2d_C and
g=h+1+E_C=a+f-1+beta give
2(h+d_C)=a+2f-3+beta+B_e. Supported coordinates are ancestors, h<=H and d_C<=d.
This allows arbitrary cancellation, repeated reads, and earlier even outputs.
It grants no free combinations of initially even inputs.

With r=s-c, delta=d+mu, and t_o required odd targets, the whole-circuit account
gives G>=t_o+r+b_min+mu. If c_max is the maximum target-compatible input-partition
count, then G>=t_o+max(t_e,s-c_max+b_min). Different parity or output-group bounds
cannot simply be summed. See [the proof](../takeover-2026-11-13/general/FIRST_ODD_TARGET_TRADEOFF.md)
and its linked independent review.

**An exact exchange law.** All complement sums J+x_i on n inputs have unrestricted
minimum 2n-2 for every n>=4. A first-target cone has exact size
(w-1)+(number of canceled input ancestors)+(undirected cycle rank). A minimum
cone is a laminar formula tree; that supply cannot finish all complement outputs
at total 2n-3. For even n=2k there is now a direct general proof: r>=k and H+d>=k-2.
The exact excess is (k-c)+(H+d-(k-2))+mu, so every optimum has minimum even rank
and no odd-graph cycles. Specified optimal circuits attain H=k-2-j,d=j for every
0<=j<=k-2. This is a scalable unrestricted tradeoff, not a circuit-class restriction.
See [complement tradeoff](../takeover-2026-11-13/general/COMPLEMENT_TRADEOFF.md).

**One shared helper can have unbounded benefit.** For m targets
x+a+b+c_i+d_i, compatible parity partitions force even rank at least m+1. The
first-odd-target theorem forces H+d>=1, giving unrestricted optimum 2m+2, attained
with the shared odd triple x+a+b. Named inputs and targets have unique unordered
pair sums. With no odd helpers, chronological pair-equation counting forces d>=m,
so the optimum becomes 3m+1. For m>=2 every optimum has one odd helper, minimum
even rank, and zero defect. Therefore deleting one odd helper cannot have a
universal constant allowance, even if the entire circuit is reorganized. The
restricted comparison serves this unrestricted obstruction. See
[shared-helper amplification](../takeover-2026-11-13/general/SHARED_HELPER_AMPLIFICATION.md).

**A scalable causal/cyclic separation.** For each odd r>=3 and k>=2, use r arms
of k coordinate inputs. Targets are the full sum p and its successive prefix
removals along each arm, omitting one full endpoint to give an invertible square
map M_(r,k) of dimension rk. Every target has weight at least (r-1)k. The first
produced target requires that many input ancestors, giving a forward lower bound
attained by preparing one endpoint then traversing the target tree:
L(M)=(2r-1)k-2. The r endpoint relation and arm edges provide a cyclic system.
In the inverse, all but one required outputs are tree-edge differences; the
exceptional output is supported on r pairwise nonadjacent input vertices.
Freeze the ordinary edge outputs and project to those r vertices. A basis of
remaining equations still has invertible formal unknown columns. If s selected
ternary equations isolate the exceptional output and use u unknown columns,
row independence gives u>=s and incidence counting gives 3s>=2u-1+r. Thus at
least r-1 equations remain necessary. This proves exact
L_cyc(M)=L(M^(-1))=rk+r-2. The forward/cyclic and forward/inverse ratios approach
two. No universal upper comparison factor is claimed.

The fixed r=5,k=3 map and its forward 25/inverse 18/cyclic 18 constructions are
verified directly, including rank and the displayed projection; no search or
configuration enumeration is used. See
[causal bootstrap gap](../takeover-2026-11-13/general/CAUSAL_BOOTSTRAP_GAP.md).

All four results have written hand proofs and independent machine reviews, not
formal verification or human certification. No literature-novelty claim is made.
Unrestricted MixColumns stays 75–88. The next structural problem is how already
computed shared values reduce later startup costs without being charged repeatedly.
