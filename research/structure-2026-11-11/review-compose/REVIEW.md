# Review of the phase-3 composition claims

Independent machine review, 2026-11-12, separate model instance (Opus, high effort) that wrote none of the
reviewed text; briefed to challenge. Saved by the main agent from its final message, lightly condensed
(arguments kept). Not a human review. `bm_exit_check.py` builds one explicit circuit (a check).

**Verdict.** No counterexample to any main theorem: Proposition 1, Corollary 2, the skip-exit lemma,
Lemma R, Corollary R, Theorem A, Proposition H and the two-pair inequality are correct as proved. Errors are
in descriptive passages; one is false (FRAMEWORK: "block-monotone circuits have no exits").

## Claim 1: compose/FRAMEWORK.md

- **Proposition 1: correct.** (a) A first gate is neither an entry (that keeps its non-pure operand's omega)
  nor an exit, so its operands have different nonzero omega; the fibre-root circuit R is well ordered,
  contains R^j (j < k) and R^k projected to E_i(w^k). Exports with omega = 0 must be dropped (as gap 2a of
  review-chain); the span condition survives. (b) Without exits P is a circuit on w^(k+1)..w^l, every
  label is a signal of P, s-parts lie in the label span by induction, so the labels span
  Even(w^(k+1)) + 0. Optimality is never used: every exit-free T costs at least M_k + M_(l-k).
- **Corollary 2: correct**; "whose review is pending" is stale (review-chain confirms Theorem 1).
- **Reindexing: correct** (relabelling; identification with the primal minimum via the duality lemma).
- **"An exit's value is a sum of labels along a path inside the fibre": wrong in general.** Counterexample
  (pair, first part on w): x = w0 + u1, y = w1 + u2 entries; h = x + y = (w0+w1 | u1+u2) a non-entry
  duplicate in the fibre of r = w0 + w1; the exit r + h = u1 + u2 is a sum of labels from two other fibres.
  Repair: the value lies in the label span and is never 0 or a single label; it is a path sum when every
  duplicate of the fibre is an entry, as in configuration (X).
- **Primal meaning of exits: imprecise; last sentence false.** A mirror gate is a partial sum of the
  adjoints of a signal's readers and depends on the summation order; it is a fan-out branch of v, not in
  general the adjoint of a primal signal. "Block-monotone circuits have none" is false: a valid
  block-monotone primal pair circuit with r1 = x0+x1, r2 = x0+x2, w1 = r1 + r2 (cancels x0 inside block b1,
  allowed) has adj(r1) = {T1_0, T2_0, T2_3}, adj(r2) = {T1_0}; summing these two first gives an exit
  across cut 1 with value {T2_0, T2_3}. Correct statement: cancellation-free circuits have no exits in any
  summation order (readers' adjoints have disjoint supports).
- **Generalised Lemma B: correct** (kernel {0, par'} with par' vanishing on Even(w^(k+1)) + 0).
- **4E boundary: correct**, with an unstated step for "pure" (injectivity forces l_(k,i) = 0 for k < l-1, so
  each zeta lives on one group). N_1 = 8. N_2 >= 17 is immediate from M_2 = 20 (three of the four even
  vectors as exports), independent of the unreviewed chain/REPORT section 4.
- **Section 3:** the observations hold, but the two "a uniform proof would follow from either of" forms are
  not precise and nothing is derived; they are programmes, not "[proved observations]".
- **Section 4 (ring):** near arc and far-arc boundary types correct. "At least 3 + 4 = 7 entries" needs a
  far arc of at least two groups; for a far arc of one group the obligation is F_2^4 alone (at least 4
  entries) and the far arc has no required pure vectors. The Q_3 remark is unaffected. The MixColumns
  bullet rests on RECORD 17 (not checked here).

## Claim 2: compose/prove3/REPORT.md

- **Skip-exit lemma: correct.**
- **Lemma R: correct.** The ten-gate lemma holds with the larger free space (Step 2 uses only
  Phi l_c = p_c and the rank-3 relation); zeta_j + zeta_k even, nonzero, not a zeta kills both stacking
  patterns in every summation order (an input as "other contribution" is odd); fibres {r, r + pi}.
- **Corollary R: correct.**
- **Theorem A: correct.** Step (i): level-3 operands are vectors on w^3, free whether or not they are X13 or
  X23 gates; entries whose non-free operand is level 1 are level-1 gates, their labels enter only through
  e1; t_M <= e'. Step (ii): level-2 first gates have two level-2 operands in different cut-2 fibres; the
  roots are level 2; level-3 labels project to 0 and are dropped; an MC_1 instance with <= e1 exports.
  The substituted "Steps 1-3" use only counting ((I) -> (ii), (E) -> (iii), Lemma B with
  K_(M,c) <= d + e'); cases exhaustive; arithmetic 20, 20, 16 + e1; t_M >= 5 gives e' = 5, n = 4.
  Survivors close as stated. K = 29 circuits are automatically reduced (else K < 29, against Theorem 1).
- **Proposition H: correct.** (3) replacing h by r + delta is legitimate: in the local model every vector
  on w^3 is a base signal and delta != 0; what is lost is fact (E) for delta and the label/time steps of
  (X), and steps (4), (5) use neither.
- **Status/source issues.** The (Y')/(Z') split comes from chain/REPORT section 3 (unreviewed); the
  reviewer re-derived the parts used (e = 5 excluded since the (X) argument at cut 2 uses only last-level
  data; e = 4 with a basis forces (D2, N2) = (4,5) with o >= 3 or (5,4) with one non-entry duplicate;
  (Z')'s fifth pure gate is forced even, else all four C_i would be 3-edge paths in a 4-edge forest).
  (Y')'s "all four labels units" not confirmed (unused). "R, a 20-gate pair circuit" should read "cost
  |R| + tau = 20". The Remark's P_2 <= 18 not checked.
- **Residual gap.** (G1) and (G2) are exhaustive. (G1): R reduced and optimal, Corollary R applies,
  d <= 6; step (ii) fails there, so e1 >= 4 is not available (correctly not claimed). (G2) accurate, with
  missing details: a length-1 path along the delta edge becomes possible (C_i = delta); if delta is even,
  paths through it have even length and the tree list must be redone; the double-star parity argument
  still applies; time order still partly applies (paths through delta come after h).

## Claim 3: compose/build29/REPORT.md

- **Two-pair inequality: correct** (inclusion-exclusion; restrictions are valid pair circuits;
  |W12| = 20 + o1 + o2 - e12 + w12'; needs w12' in D3 or U and w23' in D1 or U, which holds). Over-reading:
  alternative (a) is not implied; the inequality forces o2 + (b) + (c) + (d) >= 1 + dup12 + dup23, and o2
  is a count, not a set of gates.
- **First-contact lemma: correct after scoping.** "The earliest X-gate is X0 = W + f" needs X0 taken among
  ancestors of g (among all gates it fails: p1 = x1 + y2, p = p1 + y3, q = x1 + f gives
  X0 = y2 + y3 + f, not a duplicate in view (2,3)). The D1 ∩ D3 sentence is wrong as stated: g = p + q is
  a duplicate in at least one view unless (X-gate and b1-b2 mixer), in both only if neither;
  counterexample to "both": p = x0, q = y3 + f. "Every sharing pays at least one redundant gate ... seen
  by only one bound" over-claims: one redundant gate per first contact, not per shared gate (the hub uses
  that difference), and "only one" fails when b has only b3 material.
