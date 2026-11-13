# Feedback savings are bounded by entry rank

2026-11-13, continuing reviewed commit `edbe77f`. Hand proofs and independent machine
reviews, not formal verification or human certification. No circuit search was used.

The principal result is a general constructive bound on the benefit of feedback.
The relevant dimension is the span of the values entering the consumer, rather than
the dimension of the block later cancelled. The bound is sharp through dimension four.
The unrestricted MixColumns interval remains **75 to 88**; the previously proved
block-monotone lower bound **85** and no-feedback joint minimum **22** remain in force.

## A bound for the entire computation

Divide coordinates into a source and a consumer. All free values belong to the source.
An exit cancels the consumer part and returns a source value. Suppose all actual source
values entering consumer-bearing gates lie in a space of dimension at most `d`.

[Theorem FR](GENERAL_REPAIR.md) replaces every source-side value by a source-only
computation at an additional cost of at most

    h(d)=2^ceil(d/2)+2^floor(d/2)-d-2.

The full circuit can then run with its source computation first. The allowance is for
all feedback together, not per exit. For dimensions `0,1,2,3,4` it is `0,0,0,1,2`.
Zero is freely available, as it is in the joint model; this convention is explicit.

The proof maintains a chronological basis in two growing groups, and physically
computes all sums inside each group. Every return lies in the span of earlier entry
labels, so it is a sum of two already supplied group values. It consumes at most its
original one gate. A group of size `k` costs at most `2^k-1-k` extra gates in total.
The two groups stay balanced without moving any earlier basis element.

The dimension-three allowance is attained by a map with unrestricted minimum four
and no-feedback minimum five. At dimension four, another map has minima five and
seven. Both minima follow from short hand arguments and specified constructions.
No claim of sharpness is made in higher dimensions, and no literature novelty is
claimed for the basis-sum technique or the prefix examples.

## Feedback also pays for directions outside the target span

[Theorem FX](FEEDBACK_RANK.md) combines chronological span containment with entry
deletion. Let `D` span the source parts of the required consumer outputs, let `L_D`
be their minimum consumer cost with `D` free, and let `F` span all returned exit values.
Then the number `K` of consumer-bearing gates obeys

    K >= L_D + dim((F+D)/D).

For the two-sheet problem `L_D=10`. A ten-gate consumer can return only diagonal
values; an eleven-gate consumer can return at most one independent direction outside
the diagonal. The four first-sheet rows are independent modulo that diagonal. Returning
`k` of those rows directly as exits therefore requires at least `10+k` consumer gates.
This does not exclude rows built from exit ancestors by additional source-side gates.

## What the joint problem still needs

For exactly ten consumer-bearing gates, entry deletion puts all entry labels into
the three-dimensional diagonal. [R3](RANK_THREE.md) and the augmented minimum twelve
then force at least eleven source-side gates. At total 21, a source-only replay must
encounter an exit equal to the sum of exactly three independent available diagonal
values. A one-gate replacement, or a saving elsewhere that offsets its extra gate,
would give an impossible eleven-gate augmented supplier.

This is a necessary condition, not a proof that the exceptional exit is possible.
The extra structure of the four own triples may forbid it. A proposed shortcut using
double transposition has not identified the original physical pairs that cancel;
it is recorded as incomplete. In particular, eventual availability of a fourth entry
value cannot be substituted for its availability before an exit.

[Mirror exits](MIRROR_EXITS.md) give a complementary restriction: any mirror below
budget 22 must have an exit in a second-group output cone. With three exports,
its nonzero-first-part region needs at least thirteen gates and its zero-first-part
region has four or five gates. The latter is then strongly constrained. This does
not yet close the unrestricted joint problem.

The next useful step is to determine whether an optimal consumer can supply the
exceptional ternary return while still providing all four required rows. It should
use physical reader relations or a new structural invariant. Neither a free-feedback
normalization nor an exhaustive classification is justified by this pass.

## Why general normalization fails

[ONE_EXIT](ONE_EXIT.md) adapts the earlier attributed prefix mechanism with private
coordinates. It gives an eight-output map with four outputs on each side, independent
weight-five rows, boundary relation distance six, blocks of size at most three, and
windows meeting at most three blocks. Its unrestricted minimum is 21; forbidding
consumer feedback into first-side cones raises the minimum to 22. Only one exit from
a one-bit consumer block is used. Thus those coarse features cannot make feedback
removable for free. The map is rectangular and its first-side rows differ from
MixColumns, so it is not a counterexample for that specific target.

## Review and verification

Independent reviews cover [general repair](reviews/general-repair-review.md),
[exit-rank cost](reviews/feedback-rank-review.md), [rank three](reviews/rank-three-review.md),
[the decorated separation](reviews/one-exit-review.md), and
[mirror restrictions](reviews/mirror-review.md). The primary agent checked the span
invariants, chronology, gate accounting, private-coordinate restrictions, and scope.

Run the fixed-construction verifier from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 research/takeover-2026-11-13/feedback/check_feedback.py
```

It evaluates six specified circuits: the 4/5 and 5/7 sharp small-rank pairs, and the
21/22 decorated pair. It checks masks, sizes, liveness, and feedback; the decorated
checks also verify output weights, rank, and event count. [Results](check-results.json)
are saved. Universal lower bounds and the boundary-distance statement are hand proofs.
