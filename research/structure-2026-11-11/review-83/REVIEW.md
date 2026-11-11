# Independent machine review of RECORD.md section 9 (the 83 bound) and rotation/REPORT-PART2.md

Review of 2026-11-11 by a second model instance (Opus) that did not write the text; saved by the main
agent from the reviewer's final message. A machine review, not a human review and not a formal
verification. The reviewer's scripts and outputs are in this directory. All corrections are applied to
RECORD.md section 9.

**Verdict.** Theorem 9.2 (every block-monotone MixColumns circuit has at least 83 gates) holds. Theorem
9.1 is correct with presentation gaps. The paragraph "What an 87 would have to contain" was wrong, and
the double-service paragraphs claimed more than is proved.

## Findings, most serious first

- **"What an 87 would have to contain": WRONG.** Theorem 9.2 gives 83, so it excludes block-monotone
  circuits only up to 82 gates; "an 87 is not block-monotone" needs the conjecture J_01 = 22, J_347 = 36.
  The list of cases was also incomplete: Lemma II.6 says "exit-like or a triangle", MixColumns has four
  triangles, and the three inside a sheet support ({0,1,7}, {2,3,7}, {3,4,7}) can also break
  monotonicity; exits can land on two blocks; Lemma II.7 is proved only for Q_m, m >= 4. Counterexample
  to "double service only via {1,2,7}": two hunt records (free-02, g88-d7-d1a7d70c18e1b7cf and
  g88-d8-4d178ce621827217) are window-local and not block-monotone; their only block-cancelling gate is
  [3:s0 4:E3 7:s0] + [3:s3 4:E3 7:s3] = [3:d1 7:d1], an exit inside S_4 landing on blocks {3,7}.
  REPORT-PART2 II.8 item 3 ("the only places") is overstated for the same reason.
- **"Where double service can happen": OVERSTATED.** Lemma II.6 is right, and {1,2,7} is the only
  triangle in no single sheet support (checked by program). But only 4,264 of the 14,638 non-monotone
  kste circuits are window-local; the other 10,374 contain a gate lying in no sheet support (patterns
  0127, 027, 012, 1237, 137), and in 5,315 circuits the cancelling gate's operand supports are nested,
  so there is no triangle in the sense of II.6. The commonest corpus mechanism is "a gate whose blocks
  lie in no single sheet support".
- **Corpus statement: CORRECT, wording to tighten.** Own parser: 19,184 lines, 246 dropped (242 truncated,
  4 compute no outputs), 18,938 valid; 4,300 monotone, 14,638 not; hunt records 241 and 174. Every
  non-monotone kste circuit has exactly one block-cancelling gate whose operand union lies in no sheet
  support; the cancelled block is 2 in 14,600, 1 in 31, 7 in 7; the union always contains {1,2,7} and is
  {0,1,2,7} in 10,351. Two non-monotone hunt records have no such gate.
- **Theorem 9.2: CORRECT.** The families are eight sets F_j (ancestors of sheet j nonzero on block j; F_3
  also takes the gates on {2,7}). Disjointness: a gate in F_j and F_j' has support inside both sheet
  supports and containing j and j'; no such pair exists; blocks 2 and 7 lie together only in S_3.
  Theorem 9.1 applies to sheet 3. Numerics on 4,544 monotone circuits: no overlap anywhere; minimum F_j
  is 10 for every j except F_3 (13); minimum total 83, reached by one kste circuit, so these families
  alone can never give more than 83. Recorded 88: 11, 11, 10, 15, 10, 10, 10, 10 (total 87).
- **Theorem 9.1: CORRECT WITH A GAP (presentation).** A zero entry operand needs a class; the step
  "#B >= 10 + |E_k|" needs the explicit deletion of repeated gates; |E_a| should read dim A <= |E_a|.
  Computation with an own SAT encoding (`sat91.py`): local lemma 9 impossible, 10 possible; three-term
  sheet 13 possible; 12 gates undecided (timeout after 25 minutes), so the value 13 rests on the hand
  proof plus the local lemma. The proof's inequalities hold on 800 enumerated 13- and 14-gate circuits
  and on sheet 3 of all 4,544 monotone corpus circuits; profiles with 0, 1, 2, 3 M-gates all occur at 13.

Scripts: `sat91.py`, `families_out.txt` (corpus run), `odd_hunt.py`, `odd_exit.py` (the two hunt
counterexamples), `t12.log` (empty: the 12-gate run timed out).
