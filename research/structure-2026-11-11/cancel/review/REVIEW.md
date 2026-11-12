# Review of cancel/CANCEL.md (phase 8)

Independent machine review (separate model instance), 2026-11-12; not human review. Own code in this directory
(`rev.py` core, `run.py` girths/Q_m, `run_mc.py` MixColumns sample, `extra.py`, `collapse_check.py`,
`partner_support.py`); own MixColumns matrix (out_i = 2a_i + 3a_(i+1) + a_(i+2) + a_(i+3), 0x11b), checked
against RECORD (3.1) row by row. Methods: hand reasoning, direct evaluation of given circuits only (no SAT,
search, enumeration). MixColumns sample: recorded 88/89/97 + every 50th kste line (1, 51, 101, ... of each
file; 4 lines of circuits_2.txt are not MixColumns circuits and were skipped): 384 circuits.

## 1. Theorem K and proof: CORRECT (wording fixes)
Every step checked by hand.
- First cancellation: k is in B(g); blocks are lost only at exits; at the first exit e_1 of pi_j losing k the
  on-path operand carries k, so the off-path a'_1 does too (equal nonzero parts). Right.
- Same l: B(a'_1) is inside W_l for EVERY confining own block l, so k is in W_(l_1) for the particular l_1
  chosen non-cancelled (that is the one used for both the edge and the continuation). l_1 != k because k is
  cancelled at e_1 and l_1 is not; l_1 != j because k is in W_(l_1) but not in W_j. Not cancelled + in B(a'_1)
  implies l_1 in B(e_1), and e_1 is on pi_j, so l_1 is on the path after the exit. Right.
- Later steps: l_i = j can occur (the walk then ends at j); the text's "(edge l_1 -> j, or l_1 = j)" covers it.
  Repeated sheets in the walk are harmless (walks, not paths). A closed walk of length L in a loopless digraph
  contains a directed cycle of length <= L (shortest closed sub-walk); "two distinct vertices" is not needed.
- Exit definition is exactly what is needed (same as J9): a block disappears along a path only at such a gate,
  and then it lies in both operands.
- Hidden assumptions (all hold for MixColumns, Q_m, chains; state them): (i) the four rows of a sheet share one
  support W_j (verified); (ii) distinct sheets have distinct own blocks (non-own blocks such as a chain's free
  block are harmless: the chase only visits own blocks); (iii) A_j includes the rows themselves (g may be a
  row; pi_j then has length 0); (iv) t_j counts exits strictly after g. A gate a + a is an exit whose off-path
  operand is the same signal; its value is 0, so it is an escape; harmless.
- Fix (strengthening, recommended): the proof uses the hypothesis only at the CHASE exits (where the currently
  chased block is first lost). State it so; then t_j can be the number of chase steps, and K covers RECORD 7.2's
  block-monotone class (support containment, exits allowed), where the chase stops at once (k in B(g) in W_j).
- "t_j + t_k >= gamma - 2" for gamma infinite should read "the hypothesis cannot hold".

## 2. Corollaries and girths: CORRECT WITH FIXES
- Gamma (own code from the windows {0,7},{0,1,7},{1,2},{2,3,7},{3,4,7},{4,5},{5,6},{6,7}): edges x -> x+1 and
  7 -> 0, 1, 3, 4; every cycle passes through 7 (0 -> ... -> 6 is acyclic); girth 4. Q_2: 2, Q_3: 3, Q_4: 4,
  Q_5: 5, Q_8: 8; chain acyclic. Triangle remark (block-7 edge between two s-parts) correct.
- (a) correct; it is J9's "equivalently" sentence. It is a special case of phase 7's J8 statement only under
  J8's definition (B(a + c) = B(a) u B(c) at every gate, i.e. no exits at all). It does NOT contain RECORD
  Cor. 7.2 (block-monotone = support containment, which allows exits) unless K is stated with chase exits
  only (section 1 fix). Say which definition.
- (b) correct (one exit in total would need a cycle of length <= 3). "Plain charged closure" should be defined:
  every chase exit has a confined, non-escaping off-path operand.
- (c) correct; note that free vectors of a chain (block j-1, not an own block) are never confined.

## 3. Lemma W: CORRECT WITH FIXES
- Use of the ten-gate lemma is right: after zeroing all blocks but {j-1, j} (block 7 too for sheets 1, 3, 4;
  rows become E_c(j) + s_c(j-1), verified), gates of A_j outside F_j become free (supported on j-1, possibly 0);
  gates of F_j stay nonzero on block j, so zero never occurs among them; a projected value equal to a unit of
  block j is free; keeping first occurrences of the remaining distinct values gives a valid sequence for the
  lemma. So #distinct >= 10 and c_j <= |F_j| - 10. Measured: >= 10 in every sheet of all 384 + Q circuits.
- Fixes: the symbol pi_j is used both for this projection and for the paths of Theorem K; "non-input" means
  "not a unit of block j" (no other input can occur); A_j must include the rows.
- W1 numbers depend on an unstated convention: "collapsed" = equal to the projection of an EARLIER gate of F_j
  (collapse.py). With that convention: Q_3 6, MixColumns 2 in all 305 double-charge circuits (confirmed);
  with the symmetric reading (equal to ANY other gate of F_j): Q_3 5, MixColumns 2 in 225, 1 in 80. State the
  convention. The refutation itself (c < R) is convention-free and confirmed (below).

## 4. Numbers (own code)
- Q_3 (q3_28): E 9, R 11, U 0, c 5 (c_j 1, 2, 2), 28 = 30 + 9 - 11; 11 double-charged gates; exactly 4 exits
  (g21, g25, g30, g35), and these 4 are the exits on the paths at which the needed blocks are lost; example
  g16 / g21 = g18 + g20, g20 = [1:0011 2:1001] charged to 1, 2, own block 2 kept: confirmed (walk 1 -> 2 -> 0,
  0 -> 1). Off-path operands at needed cancellations: 20 instances, 14 confined non-escaping, 6 escapes, 0 not
  confined. In ALL 14 the off-path operand is charged to the third sheet (the 6 "reconvergent" ones included),
  so "third sheet in 8, reconvergent in 6" understates it. Q_2: E 4, R 8, no exits. Q_4, Q_8: R 0.
- MixColumns: 88/89/97 recorded: R 0 (E 5, 6, 14; c 3, 5, 7). kste: 305 of 381 have R = 3 (three gates on
  {1, 2} charged to 1, 2), 76 have R = 0. At the needed cancellations (915 instances) every off-path operand
  is an uncharged gate, never an input, never confined (0 escapes); one (exit, partner) pair per circuit
  closes all three. E >= R and E + U >= R in every circuit; (E, R, U) = (10, 3, 1) occurs (50 circuits).
- circuits_3.txt line 7451 (1-based): E 5, R 3, U 6, c 2: confirmed. 6 circuits of the sample have c < R.
- Six instances (circuits_3.txt lines 1451, 3001) of an exit on a path from a double-charged gate to sheet 1
  WITH a confined non-escaping off-path operand ({0,7}, charged to sheet 0): the exit cancels block 7, not a
  needed block. Irrelevant to K (not a chase exit) but contradicts the literal reading of "no exit operand is
  confined and non-escaping" for "exits on the paths"; restrict the sentence to the cancelling exits.
- Section 3's "(2,529 not confined, 1,059 escapes)" counts BOTH operands of each exit (partners.py classifies
  [a, b]), the on-path one included (own sample: 1,284 + 546 = 2 x 915). For the off-path operands, which the
  theorem concerns, the count is all not confined, 0 escapes. Restate.
- The partner is not always "[2:s 7:s] inside W_3": off-path operand support {2,7} in 203 of 305 circuits, but
  {0,2,7} (not inside W_3) in 102; its block-2 part is d_0 = {0,2} rather than an s in 23+21. Say "typically".
- "least |union F_j|: 82" is wrong: circuits_3.txt line 7651 has |union F_j| = 81 (E 4, R 3, U 7, c 2, G 88).
  Line 7651 = 1 + 25 x 306 is also in the document's own stride-25 sample, so the 82 (inherited from
  RECORD 22) was not recomputed. Still >= 80; the conjecture survives. Correct RECORD 22 too.

## 5. Scope and wording
- Theorem K correctly described as about the shape of closures, not a cost (section 2 end, section 5 Scope).
- "So the dichotomy the corollary predicts is what the circuits do ... (no extra gate)": overclaim. (b) is a
  prohibition for one-exit closures in MixColumns; for gamma = 3 K only PERMITS charged closure, it predicts
  nothing; "no extra gate" is a cost statement not proved. Write "is consistent with".
- "the property separating Q_3 from MixColumns is the directed girth" / "it is what distinguishes Q_3 from
  MixColumns": overclaim. Proved: girth is a difference that controls one-exit charged closures. Not proved
  that it controls savings (gamma = 4 still allows two-exit charged closures, item (iii)). Weaken.
- Conjecture G: |union F_j| >= 10 s implies G >= 10 s (G = |union| + U), so the stated consequences are
  correctly implied: L(MixColumns) >= 80, L(Q_m) >= 10 m and M_l >= 10 l (chain gamma infinite); the
  equalities "= 10 m", "= 10 l" also use the known upper bounds 10 m, 10 l (say so). "Consistent with Q_3 and
  Q_2" is vacuous (they lie outside the hypothesis); it is a non-contradiction, not a test. "Sheet systems of
  this type" should be made exact (rows E_c on the own block + s_c on every other window block, one window per
  sheet, so that the ten-gate lemma gives |F_j| >= 10).
- "Missing argument": correct that U does not enter |union F_j|; fine.
- Status "proved" for K, (a)-(c), Lemma W is justified by this review (main agent's hand proofs; machine review).
