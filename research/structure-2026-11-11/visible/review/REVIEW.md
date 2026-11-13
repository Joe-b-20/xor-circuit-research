# Review of `visible/VISIBLE.md` (phase 12), including section 5.5

**Machine review by a separate model instance. This is not a human review and not a formal verification.
No search was used.** There was no SAT, no enumeration, no least-gate search and no search over value sets.
The reviewer read the proofs by hand. Its own program `rv.py` (output `rv_out.txt`) only evaluates the
specified corpus circuits, the witness and explicit constructions. It does not import `visible.py`; it uses
`compose/compat/clib.py` only for the MixColumns rows and for loading circuits.

Background read: RECORD 3, 7, 9, 10, 17 and 26; `tenth-gate/PROOF.md`; `joint01/REPORT.md` sections 4-5;
`repair/REPAIR.md`.

## Verdicts

| statement | verdict |
|---|---|
| 1. Definitions, the four classes, backward traversal, separation | CORRECT |
| 2. Theorem G (closure, outputs, acyclicity, no events, count) | CORRECT |
| 2. Remarks (reducedness, zero values, duplicates, gates vs values) | CORRECT; one wording fix (F7) |
| 2. Sequential form | CORRECT |
| 2. Event-free implies block-monotone, and not conversely | CORRECT (explicit example below) |
| 3. Lemma S, window facts, consequences, Principle N, own-block property | CORRECT |
| 4.1 Co-occurrence graph and maximal cliques | CORRECT |
| 4.2 Lemma W1 | CORRECT |
| 4.2 Anchored events | CORRECT WITH FIXES (F2) |
| 4.3 Theorem W and its MixColumns table (80 / 82 / 81 and the two exceptions); triangle; corpus; 36 credit operands | CORRECT |
| 4.4 Tail family: construction, separation, hand proof of the event-free minimum 2n, equality in Theorem W; controls | CORRECT (minor wording, F9) |
| 5.1 G' >= 83 + U for every event-free circuit with designated outputs, with no reducedness | CORRECT |
| 5.1 Description of the families (F_3) | CORRECT |
| 5.1 Why 83 and not 84 | CORRECT, but now superseded by 5.5 (F5) |
| 5.2 Chain construction; Lemma V1; "Hence" list; in(f) table | CORRECT |
| 5.3 Theorem V | CORRECT (given Theorem 9.2) |
| 5.3 Per-sheet form | CORRECT WITH FIXES (F3) |
| 5.3 Size of kappa | CORRECT WITH FIXES (F1: the "kappa = -1" sentence is false as stated) |
| 5.4 V1-V4 and the table | CORRECT; naming fix (F4) |
| 5.5 Decomposition, G' >= 84 + \|U \ X\| | CORRECT (given Corollary 17.4 in the stated reading, which is what the proofs give) |
| 5.5 Borrower, x(f), the 84 form | CORRECT; precision fix (F8) |
| 5.5 Sole-event table (82, 82, 83, 83, 83, 82) | CORRECT |
| 5.5 One visible event gives >= 80, and >= 81 outside the stated exception; two give >= 77 | CORRECT |
| 6.1-6.3 Reading of the limits | CORRECT WITH FIXES (F5 stale after 5.5, F6 wording) |
| 6.4 Proposition M | CORRECT (minor, F10) |
| 0. Summary | CORRECT WITH FIXES (F5) |

Nothing found changes 75 <= L(MixColumns) <= 88.

## The fixes

- **F1 (5.3, last bullet of "Size of kappa"). The sentence is false as stated.** It says: "A visible event
  whose support avoids the own blocks of the sheets it reaches has kappa = -1." This fails when t(f) = 1.
  Take B(f) = {2,7} with J(f) = {3}. The support avoids block 3, yet in(f) = 1 and kappa = 0. The in(f)
  table already gives this value, so Theorem V is not affected. Only the remark is wrong.
  - *Counterexample, verified by direct evaluation* (`rv.py`, `kappa_counterexample`). Start from r88 and
    rebuild row (0,3) through new gates:
    - a1 = [2: s_0], u = a1 + x, v = x + w1, h = u + v (a hidden event that cancels 3);
    - k1 = h + x, k2 = x + w2, f = k1 + k2 (a visible event that cancels 3; its value is [2: s_0] + [7: s_0]);
    - e3 = [3: E_0], and the row is f + e3.

    Here x is an input of block 3 in the row, and w1, w2 are the row's block-7 inputs. The result is a
    reduced 97-gate MixColumns circuit with 1 visible event, 1 hidden event and Q = 6. In C', f's chain has
    exactly one gate in a family (F_3), so kappa(f) = 0.
  - *Replacement text:* "A visible event with A(f) empty has kappa = -1 if t(f) = 0, and kappa = 0 if
    t(f) = 1 (support {2,7}, 3 in J(f))."
- **F2 (4.2, anchored events).** The second consequence ("every visible event with three blocks has an
  operand in (E \ F) u Q") is true, but it does not follow from the anchored statement. A non-anchored
  event may have an operand in F. Derive it from Lemma W1 instead:
  - a three-block visible support equals W_1, W_3 or W_4 (Lemma S);
  - these are maximal cliques, so every c in C(f) is non-adjacent to some block of B(f).
- **F3 (5.3, per-sheet form).** In the definition of R_j, the j = 3 clause should read "those nonzero on
  both 2 and 7 *that have an event-free path to an output of sheet 3*". The identity
  |R_j| + sum of home in(f) = |F_j(C')| was confirmed with this reading on every circuit checked.
- **F4 (5.4 table).** Rename the column "84-form" to "direct (84 - sum(w - 2))". Section 5.5 now uses
  "84 form" for a different bound. Optionally add 5.5's form as a column. Its values are 84, 84, 81, 81,
  81, 77, 78, 497 for r88, r89, 783, 7451, 7651, 1451, 3001 and the witness (reviewer's computation).
- **F5 (statements made stale by 5.5).** Each of the following is still true but now weaker than what 5.5
  proves, or points to work that 5.5 has done:
  - Summary, "Consequences":
    - the sole-event values become 82 for sheets 1 and 3; 83 for sheets 4, 5, 6 and 7 and for sheets 0 and
      2 in general; 82 for the two exceptions;
    - "G <= 75 needs three" becomes "G <= 76 needs three".
  - 5.1, "Corollary 17.4 is not used in this section": add "see 5.5".
  - 6.1: "the sole-event profiles reach 81-82" becomes 82-83, and "at most 75 gates ... three" becomes 76.
  - 6.3, "Base 83" bullet: 5.5 resolves this by subtracting x(f).
  - 6.5, "Recover the 84": 5.5 does this, up to x(f).
- **F6 (6.1, "What is not assumed").** The list mixes non-assumptions with facts, and "Hidden events cost
  nothing" reads as if it were an assumption. Suggested text: "Not needed: a private payment per event; any
  reconstruction of hidden events (they are deleted and credited)."
- **F7 (2, relation to phase 11).** Lemma 1 is not literally a special case of Theorem G, since Theorem G
  always deletes Q. Suggested text: "With the same D, Theorem G's circuit is smaller than Lemma 1's by |Q|.
  D may also omit the hidden values, which strictly lowers K for the direct chains."
- **F8 (5.5, the exception for one visible event).**
  - State x(f) = (w_0 - 1) + [w_7 >= 1] for a sheet-1 borrower. This matched the count in C' on every
    circuit.
  - Add that "no credit" means C(f) = {7}, by Lemma W1, since 7 is the only common neighbour of 0 and 1.
    It also means |E \ F| + |Q| = 0.
- **F9 (4.4).** "Its ancestors include at least n gates" should read "T and its ancestors form at least n
  gates".
- **F10 (6.4).** Say that dead_e excludes e. Gates with no path to an output fall in dead_e vacuously;
  a minimum circuit has none.

## Notes on the main points

### 5.1: what Theorems 7.1, 9.1 and 9.2 use (item 1a, 1b)

- **7.1** fixes A as the output gates of sheet j together with their ancestors. Its only uses of A:
  - A is closed under operands;
  - after zeroing the inputs outside blocks a and b, every gate of A off D is free;
  - A contains a node for each of the four rows.

  A designated node per row satisfies all three. The local lemma (`tenth-gate/PROOF.md` Step 0) states that
  nothing is assumed distinct or nonzero. Duplicate values in C' are separate physical gates, and they only
  add to the families.
- **9.1** discards free gates and keeps the first B-gate for each restricted value. It assumes no
  distinctness. In an event-free circuit, the ancestors of the sheet-3 outputs lie inside {2,3,7}. Their
  non-free gates are exactly the B-gates (nonzero on 3) and the M-gates (zero on 3, nonzero on 2 and 7), so
  F_3 is exactly B u M. VISIBLE's description of F_3 matches 9.2.
- **9.2 disjointness** uses only that ancestors of sheet j lie inside W_j, and event-free gives this
  directly, since B(a + b) = B(a) u B(b) at every non-event.
- Therefore G' = sum |F_j| + U >= 83 + U holds for every event-free circuit with designated outputs.
  Reducedness is not needed.

### 5.2, Lemma V1 and kappa (items 1c-1g)

- **Descendants of chain gates.** D reads only inputs, and retained gates read inputs, nodes of F or
  earlier retained gates. A chain gate therefore reaches only its own later gates, f's node and the
  retained gates reachable from f through retained gates. In C those retained paths are exactly the
  event-free continuations of f.
  - `rv.py` checks directly that every chain gate reaches exactly the sheets J(f).
  - It also checks that every retained image reaches exactly J of its retained gate.
- **Own-block property.** The check found no j != k with j in W_k and k in W_j. At most one own block of
  J(f) lies in B(f), by Lemma S.
- **Where A(f) can be when t(f) = 1.** Then A(f) is 3 or empty: A = 2 would force B(f) into {2}, and A = 7
  would force it into {7}.
- **in(f) table and kappa range.** Re-derived by hand, giving -1 <= kappa <= min(4, w - 2). kappa = 4
  happens only with t = 1 and w_3 = 4, and then B(f) = W_3 is a maximal clique, so a credit follows.
  Outputs have kappa 2, and sheet-3 outputs have 3; a sheet-0 output that also reaches sheet 1 still has
  kappa 2.
- **Count arithmetic.** G' = G - |E| - |Q| + K >= 83 + sum (w - 1 - in) rearranges to
  G >= 83 + |E \ F| + |Q| - sum kappa.
- **V1-V3.**
  - With one event, kappa <= 3 gives 80, and kappa = 4 brings a credit and gives 80.
  - With two events, two kappa-4 events may share one credit gate (a Q gate read by both), so the bound is
    83 - 8 + 1 = 76.
  - With kappa sum 7, one event has kappa 4 and brings a credit, giving 77.
  - V3 is right to allow sharing.
- **The 83 / 84 remark.** The off part of a sheet-1 output is [0: s_c] + [7: s_c], a diagonal vector. Its
  chain top is exactly the kind of gate that Theorem 17.3 counts as the 21st. So the 84 cannot simply be
  added to the chain slack, and the remark is right.

### 5.5 (the coordinator's additions)

- **(a) The decomposition.** Theorem B's proof (joint01 section 5) counts D_1 (the gates nonzero on
  block 1), C_0 (the ancestors of sheet 0) and, when |D_1| = 10, one diagonal gate outside C_0.
  - In an event-free circuit, D_1 = F_1 and C_0 = F_0. The extra gate is a gate of X: it is nonzero on 0,
    zero on 1, an ancestor of sheet 1 and not of sheet 0.
  - L_01 = F_0 u F_1 u X, and X meets no family. `rv.py` asserts both on every circuit.
  - Disjointness from F_2..F_7 follows from the windows.
  - No reducedness is used:
    - |D_1| >= 10 is the local lemma;
    - the (7,3) / (6,4) structure is Step 5 of the ten-gate proof;
    - the three independent entry operands are diagonal vectors of weight >= 4, so they are gates;
    - L >= 11 (Theorem A) is a minimum over all circuits, and its 10-gate case analysis derives
      distinctness rather than assuming it.

  Hence G' >= 84 + |U \ X|. The reviewer did not re-prove Theorem A's case analysis; it rests on its own
  review.
- **(b) Borrowers and x(f).**
  - For a borrower, t(f) = 0, and A(f) is 1 or empty.
  - The chain gates in X are the block-0 piece and the 0-7 join, together with f itself when A is empty.
    That gives x = (w_0 - 1) + [w_7 >= 1].
  - Sheet-1 outputs have x = 2.
- **(c) Tables and counts.**
  - **Sole-event table.** Recomputed from the row values (`tables()` in `rv.py`); the values match.
  - **One visible event.** A bound of 80 needs kappa - credit >= 3 and kappa + x - credit >= 4. The only
    solution is kappa = 3, no credit, and x >= 1. That forces a borrower with A = 1 and w_1 = 4. B(f) is
    then {0,1}, because {0,1,7} is a maximal clique and would bring a credit, and w_0 >= 2.
  - **Two visible events.** A bound of 76 or less under the 83 form needs kappa sum 8 with one shared
    credit. Then both events have t = 1 and x = 0, and the 84 form gives 84 - 8 + 1 = 77.

### Other checks (`rv_out.txt`)

- **Windows, graph, intersections, cliques.** All as stated.
- **The seven corpus circuits and the witness.** In each one, `rv.py`:
  - rebuilt C' independently and verified it is event-free, computes the map and has the size
    G - |E| - |Q| + K;
  - verified that the families are disjoint with sizes >= 10 / 13, and that in(f) and x(f) from the hand
    formulas equal the counts in C';
  - verified Lemma S, Lemma W1 at every non-adjacent pair, the clique property of anchored events, and that
    the backward traversal reaches exactly F u R.

  Every number in the 5.4 table and in 4.2-4.3 was reproduced (the witness has 36 credit operands, all in
  Q, and sum in = 100).
- **Tail family (n = 3, 5, 8).** One event; u lies in no window; the 2n-gate event-free circuit was built
  and verified; Theorem W holds with equality.
- **Converse of "event-free implies block-monotone".** Rewrite r88's output gate 74 = a + b as
  n1 = a + x, n2 = n1 + x, o = n2 + b. This gives a block-monotone circuit with one event (which cancels
  block 7). It is not reduced, because n2 duplicates a; the claim is only existential.
- **Proposition M.** The replacement circuit loses e and dead_e and gains w(e) - 1 event-free chain gates.
  Other gates keep their operand values, so the event count drops, and minimality gives w(e) >= 3 + |dead_e|.
  For the first event, Theorem P's repair also lowers the event count. Its size G + sigma_e must exceed G,
  so s_e + delta_e - 1 >= 1, which gives s_e >= 1.
