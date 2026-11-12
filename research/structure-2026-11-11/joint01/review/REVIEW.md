# Independent machine review of joint01/REPORT.md

Review of 2026-11-12 by a second model instance (Opus) that did not write the report; saved by the main
agent from the reviewer's final message. A machine review, not a human review and not a formal
verification. No search; checks are in rv1.py (rebuilds the MixColumns matrix from GF(2^8) arithmetic,
verifies the mirror columns, and checks the 32 configurations reached in the p = 3 case).

**Verdicts.** Theorem A (L >= 11): stands, with small repairs to the wording. Theorem B (at least 21
under the hypothesis): stands, with implicit steps to be written out. Section 6: the list of residual
configurations is incomplete; the three missing ones are excluded by an existing lemma. Sections 1 and
2: correct.

**1. Mirror form: CORRECT.** Sheet 0 is E_c on block 0 plus s_c on block 7; sheet 1 is E_c on block 1
plus s_c on block 0 plus s_c on block 7. Mirror columns: b_k -> (E_k | p_k), b'_k -> (0 | E_k),
a_k -> (p_k | p_k); the exports must span the diagonal. With |B| = r = 8 the duality lemma gives
K = |T| + tau. mirror_j01.py reproduces K = 22, tau = 4, (f, D, N_0) = (7, 4, 7).

**2. K >= 20: CORRECT.** pair/PROOF uses the exports only in (I), in tau >= 3, and in "K = 19 forces
tau = 3, f >= 7". For (I): the projections of the exports to first parts span Even(w); the r = 1 bound
applies unchanged. tau >= 3 because the diagonal has dimension 3.

**3. Theorem A: CORRECT WITH SMALL GAPS.**
- Reduction, to be written out: the ten-gate lemma applies to the ancestors of the A_i, so in a 10-gate
  S every gate is such an ancestor, none has omega = 0, none has two free operands. The seven fibres
  E_i, v_m are distinct and non-unit (weights 3 against 2 or 4; the v_m independent), so f >= 7; entries
  are duplicates and tau >= 3, so 10 = 7 + 3 and there is no other duplicate. Three labels spanning the
  even space are a basis; no label is shared. A target can be an entry but never on another target (one
  target per fibre); this needs only the fibre count, not N.
- N, F2, F3: confirmed for all 28 bases; the two counting steps are valid (a service g = beta + n is a
  representation of beta; three required aux sums would add to zero against independence).
- p = 2: complete. Simpler finish: if beta = w_a + X(pi), that sum is beta's unique F3 representation
  and it is already used, since X(pi) is older than beta; so beta has no service.
- p = 3: complete, with two unstated sub-cases (X_1 + w_k with k in v_1 gives (unit | v_1), a duplicate
  that is not an entry; beta_1 + A_i with i not in v_1 lands in a unit fibre), both excluded by "D = 3,
  all entries". The case beta_2 = X_1 + w_k also closes by the F3 argument above.

**4. Theorem B: CORRECT WITH GAPS (steps to add).**
- |D_1| >= 10: restrict to blocks 7, 0, 1 and treat everything on b and a as free; the ten-gate proof
  works with an 8-dimensional free part.
- |C_0| >= 10 and disjointness: every gate of C_0 is zero on b' by hypothesis, so C_0 is a ten-gate
  local circuit and cannot meet D_1.
- |D_1| = 10: the split is (7, 3) or (6, 4); with (6, 4) the traces span F_2^4, so in both cases the
  rows l_c span the domain of Phi and image(Phi) = span of (s_c | s_c), the diagonal (step omitted in
  the report). With tau = 4 the four operands carry one relation; three are still independent. A
  nonzero diagonal vector is never an input, so these operands are gates zero on b', not in D_1.
- |C_0| >= L needs the index reversal c -> -c on both blocks (it maps (E_c | s_c) to A_(-c) and (e | e)
  to a diagonal vector).
- Block-monotone: sheet 0's outputs are zero on block 1, so their ancestors in a block-monotone
  MixColumns circuit are too; the hypothesis holds after restriction to blocks 7, 0, 1.

**5. Section 6: INCOMPLETE LIST, repairable.** Constraints: K = 20, tau >= 3, f + tau >= 10, f >= 7 when
tau = 3, f + D >= 10, D >= 4, N_0 >= 4, Lemma B. The two stated exclusions are right. Missing:
(3,9,4,4), (4,8,4,4), (5,7,4,4): in all three D = t = 4 and N_0 = 4, excluded by Lemma 3.2 of
sharing/REPORT (which uses neither f nor the exports). (4,6,4,6) and (4,7,4,5) are excluded by Lemma B.
(3,8,5,4), (3,7,6,4), (4,6,6,4) remain only in their four-entry sub-case (five entries is (X)).

**6. Section 8: overstatements.** The exports need only span a space containing the diagonal (the
recorded circuit has non-diagonal exports), and likewise in the pair problem; F3 limits services with a
named partner only (aux + aux sums are counted separately); "three aux cannot carry seven targets,
hence the eleventh gate" is shown only inside a 10-gate S, i.e. for L, not for the whole count; 22 is
not proved optimal ("the known 22-gate circuits"); "includes block-monotone circuits" holds after
restricting a MixColumns circuit to blocks 7, 0, 1.
