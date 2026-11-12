# Review of compose/sb/REPORT.md (SB, SB', Theorems S1, S2, Lemma Q)

Independent machine review, phase 4 (2026-11-12), separate model instance (Opus, high effort). Saved by the
main agent from its final message, condensed (arguments kept). Not a human review. `ev.py` is the
reviewer's own circuit evaluator (independent of mcheck.py); tscan.py and t1-t3 were not run.

**Verdict.** Every main claim holds; three repairable gaps; no counterexample to any proved statement.

1. **Counterexample to SB: correct (checked).** dangle2.txt: 22 gates, tau = 3, cost 25, reduced, all
   targets, exports span Even(w^1); f1 = 7, h1 = 0, near1 = 10, e1 = 7, |P| = 8, far1 = 15; one exit
   B3 = u0+u1+u2 costing exactly 2 from the labels before it (BFS): beta = 1 > 0. SB' holds (tau_min = 3,
   sigma = 4). tight_o2.txt: cost 23, reduced, valid, f1 = 6, h1 = 1, tau = 4, near1 = 11, labels
   u0, u3, u2+u3, u1+u3 (o = 2), only exit u0+u3 (beta = 0). The diagnosis (Lemma 2.1 charges all e1
   entries as exports, only tau_min are needed) is right.
2. **Lemma 2.1' and SB' => M_l = 10 l: correct.** far1 >= |P'| - beta + e1 = (|P'| + tau_min) - beta + sigma.
   Needs SB' for every reduced one-sheet instance with e1 >= 4; e1 = 3 via Theorem 4.1; M_l <= 10 l from
   RECORD 16. Added observation: the clean labels already span Even(w^2) + 0, so tau_min <= t and
   sigma >= e1 - t (each unclean, e.g. dangling, entry pays 1 in sigma).
3. **Theorem S1: correct, including staging** (dimension 3 with >= 4 available values: the six other
   nonzero vectors pair as {a, a + v}, four available values fill a pair; "available" includes earlier
   computed values; each exit judged at its own moment).
4. **Lemma Q: correct, including staging** (any 3-subset of {1,2,3,4} contains a block of any split into
   two pairs; the complementary pair is built only when a request contains both of its labels; first heavy
   request with three labels present still gives extra <= 2).
5. **Theorem S2: statement correct; two repairs.** Facts (a), (b), (e) check. o = 1, near1 = 10: correct
   (|L1| = 11 follows because tau = 4 is excluded). o = 2, near1 = 10: conclusion correct, attribution
   wrong: fact (a) needs tau = 3 as hypothesis; correct route: t = 4, Lemma B gives |T*| >= 7, so f1 >= 7,
   hence tau = 3; stacking: shared operand impossible for every pair (A + A first gives a zero gate; A + B
   not a T* value); entry-on-entry only for the odd pair with empty rest; beta = 0. **o >= 3, near1 = 11,
   h1 = 0: stated reason false for o = 3** (Lemma B's kernel gives zeta_1 + zeta_2 + zeta_3 = 0 over the odd
   labels, so zeta_1 + zeta_2 = zeta_3 is a T* value and stacking can occur). Repair: the even entry can
   neither share an operand nor stack, so it is isolated; exits are path sums over the three odd edges;
   only lambda_1 + lambda_2 + lambda_3 has weight 3; beta <= 1 = near1 - 10, SB' holds. o = 2, near1 = 11:
   possibilities (tau, f1, h1) = (4,6,1), (4,7,0), (3,7,1), (3,8,0); (4,7,0) was omitted: tight with h1 = 0,
   excluded as at near1 = 10.
6. **Exclusion of (G2) with e1 = 4: correct.** D1 = b + c, c = 0 and b = e1 (both from Proposition H), so
   h1 = 0 and near1 = a + tau = 10; at near1 = 10, e1 = 4 SB' holds in every case (o = 0: S1; o = 1, 2:
   beta = 0; o >= 3 impossible). "Still open: (G1) and (G2) with e1 >= 5 and some odd label" (the qualifier
   applies to G1 too). "Any 29 with e1 = 4 lies in Omega with far1 = 18" correct; beta = 2 may also come from
   two weight-3 exits; "the natural one ... is at least 19" has no argument (unproved).
7. **Omega: imprecise.** The Omega1 cross-sum description is valid only for o = 4 (o = 3 allows stacking).
   "beta = 2 needs essentially delta = lambda_1 + .. + lambda_4" is wrong: delta = lambda_1 + lambda_2 +
   lambda_3 with lambda = lambda_4 gives the exit (r + pi) + h of weight 4. Correct: some exit has weight 4,
   or two exits of weight >= 3 need both auxiliary pairs. Omega2: add the excluded (4,7,0); (3,8,0) stays open.
8. **Mirror identity: correct** ((2K' + 4 + m) - (4 + t + K') = kept non-entry gates + 2m). Caveats:
   cleaning with exits as targets keeps ancestors of exits that are not ancestors of the A_i (e.g. dangling
   stacks); "not sharp" is only a counting observation.
**Scope.** "(proved)" labels were hand arguments without review before this one. Section 7 ("every l") is
accurate for S1, Q, 2.1', S2 (generalised Lemma B and fact (a) are length-independent). mcheck.py's beta
sums single-exit costs (an upper bound on the joint beta).
