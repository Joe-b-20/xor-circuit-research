# Repairing whole-block cancellations (phase 11)

Main agent (Opus 5.5), 2026-11-13. The joint repair lemma, the direct repair and the sharpness family are the
user's; they were verified here independently. The sequential and projection repairs (sections 1.2 and 4) are
new.

Status words:
- **proved**: a hand argument;
- **check**: direct construction and evaluation of specified circuits (`repair.py`, output `repair_out.txt`).
No SAT, no exhaustive or finite-family check, no case enumeration and no least-gate search was used, by the main
agent or by the reviewer. Machine review is in `review/REVIEW.md` (not human review, not formal verification).

Nothing here changes 75 <= L(MixColumns) <= 88, and nothing excludes an 87.

**Phase-12 note (2026-11-13).**
- `visible/VISIBLE.md` refines this account:
  - only visible events need rebuilding;
  - the class bounds below are improved: a sole event at a weight-7 output gives 81-82, not 79.
- Statements of this file that were overstated are corrected in place: sections 0, 3, 4 (table and the
  paragraph after it), 5, 6 and 7.

## 0. Summary

- **Repair inequality.** A circuit with whole-block cancellations can be turned into one without them by
  recomputing only the cancelling gates' values. If B is the known lower bound for circuits without
  cancellations, the original circuit satisfies G >= B + |E| - K. Here E is the set of cancelling gates and K
  is the cost of the explicit recomputation. For MixColumns, B = 84.
- **Direct repair.** It gives G >= 84 - sum (w(e) - 2). Hence a circuit whose only cancellation is at a weight-7
  output has at least 79 gates, and at a weight-5 output at least 81.
- **Sharpness.** For general maps one cancellation can save w - 2, without bound.
- **Projection repair** (new). The saving of a cancellation is limited by the cancelled content that sits in
  *shared* ancestors whose clean versions are absent. Cancelled content that is private to the event costs
  nothing to remove.
- **Where the formula is exact (corrected in phase 12).** Theorem P's formula equals the explicit projection
  overhead in the following cases:
  - the prefix family;
  - the three single-event triangle circuits (2);
  - each step of Q_3's sequential repair (2, 2, 2, 3).

  It is only an upper bound elsewhere. Each term s_e + delta_e - 1 is at least -1, while the 32-event
  superposition witness has projection overhead -322 (-324 in the reviewer's order). Pruning there removes
  dominated work that the formula does not count.
- **What is not achieved here.** No class bound better than the direct one is proved in this file for any
  event profile of MixColumns. Phase 12 proves some (`visible/VISIBLE.md`).

## 1. The repair lemma (user's; verified)

A gate e = a + b is an **event** if some block c has pi_c(a) = pi_c(b) != 0; equivalently, B(a) u B(b) contains
a block that B(e) misses. Whether a gate is an event depends only on the values of its operands. Let E be the set
of event gates. Each physical gate is counted once, however many blocks it cancels.

**Lemma 1 (joint repair; proved).** Let C be a reduced circuit with G gates. Let D be a circuit that:
- reads only the inputs;
- has no events;
- computes every value val(e), for e in E;
- has K gates.

Then there is a circuit with no events, computing everything C computes, with at most G - |E| + K gates.

*Proof.* Put D first. Then keep the non-event gates of C in their original order, and point every reference to
an event e at the node of D with value val(e). A retained gate has its original operand values, so it is still
not an event, and D has no events by hypothesis. There are G - |E| retained gates and K gates of D.

Two normalisations only lower the count, and both keep the property:
- *Duplicate reuse.* Redirecting the readers of a node to an earlier node of equal value leaves every operand
  value unchanged, so no gate becomes an event.
- *Dead-gate pruning.* It removes gates and changes nothing else.

An event-free gate never has value 0: equal operands would cancel a whole block. It can have the value of an
input, after a partial cancellation inside one block; that is a duplicate, removed by reuse. QED

**Compatibility with the recorded 84.** In an event-free circuit, block supports grow along every edge. So every
ancestor's support lies inside each descendant's, and the circuit is block-monotone in RECORD 7's sense. There
Corollary 17.4 gives at least 84 gates for MixColumns.
The implication goes one way only. Block-monotone circuits may have events, for example a cancelled block that a
later gate restores. The repair needs only the implication into the class that the 84 covers.
- The repaired circuit may in any case be taken reduced and fully live, since normalisation preserves
  event-freeness; so whatever reducedness the local proofs use is available.
- Its status is "proved given Theorem 17.3 and the decomposition of RECORD 9", with hand proofs that have had
  machine review only.
- 84 enters only through an actual transformation into the class that theorem covers. The baseline of the
  80-charge identity G = 80 + E - R + U stays 80.

**Theorem 1 (proved).** For every reduced MixColumns circuit C (lower bounds may assume reducedness: reduce
first) and every D as in Lemma 1,

    G(C) >= 84 + |E| - K.

The statement holds at every size. Depth is not preserved.

### 1.2 Sequential repair with reuse (new; proved)

Gadgets may also read the nodes that already exist at the position of the event they replace.
- Process the gates in order, and replace each event e by a gadget: event-free gates that compute val(e).
- A gadget may read inputs, retained gates earlier than e, and gadget nodes of earlier events.
- **Availability.** These nodes precede e in the new order and carry their original values; the gadget reads
  nothing later, so no cycle arises. Retained gates are unchanged, so they are still not events.
- **Count.** The result has at most G - |E| + sum K_e gates, where K_e counts the gadget's new gates.
- **No double counting.** A gadget node that a later gadget reads is one gate, and duplicate values are reused.
- Lemma 1 is the special case in which every gadget reads only inputs and other gadget nodes.
- **Notation.** sigma = G' - G is the overhead of an explicit repair, where G' is the size after pruning. Then
  G >= 84 - sigma. sigma is negative when the repair also removes waste.

## 2. Direct repair (user's; verified)

Let w(e) be the weight of val(e) in the input basis; w(e) >= 2 by reducedness. Build val(e) as a chain over its
w(e) inputs, each step adding an input not yet present. Each step joins disjoint supports, so it is event-free.
Hence K <= sum (w(e) - 1), and:

**Theorem 2 (proved).** G >= 84 - sum over e in E of (w(e) - 2).

MixColumns rows have weight 5 (sheets 0, 2, 5, 6, 7) or 7 (sheets 1, 3, 4) (check). Consequences:
- **Sole event at a weight-7 output** (sheets 1, 3, 4): G >= 79. In four of the five corpus lines the triangle
  event sits at a weight-7 output (sheet 1). So the "84 - s" target of phase 10 holds with s = 5 for every
  circuit whose sole event is at a weight-7 output, with no triangle-specific assumption. It does not cover
  every triangle event: in circuits_3.txt line 3001 the triangle event is an internal weight-5 gate, and a sole
  internal event of weight w gets only 84 - (w - 2).
- **Sole event at a weight-5 output:** G >= 81.
- **Any number of events, all of weight 2:** G >= 84.
- **G <= 78** forces sum (w(e) - 2) >= 6. So such a circuit has at least two events, or one event of weight
  at least 8. Outputs have weight at most 7, so that event is not at an output.
- **G <= 80** with a single event forces w >= 6, so the event is not at a weight-5 output.

**Scope.** These results are for circuits with the stated event profiles. They do not raise the unrestricted 75,
since a circuit with 75-83 gates may have events with sum (w - 2) >= 84 - G. They say nothing about 84-88.

## 3. Sharpness family: one cancellation can save w - 2 (user's; verified)

**Attribution added 2026-11-13.** This construction is the parameter-shifted matrix of
Boyar and Find, *Cancellation-free circuits: An approach for proving superlinear lower
bounds for linear Boolean operators*, Theorem 2 (2012), where it is attributed to Svensson.
See the [primary paper](https://arxiv.org/pdf/1207.5321). Its appearance here is not a claim
of a new separation family.

The construction:
- Inputs x, y_1, ..., y_n (n >= 2), each its own block.
- Required outputs p_i = x + y_1 + ... + y_i (i = 1..n) and T = y_1 + ... + y_n.
- p_1 = x + y_1 and p_i = p_(i-1) + y_i, then T = p_n + x: n + 1 gates.

This circuit has the following properties.
- There is exactly one event, T, which cancels x.
- Every gate is a required output, so the circuit is reduced and fully live.
- There are n + 1 distinct non-input outputs, so the circuit is optimal.

Event-free circuits need at least 2n - 1 gates.
- With no events, supports grow along edges, so no ancestor of T contains x.
- The ancestors of T compute a weight-n vector with growing supports, which takes at least n - 1 gates, all
  free of x.
- These gates are disjoint from the n output gates p_i, which contain x. Hence at least 2n - 1 gates.
- The bound is attained: q_i = y_1 + ... + y_i for i = 2..n (n - 1 gates, with q_n = T), then p_1 = x + y_1 and
  p_i = x + q_i (n gates).

So the saving is exactly n - 2 = w(T) - 2, and Theorem 2 is sharp for general maps.
*Check:* for n = 2, 3, 5, 8, 12 (only these), the direct and the projection repair both return 2n - 1 gates
(sigma = n - 2).

**What it teaches.**
- No penalty that depends only on the number of events, and not on the dimension, is possible for general maps.
- The saving is large because the cancelled component x sits in every shared partial sum, and no x-free partial
  sum exists.
- Any proposed general bound must be compatible with this saving. It need not be exact on the family unless
  exactness is claimed. Both repairs below are exact here.
- The family does have output windows: p_i on {x, y_1..y_i}, T on {y_1..y_n}. What it lacks as a control is
  separation: T's support together with the cancelled x lies in the single window of p_n. So x co-occurs with
  every block of T, and no operand is forced outside the windows (phase 12, section 4).
- It does not rule out a stronger MixColumns-specific theorem.

## 4. Projection repair: only shared cancelled content costs (new)

**Lemma Z (zeroing preserves event-freeness; proved).** Let u + v be a gate that is not an event, and let P zero
a set C of blocks. Then either one of P(u), P(v) is 0, or P(u) + P(v) is not an event.
*Proof.* Suppose pi_d(P u) = pi_d(P v) != 0. Then d is not in C, so pi_d(u) = pi_d(v) != 0, and u + v would be
an event. QED

So P(u) = P(v) != 0 cannot occur, and zeroing an event-free circuit leaves an event-free circuit once the
trivial gates are dropped.

**Theorem P (projection gadget; proved; corrected in review).** Let the current circuit be reduced and fully
live, and let e = a + b be its first event, so that its ancestors are event-free. Let C = C(e) be its cancelled
blocks and P the map that zeroes C.

*Construction.* Build P(u) recursively over e's ancestors:
- P(u) = u if u has no content on C;
- reuse a node *before e* whose value equals P(u), if one exists (a later node may descend from e);
- drop P(u) if it is 0;
- otherwise create the gate P(u1) + P(u2) from the projections of u's operands.
Then set e' = P(a) + P(b), or the nonzero one of them if the other is 0. Since e is zero on C, P(e) = val(e).
By Lemma Z every new gate is event-free. The final gate is event-free too: a block d outside C with equal
nonzero parts would be cancelled by e itself.

*Count.* Call an ancestor u of e **dominated** if every path from u to an output passes through e; otherwise u
is **shared**. Let
- s_e = the number of shared *gate* ancestors u of e with content on C whose projection P(u) is nonzero and is
  not the value of any node *other than e*;
- delta_e = 1 if both operands have content outside C, and 0 otherwise.
Then the gadget followed by normalisation has overhead

    sigma_e <= s_e + delta_e - 1.

*Proof.* Each C-carrying ancestor adds at most one gate, and only when P(u) is not the value of a node before e;
the final gate is added only when delta_e = 1. Every new gate is offset by a death, except those counted by s_e
and the final gate:
- (i) e itself dies;
- (ii) every dominated C-carrier dies. Its readers are e, or ancestors of e, which carry content on C (e's
  ancestry is event-free, so supports grow along it) and are again dominated; a dead reader is excluded because
  the circuit is fully live. No gadget node carries content on C, so none reads it;
- (iii) every node after e whose value equals a new gadget node's value dies as a duplicate. These nodes are
  distinct, and they are neither dominated nor e.
What remains is at most s_e new gates from shared ancestors, plus delta_e, minus 1 for e. QED

*Why "other than e" matters (review, example A1).* Take inputs x, y, z as separate blocks and outputs g1 = x + y,
g2 = g1 + z, e = g2 + x = y + z. If val(e) counted as present, s_e = 0 and delta_e = 0 would give a bound of -1,
that is, a 2-gate event-free circuit, but 3 distinct non-input outputs need 3 gates. Steps (iii) and the
normalisation between events were missing from the first version of the proof (review, gaps (a) and (b)).

Combined with Theorem 2, the saving of e below the event-free baseline is at most min(w(e) - 2, s_e + delta_e - 1).
For several events, repeatedly repair the first event of the current circuit and normalise it again; each
event's quantities are taken in the current circuit, and the overheads add.

**Interpretation.**
- Removing a component costs only where that component sits in *shared* values whose clean versions are absent.
- Cancelled content that is private to the event (dominated) is stripped at no cost.
- At the level of one event, this is an oracle-free answer to phase 9's question about removing unwanted
  components from shared values.
- In the prefix family, s_T = n - 1 (p_2, ..., p_n; P(p_1) = y_1 is an input, and P(p_n) = val(T) is not counted
  as present) and delta_T = 0, giving n - 2. This is exact, since the lower bound 2n - 1 is proved.

**Check (repair.py, explicit repairs, each verified to compute the map with no events).**

| circuit | G | events | sum(w-2) | sigma: direct / projection | resulting statement for this circuit |
|---|---|---|---|---|---|
| prefix family, n = 2, 3, 5, 8, 12 | n + 1 | 1 | n - 2 | n - 2 / n - 2 | exact |
| circuits_2.txt line 783, circuits_3.txt lines 7451, 7651 (triangle event only) | 88 | 1 | 5 | 4 / 2 | G >= 82 |
| circuits_3.txt lines 1451, 3001 (triangle event plus a {0,7} exit) | 88 | 2 | 9, 7 | 8, 7 / 5, 5 | G >= 79 |
| r88, r89 | 88, 89 | 0 | 0 | 0 / 0 | G >= 84 |
| superposition witness (block order) | 521 | 32 | 120 | -375 / -322 (-324 with the reviewer's order of processing) | the direct repair has 146 gates; the projection repair has 199 (197 in the reviewer's order) |
| Q_3 (q3_28; event-free baseline 30) | 28 | 4 | 13 | 11 / 9 | G >= 21 (weak; Q_3 lies at least 2 below the bound 30) |

With the definition above, the formula s_e + delta_e - 1 equals the explicit projection overhead in these
cases (review, own code; `repair.py` also checks it):
- the three single-event triangle circuits give 2, against w - 2 = 5. In line 783 the shared carriers with
  absent projections are two {1,2} gates, and delta_e = 1.
- Q_3's four events give 2, 2, 2, 3, per step of the sequential repair.
- The prefix family gives n - 2.

Elsewhere it is only an upper bound (corrected in phase 12):
- **Two-event lines 1451 and 3001.** The formula was evaluated for the first event only (2), against a
  total overhead of 5.
- **Superposition witness.** Every term is at least -1, so the formulas sum to at least -32, while the
  measured overhead is -322 (-324). The difference is extra pruning: after an event is replaced, its
  dominated ancestors without content on the cancelled blocks die as well. The proof counts only the deaths
  (i)-(iii).
(The first version of `repair.py` counted cancelled inputs and zero projections too, and reported 5 for the
triangle circuits.) These are statements about those circuits, which have 88 gates anyway, not class bounds.

## 5. What makes joint repair cheap or expensive

- **Cheap.**
  - The event's cancelled content is private (dominated), for example an uncharged partner used only by e.
  - The clean projections of the shared carriers already exist.
  - The pieces of val(e) are present, so a gadget reads them; reuse is always counted once.
- **Expensive.** The cancelled component runs through many shared values with no clean versions, as in the
  prefix family.
- **Several events.** Sequential repair handles events that interact: later gadgets read earlier gadget nodes.
  But the overheads add, and on Q_3 (4 interacting events) the repair overhead is 9, while Q_3 lies at least 2 below the event-free bound 30
  (the event-free minimum is unknown).
  So this method is weak for interacting events.
- **What MixColumns contributes.** Output weights are bounded (5 or 7), which caps the saving of an event at an
  output at 3 or 5. For events at internal gates no MixColumns feature enters these arguments. The prefix
  mechanism needs a heavy event whose cancelled block runs through many shared nodes with no clean versions; in
  MixColumns that can only be an internal, non-output value.
- **Beyond the direct bound.** Theorem P is a per-circuit improvement, with an explanation: only shared
  cancelled content costs.
  - Its formula is exact in the cases listed in section 4, which give 82 for the three single-event triangle
    circuits.
  - It is not a class bound. Class bounds above Theorem 2 come only in phase 12, by a different mechanism.

## 6. Open for unrestricted MixColumns

- 75 <= L <= 88 stands. A circuit with 76-83 gates must have events with sum (w(e) - 2) >= 84 - G. Nothing
  here excludes such circuits.
- (Phase 12: a sole event at a weight-7 output gives 82 for sheets 1 and 4, and 81 for sheet 3. This is
  proved without any control of s_e; see `visible/VISIBLE.md`.)
- Many events and heavy internal events are not controlled by any argument here.

## 7. Next direction (justified by Theorem P and the sharpness family)

**Main target as stated in phase 11, corrected in phase 12.**
- *Scope of s_e.* Within the estimate min(w(e) - 2, s_e + delta_e - 1), the only term that can fall below
  w(e) - 2 is s_e + delta_e - 1. Other estimates can improve the direct penalty differently, and phase 12
  does so by a different mechanism.
- *No bound on s_e, but none disproved.* No useful small bound on s_e has been established for any class.
  The review's statement that wasteful circuits with the same profile "can have any number of shared
  carriers" was not supported by a construction for a fixed reduced MixColumns class, and is withdrawn.
  Not having a bound is different from proving that none exists.
- *What a class statement would need.* For "every circuit whose sole event is at a sheet-j output has at
  least 84 - t_j gates, t_j < w - 2", the shared cancelled content would have to be matched by genuine
  additional slack beyond the applicable baseline. Membership in gates that the baseline already counts does
  not qualify.
- *Carriers need not be paid one by one.* Joint reconstruction, repeated clean projections and deleted
  original work must be allowed.

**A first step (Lemma L, carrier location; reviewer; proved).** Let e be the only event of a reduced circuit,
with val(e) a sheet-j row and cancelled blocks C, and let u be an ancestor of e with a path to an output o' of
sheet j' that avoids e. Then B(u) lies inside (W_j u C) n W_j', and every cancelled block that u carries lies in
W_j'. *Proof.* Supports grow along the event-free path from u to o', and along the event-free ancestry of e up
to its operands, whose block union is W_j u C. QED
For the triangle (j = 1, C = {2}) every shared carrier lies on blocks {1, 2} (serving sheet 2), on {2, 7}
(serving sheet 3) or on block 2 alone, as line 783 shows. s_e then counts the {1,2} and {2,7} carriers whose
pure-block-1 or pure-block-7 parts are not computed. The concrete local question is whether such an absent
clean part costs a gate in sheet 2's family F_2 or in the joint problem J_01 (RECORD 17).

**Control.** The prefix family has output windows but no separation (section 3). A MixColumns argument
must fail on it through a property MixColumns has and the family lacks.

**Second target (as stated in phase 11; superseded).** The two-event regime.
- G <= 78 forces it, unless there is a heavy internal event. Phase 12 shows instead that G <= 79 forces
  two *visible* events, whatever their weights.
- In the tested two-event circuits (lines 1451 and 3001: a triangle event plus a second event cancelling
  block 7) the second event resembles Lemma L with C = {7}. But Lemma L is proved for a sole event. In a
  two-event circuit it applies only to paths that avoid the other event, which has to be checked.

## 8. Corrections to phase 10 (brief; applied in `copies/COPIES.md`, RECORD 25, SUMMARY, CHECKPOINT)

- **Restriction statement.** The claim "an event gate is never removed when its cancelled block is zeroed" is
  false. Counterexample:
  - Take x in the cancelled block, and set a = x + y, b = a + z, e = b + x = y + z.
  - After x is zeroed, b and e both project to y + z, so e is removed as a duplicate of b.
  - The same mechanism appears in C3.
  - Embedded in MixColumns (check): x = x_(0,7), y = x_(1,0), z = x_(2,0), with e used in
    y_(0,0) = e + x_(3,0) + x_(0,7) + x_(1,7) and the other outputs computed by chains. This circuit has 148
    gates, is reduced and fully live, and has the single event e, which is removed when block 7 is zeroed.

  Correct statement: zeroing a cancelled block leaves the event's value unchanged, but an earlier projected value
  may become equal to it, making the event removable. The zero counts measured earlier are observations about
  those circuits.
- **C4 is kept.** It is a capacity result: k non-output gates can carry independent copies of rank k(k-1)/2,
  which is why linear partner charging fails.
- **Scope of the verdict.** It is not that no valid cost relationship exists. The examined copy formulations do
  not give the desired new MixColumns bound, and the repair lemma is a valid cost relationship.
- **Circuit dependence.** A theorem may use the structure of an arbitrary given circuit without knowing an
  optimum; that is not circular. Exemptions defined through an unknown optimal completion need further
  justification.
- **Theorem F** limits unconstrained counting of rank-one terms when the production and compatibility of the
  factors are ignored. It does not rule out every circuit-constrained single-cut argument.
- **Proposition R.** Its implication to an unconditional 76 is a proof obligation for that particular route,
  not a general impossibility ceiling or a proved hardness equivalence.

## 9. Review status

`review/REVIEW.md` (machine review with its own code; not human review, not formal verification; no search).
Verdicts: Lemma 1 and Theorem 1 CORRECT WITH FIXES (reducedness stated); 1.2, the compatibility with
Corollary 17.4, Theorem 2 and its numbers, the sharpness family and Lemma Z CORRECT; Theorem P CORRECT WITH
FIXES (definition of s_e, proof steps (ii)-(iii), normalisation between events; one reading of the first version
was false); the table reproduced. All fixes are applied above, including the triangle qualifier (line 3001), the
Q_3 wording, the trade-off form of the next target and the reviewer's Lemma L.
