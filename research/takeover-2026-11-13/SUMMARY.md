# What changed in the takeover

**Current continuation after `ed374d1`, 2026-11-14:**
[charged forests separate global and local source directions](feedback/CHARGED_FRONTIER.md).
For t distinct traces in the remaining six-entry interface, forest charges have
quotient rank t-4, and repeated-class residual sectors have total dimension 6-t.
Their physical carriers are the subtrees joining each class's ports; repeated pairs
give paths. No trace can occur three times. Two repeated-even pairs and a separated
triangle/pair profile are also excluded. Source-own parity must be mixed, with 2–5
odd-own entries. Free-seeded replay and strict equal-trace series give further
physical-value restrictions. The twelve-consumer case remains open; the structural
identities alone are not gate-cost bounds. Reviews and precise scope are linked
from the current frontier.

A [specified exposure counterexample](feedback/TRACE_EXPOSURE_LIMIT.md) invalidates
an attempted global adjacency bound: local accumulator reorderings can change
unmarked helper values. The attempted all-odd repeated-trace closure is withdrawn;
that case remains open. The reviewed results above do not rely on this inference.

**Previous continuation after `8ab0b3e`, 2026-11-14:**
[the twelve-consumer problem now reduces to six target-live entries](feedback/SIX_ENTRY_FRONTIER.md).
Every outside-entry case and the target-live five-entry case are excluded below
total 22. The general mechanisms are affine-tree transfer with physical credits,
an odd-value forest forced by independent even mirror helpers, and chronological
replay through a free-coordinate section. The forest gives clean endpoints in the
seven-gate mirror and controls returns between separate roots. Difficult returns
need at most three extra replay gates but force four clean diagonals, contradicting
the thirteen-gate supplier bound. A separate source theorem excludes all-even-own
entry spaces at source cost below ten, at any consumer budget. The remaining
rank-five entry span has one even free direction and two odd nonclean cosets.
The six-entry case and larger consumer budgets remain open; MixColumns stays 75–88.
Proofs, coverage, independent reviews, and timing caveats are linked from the frontier.

**Previous continuation after `cfab8f6`, 2026-11-14:**
[the twelve-consumer structural frontier](feedback/TWELVE_CONSUMER_FRONTIER.md)
adds a general equality theorem: when quotient cost is saturated, projected physical
collisions are exactly selected entry-tree paths, and each actual nonclean label has
a unique physical pair. Gates outside the relaxed output cones must be quotient
coloops. A greedy chronological complement gives a general physical-value replay
bound. New source arguments force at least ten gates at entry rank at most four,
and at least fifteen for the source rows plus all seven clean diagonals (attainment
not asserted). A twelve-consumer candidate below 22 must have entry rank five,
at most two physical clean values, and at most one outside-cone gate, supporting
multiple useful returns. Target-live five-entry candidates require an exit crossing
the two components of a unique two-root fibre; six-entry candidates satisfy explicit
trace relations. A fixed seven-gate example refutes an unqualified extension of
even-wire separation. The twelve-consumer case and larger budgets remain open.
Reviews and exact hypotheses are linked from the new frontier.

**Previous continuation after `d8bfd65`:** [the eleven-consumer joint minimum is 22](feedback/ELEVEN_CONSUMER_CLOSED.md).
The physical fibre trees and marked-wire derivatives of a tight six-gate mirror close
all remaining eleven-consumer profiles. A new supplier theorem forbids six physical
values in one diagonal coset within eleven source gates, closing the last nonclean
return. The existing `(11,11)` construction attains 22. Together with the ten-consumer
case, any joint circuit below 22 now needs at least twelve consumer gates and at most
nine source gates; those larger budgets remain open.
The [preceding source-credit phase](feedback/FIVE_ENTRY_PROGRESS.md) supplied the general
credited replay theorem and closed the two- and three-nonclean five-entry cases.
The [preceding continuation](feedback/FOUR_DIAGONAL_FRONTIER.md) proved the sharp
four-diagonal source bound and closed the four-entry mixed class at 22.
The [previous continuation](feedback/ELEVEN_FRONTIER.md) established physical-collision
accounting, direct-return restrictions, and source cost twelve under clean confinement.
The preceding [five-diagonal result](feedback/FIVE_DIAGONALS.md) closed the ten-consumer
case at 22 even with feedback. Other established results include
[general rank-based repair](feedback/GENERAL_REPAIR.md),
[helper-value and source-repair lower bounds](feedback/SIDON_REPAIR.md),
[augmented minimum twelve and block-monotone 85](augmented/README.md),
[supplier closure](crossing/README.md), [rank-one exclusion](frontier/README.md),
[relation rank](tradeoff/README.md), and [entry deletion](compatibility/README.md).
The unrestricted MixColumns interval remains 75 to 88.
The [row-cost pass](row-cost/README.md)
proved exact local costs, source saturation, and completion geometry. The [earlier pass](continuation/README.md)
proved affine-completion bounds and a sparse counterexample to controlling savings by
hidden-gate count. The first-pass account below remains the history and foundation;
its next-direction assessment is superseded by the current summary.

The most useful advance is a way to force hidden work jointly. The previous repair theorem
could show that a cancellation needs a hidden operand, but many cancellations might use the
same operand. We now have a theorem limiting that sharing, and a stronger rank argument that
uses the output windows to make all uncounted partners disappear.

The unrestricted MixColumns interval remains **75 <= L <= 88**. The new statements are
general structural theorems and bounds for stated circuit classes. They have independent
machine reviews, not formal verification or human certification.

## Why some hidden work is unavoidable

Fix a maximal output window and some events whose values fill that window. At least one
operand of each event has support outside every output window; such an operand is hidden
from all outputs behind a later cancellation. Join two such operands when one selected
event XORs them.

Every connected component carries the same nonzero value outside the window. Choose the
window blocks that cannot coexist with that outside value in an output. Any local partner
must be zero there. Consequently the selected target values on those blocks have to come
entirely from the hidden operands. Their rank is a lower bound on the number of those
physical gates. This is [Theorem HR](directions/independent.md).

The proof solves a specific difficulty exposed by the earlier copy-rank failures: it
identifies counted gates as the only possible sources before using rank. It does not treat
rank of arbitrary available values as a gate count.

A complementary operand-forest theorem gives `t <= 2h-c` when the target values are independent
and distinct on each window block. A symbolic family attains the bound, including the
component correction if a forest replaces the tree. The construction explains precisely
why stronger general constants need additional hypotheses.

For MixColumns, any three of a sheet's four rows are independent on every block in that
sheet's window. This gives hidden-operand requirements `1,2,3,3` for one through four
output events in sheets 1,3,4,5,6,7. The bound applies even with other events elsewhere;
it cannot be summed across sheets without controlling shared operands.

## Sharing repair work is safe when its descendants are counted

An old sentence said repair chains reaching different sheets could not share without
changing their charged-family memberships. That was too strong: a shared block-7 piece
can remain uncharged. Theorem V itself used private chains and was unaffected.

[Joint reconstruction](directions/JOINT.md) now counts this sharing exactly for in-block
pieces. A shared piece is charged if any of its downstream uses charges it; merging several
charged copies saves their count minus one. Two distinct own-block triple sums can share
their common pair, saving one gate in the repair accounting. Combining this saving with HR
gives the class table in [the checkpoint](CHECKPOINT.md). For example, if the only visible
events are two outputs of a single sheet 4,5,6, or 7, then the circuit needs at least 83
gates, with arbitrarily many hidden events allowed.

When every output is itself an event, joint reconstruction alone still just bounds the
reconstructed circuit. The separate hidden-work theorem is essential.

## A global repair theorem, and its exact limitation

[Projection repair](directions/PROJECTION.md) cleans the original circuit simultaneously.
At every node it retains the block sets requested by downstream uses, intersects them
with operand supports, and reuses equal requested values. The distinct non-input requested
values `P` always admit an event-free execution. For reduced original gate values `V`:

    G >= B + |V minus P| - |P minus V|,

where B is any event-free lower bound for the target map. Original values no longer needed
are credited; genuinely missing clean values are paid for. The construction handles events
feeding events and repeated clean values without an event-processing order.

This is a repair guarantee, not an explanation of every optimal saving. An optimal
five-gate circuit on four inputs requests an extra clean value under the repair, while
another event-free wiring still uses five gates. The counterexample is proved and directly
verified. A simpler unbounded overcount disappears when equal projected values are merged.
The familiar sharp prefix family is attributed to the earlier Boyar–Find/Svensson construction.

## Assessment and what to pursue

The existing 10/13 local proofs, 83/84 monotone bounds, visible repair, and Theorem V survive
the independent reconstruction needed here. The 66-charge counterexample still blocks
unconditional distinct-charge counting. Interface-independent cut baselines, fixed-rule
transposes, and copy ranks retain the limitations recorded in the earlier phases; they
were not rerun or promoted to impossibility claims beyond their proved scope.

The most promising direction is HR: turn output support incompatibility into coordinates
where all uncounted partners vanish, then measure the target rank that remains. Extending
that argument to internal visible events and several windows is a real mathematical task.
The current theorems do not solve it. Repeating per-event accounting or optimizing a repair
that follows one wiring is less promising without a new structural reason.

## Review and verification

The primary agent reconstructed the repair arguments and checked both new directions.
An independent research agent (gpt-6-astra, xhigh) developed H and the sharp family; the
primary agent proposed the component projection-rank strengthening, which was proved in
the same note. Independent reviewers (gpt-6.1-terra and gpt-6.1-sol, xhigh) challenged the
claims. Their files record scope, corrections, and counterexamples. The sol reviewer also
reconstructed the foundational 84 argument from its actual local proof.

All universal results have hand arguments. The direct verifiers only construct and check
named examples; they search no circuit or configuration space. See [checks](checks/README.md).
