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

What these classical tools give for MixColumns, and why they stop. I checked the proof of P1 myself; the
rest is as reported.

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

## 6. Cyclic systems: what the published framework actually bounds (cyclic/REPORT.md)

Delegated. I re-ran three of its scripts and checked Example 1, Theorem C(i) and Theorem W by hand. The
audit (its section 3) is under independent machine review; until that is in, everything resting on it
is conditional.

**Definition.** A *cyclic system* for M is a set S of distinct nonzero vectors containing the unit
vectors and the rows of M whose linear relations are all generated by its collinear triples. Its size
is |S| - n; L_cyc(M) is the least size. Every circuit is one (the gate equations), so L_cyc <= L. A
cyclic system is a circuit exactly when its equations can be solved one at a time.

- **Proved: L_cyc < L happens.** Smallest example (n = 5, six rows 11100, 11110, 11111, 01111, 00111,
  11011): the six triples {e4, 11100, 11110}, {e5, 11110, 11111}, {e1, 11111, 01111}, {e2, 01111, 00111},
  {e3, 11111, 11011}, {11100, 00111, 11011} generate all relations, no triple contains two inputs, so
  nothing can be computed first: L_cyc = 6, L = 7. Examples exist for invertible matrices with all rows
  and columns odd and minimum relation weight 4 (n = 7: L_cyc = 10 < 11 = L). No example with n <= 4 or
  L_cyc <= 5 exists (proved).
- **Proved: L_cyc does not see which boundary vectors are the inputs.** It is the same for a matrix,
  its inverse, its transpose (up to m - n) and every other choice of information set. A circuit for A,
  read from its outputs, is a cyclic system for the inverse of A. So L(A) and L(A^-1) can differ only
  through causality.
- **Proved (Theorem W): what separates the two.** A based cyclic system is a circuit iff every
  nonempty set of its equations contains a non-input signal occurring in exactly one of them (the *leaf
  property*); cyclicity only gives a signal occurring an odd number of times. Equivalently a circuit
  stays uniquely solvable under arbitrary nonzero coefficients over a field with at least three
  elements. Arguments that use the gate equations only through linear algebra over F_2 (independence,
  rank, parity, counting) are arguments about cyclic systems.
- **Conditional (audit, one machine pass, review pending):** no lemma of PROOF uses the gate order
  essentially; ten are written with it and each has an order-free proof. If so, PROOF shows
  L_cyc(MixColumns) >= 75, and therefore L(InvMixColumns) >= 75 and the same for every systematic form
  of the same [64,32] code. It also means that this kind of argument can never prove more than
  L_cyc(MixColumns), which is at most 88 and not known to equal L(MixColumns).
- **Observed:** the recorded 88-gate MixColumns circuit read from its outputs is not a circuit for the
  inverse (only 44 of 120 masks are reachable), while the recorded 88-gate inverse circuit read from
  its outputs is a circuit for MixColumns.
- **Open:** whether L_cyc(MixColumns) = L(MixColumns); whether L <= C L_cyc in general (every observed
  gap is 1; only L <= L_cyc^2 is proved).
