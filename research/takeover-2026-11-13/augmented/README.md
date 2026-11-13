# The augmented gap closes; the block-monotone bound becomes 85

2026-11-13, continuing reviewed commit `a04558e`. Hand proofs with independent machine
review, not formal verification or human certification. No circuit search was used.

**New exact local results:** the augmented supplier minimum is twelve, and the joint
0/1 minimum under no feedback is 22. **New restricted MixColumns lower bound:** 85 for
block-monotone circuits, including event-free circuits. **Unrestricted MixColumns
remains 75 to 88.**

## Four rows plus three independent diagonals cost twelve

[Theorem A12](PROOF.md) resolves the former eleven-versus-twelve gap. With one ordinary
four-bit block and a separate block whose every vector is free, computing the four
first-sheet rows and exposing three independent even diagonal values needs at least
twelve XOR gates. The proof permits arbitrary intermediate cancellations. The recorded
twelve-gate event-free circuit attains the bound for one choice of diagonal basis.
The lower bound holds for every basis; a twelve-gate realization of every prescribed
basis is not claimed.

The proof does not depend on the preceding ten-gate supplier closure or on all diagonal
values being ancestors of rows. A short new relation-rank argument first rules out ten
and justifies even free labels at eleven. Seven distinct required own masks then leave
only three or four entry gates. Both possibilities are impossible.

The [three-entry argument](THREE_ENTRIES.md) forces at most two odd helpers. In its tight
case, two residue groups must each be connected through nonclean even values. That would
require two different values to have three pair representations, contrary to uniqueness
of the helpers' three-term named expansions.

The [four-entry argument](FOUR_ENTRIES.md) forces exactly three independent even own
masks and forbids even-only equations. With few odd helpers, valid pair sums have too
little independent relation rank. With three helpers, four required named-pair sums
would force the three clean diagonals themselves to be dependent. These are structural
population and dependency arguments, not a classification of candidate circuits.

The twelve-gate witness uses seven first occurrences and five entries. Its extra entry
is one way to pay the cost that the eleven-gate arguments prove unavoidable.

## Exact joint cost and the 85-gate consequence

[Theorem J22](CONSEQUENCES.md) combines A12 with the preceding ten-gate producer closure.
For the two-sheet problem with the shared block free, any computation in which no
first-sheet output ancestor carries the consumer's own block needs 22 gates. An
event-free 22-gate circuit attains this minimum. The proof allows other cancellations;
it is the stated feedback restriction that remains essential to the argument.

[Theorem M85](CONSEQUENCES.md#the-block-monotone-class) places that joint computation in
a physically disjoint family of MixColumns gates. The other charged families contribute
thirteen and five times ten, giving

    22 + 13 + 5*10 = 85.

Block-monotone here means that every ancestor of an output stays inside that output's
block window. It can include intermediate block cancellations. Event-free circuits
satisfy this condition, so they also need at least 85 gates. The proof explicitly checks
all overlaps; it does not assume that circuit costs add across arbitrary subproblems.

Generic repairs that produce event-free circuits may now use baseline 85. The projected
value inequality becomes `G>=85+|V minus P|-|P minus V|` under its original definitions.
Its correction can be negative. Historical charged-slack formulas retain their own
hypotheses; they are not all obtained by replacing an old number mechanically.

## Judgment and the next direction

The local augmented problem is settled. Further refinements of its event-free special
cases are no longer the main target. The next useful question is the cost of feedback:
can a first-sheet ancestor introduce the consumer block and later cancel it cheaply
enough to beat 22? The unrestricted local joint problem has not been closed by this
pass, and the unrestricted MixColumns lower bound has not increased.

The explanatory mechanism worth retaining is the distinction between valid pair sums
and independently executable equations. Odd-node relations can look plentiful while
sharing a common formal sum or closing an alternating cycle. Entry cost, residue
components, and those dependencies together force extra work. A feedback theorem should
track the actual new values and the relations they enable, rather than crediting each
cancellation or each hidden gate independently.

## Independent review and direct checks

Reviews cover [the three-entry branch](reviews/three-entries-review.md),
[the four-entry branch](reviews/four-entries-review.md),
[the consolidated proof and normalization](reviews/exactness-review.md), and
[the exact joint and disjoint 85-gate consequences](reviews/consequences-review.md).
The primary agent independently reconstructed the short ten-gate baseline, parity
projection, both entry branches, and the global disjointness argument.

Run the direct check from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 research/takeover-2026-11-13/augmented/check_witnesses.py
```

It evaluates the specified twelve-gate source and its 22-gate completion, checking all
required masks, diagonal rank, liveness, distinctness, event-freeness, and absence of
feedback into the first sheet. [Results](check-results.json) are saved. These checks
establish the displayed upper constructions; the universal lower bounds are hand proofs.
No SAT, enumeration of circuits or diagonal bases, or computer-driven case elimination
supplies any step of the proof.
