# Physical diagonal values close the ten-gate consumer case

2026-11-13, continuing reviewed commit `242ee0a`. Hand proofs and independent machine
reviews, not formal verification or human certification. No circuit search was used.

The joint minimum is now **22 whenever the consumer uses ten gates**, allowing feedback
into the first-sheet outputs. The proof counts the physical values that a repair
creates. A separate general theorem explains why targets without short XOR relations
force extra intermediate values, and gives an exponential lower bound for preserving
source values during feedback removal. **Unrestricted MixColumns remains 75 to 88**;
the block-monotone lower bound remains 85.

## Five diagonal values cost more than a diagonal basis

[Five diagonals](FIVE_DIAGONALS.md) proves that supplying the four first-sheet rows and
five distinct nonzero diagonal values requires at least thirteen source gates, even
with arbitrary cancellation. The earlier augmented minimum twelve requested only
three independent diagonals. No thirteen-gate attainment claim is made here.

At twelve gates, the nine required ordinary masks and three entry directions exhaust
the budget. Physical relation rank then forces at least two even values outside the
diagonal, leaving room for at most one extra odd value. With so few odd values, the
available pair relations and even-only equations cannot provide the nine independent
gate equations needed. The proof uses ranks and populations, without listing circuits
or diagonal bases.

A ten-gate consumer admits only rank-three diagonal entry labels. The previous
[chronological repair](RANK_THREE.md) uses at most one extra source gate. At total 21,
a repair with no overhead contradicts the augmented minimum twelve. A repair that
needs the extra gate keeps three independent diagonal values and creates both a pair
sum and their three-term sum: five distinct physical diagonals. It would supply these
and the four first-sheet rows in at most twelve gates, contradicting the new lemma.
The known 22-gate construction attains the lower bound with ten consumer gates.

This closes all feedback patterns in that consumer-budget class. It does not settle
the unrestricted joint minimum: eleven or more consumer-bearing gates may change
which source information can be returned and how much source work is needed.

## A local ternary return is possible

The [specified ten-gate consumer](TERNARY_CONSUMER.md) produces all four required
own-triple rows and admits an early exit equal to the sum of three independent source
labels. It refutes a proposed local claim that every exit must already be one XOR
away. Its four entry labels have a three-term relation, a case omitted by an attempted
two-way division into repeated labels and four-term relations.

That local difficulty need not save work overall: computing the missing fourth entry
label during repair lets its later supplier be bypassed. The extra gate is recovered.
More broadly, the five-diagonal theorem proves the total joint obstruction without
needing to exclude every local ternary return.

Two secondary tools are retained: [entry matching](ENTRY_MATCHING.md) constrains
three-entry consumers, and [marked-wire duality](WIRE_DUALITY.md) rigorously identifies
original entry masks through an explicit XOR/copy network. It proves a repeated-label
restriction. The main five-diagonal proof does not depend on either tool.

## A general reason that sharing requires extra values

Let `T` contain `N` nonzero, non-input targets with no relation among three or four
distinct targets. In a reduced circuit on `d` coordinate inputs, let `A` count gates
whose values are not targets, and put `R=d+A`. [The helper-value theorem](SIDON_REPAIR.md)
gives

    N <= R + (R/4)(1+sqrt(4R-3)),
    A >= (4N/7)^(2/3)-d.

A non-target value can connect only one target pair. Targets formed from two non-target
values form an edge graph with no four-cycle; such a cycle would give a forbidden
four-target relation. Counting common neighbours bounds its edges. This counts actual
intermediates, rather than treating rank alone as a gate count.

The explicit binary family `t_x=(x,x^3)` over `GF(2^k)`, in dimension `d=2k`, has the
required relation properties by two field identities. It forces `Omega(2^(d/3))`
auxiliary gates. A fixed feedback circuit can supply each `t_x` with one source-side
exit, so any source-only realization preserving these values requires that many extra
source gates, even with full advance knowledge. **This is not an exponential gap
between full circuit optima:** the original consumer computation may be expensive.

The [balanced-basis repair theorem](GENERAL_REPAIR.md) still supplies the general upper
bound `h(d)=2^ceil(d/2)+2^floor(d/2)-d-2`, sharp at ranks three and four. Its exponential
source-replay dependence cannot be replaced by a universal linear bound. The upper
exponent `d/2` and fixed-family lower exponent `d/3` remain different.
[Online repair](ONLINE_REPAIR.md) separately matches the upper asymptotic order against
an adaptive adversary, and records the exact fixed-prefix full-circuit saving `d-2`.

## Next direction and review

The next joint target is a consumer with eleven gates. [Entry deletion and return rank](FEEDBACK_RANK.md)
permit only one independent returned direction outside the diagonal. Determine whether
that direction can reduce the first-sheet work enough to beat 22. The successful
mechanism in this phase was to count the additional physical values forced by repair,
not to assume that an optimal consumer cannot return useful information.

Reviews cover [five diagonals](reviews/five-diagonals-review.md),
[an additional independent check](reviews/five-diagonals-second-review.md),
[the explicit consumer](reviews/ternary-consumer-review.md),
[the helper-value bound](reviews/SIDON_REPLAY-review.md),
[online repair](reviews/online-repair-review.md),
[entry matching](reviews/entry-matching-review.md), and
[wire duality](reviews/wire-duality-review.md).
Earlier reviews of [general repair](reviews/general-repair-review.md),
[return rank](reviews/feedback-rank-review.md), [rank three](reviews/rank-three-review.md),
[the decorated separation](reviews/one-exit-review.md), and [mirror exits](reviews/mirror-review.md)
remain available.

The [new direct checker](check_ternary_consumer.py) evaluates one specified consumer,
its chronology, trace ranks, and the MixColumns label substitution;
[results](ternary-consumer-check.json) are saved. The prior
[six specified witnesses](check-results.json) remain unchanged. Universal bounds,
finite-field identities, and graph estimates are hand proofs, not computer-driven
case elimination.
