# MixColumns sheets 0 and 1 with block 7 free ("J_01"): a test case

Report of the delegated investigation of 2026-11-12, saved by the main agent from the investigator's
final message. Machine work; review status in `../RECORD.md` section 17. No SAT and no search: the
programs evaluate given circuits and check case lists of small parity lemmas. This is a test case for
arguments about shared costs, not a route to the MixColumns bound.

**Corrections from the independent review (`review/REVIEW.md`), to be read with the text.** Theorems A
and B stand. Theorem A: the reduction to "7 first gates plus 3 entries" should be read with the
reviewer's justification, and two sub-cases of p = 3 are excluded by "all duplicates are entries".
Theorem B: four implicit steps are written out in the review (why the entry operands span exactly the
diagonal; the index reversal needed for |C_0| >= L; the free part of dimension 8; disjointness). The
list in section 6 is incomplete: (3,9,4,4), (4,8,4,4), (5,7,4,4) are missing and are excluded by Lemma
3.2 of sharing/REPORT.md; three of the listed configurations remain only with four entries. Section 8
over-states in places: exports need only SPAN a space containing the diagonal; the "three aux cannot
carry seven targets" count is shown only inside a 10-gate sheet circuit; 22 is an upper bound, not a
proved optimum.

**Problem.** Blocks a (free), b, b'. Targets (E_c on b) + (s_c on a) [sheet 0, a = block 7] and
(E_c on b') + (s_c on b) + (s_c on a) [sheet 1, which has the reduction term on block 7]. Known before:
between 20 and 22.

**Outcome.** 20 is not excluded for arbitrary circuits. At least 21 is proved for circuits in which no
ancestor of a sheet-0 target is nonzero on b' (this includes block-monotone circuits). 22 remains the
upper bound; no circuit with 20 or 21 gates was found or designed.

## 1. Mirror form (proved; checked on the recorded circuit)

By the duality lemma with B = b + b', r = 8: K = |T| + tau, T a circuit on w, w' containing
A_i = (E_i | p_i) and B_i = (0 | E_i), p_i = u_(i-1) + u_i, with tau signals spanning a space containing
the DIAGONAL {(e | e) : e even} (the adjoint of the unit a_i is (p_i | p_i)). The pair problem differs
only in its export space, Even(w) + 0. `mirror_j01.py` on the recorded 88-gate circuit: K = 22, tau = 4,
|T| = 18, (f, D, N_0) = (7, 4, 7).

## 2. K >= 20 (proved, given pair/PROOF.md)

That proof uses the exports only through f + tau >= 10 and tau >= 3. Both hold here (the first parts of
the exports span the even space; the diagonal has dimension 3).

## 3. Upper bounds (verified by evaluating given circuits)

A hand-built T with tau = 3 and 19 gates gives 22 with (f, D, N_0) = (7, 5, 7). Let L be the least size
of a sheet-0 circuit (units w, all (0 | s) free) containing A_0..A_3 and three independent diagonal
vectors X_m = (v_m | v_m). That T shows L <= 12.

## 4. Theorem A: L >= 11 (hand proof; replaces the computed fact "SL")

Let S be such a circuit with 10 gates. The seven targets lie in seven distinct non-unit fibres and the
p_i need three independent labels, so S is 7 first gates plus 3 entries; the labels are a basis of the
even space, each read once; no equal values. Call w_i, A_i, X_m *named*, the seven targets *required*,
the other three gates *aux*.
- **N.** No required vector is the sum of two named vectors. So every required gate reads an aux, and a
  required entry sits on an aux of its own fibre.
- **F2.** The seven required vectors are independent, and no two differ by (unit | 0) or (even | 0).
- **F3.** An aux beta has at most one representation beta = required + w_i or required + required, and
  none if beta = (even | 0). So besides an entry in its own fibre, an aux serves at most one required
  gate with a named partner.
(N, F2, F3 are case checks on parities and on which p_i can equal which vector; `check_j01.py` confirms
them for all 28 bases.)
Let p be the number of required entries: p aux first gates, 3 - p aux entries, 7 - p required first
gates, each "aux + named" (at most one per aux) or "aux + aux". By F2 at most two of the three aux sums
are required.
- p <= 1: 7 - p >= 6 > 3 + 2.
- p = 2: 5 = 3 + 2 forces every aux to have a named service. The first gate is then an entry
  gamma = (u_k | pi) on a unit, not a pure pair. Before the next aux beta the only possible gates are
  gamma and X(pi) = gamma + w_i, so beta = w_a + gamma or w_a + X(pi) (any other sum is a pure pair, a
  repeated value or a non-entry duplicate). Then gamma + beta is w_a or (pair | 0), not required; the
  other two aux sums must both be required and differ by it, contradicting F2.
- p = 3: the first gate beta_1 = w_a + w_b is a pure pair v_1 with no named service,
  X_1 = beta_1 + pi_1, and 4 = 2 + 2 is forced. The second aux beta_2 is: a pure pair (no service,
  contradiction); or beta_1 + w_k (then beta_1 + beta_2 = w_k and the two required sums differ by a
  unit, contradicting F2); or X_1 + w_k = (E_l | v_1). In the last case beta_1 + beta_3 and
  beta_2 + beta_3 are required and differ by (u_k | v_1), so they are some A_i and X_m. If
  beta_1 + beta_3 = X_m, beta_3 lies in the fibre v_1 + v_m and the three v are dependent. If
  beta_1 + beta_3 = A_i, then beta_3 = (E_j | p_i) with v_1 = {i, j}, l = i - 1; only w, beta_1, X_1,
  beta_2, A_l exist before beta_3 and no two of them sum to it.
So L is 11 or 12.

## 5. Theorem B: at least 21 when no ancestor of a sheet-0 target is nonzero on b' (hand proof)

Block-monotone circuits satisfy the hypothesis. Let D_1 be the gates nonzero on b' and C_0 the ancestors
of sheet 0: |D_1| >= 10, |C_0| >= 10, disjoint. If |D_1| = 10 its mirror has (7 gates, 3 entries) or
(6, 4); in both cases the traces are independent (with six gates only two even signals exist), so the
entry operands are diagonal vectors s(b) + s(a) spanning the diagonal: three independent gates zero on
b'. Either all three lie in C_0, so |C_0| >= L >= 11, or one is an extra gate. Hence K >= 21.

## 6. General circuits: residual configurations for K = 20 (list derived, not closed)

Running the steps of pair/PROOF with K = 20 and Theorem A: all clean labels even forces
(tau, f, D, N_0) = (3, 7, 3, 7), a 10-gate S: excluded. (4, 7, 5, 4) is excluded by configurations (X)
and (Y) of the pair proof. Remaining: (3,7,4,6), (3,7,5,5), (3,8,4,5), (3,7,6,4), (3,8,5,4), (4,6,5,5),
(4,6,6,4). All have at least four entries, at least two odd labels and N_0 <= 6, so some B_i is an exit
or built from a single even vector.

## 7. What blocks 21 in general, and 22

1. Whether L is 11 or 12 (conjectured 12). L >= 12 would kill (3,7,4,6) and give 22 whenever
   |D_1| = 10 under the hypothesis of section 5.
2. Under that hypothesis, the case |D_1| = 11 with |C_0| = 10.
3. The exit configurations of section 6; the tree arguments of the pair proof were not redone with
   diagonal exports.

## 8. Why the reduction term costs extra (account; follows sections 4-5, not more)

In the pair problem the three exports are pure vectors (v | 0) of the first sheet's mirror: sums of
inputs, by-products of the seven gates that build the E_i (3 + 10 + 7). Here each export must carry the
same even vector on the second group. No export and no A_i is a sum of two inputs or targets (N), so
each needs an auxiliary gate; what is counted is auxiliary gates against the seven required vectors of
the first group. Sharing is possible: one aux (v | p_j) gives A_j by adding a unit and X(v) by adding a
label, used twice in the 22-gate T. The compensation is F3: an aux serves only one required gate beyond
its own fibre, and pure pairs serve none; three aux cannot carry seven targets, hence the eleventh
gate. The known optima pay two: a fourth export and a fourth entry (recorded, 4 + 7 + 4 + 7), or five
entries (3 + 7 + 5 + 7).

## Files

show_j01.py, mirror_j01.py, check_j01.py.
