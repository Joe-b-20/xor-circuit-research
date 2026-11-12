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
gates, with or without such a gate. That is all this establishes: these particular circuits gain
nothing from their double service; it does not show that double service cannot gain.

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
of the even space, has at least 11 gates). Not used anywhere.

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
n^3 / (2 log n). Sources read by the investigator: notes of Jukna crediting Sergeev (web page), Paul 1976
(scan, partly illegible), Find et al. (arXiv, read). No explicit or small example is known; by the
investigator's own computation the counting argument starts to certify a failure only near n = 2^37.
Additivity is known for depth-2 XOR circuits, SUM/OR circuits, monotone circuits and cancellation-free
XOR circuits. So "sharing between unrelated parts never helps" is false as a general principle, and any
compensation theorem must use properties of the parts.

**Proved by the investigator (every circuit; unreviewed).**
- Count: classify each gate by whether its X-part and its Y-part are new. G = N_X + N_Y - d + w, with d
  the gates new on both sides and w those new on neither, and N_X >= L(A), N_Y >= L(B). What is counted:
  new values on each side. Where sharing reduces the count: a gate new on both sides. What compensates:
  gates new on neither side, which are forced at the first mixing of the two sides and at every
  separation that uses a pure signal of the other side.
- Span lemma: the mixed signals carry at most r independent Y-parts, one per mixed gate that is not new
  on the X side, and then d <= 2^r - r - 1.
- Theorem: the saving is at most h_B - ceil(log2(h_B + 2)), h_B = L(B) - (number of distinct rows of
  weight >= 2). Hence additivity whenever one part has h <= 3, in particular whenever one part has at
  most 4 inputs. Any counterexample needs both parts with h >= 4, at least 5 inputs and joint size >= 13.
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
- **Proved given the joint local lemma (unreviewed): the charge theorem has an order-free twin.** For
  every cyclic system of the rotation model or of MixColumns, every basis T of triples and every family
  J of pairwise non-adjacent sheets, at least 10|J| members of T occur (with odd multiplicity) in the
  derivation of an output of J and have two members nonzero on the blocks of J. The joint local lemma
  itself (section 11, Theorem 11.1) was re-derived independently in a form valid for non-executable
  local systems. Consequently: the premises of the charge framework hold for all cyclic systems, so that
  framework cannot prove more than the cyclic minimum (a statement about these premises). And applying
  the charge count to every initial segment of a circuit adds nothing, because each such inequality is
  indexed by a set of outputs and has an order-free twin.
  *Correction:* in an earlier report I called the charge theorem "genuinely causal" because it uses
  ancestors. It is not: derivation-membership replaces ancestry. The 83 argument was not examined for a
  twin.
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

**State of the causal question.** Nothing proved so far in this study needs the gate order: the 75
argument (audited), the charge theorem and the family theorem all have order-free forms. The only
places where order is used and not yet shown removable are the last step of L(M2) = 26 (for partitions
other than the natural one) and the 83 argument (not examined). Whether order can yield a bound that
fails for cyclic systems of MixColumns-like maps is open.
