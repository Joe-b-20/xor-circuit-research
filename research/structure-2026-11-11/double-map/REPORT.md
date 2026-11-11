# Double maps D_T and their second-level cost eps(T)

Report of the delegated investigation of 2026-11-11, saved by the main agent from the investigator's
final message. Produced with large-language-model assistance; checked only by the programs in this
directory. No human or formal verification, and no second machine review yet. Status words: **proved**,
**conditional**, **conjectured**, **observed**, **disproved**. "PROOF x.y" refers to
`lower-bound-proofs/mixcolumns-lb75/PROOF.md`.

## 0. Results at a glance

| # | Statement | Status |
|---|---|---|
| A | Reduced T: every valid partition has at most m blocks, so x >= m and L(D_T) >= 3m. A zero column gives m+1 blocks. | proved |
| S | Any circuit, any partition: x + y >= (4m + h) - c - rho_4(B u H). | proved |
| B | Circuits without helpers: x >= 2m - c, y >= delta(T); refinement y >= delta_i + ceil(log2 i) - 1; identity x + y = 2m - c + delta + nu + n_0. | proved |
| E | Any circuit: N >= m + delta + (m - c) + sum_H (1 - d_H) + z + q'. | proved |
| F | Pair-partition circuits: eps >= min(delta, 2). | proved |
| C | L(D_T) = 3m iff delta(T) = 0 iff T is a direct sum of arc blocks. | proved |
| D | L(M2) = 26. | proved, computer-assisted (two finite checks); 8-block case also confirmed by exhaustive search |
| G | eps(T) >= max(delta(T), delta(T^T)) for every reduced T. | conjectured; observed for m <= 4 (70 classes determined, 2 lower-bounded), M2, three 5x5 instances |
| X1 | "An optimal circuit with the pair partition always exists." | disproved |
| X2 | "delta(T) = delta(T^T)." | disproved |
| X3 | "eps = max(delta, delta^T)." | disproved (three 4x4 classes with +1) |
| X4 | "Every helper raises rho_4 by at most 2." | disproved (M2: four masks raise it by 3) |

## 1. Setting

**The map.** w = u + v; D_T(u, v) = (u + Tw, v + Tw). Outputs o_j = u_j + t_j, o'_j = v_j + t_j, with
t_j = sum of w_k over k in S_j, S_j = support of row j, w_k = u_k + v_k. W = span(w_k), dimension m.

**Exact symmetries of the gate count.** (1) Zero diagonal: if T_jj = 1 then u_j + t_j = v_j + (t_j + w_j),
so changing T_jj swaps o_j and o'_j; from now on j is not in S_j. (2) Simultaneous permutation of
indices. (3) Transposition: (D_T)^T = D_(T^T), and L is transposition invariant (PROOF 3.1). (4) Swap
u_j and v_j for any set of j.

**Reduced T.** Zero diagonal, no zero row, no zero column. Then the 2m outputs are distinct, odd, and
none is an input.

**Circuit quantities.** x = odd+odd gates (producers), y = even+even gates (adders), h = helpers,
N = x + y + h, eps := L(D_T) - 3m. The odd graph (PROOF section 4) has a producer edge between the
operands of a producer and a tree edge between an odd gate and its odd operand, labelled by the even
signal of the gate.

**Sheets and lines.** Sheet k is the affine plane {u_k, v_k, o_k, o'_k} = u_k + U_k, U_k = <w_k, t_k>.
Its line is L_k = {w_k, a_k, b_k}, a_k := t_k, b_k := t_k + w_k. D := union of the lines. B := the 4m
boundary points.

## 2. Lemma A: the baseline 3m

**Lemma A (proved).** Let T have zero diagonal. A valid partition of the 2m inputs with more than m
blocks forces a zero column of T. Conversely a zero column k makes "all pairs, with u_k and v_k
separated" valid with m+1 blocks.

*Reason.* A split pair behaves like an edge between blocks. More blocks than pairs forces a tree of
blocks made only of split pairs; tree edges are linearly independent, leaving no room for any row to
involve those pairs.

*Proof.* For pair k let d_k be the vector over blocks: 0 if the pair is unsplit, 1_{B(u_k)} + 1_{B(v_k)}
if split. The parity vectors of o_j, o'_j over the blocks are 1_{B(u_j)} + D_j and 1_{B(v_j)} + D_j,
D_j = sum of d_k over k in S_j; validity says both have weight 1. Let Z be the split pairs and c > m. At
most m - |Z| blocks contain an unsplit pair, so more than |Z| blocks are "split-only", each of degree
>= 1 in the multigraph (blocks, split pairs). Some component K is then a tree with only split-only
vertices and at least one edge. Its d_k are independent and supported on V_K; all other d_k vanish on
V_K. Restrict the parity vectors to V_K. If j is not in Z_K the restriction is the sum of d_k over
k in S_j and Z_K: even weight and at most 1, hence 0, hence S_j avoids Z_K. If j is in Z_K the two
restrictions 1_{B(u_j)} + R and 1_{B(v_j)} + R have weight 1 and sum d_j, so R = 0 or R = d_j; R = d_j
is impossible since j is not in S_j. So the columns Z_K are zero. QED

**Consequence.** Reduced T: c <= m, x >= 2m - c >= m, L >= 3m. Valid m-block partitions other than the
pair partition are common: M2 has 171 valid 8-block partitions and 4786 with 7 blocks.

## 3. The relation code K and the defect delta

**Lemma R (proved).** A zero-sum 4-subset of B is either a sheet (the sheet relation rho_k) or a pair on
sheet j plus a pair on sheet k != j with the same difference d in U_j and U_k (a coincidence relation).
Every zero-sum subset of B meets every sheet evenly. (Modulo W every point of sheet k is u_k, and the
u_k are independent modulo W.)

**The code.** R := zero-sum subsets of B, dim R = 2m. On sheet k, even subsets modulo rho_k are
identified with U_k by mask sum. So R / <rho_0..rho_(m-1)> = K := { (d_k)_k : d_k in U_k, sum d_k = 0 },
dim K = m. Weight of a word = number of nonzero d_k; K_i := span of words of weight <= i. Row j gives
the word (t_j at j; w_k at each k in S_j) of weight 1 + |S_j|.

**Definitions.** rho_4(X) := dimension of the span of the zero-sum 4-subsets of X.
delta(T) := 2m - rho_4(B) = dim K/K_2. delta_i(T) := dim K/K_i.

**Formula (proved).** delta(T) = |D| - 2m + s, with s the number of pairs {j,k} with t_j = w_k and
t_k = w_j.

*Plain words.* Each sheet brings three difference vectors; two per sheet are free (one produced there,
one imported). delta counts the vectors no other sheet shares. For M2:

    L_0: w0, w7, w0+w7        L_1: w1, w0+w7, w0+w1+w7   L_2: w2, w1, w1+w2    L_3: w3, w2+w7, w2+w3+w7
    L_4: w4, w3+w7, w3+w4+w7  L_5: w5, w4, w4+w5          L_6: w6, w5, w5+w6    L_7: w7, w6, w6+w7

Six coincidences (w7, w0+w7, w1, w4, w5, w6): |D| = 18, delta = 2, rho_4(B) = 14 (`geom.py m2`).

## 4. Lower bounds for all circuits

### 4.1 Spanning inequality

**Lemma S (proved).** For a normalized circuit of D_T (T reduced) with helper set H and a final partition
of c blocks:  x + y >= (4m + h) - c - rho_4(B u H).

*Reason.* The odd graph connects each block. Two edges with one label form a parallelogram, i.e. a
zero-sum 4-set. Modulo parallelograms there are only as many edge classes as labels, but edges span a
space of dimension (points - blocks).

*Proof.* (i) The odd graph is simple and same-label edges are disjoint (PROOF 4.1). (ii) It has exactly
c components. (iii) Let F_0 = span of pair(e) = [P] + [P'] over edges; dim F_0 = 4m + h - c. For
same-label edges, pair(e) + pair(e') is a zero-sum 4-subset. So F_0 modulo the 4-subset span is spanned
by one class per label that labels an edge (at most x + y), and has dimension
>= dim F_0 - rho_4(B u H). QED

No time order and no assumption on partition, x or cancellation is used. The proof holds for any target
set: x + y >= |B u H| - c - rho_4(B u H).

### 4.2 Circuits without helpers

**Theorem B (proved).** Let C be a normalized helper-free circuit of D_T (T reduced).
(a) x >= 2m - c >= m and y >= delta(T); so C has at least 3m + (m - c) + delta(T) gates.
(b) For every i >= 2 with delta_i >= 1: y >= delta_i + ceil(log2 i) - 1.
(c) x + y = (2m - c) + delta + nu + n_0, where n_0 = even signals labelling no edge and nu = dimension
of the linear relations among the canonical classes of the labels in F_0 / span(4-subsets of B).

*Reason.* Without helpers every output is boundary point + label. A label that is a boundary difference
makes the output's relation a parallelogram. Only adders give other relations, one per adder, and delta
are missing.

*Proof.* Expand every even signal into producers: pi(L) = [L] for a producer, pi(L') + pi(L'') for an
adder; s(L) = weight of pi(L); xi(L) = sum of the operand pairs of the producers in pi(L). For an output
O = b + L let r_O = [O] + [b] + xi(L). Eliminating the even signals from the gate equations leaves the
r_O, so they form a basis of R. The image of r_O in K has weight <= s(L) + 1. Two outputs with the same
label differ by a zero-sum 4-set, in K_2. So K/K_i is spanned by one class per label with s(L) >= i: at
least delta_i adders have s >= i. With i = 2 this is (a). (b) Let L_1 be the earliest adder with s >= i;
one summand has s >= ceil(i/2) and, being earlier, s < i; repeat. (c) The map label -> class of the pair
of any of its edges is well defined and onto; dim F_0 = 4m - c, and the 4-sets span dimension
2m - delta inside F_0. QED

### 4.3 Circuits with helpers

**Proposition E (proved).** Let d_H = number of gates using helper H, z = edges joining two helpers,
q' = labels that label an edge but no boundary-boundary edge. Then

    N >= m + delta(T) + (m - c) + sum_H (1 - d_H) + z + q'.

Static form: N >= 3m - c + 2h - rho_4(B u H).

**Corollary F (proved).**
1. If every helper is used by exactly one gate, eps >= delta. Each further use weakens the bound by one.
2. eps >= min(delta, 1). If delta >= 2, a circuit with eps = 1 has x = m, y = 0, one helper H, c = m,
   d_H >= 2, and rho_4(B u {H}) >= rho_4(B) + 3.
3. Pair-partition circuits satisfy eps >= min(delta, 2).

*Proof of 3.* Suppose delta >= 2 and N = m + 1. Then x = m, y = 0, h = 1 and the m labels are
independent. By E, H has at least three neighbours; they are boundary points of H's own sheet, with
labels H + P. Four neighbours: the labels sum to 0. Three neighbours P_0, P_1, P_2: the fourth point P_3
has an edge to one of them, say P_0, with label P_3 + P_0 = (H + P_1) + (H + P_2). Either way the labels
are dependent. QED

## 5. Theorem C: which T have eps = 0

**Arc blocks.** Let pi be a cyclic permutation of a set J (|J| >= 2) and Rt a nonempty set of roots in J.
Let A(i) = {i, pi(i), pi^2(i), ..., first root reached}. The arc block has rows S_j = A(pi(j)) \ {j}.
With Rt = J it is the permutation matrix of pi.

**Theorem C (proved).** For reduced T, equivalent: (a) L(D_T) = 3m; (b) delta(T) = 0; (c) T is, after
simultaneous permutation, a direct sum of arc blocks.

*Reason.* delta = 0 forces the lines into cycles: each line has exactly one private point, every shared
point lies on exactly two lines. Around a cycle each sheet imports one shared vector and exports the
other. A sheet that exports its own w needs nothing first; any other sheet must be entered before it can
export. The cycle can be scheduled in time exactly when all sheets exporting their own w point the same
way, and the algebra forces that.

*Proof.*
(c) => (a). For a root j make lambda_j = w_j. Going round the cycle against pi from a root, sheet j
imports l_j = lambda_pi(j), makes u_j + l_j and v_j + l_j, and if j is not a root makes
lambda_j = l_j + w_j as one producer. m producers, 2m outputs.
(a) => (b). A 3m-gate circuit has x = m, y = h = 0; Theorem B(a).
(b) => (c). Assume delta = 0, so the evaluation map from the space U~ (one generator per element of D,
one relation per line) to W is an isomorphism.
*Step 1, components.* Split the lines into components of the point-line incidence graph. Each component
J has S_k inside J for k in J, and (points) - (rank of lines) = |J|.
*Step 2, at most one leaf per line.* A leaf is a point on exactly one line. In F_2^D the vector
1_{a_j} + sum over i in S_j of 1_{w_i} lies in the span of the lines. Three leaves: a one-line component
has 3 - 1 = 2 != 1. Leaves a_k, b_k: |S_k| >= 2, the vector for j = k uses L_k, so b_k has coefficient 1,
but b_k is not in the vector. Leaves w_k and zeta in {a_k, b_k}: column k is nonzero, so k is in some S_j
with |S_j| >= 2; the vector for j uses L_k, so zeta = a_j (then on L_j) or zeta = w_i (then on L_i).
*Step 3, counting.* With m' lines, s' 2-cycles and n_i points on exactly i lines: sum n_i = 2m' - s',
sum i n_i = 3m', so sum over i >= 2 of (i - 2) n_i = n_1 - m' + 2s'. Lines of a 2-cycle have no leaf, so
n_1 <= m' - 2s'; equality throughout. Every shared point is on exactly two lines, every other line has
exactly one leaf, and a 2-cycle is a whole component. Otherwise "sharing a point" is a 2-regular
connected simple graph: a cycle k_1..k_r, r >= 3, with d_i in L_{k_i} and L_{k_{i+1}}.
*Step 4, orientation (the causal step).* The leaf of L_{k_i} is d_{i-1} + d_i. Call the line type W if
its leaf is w, type A/B otherwise. The leaves sum to 0 round the cycle and the w's are independent, so
not all lines are type W. An A/B line k shares w_k with a neighbour i with a_i = w_k; say k points to i.
Claim: all A/B lines point the same way. Otherwise k_p points to k_{p+1} and k_q points to k_{q-1},
q > p, with only W lines between. Then d_p = w_{k_p} and each W line adds its own w, so d_{q-1} has
weight q - p; it must equal w_{k_q}, which forces q - p = 1 and w_{k_p} = w_{k_q}. Contradiction.
Orient so A/B lines point forward, set pi(k_{i+1}) = k_i, roots = A/B lines. Then d_i has support A(k_i)
and S_{k_{i+1}} = A(k_i) \ {k_{i+1}}. QED

**Consequences.** eps >= 1 exactly when T is not a sum of arc blocks. Arc matrices are rare: 14 of 18
reduced matrices for m = 3, 93 of 1699 for m = 4, 884 of 592,260 for m = 5 (`delta_vs_forest.py`, which
re-checks (b) <=> (c) by brute force for m <= 5). M2 is the arc block of the cycle j -> j-1 with roots
1..7 plus two extra entries (w7 in rows 3 and 4); delta = 2.

## 6. Theorem D: L(M2) = 26

M2 = D_T, m = 8, S_0 = {7}, S_1 = {0,7}, S_2 = {1}, S_3 = {2,7}, S_4 = {3,7}, S_5 = {4}, S_6 = {5},
S_7 = {6}. A 26-gate circuit is verified by `../tools/m2_check.py`.

**Theorem D.** Every circuit for M2 has at least 26 gates.

*Proof.* Suppose N <= 9.
1. Lemma A: c <= 8, x >= 8, so y + h <= 1.
2. Fact F1: rho_4(B) = 14, delta = 2. If h = 0, Theorem B gives x + y >= 10. So h = 1, y = 0, x = 8,
   c = 8.
3. Lemma S: rho_4(B u {H}) >= 17 = rho_4(B) + 3. Fact F2 (`m2_proof.py`, all 32,736 odd masks outside
   B): the increase is 0 for 29,992 masks, 1 for 2,548, 2 for 192, 3 for exactly four: u3+w7, v3+w7,
   u3+w2, v3+w2. By the symmetry u3 <-> v3, H = u3+w7 or u3+w2.
4. Residual case. Since y = 0, every label is a difference of two earlier points. So for every odd gate
   O with tree edge (O, P) and label Q_1 + Q_2:
   **(P)** {O, P, Q_1, Q_2} is a zero-sum 4-subset of B u {H} with P, Q_1, Q_2 created before O; tree
   edges and the producer edge of one label are pairwise disjoint pairs with the same difference.
   The 4-subsets are those of B plus {H} u (boundary triple with sum H); `m2_residual_facts.py` prints
   the lists. Let O_k be the first-created output of sheet k and l_k its label.

   *Case H = u3+w7.* Triples: {u3,u7,v7}, {u3,o7,o'7}, {u3,u0,o0}, {u3,v0,o'0}, {v3,u4,o4}, {v3,v4,o'4},
   {o3,u2,v2}, {o3,o2,o'2}.
   - The only 4-subset containing o'3 is rho_3. So o'3 comes after o3, and its label L' has difference
     w3, w2+w7 or w2+w3+w7, each carried by exactly two pairs, both in sheet 3.
   - The l_k are pairwise distinct. If l_j = l_k, three disjoint pairs share the difference: two tree
     edges and the producer pair, which precedes both. Differences with three disjoint pairs: w1, w2,
     w4, w5, w6, w7, w0+w7, w3+w7. For each, the pairs usable as a first-output tree edge lie on one
     sheet. The exception is w0+w7 with pairs (u0,o'0), (v0,o0), (u1,o1), (v1,o'1): a tree edge on each
     of sheets 0 and 1 leaves as producer only a pair containing a second output, which does not
     precede the first.
   - L' is none of the l_k (only two pairs).
   So at least 9 labels, but x + y = 8.

   *Case H = u3+w2.* Triples: {u3,u2,v2}, {u3,o2,o'2}, {o3,u7,v7}, {o3,o7,o'7}, {o3,u0,o0}, {o3,v0,o'0},
   {o'3,u4,o4}, {o'3,v4,o'4}.
   - The only 4-subset with o4 and not o'4 is {H,o'3,o4,u4}, symmetrically for o'4: the first output of
     sheet 4 comes after o'3.
   - The 4-subsets containing o'3 are rho_3 and two containing a sheet-4 output. So o'3 is made through
     rho_3, after o3, with a label L' as before.
   - Every 4-subset containing o3 other than rho_3 contains H, so H precedes o3. H's own 4-subset is
     then {H,u3,u2,v2} or {H,u3,o2,o'2}, and its label L_H has difference w2 or H + c with c on sheet 2.
   - Same difference list: the only one with first-output tree edges on two sheets is w7 (sheet 0, and
     (o3,H)). w2 has no pair with exactly one output; H + c has fewer than three pairs.
   So at least 7 distinct l_k, plus L' and L_H: at least 9. QED

**Computer-assisted parts.** F1 (also by hand from the six coincidences) and F2. The lists in step 4 can
be checked by hand from the lines.

**Independent checks (not a replacement for the argument).** `m2_exhaustive.sh R`: all circuits with 8
independent even signals and one helper among the four masks: none (1,325,676 nodes). `m2_exhaustive.sh
A`: all circuits with at most 25 gates whose final partition has 8 blocks: none (49,559,814 nodes, 139
CPU-s); it uses Lemma A, the partition lemma and the 171 valid 8-block partitions as pruning rules, not
Lemma S, Theorem B or F2. The 7-block case (nine independent producers) rests on Theorem B only; its
exhaustive search was stopped early. `m2_residual_sat.py` gave no answer in 420 s.

## 7. Ground truth, conjecture, counterexamples

### 7.1 Exact values

`exh.c` decides by exhaustive search whether D_T has a circuit with N non-output gates; pruning uses only
Lemma A and the partition lemma. Tables: `table_m3.txt`, `table_m4.txt`, `table_m5.txt`. Classes are up
to simultaneous permutation and transposition.

m = 3, all 5 reduced classes: 1|2|0, 1|2|01, 1|02|01 (delta 0, arc, L = 9); 1|02|1 and 12|02|01
(delta 1, L = 10).

m = 4, all 67 reduced classes:

| delta (listed representative) | eps | classes |
|---|---|---|
| 0 | 0 | 6 |
| 1 | 1 | 25 |
| 1 | 2 | 5 |
| 2 | 2 | 24 |
| 2 | 3 | 1 |
| 3 | 3 | 4 |
| 4 | >= 4 (no circuit with 15 gates) | 2 |

The six classes with eps > delta(representative):

| T | rank | delta | delta(T^T) | delta_3 | eps | explanation |
|---|---|---|---|---|---|---|
| 1\|2\|03\|12 | 3 | 1 | 2 | 0 | 2 | transpose |
| 1\|2\|013\|12 | 3 | 1 | 2 | 0 | 2 | transpose |
| 1\|023\|03\|012 | 4 | 1 | 2 | 0 | 2 | transpose |
| 1\|023\|1\|1 | 2 | 1 | 1 | 1 | 2 | weight: Theorem B(b) gives y >= 2 helper-free |
| 123\|023\|013\|012 (J - I) | 4 | 1 | 1 | 1 | 2 | weight, same |
| 12\|23\|013\|012 | 3 | 2 | 2 | 0 | 3 | neither; by B(c) every helper-free optimum has (m - c) + nu + n_0 = 1 |

m = 5, ten instances searched up to eps = 1 (`list_m5.txt`): three arc matrices, eps = 0; four matrices
with delta = 1 (among them multiplication by x mod x^5+x^2+1), eps = 1; three with delta >= 2 have no
circuit with 16 gates.

SAT cross-checks independent of `exh.c`: all 13 classes for m = 3; six m = 4 classes (`xcheck_sat.txt`).
All agree. The first version of `exh.c` contained an expression with unspecified evaluation order; it was
fixed and all tables regenerated; the eps values did not change.

### 7.2 What the tables say

- **Observed:** eps >= max(delta(T), delta(T^T)) in all 70 classes with m <= 4 whose eps was determined;
  equality in 67, +1 in three.
- **Observed:** every determined class has a helper-free optimum.
- **X1, disproved.** For T = 12|03|013|012: L = 13, pair-partition optimum 14 (exhaustive search and
  SAT). Optimal circuits use blocks {u0,u3} | {u1,u2} | {v0,v3} | {v1,v2}.
- **X2, disproved.** delta(T) != delta(T^T) for 144 of the 1699 reduced 4x4 matrices. Since L is
  transposition invariant, the bound must use the maximum.

### 7.3 Conjecture G and the obstacle

**Conjecture G.** For every reduced T and every circuit, N >= m + delta(T); hence
eps(T) >= max(delta(T), delta(T^T)).

Proved cases: helper-free circuits (B); every helper used once (F.1); eps <= 1 in the pair partition
(F.3); eps <= 1 when no mask raises rho_4 by 3 (F.2); M2 (D).

**The obstacle.** By Proposition E each use of a helper beyond the first could save one gate. In every
configuration analysed the saving is cancelled by a linear dependency among labels: the labels at H
towards boundary points P_i of one sheet satisfy L_i + L_j = P_i + P_j, a vector of that sheet's line,
while x = dim E leaves no room for dependent labels. Two things block a general proof: (1) the
dependency lives in mask space and the saving in relation space modulo parallelograms; the two are tied
only through time order, which was made precise for one helper only; (2) in other partitions a helper
has neighbours on other sheets through labels outside W.

**No exact formula.** eps contains a shortest-linear-program problem (heavy rows, B(b)) and a scheduling
problem (which sheet exports which vector, B(c)). The two-sided statement is
max(delta(T), delta(T^T)) <= (conjectured) eps(T) <= eps_hf(T) = min over helper-free circuits of
(m - c) + delta + nu + n_0, with eps = eps_hf in all 70 determined classes (observed).

## 8. The four-byte map (full MixColumns)

**What carries over.** Lemma S holds for any boundary. For MixColumns |B| = 64, c <= 8 (PROOF F1),
rho_4(B) = 0 (PROOF F2), so

    G >= 88 + 2h - rho_4(B u H)    and    G >= 88 + sum_H (1 - d_H) + z + q'.

Without helpers this is 88. The analogue of delta is dim R/R_4 = 32, the whole relation space;
"G = 32 + 24 + 32" is the equality case. An 87-gate circuit needs rho_4(B u H) >= 2h + 1 and a helper
used by at least two gates. Theorem B(b) carries over: for orientation M, rho_6 = 20, so in a
helper-free circuit at least 12 output relations need labels built from three or more producers.

**What fails.** (1) Smallness: Theorem D works because eps - 1 leaves room for one helper and no adder.
(2) Planes: a double-map sheet has 4 points and one relation, which turns fan-out of a helper into a
dependency among labels; a MixColumns sheet has 8 boundary points and no relation of weight below 6.
(3) Entering labels: in MixColumns no output lies in any boundary parallelogram. (4) Rank tightness: for
MixColumns x = 24 is not forced.

**Analogue of the invariant.** At the first level delta generalises to dim R/R_4(B) with Lemma S and
Theorem B as stated, and "helpers never beat it" is exactly the optimality of 88. It is false for
general matrices: for the three outputs x1+x2+x3 + (x4+x5 | x6+x7 | x8+x9), one helper x1+x2+x3 used
three times gives 8 gates, while helper-free circuits need 10 by Lemma S.

## 9. Files

`dmap.py` (library), `geom.py` (lines, rho_4, delta, arc criterion), `partitions.py`, `exh.c` with
`run_exh.py`, `exh_part.c` with `run_part.sh`, `batch_tables.sh`, `summarize.py`, `show_optimal.py`,
`delta_vs_forest.py`, `transpose_check.py`, `m2_proof.py` (facts F1, F2), `m2_residual_facts.py`,
`m2_exhaustive.sh` (logs `m2_exh_R.txt`, `m2_exh_A.txt`), `m2_residual_sat.py` (no answer),
`sat2.py`, `opt_small.py`, `xcheck_sat.sh`. About 1.3 CPU-hours in total, one core, every run under
`ulimit -v 8000000`.
