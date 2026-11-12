# Independent machine review of sharing/REPORT.md

Review of 2026-11-12 by a second model instance (Opus) that did not write the report; saved by the main
agent from the reviewer's final message. A machine review, not a human review and not a formal
verification. No SAT and no exhaustive search; the scripts verify given objects or test claims on
recorded and randomly perturbed circuits and establish nothing universal. Scripts are in this directory.

## Findings, most serious first

**1. Proposition 4.1: WRONG (first sentence false, proof fails; the bound is unproved, not refuted).** It
says that in a (W1) circuit, mu = 2 happens only through a backward exit. A gate can also reach sheet j
the long way round the cycle through forward exits. Explicit example built from q4_40 (r4_w1.py): take g
on blocks {0,1}, which serves sheet 1; set g1 = g + [0: g's block-0 part] on {1} (a forward exit),
g2 = g1 + p2 on {2}, g3 = g2 + p3 on {3}; splice g3 into the operand y of a reader-free sheet-0 output:
z = (y + unit(0,3)) + g3, which equals y. A correct 49-gate circuit with no (W1) violation, mu(g) = {0,1},
and no backward exit at all. So "replace each exit ...; no gate then has mu >= 2" does not follow, and
the bound G >= 10m - sum(L(H_j) - |H_j|) and the "self-generating" remark are unproved. (The replacement
step itself is valid; L(H) <= |H| + 2 is correct; "trimmed block-monotone implies (W1)" is correct; "the
four triangle gates are exactly Q_3's (W1) violations" is verified by program.)

**2. "What a 19 would have to be (proved reductions)": OVERSTATED.** Proved and correct: f_w + tau = 10;
(f_w, tau) is (7,3) or (6,4); tau' >= 4; the case list (R1)/(R2) is complete; the (R2) B_i are T-exits;
K = tau + N_10 + f_w' + D' with f_w' >= 8 and D' >= 4. Lacking proof: (R1) "one even P" (repair: an odd P
has the value of a w'_k or of some B_l and can be deleted, giving 18); (R1) "three unit-labelled entries
form a path in one fibre"; (R1) "one of B_i or P is a T-exit" (repair: without T-exits the omega = 0
gates form a circuit on w' for the four E_c, which needs 6 > 5 gates); (R2) "exactly four duplicates are
entries" (the exclusion of five entries is asserted, not given); (R2) "labelled by the four units" (with
a non-entry duplicate the fibres are no longer trees); "at most one second part beyond ..." (holds when
tau = 3, no argument for (f_w, tau) = (6,4)).

**3. Theorem 3.3 (the pair problem needs at least 19): CORRECT, given the r = 1 theorem.**
- Mirror form: |T| = (2K + 8) - (8 + tau + K) = K - tau; the adjoint of b_i is
  A_i = E_i(w) + w'_(i-1) + w'_i (consistent with s_c = e_c + e_(c+1)); the adjoint of b'_i is E_i(w');
  the exports span a space containing Even(w) + 0. Asserted by program.
- 3.1(a): a first gate cannot have an operand with omega = 0 nor two operands in one fibre; the inputs
  w_c are the roots of the unit fibres; replacing each operand by its fibre root gives a genuine circuit;
  the theorem is applied to signals. Wording: "span Even(w)" should read "span a space containing
  Even(w)".
- 3.1(b): every entry is a duplicate; non-entry duplicates exist but only D >= tau' is used; the span
  induction holds however the operand was produced, T-exits included.
- 3.1(c), (d): correct (in (d) the three operands are distinct gates outside the B_i).
- Lemma 3.2: correct ("a tree" should read "a forest"; any forest with four edges has at most two 3-edge
  paths, and paths never cross fibres).
- Arithmetic: all cases with K <= 18 are covered.
- Translation to circuits: correct; checked against the MixColumns matrix: exactly the pairs (1,2) ...
  (7,0) restrict to the pair problem; for (0,1), sheet 1's restricted outputs carry s_c on the free block
  7, a different problem.

**4. Theorem 3.4 (level-monotone mirrors): CORRECT WITH A GAP.** The induction must run on the mirror-form
statement: every level-monotone T containing the required vectors, with tau signals spanning a space
containing Even(group 1) + 0, has |T| + tau >= 10 l; base case the r = 1 theorem. With that wording the
proof holds. The class is well defined as an existential property over orders; checked over every
ordering of each signal's readers: q3_28 has no level-monotone order on any pair, q4_40 and q8_80 do.
"Not comparable with block-monotone circuits": not verified.

**5. Lemma 1.1: OVERSTATED wording.** For adjacent sheets j, j+1, paths to sheet j+1 need not cancel block
j; the statement holds only for the sheet whose window misses the other sheet's own block; and the
partner carries the component held by the path operand at that point. Lemma 2.1: correct.

**6. Sections 2 and 6: CORRECT, reproduced with independent code.** q3_28: |D_j| = 12, 13, 14, giving
28 = 30 + 9 + 0 - 11. Recorded MixColumns: 88 = 80 + 5 + 3 - 0, 89 = 80 + 6 + 3 - 0, 97 = 80 + 14 + 3 - 0.
The eleven corpus circuits of section 6 reproduce exactly.

**7. Numerics** as (K, tau, |T|, f_w, D, N_0, tau'): q8_80, all 8 pairs: (20,3,17,7,3,7,3), no T-exits.
q3_28: (23,6,17,6,6,5,6), (24,6,18,6,6,6,6), (24,6,18,6,6,6,5), with 1, 1, 2 T-exits. MixColumns 88,
pairs (1,2)...(7,0): K = 21, 25, 24, 20, 20, 20, 21; 89: 22, 23, 25, 21, 20, 20, 22; 97: 23, 26, 31, 24,
20, 21, 22. Lemma 3.1 (a)-(d) and |T| = K - tau held on every pair under 52 accumulation orders and on
600 randomly perturbed valid pair circuits (156 with T-exits). A test, not a proof.

Not reviewed: Proposition 1.2, the lifts, section 5.

Scripts: rlib.py, r1_pairs.py, r2_perturb.py, r3_levelorder.py, r4_w1.py, r5_charges.py, r6_corpus.py.
