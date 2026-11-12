# Review of compose/TWOSIDED.md

Independent machine review, phase 4 (2026-11-12), separate model instance (Opus, medium effort). Saved by
the main agent from its final message, condensed (arguments and counterexamples kept). All points checked
by hand; no scripts. Not a human review.

**Verdict.** Theorem 4.1 correct, with one missing step (an exit could be a label signal) that closes by
independence of the labels. Lemma 2.1 correct once L_Lambda(S) is defined with strict staging (otherwise a
circular free computation is allowed). Section 5's arithmetic is correct, but "SB is a one-sheet
statement" holds only with a near-side staged L. Section 6 correct. Three side statements wrong.

## Sections 0-1
- Split identity correct (level-1 gates are f1 + e1 + h1; a gate with a far operand keeps the other
  operand's omega, hence is a duplicate; far gates have equal omegas). "One level-1 and one far operand
  is an entry": correct. P = ordinary far gates + exits: correct. V contains Even(w^2) + 0: correct.
  (F1) and the exit-free bound: correct.
- **Support claim wrong.** Labels lambda_1 = u (a w^2 unit) and lambda_2 = u + v (v on w^3): entries
  r + pi_1 and r + pi_2 on one level-1 signal r give the exit pi_1 + pi_2 = v, with zero w^2-part although
  both labels have nonzero w^2-parts (an X13 exit; consistent with the skip-exit lemma). Repair: zero
  w^2-part exactly when the w^2-parts of the support labels cancel. Parity claim correct.
- **Static relaxation sentence wrong** for Lemma 2.1, which relies on label signals preceding the exit;
  statically a label can be computed from the supplied value and the replacement becomes circular.
- **(N) incomplete:** (a) exports need only their w^1-parts to span Even(w^1); they may be far signals or
  have U-parts that cancel; (b) in T a label is available to the near side only once its far signal
  exists, and that signal may depend on exits; (N) drops this interleaving, so it is a relaxation.

## Lemma 2.1
- Exit values lie in the span of labels whose signals precede the exit: correct.
- **Definition gap:** if an exit value is later used as a label, "computing S from the label signals" could
  use s itself at cost 0 (L < |S|, bound false). Required: each s computed only from label values whose
  signals strictly precede its exit, exits among them replaced earlier in time order. Then L >= |S| and
  beta >= 0. Safest single-sheet version: L_near (labels of entries placed before the exit), which is at
  least the above, so the lemma holds a fortiori.
- P' is an MC_(l-1) circuit: correct. Replacement by the receiver's own earlier signals also valid.
- All-ones example: (i) beta = 2 is the bound; the actual far-side gain there is 6 - (4 + 1) = 1;
  (ii) wrong: "with labels a basis of the even space, 1111 is a sum of two labels"; for the basis
  u0+u1, u0+u2, u0+u3 it is the sum of all three (beta = 1). Repair: "for some bases".

## Theorem 4.1
- Labels a basis, V = Even(w^2) + 0: correct.
- **Gap, closes:** reducedness excludes an exit equal to another signal, not the exit BEING a label signal
  pi_j. Repair: then entry j comes after the exit and is not an ancestor of its operands, so lambda_j lies
  in the span of the other two labels, contradicting independence.
- Staging correct (unique expressions over a basis; ancestor entries include every label of the
  expression). beta <= 1; beta = 0 without a triple-sum exit.
- Near side correct (no exit: Proposition 1; h1 >= 1: (F1); h1 = 0: |L1| >= 10, Lemma R excludes 10,
  f1 >= 8, near1 >= 8 + tau >= 11, tau >= 3 implicit). Lemma R's proof uses only rigidity and the
  no-repeated-value property, so it applies to reduced T.
- Reduction can change e1, harmless: the theorem is for reduced circuits; optimal circuits are reduced;
  the Consequence (a 29 has e1 >= 4) is correct (a cost-29 circuit is optimal by M_3 >= 29).

## Section 5
- Arithmetic correct given Lemma 2.1 and SB with the same L, plus Theorem 4.1 for e1 = 3.
- Gaps: (a) equality needs M_l <= 10 l (RECORD 16), not cited; (b) the e1 = 3 case enters through Theorem
  4.1, not SB; (c) "SB is a statement about ONE sheet" holds only with L = L_near; with the static L the
  implication fails; with the far-side version SB depends on the far circuit's order. Repair: state SB
  with L_near.
- "(G1), (G2) are the l = 3 instances of SB": over-claim; SB would exclude them (sufficient, not
  equivalent).

## Section 6
- 4E definition matches L18; four distinct nonzero vectors in the 3-dimensional even space span it;
  N_1 = 8 and N_2 >= 17 correct; "pure" still relies on the unwritten injectivity step.
- (Z') correct (tau = 4 would give |T*| <= 16 < 17; so tau = 3, |T*| <= 17). (Y') correct: N = 4 forces all
  labels odd via fact (E); t = 3 would need N >= 7; so t = 4, o = 4 (does not need "all four labels
  units"); |T*| <= 21 - tau, one less if h unclean; 18 excludes tau = 4 and unclean h, not tau = 3 with h
  clean and |T*| = 18.
- "18 does not settle M_3 by itself": correct only for this reduction route; not shown that 18 plus
  Theorem A and Proposition H cannot close (Y').
