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

**What it does not give.** Combining several points by linear programming gives nothing beyond the best
single point: with two points x1, x2 the signals fall into four classes, and the inequalities for x1, x2
and x1 + x2 are all satisfied by the same assignment that meets the single-point bound (checked by hand
for MixColumns: the system "N_a + N_b >= 32, N_c + N_0 >= 24, N_a + N_0 >= A, N_b + N_0 >= B" has the
solution N_0 = 0, N_c = 24 whenever A + B <= 32, which always holds). The reason is structural: with a
quotient of dimension k >= 2 there are gates joining two different nonzero classes, and nothing forces
the span of the fully dead signals to be large. Status of this negative remark: proved for the linear
relaxation described, not a statement that no multi-point argument exists.

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

(2.1) is the "ledger" G >= 88 + 2h + p - r of the sprint findings (F20) in exact form. By itself it is a
rewriting. Its use is to say what a saving is: G < 2n + x needs S > 0, and S > 0 can only come from
(i) helpers that are a sum of three boundary points in three ways (r_p = 3; at most 3 by F3),
(ii) two helpers whose difference is a boundary difference that some gate realises, or (iii) a missing
label carried by two or more edges. With x >= 24 for MixColumns: an 87-gate circuit needs S >= x - 23.

**Observed.** Recorded 88-gate circuits for MixColumns and its inverse have x = 24 and S = 0 exactly
(h + y = 32). This is NOT a law: other recorded maps with the same hypotheses have S > 0, e.g.
small-scale AES MixColumns over GF(16) (n = 16, G = 42 = 2n + 12 - 2) and lw16-4x4-gf256-inv-had
(n = 32, G = 84, x = 25, h + y = 27). `tools/survey.py` prints the table. **Disproved:** "h + y >= n
whenever the boundary has no relation of weight <= 4".

## 3. MixColumns in the sheet language (proved; verified on the recorded circuits)

Index the inputs (c, j) = bit j of byte c; block j = {(0,j), (1,j), (2,j), (3,j)}. On a block write
s_c = e_c + e_(c+1) (c mod 4), d_0 = e_0 + e_2, d_1 = e_1 + e_3, t = e_0 + e_1 + e_2 + e_3 and
E_c = t + e_c. Then the MixColumns row for output (c, j) is

    o(c,j) = E_c on block j + s_c on block j-1 (+ s_c on block 7 if j is 1, 3 or 4),   j >= 1,
    o(c,0) = E_c on block 0 + s_c on block 7.                                                     (3.1)

**Proof.** out_c = 2 b_c + 3 b_(c+1) + b_(c+2) + b_(c+3) = (b_(c+1) + b_(c+2) + b_(c+3)) + 2 (b_c + b_(c+1)).
Bit j of the first bracket is E_c on block j. With w = b_c + b_(c+1), bit j of 2w is w_(j-1), plus w_7
when j is 1, 3 or 4, and bit 0 is w_7 (reduction by x^8 + x^4 + x^3 + x + 1); w_k is s_c on block k. QED

**Structure behind it.** MixColumns is multiplication by 2 + 3y + y^2 + y^3 in R = F_256[y]/(y^4 + 1) and
y^4 + 1 = (y + 1)^4, so MixColumns = 1 + (1 + y)(3 + y^2) with 3 + y^2 a unit. The masks that vanish
on (1+y)^(4-k) R form a flag W_1 < W_2 < W_3 of dimensions 8, 16, 24: on each block, W_3 = even weight,
W_2 = {0, d_0, d_1, t}, W_1 = {0, t}. MixColumns is the identity on each quotient W_k / W_(k-1).

**A family.** For an m x m matrix T over F_2 define Q_T on 4m inputs by o(c,j) = E_c on block j plus s_c
on every block k with T[j][k] = 1. MixColumns = Q_T for T = multiplication by x. Restricting the inputs
to (u, v, u, v) gives the two-point "double map" D_T: (u, v) -> (u + T(u+v), v + T(u+v)). For T a cyclic
shift, Q_T is multiplication by a weight-5 element of F_2[C_m x C_4] ("rotation model").

**Observed on the recorded 88@5** (`tools/sheets.py`, `tools/levels.py`): partition = the eight blocks;
24 producers, of which 19 are differences of two inputs and 5 are differences involving a helper;
exactly 2 helpers on every sheet; 16 sums. Extras (helpers + sums) by sheet: 3 on each of sheets 2, 5,
6, 7; 4 on sheet 0; 16 on the three sheets 1, 3, 4 whose rows have the extra block-7 term. The flag is
barely populated: 10 gate signals lie in W_2 (rank 7 of 16), 2 in W_1.
The eight-block partition is not unique: the recorded 89@4 and the recorded inverse 88 have 8 blocks
that are not the bit positions (`tools/m2_check.py`).

**Checked.** M2 = D_T for T = multiplication by x has a 26-gate circuit (16 + 8 + 2), one fewer than the
obvious 27 (`tools/m2_check.py`).

## 4. Ideas that failed, and why

- *Quotient by W_2* (restrict inputs to (u,v,u,v)). Every circuit for MixColumns restricts to a circuit
  for M2 in which at least 16 output gates and at least rank-many dead gates disappear; this yields only
  G >= L(M2) + 32, weaker than 56. Reason: the relations of weight 6 that make MixColumns hard become
  relations of weight 4 in the quotient (the two outputs of a sheet differ by an input difference), so
  the quotient cannot see why labels are hard to reuse.
- *Several evaluation points*: see section 1.
- *"h + y = n is forced"*: disproved in section 2.
- *The rank of the lower flag levels as a cost*: real circuits do not fill W_2 and W_1 (section 3), so no
  bound can come from "the circuit must span the lower levels".
