# Independent machine review of causal/REPORT.md and direct-sum/REPORT.md (section 2 and literature)

Review of 2026-11-12 by a second model instance (Opus) that wrote neither report; saved by the main agent
from the reviewer's final message. A machine review, not a human review and not a formal verification.
No SAT and no exhaustive search; the scripts inspect recorded, designed or random objects and establish
nothing universal. Scripts and outputs are in this directory.

## Findings, most serious first

**1. Theorem 3.2 (cyclic charge theorem): CORRECT WITH A GAP; the written reason is false as stated.**
"Projecting a derivation of the outputs of J onto their blocks is a local system" fails literally: with
equations Lam_J and unknowns the members nonzero on the blocks of J, the system need not be square or
invertible. Valid circuit counterexample (gadget_out.txt): in q4_40 compute the free vector s on block 0
through block 1 (y1 = e + a, y2 = e + b, s = y1 + y2); a correct 42-gate circuit in which, for J = {1},
Lam_J has 13 triples on 12 live unknowns. Repair: every output o of J has e_o equal to the sum of the
rows of T_o in Lam_J; take a row basis Lam' inside Lam_J and a column basis U containing the outputs
(they are independent in the column matroid); set every live unknown outside U to 0 (a free vector);
then N[Lam', U] is invertible and the targets keep their true values; Theorem 2.4 applies with
K <= |Lam_J|. Checked on 1,260 based systems plus the gadget circuits. The hypothesis of Theorem 2.4
holds for all 37 independent MixColumns families (every j in J has the private free block j-1; only
block 7 can be shared, and it is settled after the private blocks). Proposition 3.1 has no written
proof; it is true by the same row-basis / column-basis argument.

**2. "The premises of the charge framework hold for all cyclic systems" and "block-monotone cyclic
systems need 80": OVERSTATED.** What is proved is a twin inequality in which membership in the
derivation of an output replaces ancestry; the two counts differ (Q_3: wire charges 12, 13, 14; dual
charges 12, 12, 13). "Block-monotone" is not defined for cyclic systems; Corollary 3.3(b) proves 10m (80
for MixColumns) for dual-block-monotone BASED systems (S, T), a property of the basis that is weaker than
block-monotonicity of circuits. Corrected wording: arguments using only the inequalities
|Lam_J| >= 10|J| cannot exceed L_cyc; arguments that use ancestor structure are not covered (Lemma 1.3,
Lemmas II.6 / II.7, and the 83). "Theorem 3.4 shows the Q_3 mechanism needs all sheets pairwise
adjacent" is also overstated: it only rules out a net gain inside independent families.

**3. direct-sum Theorem 2: CORRECT WITH A GAP (no proof written).** Proof: union-find on Y-coordinates,
merging at every gate whose operands both have nonzero Y-part; at least n_B - c_B merges are needed; a
gate new on the X side can merge only two classes that both contain mixed Y-supports; a new mixed class
is created only by a mixer, which is not X-new and merges nothing; so X-new gates make at most as many
merges as there are mixers, and G - N_X >= n_B - c_B. Held on 9,000 random circuits.

**4. Corollary 3.5 and Proposition 5.2.** 3.5(a), (b) and the main claim of (c): CORRECT. "For m = 3 it is
vacuous": WRONG (with three singleton colour classes every block-monotone Q_3 circuit satisfies the
hypothesis, and (c) gives 30). Proposition 5.2: "ideals add nothing" CORRECT but trivial; "each has an
order-free twin" OVERSTATED (the twin bound equals the circuit bound only where the local-system minimum
is known to equal the local-circuit minimum: subsets of one sheet and independent families; not shown
for adjacent sheets).

**5. Lemma 2.3: CORRECT.** Cleaning keeps invertibility; formal inputs; the dual U = Sel N_y^(-1); the
split dual is square and uniquely solvable; two-term stars are allowed, so the gap G3 of the cyclic audit
does not arise; the count K - tau + r - p'' matched numerically on every run. Unstated hypotheses:
distinct targets and no zero row of P (both hold in Theorem 2.4).

**6. Theorem 2.4: CORRECT, including for non-executable systems.** Both parts (a) and (b) check; only
invertibility and cyclicity are used.

**7. Lemma 1.1 and rigidity: CORRECT; counts confirmed.** Collinear triples recounted independently:
q3_28 has exactly 28, MixColumns 88 has 88, q4_40 has 40, q8_80 has 80, MixColumns 89 has 91. Q_3 wire
charges 12, 13, 14 and dual charges 12, 12, 13 confirmed; eleven gates with mu = 2. What S forces is the
ancestor order, not a linear order; the forced-relay claim was not checked.

**8. Proposition 4.1: CORRECT, given double-map Lemma A and Theorem C.** "Step 4 is algebra" is true by
inspection (it sits inside an implication that concerns only T). "No gap" holds only at eps = 0.

**9. Direct sums, section 2.** Lemma 1, Lemma 2 (both forms): CORRECT. Lemma 3(c): CORRECT WITH A SMALL
GAP (the r Omega_mix Y-parts that raise the span are never Y-parts of gates new on both sides; that is
what excludes r vectors). Theorem 1: CORRECT, every step. Corollaries: CORRECT (a part with at most 4
inputs even has h <= 2). Floor for a counterexample: CORRECT. The identity, Lemma 3 and the span lemma
held on 9,000 random circuits; 141 attain d = 2^r - r - 1 > 0.

**10. Literature: partly confirmed from the raw pages.** Jukna's note of 22 May 2015 "On XOR complexity
of direct sum of matrices" confirms the failure of additivity via Strassen-type O(n^omega) multiplication
against Omega(n^3 / log n); it credits only "Igor" (the name Sergeev does not appear) and does not
mention depth. The page on Problem 7.7 repeats the argument with the footnote that it was "told to
Wolfgang Paul by an anonymous referee" (Paul 1976, Corollary 2), and its addendum of 4 June 2017 proves
depth-2 additivity, which makes the failure an unbounded-depth one. Find et al., Section 3.1 (ar5iv
rendering): x -> (I (x) A)x is well known to admit nontrivial XOR circuits. Not confirmed: the attribution
to Sergeev; the phrase "unbounded depth" on the first page.

Files: rp_lib.py, review_causal.py, gadget.py, ds_check.py, lit_grep.sh, lit_grep2.sh, run_*.sh,
*_out.txt.
