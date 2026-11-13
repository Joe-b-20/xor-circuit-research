# Visible cancellations (phase 12)

Main agent (Opus 5.5), 2026-11-13.
- **The user's.** The global repair refinement (section 2), the output-support consequences (section 3) and
  the sole-event window credit (section 4). They were verified here independently.
- **New.**
  - the tail family, showing that the window credit is sharp for general maps (4.4);
  - the family-slack repair, Theorem V (section 5), with its per-sheet form;
  - the reading of the limits (section 6);
  - Proposition M on minimal circuits (6.4).

Status words:
- **proved**: a hand argument;
- **check**: direct evaluation of specified objects (`visible.py`, output `visible_out.txt`). These are the
  eight output windows, the circuits named there and explicit constructions.

No SAT, enumeration, least-gate search or search over value sets was used, by the main agent or by the
reviewer. Machine review is in `review/REVIEW.md` (not human review, not formal verification).

Nothing here changes 75 <= L(MixColumns) <= 88, and nothing excludes an 87.

## 0. Summary

- **Only visible cancellations need rebuilding** (user's; proved).
  - Trace back from the outputs and stop at the first cancelling gate on each branch. The cancelling gates
    reached are the visible events F.
  - Everything not reached can be deleted once F is recomputed without cancellation: hidden events, and the
    work behind them.
  - Hence G >= B + |E| + |Q| - K, where B is the event-free bound and K the cost of recomputing F.
- **Visible events live inside output windows** (user's; proved).
  - They occupy at most 3 blocks, or at most 2 if they reach two sheets without a further event.
  - If they reach three or more sheets that way, they lie on block 7 alone.
- **Window credit** (user's; proved). An operand whose support lies in no window is never retained. With
  one event this gives:
  - G >= 80 for an event at a weight-7 output;
  - G >= 82 at a weight-5 output of sheets 5, 6, 7.
  - For general maps the credit is exactly one gate (tail family, new).
- **Theorem V (new; proved given Theorem 9.2).**
  - A visible event can be rebuilt mostly from gates that the 83-gate decomposition of Theorem 9.2 never
    counts.
  - Each visible event f therefore costs at most kappa(f) <= 4 against 83, whatever its weight:
    G >= 83 + |E \ F| + |Q| - sum kappa(f).
  - Equivalently, the retained gates plus at most five gates per visible event cover the 83. They cover
    each sheet's 10 (13 for sheet 3) separately.
- **Consequences of Theorem V** (any number of hidden events):
  - one visible event gives G >= 80;
  - a sole event at an output gives 82 (sheets 1, 4, 5, 6, 7) or 81 (sheet 3; sheets 0 and 2 in one case
    each);
  - G <= 79 needs two visible events;
  - G <= 75 needs three.
- **With the 84 form (5.5; also uses Theorem 17.3):**
  - a sole event at an output gives 83 (sheets 0, 2, 4, 5, 6, 7) or 82 (sheets 1, 3; sheets 0 and 2 in one
    case each);
  - G <= 76 needs three visible events.
- **Limit.**
  - The bound loses up to 4 per visible event.
  - When every output is itself a visible event (the superposition witness), the inequality constrains
    only the rebuilt chains and says nothing about G.
  - The theorem credits hidden work but derives no lower bound for it.

## 1. Definitions

- **Gates and events.** Blocks, windows W_j and sheets are as in RECORD 3 and 9. Each row has one
  designated output node; in a reduced circuit it is the unique node with that value. A gate e = a + b is an
  **event** if some block c has pi_c(a) = pi_c(b) != 0. Its cancelled blocks are C(e). E is the set of event
  gates, each physical gate counted once.
- **J(v).** For a node v, J(v) is the set of sheets j such that some designated output of sheet j is
  reachable from v along a path whose nodes after v are not events. The trivial path counts, so J(v)
  contains v's own sheet if v is an output.
- **The four classes.**
  - F: events with J nonempty (**visible**);
  - E \ F: events with J empty (**hidden**);
  - R: non-event gates with J nonempty (**retained**);
  - Q: non-event gates with J empty.

  These are the user's sets. A non-event gate is in Q exactly when every path from it to an output passes
  through an event; an event is visible exactly when some path from it reaches an output with no further
  event. Every gate lies in exactly one class.
- **Backward traversal.** Start at the outputs, expand non-event gates, and stop at events. The events
  reached are F, and the non-event gates reached are R.
- **Separation (proved).** Every path from a gate of (E \ F) u Q to an output passes through F: the last
  event on it has an event-free continuation. So F separates the hidden part H = E u Q from the outputs.
- **Support.** B(v) is the set of blocks on which v is nonzero, and w(v) its weight.

## 2. The global repair (user's; proved)

**Theorem G.** Let C be a circuit with designated outputs, and let D be a circuit that:
- reads only the inputs;
- has no events;
- has K gates;
- contains a node of value val(f) for every f in F.

Let C' consist of D, followed by the gates of R in their original order, each reference to f in F redirected
to D's node of value val(f). Then:
- C' is acyclic and has no events;
- it computes every required output;
- it has G - |E| - |Q| + K gates.

So for any lower bound B valid for event-free circuits of the map, G >= B + |E| + |Q| - K.

*Proof.*
- **Closure.** Let g in R read u.
  - If u is a non-event gate, the event-free continuation of g gives one for u, so u is in R. In particular
    no retained gate reads a gate of Q.
  - If u is an event, the path u -> g -> ... is event-free after u, so u is in F.
  - Otherwise u is an input.
- **Outputs.** A designated output is:
  - an input;
  - a non-event gate, which is in R by the trivial path;
  - or an event, which is in F by the trivial path.
- **Acyclicity.** D reads only inputs. A retained gate reads inputs, D, or earlier retained gates.
- **No events.** A retained gate keeps its original operand values, and being an event depends only on
  those, so it is not an event. D has none by hypothesis.
- **Count.** C' has |R| + K = G - |E| - |Q| + K gates. QED

**Points checked in the proof.**
- *Reducedness and liveness.* Neither is needed for the inequality. Dead gates have J empty and lie in Q or
  E \ F, so they are deleted and credited.
  - In a reduced circuit the values of F are distinct and nonzero, so D needs K <= sum over F of
    (w(f) - 1).
  - In a non-reduced circuit, a visible event of value 0 would need a node of value 0. A retained reader of
    such a node is a copy of its other operand and can be bypassed, so the count only falls. We state
    results for reduced circuits.
- *Duplicates and pruning.* Both are optional and only lower the count. Redirecting readers to an earlier
  node of the same value changes no operand value, so no event appears. An event-free gate is nonzero:
  equal operands would cancel a whole block.
- *Physical gates against values.* E, F and Q are sets of physical gates. D is asked for values. Two visible
  events with equal values need one node.
- *Internal values are not preserved.* The values of Q and of hidden events disappear; only the required
  outputs are kept.
- *Depth is not preserved.*
- *Relation to phase 11.* With the same D, the circuit of Theorem G is |Q| gates smaller than that of
  Lemma 1 of phase 11. Moreover D may omit the values of hidden events.

**Sequential form (proved).** Place f's gadget at f's position in C.
- The gadget may read inputs, retained gates before f, and gadget nodes of earlier visible events. It must
  not read Q or hidden events.
- The proof is the same, and acyclicity follows from the original order.
- K then counts the gadget gates.

**For MixColumns.**
- An event-free circuit is block-monotone in RECORD 7's sense: supports grow along every edge. The converse
  fails, because block-monotone circuits may cancel a block that a later gate restores.
- Corollary 17.4 therefore gives B = 84 for the repaired circuit. The 84 enters only through this
  transformation.
- The 80 of the charge identity G = 80 + E - R + U is a separate statement and is not changed.
- Rebuilding each visible value as a chain over its inputs gives K <= sum (w(f) - 1). Hence

      G >= 84 + |E \ F| + |Q| - sum over f in F of (w(f) - 2).

- Interacting events are handled globally: an event hidden behind later events is deleted, not rebuilt.

## 3. Where visible events live (user's; proved)

**Lemma S.** If v is in F u R and j is in J(v), then B(v) lies in W_j.
*Proof.* Along the event-free continuation every gate is a non-event, and a non-event gate a + b has
B = B(a) u B(b). So supports grow from v to the output, whose support is W_j. QED

**The windows (check, against the matrix).**
- Windows: W_0 = {7,0}, W_1 = {0,1,7}, W_2 = {1,2}, W_3 = {2,3,7}, W_4 = {3,4,7}, W_5 = {4,5}, W_6 = {5,6},
  W_7 = {6,7}. Every row of sheet j has support exactly W_j.
- Row weights: 5 or 7, with weight 3 on the sheet's own block j and 2 on each other block.
- Pairwise intersections have at most 2 blocks: {0,7} for sheets 0, 1 and {3,7} for sheets 3, 4. All the
  others have one block or none.
- Every nonempty intersection of three windows is {7}.

**Consequences (proved).** Let f be in F.
- B(f) has at most 3 blocks, so w(f) <= 12.
- If J(f) contains two distinct sheets, then B(f) lies in their window intersection, which has at most two
  blocks.
- If J(f) contains three or more distinct sheets, then B(f) lies in {7}.

These statements are about event-free continuations only. A visible event may still reach other sheets
through later events, and nothing here confines all its uses to one sheet. The same holds for every retained
gate.

**Principle N (proved).** A gate whose support lies in no window has J empty, by Lemma S. So it is in Q, or,
if it is an event, in E \ F. Such a gate is never rebuilt: in particular, a heavy internal event outside every
window is hidden and is deleted.

**Own-block property (check by inspection of the eight windows).** There are no sheets j != k with j in W_k
and k in W_j. Hence (proved) at most one own block of the sheets in J(f) lies in B(f). Two would lie in each
other's windows, because B(f) lies in both.

## 4. The window credit (user's; proved), and its limit for general maps

### 4.1 Co-occurrence graph

Join two blocks if some output contains both, that is, if some window contains both. This is the window
graph of RECORD 9 and 23:
- the edges 0-1, 0-7, 1-2, 1-7, 2-3, 2-7, 3-4, 3-7, 4-5, 4-7, 5-6, 6-7.

*Maximal cliques (hand).*
- Block 0 has neighbours {1,7}, block 5 has {4,6}, and block 6 has {5,7}.
- On {1,2,3,4,7}, the graph is the path 1-2-3-4 with 7 adjacent to all four.
- So the maximal cliques are {0,1,7}, {1,2,7}, {2,3,7}, {3,4,7}, {4,5}, {5,6} and {6,7}.
- `visible.py` checks that these are cliques, are maximal, and cover every edge.
- {1,2,7} is the triangle of RECORD 9; it is a clique but lies in no window.

Windows W_1, W_3, W_4, W_5, W_6 and W_7 are maximal cliques. W_0 extends by block 1 and W_2 by block 7
(check).

### 4.2 The credit

**Lemma W1 (proved).** Let f = a + b be a visible event. Suppose c in C(f) and b' in B(f) are not adjacent.
Then the operand containing b' also contains c, its support lies in no window, and it is a gate of
(E \ F) u Q.
*Proof.*
- Both operands contain c.
- Some operand contains b', since b' is in B(f), which lies in B(a) u B(b).
- {b', c} lies in no window, so Principle N applies.
- The operand has two blocks, so it is not an input. QED

**Anchored events (proved).** Suppose both operands of a visible event f are inputs or retained gates. Then
B(f) u C(f) is a clique:
- each operand's support lies in a window (Lemma S), and contains every block of C(f);
- each block of B(f) lies in one of the operands;
- B(f) itself lies in a window.

For MixColumns this gives: an anchored visible event has at most two blocks.

Separately, by Lemma W1, every visible event with three blocks has an operand in (E \ F) u Q. Its support is
W_1, W_3 or W_4, and each of these is a maximal clique. (This does not follow from the anchored statement: an
operand may itself be visible.)

In `circuits_3.txt` line 3001 both visible events are anchored: B u C = {1,2,7} for one and {0,1,7} for the
other (check).

### 4.3 Sole event (user's; proved)

**Theorem W.** Let C be reduced and fully live with exactly one event e. Then:
- e is visible;
- every non-event gate is in R or Q;
- if some c in C(e) is not adjacent to some block of B(e), then |Q| >= 1.

With K = w(e) - 1 this gives G >= B - (w(e) - 3).

The condition holds whenever B(e) is a maximal clique: otherwise B(e) u {c} would be a clique.

**For a sole event at a MixColumns output** (with 84 as B):
- sheets 1, 3, 4 (weight 7): 80;
- sheets 5, 6, 7 (weight 5): 82;
- sheet 0: 82 unless C(e) lies in {1}, then 81;
- sheet 2: 82 unless C(e) lies in {7}, then 81.

The two exceptions are exactly the extensions found in 4.1.

**For the familiar triangle** (event at a sheet-1 output, cancelled block 2):
- the operand containing block 0 also contains block 2;
- no window contains {0, 2};
- so that operand is private, and the bound is 80.

In the three single-event corpus circuits the private operand is the only gate of Q (check).

**Several events.**
- The credit operand may itself be a hidden event, not a gate of Q.
- One gate can serve as credit operand for several visible events, so only distinct gates are credited.
- The superposition witness has 36 distinct credit operands for 32 visible events (check).

### 4.4 The tail family: the credit is exactly one gate for general maps (new; proved)

**Construction.**
- Inputs: x, y_1..y_n and z (n >= 3), each its own block.
- Outputs: p_i = x + y_1 + ... + y_i (i = 1..n), and T = y_1 + ... + y_n + z.
- Circuit: the chain p_1, ..., p_n, then u = p_n + z, then T = u + x. That is n + 2 gates, with the single
  event T, which cancels x.

**Separation holds.** T's support is {y's, z}, and it is a maximal clique: x and z never co-occur in an
output. So u is private.

**Event-free minimum is 2n.**
- In an event-free circuit, supports grow, so every ancestor of T avoids x.
- T has weight n + 1, so T and its ancestors form at least n gates: a gate DAG reaching k inputs has at
  least k - 1 gates.
- The n outputs p_i are distinct gates containing x, so they are not among those ancestors.
- 2n is attained (check, n = 3, 5, 8): q_i = y_1 + ... + y_i, then T = q_n + z, then p_i = x + q_i.

**So** the saving is n - 2 = w(T) - 3, and Theorem W holds with equality. Support growth and the
co-occurrence graph alone give exactly one gate beyond the direct repair.

**Controls.**
- The prefix family of phase 11 has windows. What it lacks is separation: T's support together with x is
  the window of p_n. So x co-occurs with every block of T, and no credit arises.
- For Q_3 the co-occurrence graph is complete on its three blocks, so no event is ever separated (check).

## 5. Theorem V: rebuilding off the charged families (new)

### 5.1 The ingredient: Theorem 9.2 with its slack

**Definitions.**
- An event-free circuit, with one designated output node per row.
- F_j: gates nonzero on block j that are designated outputs of sheet j or ancestors of one (along wires).
- F_3 also contains the ancestors of sheet 3 that are nonzero on both block 2 and block 7.

**What the proofs give.** The proofs of Theorem 7.1, Theorem 9.1 and Theorem 9.2 (RECORD 7 and 9) give:
- |F_j| >= 10 for every j, and |F_3| >= 13;
- the eight families are pairwise disjoint.

Hence

    G' >= 83 + U,    U = the number of gates in no family.

**Hypotheses used (checked against the recorded proofs).**
- The proof of 7.1 takes A = the outputs of sheet j and their ancestors. It applies the local lemma, which
  allows zero and repeated values. So any designation of one node per row works, and reducedness is not
  needed.
- Disjointness uses only that supports grow towards the designated outputs.
- Status: proved given the local lemma, which has a hand proof (RECORD 10); machine review only.

**Why 83 and not 84.** The step from 83 to 84 (Theorem 17.3) supplies, in one case, an extra gate outside
F_0 u F_1: a diagonal entry operand of sheet 1 on blocks {0,7}. The rebuilt gates below can be exactly
such gates, so the 84 cannot simply be added to their count. Section 5.5 shows exactly which rebuilt gates
the 84 absorbs. Sections 5.1-5.4 do not use Corollary 17.4.

### 5.2 The construction

**The chain for a visible event f.**
- Let A(f) be the own block of J(f) that lies in B(f). By the own-block property there is at most one;
  A(f) may be empty.
- Let t(f) = 1 if 3 is in J(f) and B(f) contains both 2 and 7.
- Pieces: the part of f on each block, built as an in-block chain. A gate a + b inside one block, with a, b
  different and nonzero, never cancels the block.
- *If t(f) = 0:*
  - build the pieces off A(f) and combine them (the off part; each step joins disjoint supports);
  - build the A(f) piece;
  - add the two.
- *If t(f) = 1:*
  - build the block-2 and block-7 pieces;
  - add the block-3 piece (if any) to the block-2 piece, then add the block-7 piece.

Every step is event-free. The chain has w(f) - 1 gates.

**Lemma V1 (proved).** In C' = D followed by R, the chain gates of f lie in exactly those families F_j with
j in J(f) for which the gate is nonzero on block j, together with F_3 when 3 is in J(f) and the gate is
nonzero on both 2 and 7.
*Proof.*
- A chain gate's descendants in C' are later chain gates, f's node, and the images of retained gates
  reached from f through retained gates only. D reads nothing retained.
- Those retained paths are exactly the event-free continuations of f in C.
- So the designated outputs below a chain gate are those of the sheets in J(f). QED

**Hence (proved).**
- A chain gate lies in a family only if it has content on A(f), or t(f) = 1 and it has content on both 2
  and 7.
- All such gates lie in the one family F_A(f) (F_3 when t(f) = 1).
- The others lie in no family.
- The number of chain gates in a family is

      in(f) = w_A          if A(f) and the off part are both nonempty,
              w_A - 1      if f lives on A(f) alone,
              0            if A(f) is empty and t(f) = 0,
              w_3 + 1      if t(f) = 1 and w_3 >= 1,
              1            if t(f) = 1 and w_3 = 0,

  where w_A is the weight of f on A(f) and w_3 its weight on block 3. Put kappa(f) = in(f) - 1.

### 5.3 The theorem

**Theorem V (proved given Theorem 9.2).** For every reduced MixColumns circuit,

    G  >=  83 + |E \ F| + |Q| - sum over f in F of kappa(f).

Equivalently, |R| + sum over F of in(f) >= 83: the retained gates and the charged chain gates cover the 83.

**Per-sheet form.** Let R_j be the retained gates that are nonzero on block j and have an event-free path to
an output of sheet j. For j = 3, add the retained gates nonzero on both 2 and 7 that have an event-free path
to an output of sheet 3. Then

    |R_j| + sum of in(f) over the visible f with home family j  >=  10    (13 for j = 3).

The home family of f is the family of A(f), or F_3 when t(f) = 1.

*Proof.*
- Apply Theorem G with D the chains of 5.2.
- C' is event-free with G - |E| - |Q| + K gates, where K = sum (w(f) - 1).
- By Lemma V1, sum (w(f) - 1 - in(f)) chain gates lie in no family. So 5.1 gives
  G - |E| - |Q| + K >= 83 + sum (w(f) - 1 - in(f)), and rearranging gives the theorem.
- The family of a retained gate in C' is determined by its retained (event-free) descendants, which gives
  the per-sheet form from |F_j| >= 10 and |F_3| >= 13. QED

**Size of kappa (proved).** -1 <= kappa(f) <= min(4, w(f) - 2).
- kappa(f) = 4 only if t(f) = 1 and w_3 = 4. Then B(f) = W_3 has three blocks and Lemma W1 gives a credit
  gate.
- kappa(f) = 3 needs either t(f) = 0 with w_A = 4 and a nonempty off part, or t(f) = 1 with w_3 = 3.
- Outputs have kappa = 2, except sheet 3 outputs, which have 3.
- If A(f) is empty, kappa = -1 when t(f) = 0: rebuilding f costs nothing against 83. When t(f) = 1,
  kappa = 0. (Review counterexample to an earlier wording: B(f) = {2,7}, J(f) = {3}.)

### 5.4 Consequences (proved given Theorem 9.2)

- **V1. One visible event** (and any number of hidden events) gives G >= 80.
  - kappa <= 4, and kappa = 4 comes with a credit gate.
  - The two-block cases with kappa = 3 and no credit also give 80.
- **V2. Sole event at an output.** Bound = 83 - kappa + credit:

  | sheet | weight | kappa | credit (4.3) | Theorem V | phase 11 direct | 4.3 (direct 84 - (w - 3)) |
  |---|---|---|---|---|---|---|
  | 1, 4 | 7 | 2 | 1 | **82** | 79 | 80 |
  | 3 | 7 | 3 | 1 | **81** | 79 | 80 |
  | 5, 6, 7 | 5 | 2 | 1 | 82 | 81 | 82 |
  | 0 (C not in {1}), 2 (C not in {7}) | 5 | 2 | 1 | 82 | 81 | 82 |
  | 0 (C = {1}), 2 (C = {7}) | 5 | 2 | 0 | 81 | 81 | 81 |

- **V3. Number of visible events.**
  - G <= 79 needs at least two visible events.
  - Two visible events give G >= 76: kappa sums to at most 8, and a kappa-4 event brings a credit, possibly
    shared.
  - So G <= 75 needs at least three visible events.
- **V4. Hidden work is bounded in cheap circuits:** |E| + |Q| <= G - 83 + sum over F of in(f).

**Checks (`visible_out.txt`).** For each circuit the program builds C' explicitly and verifies:
- it computes the map and has no events;
- its size is G - |E| - |Q| + K;
- its eight families are disjoint, with sizes at least 10 and 13 (as the theorem requires);
- every chain has exactly in(f) gates in families, all in the home family;
- no chain gate repeats a row value.

| circuit | G | E: visible / hidden | R / Q | kappa | direct 84 - sum(w - 2) | Theorem V | 84 form (5.5) | this circuit (83 + U - overhead) |
|---|---|---|---|---|---|---|---|---|
| r88, r89 | 88, 89 | 0 / 0 | all / 0 | - | 84 | 83 | 84 | 84, 86 |
| circuits_2 783, circuits_3 7451, 7651 (sole triangle event) | 88 | 1 / 0 | 86 / 1 | 2 | 80 | 82 | 81 | 85, 84, 86 |
| circuits_3 1451 (triangle event plus a {0,1} event reading it) | 88 | 2 / 0 | 85 / 1 | 2, 2 | 76 | 80 | 77 | 81 |
| circuits_3 3001 (two anchored events) | 88 | 2 / 0 | 86 / 0 | 2, 2 | 77 | 79 | 78 | 79 |
| superposition witness | 521 | 32 / 0 | 0 / 489 | 28 x 2, 4 x 3 | 453 | 504 | 497 | 504 |

In the triangle circuits, sheet 1's family in C' has 7 retained gates and 3 chain gates. The event takes
over three of sheet 1's ten charged gates and none of any other sheet's.

### 5.5 The 84 form (proved given Corollary 17.4, read as below)

**The decomposition.** The proof of Corollary 17.4 counts three disjoint parts of an event-free circuit:
- F_2, F_5 and F_6, at least 30 gates;
- the local circuit L_01 of Theorem 17.3, at least 21 gates;
- F_7, F_3 and F_4, at least 33 gates.

L_01 consists of the ancestors of sheets 0 and 1 that are nonzero on block 0 or block 1. It is F_0 u F_1
plus the set X of gates that are:
- nonzero on block 0;
- zero on block 1;
- ancestors of sheet 1;
- not ancestors of sheet 0.

X lies in no family. Hence

    G' >= 84 + |U \ X|.

**Chain gates in X.** A chain gate of f lies in X only if:
- 1 is in J(f);
- 0 is not in J(f);
- the gate has content on block 0 and lies off the families.

Call a visible event with 1 in J(f), 0 not in J(f) and 0 in B(f) a *sheet-1 borrower*, and let x(f) be its
number of chain gates in X (0 for every other event). With the chain of 5.2, x(f) = (w_0 - 1) + [w_7 >= 1]
for a borrower: the block-0 piece, plus the {0,7} combination when block 7 is present. Then

    G  >=  84 + |E \ F| + |Q| - sum over F of (kappa(f) + x(f)),

and Theorem V's 83 form also holds. Whichever is larger applies.

**Sole event at an output, both forms.**

| sheet | 83 form (Theorem V) | 84 form | bound |
|---|---|---|---|
| 1 (a borrower, x = 2) | 82 | 81 | **82** |
| 3 | 81 | 82 | **82** |
| 4 | 82 | 83 | **83** |
| 5, 6, 7 | 82 | 83 | **83** |
| 0 (C not in {1}), 2 (C not in {7}) | 82 | 83 | **83** |
| 0 (C = {1}), 2 (C = {7}) | 81 | 82 | **82** |

**Counts of visible events.**
- One visible event gives G >= 80 in every case. It gives G >= 81 unless the event is a sheet-1 borrower
  on {0,1} with weight 4 on block 1, weight at least 2 on block 0 and no credit, that is, C(f) = {7} (Lemma W1) and |E \ F| + |Q| = 0.
- Two visible events give G >= 77, so G <= 76 needs three visible events.

**Status.** This section uses Theorem 17.3 as a lower bound on all of L_01, the reading under which
Corollary 17.4 adds 21 to 30 and 33. Theorem 17.3 has hand proofs and machine review only, and its proof
goes through the pair proof of RECORD 15 and Theorem 17.2. Section 5.3 does not depend on it.

## 6. The main question: what the window structure forces

The question was how three things are related:
- (1) the cancellation values visible from the outputs;
- (2) the joint cost of reconstructing them without cancellation;
- (3) the original gates that become unnecessary.

### 6.1 What is established

- **(1) to (3).**
  - Only visible values need reconstruction (Theorem G).
  - The window structure forces deleted work wherever a visible event combines blocks that never share an
    output: every three-block visible event has a hidden operand.
  - Anchored visible events are confined to cliques of the co-occurrence graph.
- **(1) to (2): the aggregate mechanism (Theorem V).**
  - Measured against the charge families of the event-free bound, reconstruction is cheap. A visible event
    carries at most one own block of the sheets it reaches (own-block property), and the part of it off
    that block can be rebuilt by gates no family counts.
  - So each visible event costs at most 4 against 83, independent of its weight.
  - It costs only in the family of its own block, which is the per-sheet form.
- **Not needed:** a private payment per event, or any reconstruction of hidden events (they are deleted and
  credited).
- **Facts that the mechanism covers.**
  - A visible event may read another visible event (line 1451).
  - The heavy internal events that defeated the direct repair (weight up to 12) cost at most 4 like the
    others, or are hidden.
- **What it implies for MixColumns.**
  - The class bounds V1-V3 and 5.5. Every circuit with at most 79 gates has at least two visible events,
    and every circuit with at most 76 gates has at least three.
  - The sole-event profiles reach 82-83.

### 6.2 Hypotheses that remain essential

- **Theorem 9.2 and its proof structure.** Ten charged gates per sheet, thirteen for sheet 3, in pairwise
  disjoint families of an event-free circuit. The local lemma has a hand proof; all of it has machine review
  only.
- **Support growth along non-event gates.** This is why J(f) must be computed through event-free paths only:
  a path through a later event gives no support information.
- **The own-block property of the windows.** Without it a visible event could carry content charged to two
  sheets, and kappa would not be bounded by the weight on one block.
- **Separation in the co-occurrence graph,** for the credit. It fails in the prefix family and in Q_3.
- **Reducedness** is used only to count the chains (distinct, nonzero values).

### 6.3 Where it reaches a precise limit

- **Linear decay.** The bound loses up to 4 per visible event, so three or more visible events give nothing
  above 75.
- **The whole output set visible.** Then R is empty and the theorem reads sum in(f) >= 83. That is a fact
  about the chains alone, independent of G. In the superposition witness all 32 outputs are events, R is
  empty, and sum in(f) = 100.
  - In general, the content of Theorem V is |R| + sum in(f) >= 83, a lower bound on the retained part.
  - The hidden part enters only as a credit, one gate per gate.
  - When F is all of the outputs, rebuilding F is the original event-free problem, done here by brute
    chains (152 gates in the witness). Its only information is the slack U of those chains.
- **No lower bound on hidden work.** Nothing ties |E \ F| + |Q| to F beyond Lemma W1's single credit.
  Cheap circuits may in principle have many visible events with little hidden work behind them.
- **Base 83 or 84.** The 84 of Corollary 17.4 combines with the chain slack except for the rebuilt gates in
  X: block-0 gates of sheet-1 borrowers. Those can count towards Theorem 17.3's twenty-first gate (5.5).
- **Private chains.** Visible events with different J(f) cannot share chain gates without changing which
  families the shared gate joins. So joint reconstruction is not exploited.
- **The window credit is sharp for general maps** (tail family). kappa is not claimed sharp, and the
  sole-event bounds 81-82 are not claimed attained.

### 6.4 Conditioning on minimal circuits (Proposition M; proved)

Let C have minimum size, and the fewest events among minimum-size circuits.
- **Every event e has w(e) >= 3 + |dead_e|,** where dead_e is the set of gates other than e all of whose
  paths to outputs pass through e.
  - Replace e by a chain from the inputs and delete e and dead_e. The other gates keep their operand
    values, so the event count drops.
  - The size is G - 1 - |dead_e| + w(e) - 1, which must exceed G.
- **For the first event,** Theorem P of phase 11 gives an explicit repair with fewer events. So
  s_e + delta_e >= 2: the first event always has a shared carrier of its cancelled blocks whose clean
  projection is absent.

These constraints are local. Minimality pushes hidden work down, while the repair inequality gains from
hidden work, so conditioning does not by itself give a class bound. It is recorded as a structural fact
about optimal circuits.

### 6.5 Next direction

- **A lower bound on hidden work in terms of visible events.**
  - Theorem V reduces "below 80" to circuits with several visible events and little hidden work, and the
    per-sheet form says where the events must act. Each visible event replaces at most w_A + 1 <= 5
    charged gates of one sheet.
  - A sheet whose own block appears in no visible event keeps ten retained charged gates.
  - The natural question: if a sheet's family is mostly supplied by visible events, what must the hidden
    part (the gates behind those events) contain? Lemma W1 is the first instance.
- **Sheet-1 borrowers.** Their rebuilt block-0 gates are exactly where 83 and 84 differ.
- **Not recommended:**
  - per-event carrier lemmas (phase 11's Lemma L route);
  - "one event, then two" sequences;
  - bounds on s_e alone.

## 7. Review status

`review/REVIEW.md` is a machine review by a separate model instance, with its own code (`rv.py`). It is
not a human review and not a formal verification, and it used no search. It rebuilt every C' from
scratch.

**Verdicts.**
- CORRECT: Theorem G, Lemma S, Lemma W1, Theorem W, the tail family, Theorem V and section 5.5. For 5.5 the
  review confirmed that Theorem B of `joint01/` bounds all of L_01 and that neither it nor Theorem 17.3
  assumes reducedness. It did not re-prove Theorem A's case analysis.
- WRONG: one sentence (kappa = -1 when A(f) is empty; it is 0 when t(f) = 1).
- Wording and precision fixes F2-F10.

All fixes are applied above.
