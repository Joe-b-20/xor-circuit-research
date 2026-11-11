# Independent machine review of cyclic/REPORT.md

Review of 2026-11-11 by a second model instance (Opus) that did not write the report; saved by the main
agent from the reviewer's final message. A machine review, not a human review and not a formal
verification. The reviewer's own code and outputs are in this directory.

**Verdict.** Nothing fatal. The examples and Theorems A, B, C(i), C(ii), W are correct. As written, the
audit (report section 3) does not fully prove two lemmas; both are true and the repairs G1-G3 below are
short. With them the main conclusion holds, given that PROOF.md is correct for circuits:
L_cyc(MixColumns) >= 75 and L(InvMixColumns) >= 75.

## Gaps and their repairs

**G1. Audit of Lemma 2.1: the inequality is proved in the wrong direction.** The audit shows that every
even element has even weight on each component's inputs, which gives dim span(even) <= 32 - c. The step
"y <= #even - dim E, i.e. x >= 32 - c" needs dim span(even) >= 32 - c. Repair: along a path in the odd
graph consecutive odd vertices differ by the edge's label, an even element; so e_i + e_j is in the span
of the even elements whenever inputs i and j are in the same component, and that span is exactly the
within-block even space, of dimension 32 - c. Checked numerically on every test system.

**G2. Audit of Lemma 3.1 ("the transpose of a minimum system is minimum and normalized").** Theorem C(iii)
alone gives L_cyc(M^T) = L_cyc(M) and size <= G for the set of dual values; sections 7-9 of PROOF need
that the dual variables have distinct nonzero values and that the split star equations form a basis.
Repair: after the 2-term stars are merged the dual has exactly m + G variables and G three-term
equations (sum of (D_v - 2) = G). By Proposition 1(b) its distinct nonzero values form a cyclic system
for M^T of size <= G. Because L_cyc(M^T) = G there must be exactly m + G distinct nonzero values; so no
two variables share a value and none is zero, and the G independent equations map to G triples, a basis.
The same count rules out a merged variable occurring twice in one star. So "minimum based cyclic system"
is closed under canonical duals, and the orbit of PROOF section 8 and Lemma 9.1 go through.

**G3. Stars with 2 terms (fan-out 1) are not handled in Theorem C(iii) and the audits of 7.1 and 7.4.**
C(iii) must merge the two terms of a 2-term star (or note that a 2-term equation maps to 0). In 7.1 the
star of a merged class reads "sum of V over the class's leaf points = 0", which is the sum of the class's
triples, so the true values satisfy it and uniqueness still gives V_v = v. In 7.4, a merged class lies in
as many dual triples as the support of the sum of its member triples, a nonzero relation, hence at least
3. Lemmas 6.1 and 7.3 survive merges. All held in tests that included 14,712 two-term stars.

## Overstatements

- The table of report 3.3 marks 4.2, 6.2, 7.2, (L10), 10.3(i) as "text does not use order". Their texts
  do say "its defining gate", "degree d_v + 1", "one odd operand", "degree >= 2"; each translates at once
  with D_v = d_v + 1 and degree >= 2 from minimality.
- "Ten" lemmas: eleven are treated (6.1 included).
- "Bounds L_cyc and nothing more" and "every argument that uses F_2-linear algebra is about cyclic
  systems" are heuristics, not theorems.
- Example 3 is not "MixColumns flavour" in both orientations: column 6 of A has weight 1, so the code has
  a weight-2 word. The stated numbers are correct. The reviewer found no 7 x 7 matrix with odd rows and
  columns of weight >= 3 in both orientations and L_cyc < L in about 8 CPU-minutes of search.

## Item by item

- Proposition 1 (a), (b), (c): CORRECT. Theorem C(i), (ii): CORRECT. C(iii): CORRECT WITH A GAP (G3).
- Parity is invariant under re-encoding for MixColumns: all 64 boundary vectors are odd, so the parity
  functional in the new coordinates is again "all ones"; the relation facts F2-F14 are invariant under
  linear maps of the boundary. The deduction for InvMixColumns needs only the equality of L_cyc values.
- Theorem W and the leaf property: CORRECT (verified on 348 non-circuit bases: the F_3-weighted matrix
  was singular every time).
- Examples 1-4, recomputed with own code: CORRECT. Example 1: exactly 60 non-circuit cyclic sets of size
  6 at n = 5, one S_5-orbit; none at n = 4. Example 2: L_cyc 7, L 8. Example 3: L_cyc 10, L 11.
  Example 4: 52 edge vectors of rank 16, 36 triangles, rank 36 over F_2 and 35 over F_3.
- Audit: 1.1 CORRECT; 2.1 GAP (G1); 3.1 GAP (G2, G3); 3.2 CORRECT; 4.1, 4.4 CORRECT; 6.1 CORRECT;
  7.1 GAP (G3); 7.3 CORRECT; 7.4 GAP (G3); 10.3(ii) CORRECT; 9.1 CORRECT once G2 is in place. The
  dictionary identities (G = 32 + x + y + h, (3.1), (3.3), (4.1), 6.2 (A) and (B), 7.2, 8.1) hold.
  Spot checks of 4.2, 4.6, 5.1, 6.2, 10.2, 10.3(i): no essential use of order.
- Numerical tests: 748 minimum based systems at n = 6 from 11 matrices in both orientations, including
  26 non-circuit minimum sets and 348 non-circuit bases, each with duals, double duals and a 12-step
  orbit; every check passed. Limits: the "new variable" branch of 7.4 and the inequality of 3.2 were
  tested only trivially; nothing depending on MixColumns' own finite facts was tested.

## What is established

- **L_cyc(MixColumns) >= 75**: follows, given PROOF.md is correct for circuits, once G1-G3 are written
  in. As written, report section 3 is incomplete at 2.1 and 3.1.
- **L(InvMixColumns) >= 75**: follows on the same terms (L(InvMC) >= L_cyc(InvMC) = L_cyc(MC)).

Scripts: `lmin.c`, `examples.py`, `audit_test.py`, `audit_driver.py`, `ex3_dual_probe.py`,
`mc_parity.py`, `run_examples.sh`, `run_at.sh`; about 15 CPU-minutes.
